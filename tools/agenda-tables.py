#!/usr/bin/env python3
"""Rebuild a posted agenda's warrant-article table from the PDF's own geometry.

    python3 tools/agenda-tables.py --scan
    python3 tools/agenda-tables.py --board "Finance Committee" --year 2026
    python3 tools/agenda-tables.py --board "Finance Committee" --year 2026 --apply

Why this exists. CivicClerk serves each agenda two ways: a plain-text rendition
and the PDF itself. The plain text is what `CIVIC_AGENDAS` is built from, and
for an ordinary agenda it is fine. But where an agenda carries a table, the
plain text flattens it into one run-together list item **with the columns
interleaved** — wherever a cell wraps to a second line, that line is emitted
wherever it physically fell, which puts it inside the neighbouring cell:

    35 Select Board for Zoning Map Change: RC-2 to CMI or CTEC - 43 Nobadeer
    Planning Board Farm Road

is really article 35, sponsored by *Select Board for Planning Board*, to make a
*Zoning Map Change: RC-2 to CMI or CTEC - 43 Nobadeer Farm Road*. The words are
out of order, so no amount of splitting the stored string repairs it — a regex
just produces tidy-looking rows with the wrong text in them. The PDF has to be
read instead, and read as geometry rather than as text.

That part is easier than it sounds, because these tables are ruled: vertical
rules at x=95.6/145.0/235.0/561.4 and a horizontal rule every ~25.3pt, the same
in the 2025 and 2026 templates. So PyMuPDF's line-based table finder returns
true cells with no clustering heuristics and nothing to tune.

Four things that are not obvious and that this script handles:

- **A date can carry several postings, and CivicClerk labels Agenda Packets
  `type: Agenda` too.** March 4, 2025 offered a 2-page agenda and a 145-page
  packet. Scoring the candidates against the stored text picks the packet,
  because it contains the agenda plus everything else; so candidates are scored
  to rule out the unrelated ones, and then the *shortest* survivor wins.

- **A cell that overflows its ruled row gets its own ruled row**, with an empty
  Article cell — `['', 'al', '']` is the tail of "et al". Those fold back into
  the row above. Five of the eight 2026 agendas needed it and none of the ten
  2025 ones did, so a clean run proves nothing about the next.

- **A leading article number can be eaten as a list marker.** Where a row began
  a line, whatever built the stored HTML read the number as an ordered-list
  marker and consumed it. Two shapes, both real: February 5, 2026 opened a
  spurious nested `<ol>` mid-table and lost article 1's number; March 10, 2026
  started a new sibling `<li>`, lost article 8's number, and that stray item
  then swallowed the real agenda item 8, "Committee Reports". So the rebuild can
  *gain* content, and each gain is declared in RECOVERED below and asserted on,
  rather than being absorbed quietly into a total.

- **The table can run past its own list item.** Walk forward until every cell
  token is accounted for, or half a table gets left behind.

The check that makes this safe is a token comparison: every word of every
extracted cell must already be present in the stored text, allowing for what
the template itself adds (one literal "Article" per row) and drops (the four
scrambled header words). Passing it proves the rebuild is a re-ordering of the
posting rather than a paraphrase of it. Compare alphanumeric tokens only —
a raw word comparison trips over the added dashes and brackets, and over
`Owner&rsquo;s` in the stored text against `Owner's` in the PDF.

Output is a nested `<ol>`, which is the vocabulary `CIVIC_AGENDAS` already uses
(most agendas nest; the stylesheet styles level two lower-alpha). So this costs
no CSS and **ASSET_VER must not move** — it is a content change.

Requires PyMuPDF (`pip3 install pymupdf`), and only to read an agenda; the site
builds without it.
"""
import argparse
import ast
import collections
import html
import json
import os
import re
import shutil
import sys
import urllib.parse
import urllib.request

sys.path.append(os.path.expanduser('~/Library/Python/3.9/lib/python/site-packages'))

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(os.path.dirname(HERE), 'build.py')
API = 'https://nantucketma.api.civicclerk.com/v1'
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/125.0 Safari/537.36')

# The only table header seen so far, and the row format Frank chose for it:
# description first, sponsor in brackets. Any other header is reported and
# left alone — the row format for a new shape is his call, not this script's.
KNOWN_HEADER = ('article', 'primary sponsor', 'description')
HDR = re.compile(r'Article\s+Primary\s+Description\s+Sponsor')

# Article numbers the stored text lost to a stray list marker and the PDF puts
# back. Keyed by video id, so every gain is audited. Add to this rather than
# relaxing the token check.
RECOVERED = {'XsYH_4F2-T0': {'1': 1}}

# Agenda items a stray list marker swallowed, restored with the table.
RESTORED_ITEMS = {'Px8HsqBNiyE': 'Committee Reports'}

MONTHS = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
          'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}


# -- build.py -----------------------------------------------------------------

def literal(src, name):
    """The dict assigned to `name`, plus the exact source text of its block."""
    m = re.search(r'\n%s = \{\n.*?\n\}\n' % name, src, re.S)
    if not m:
        sys.exit('%s not found in build.py' % name)
    return ast.literal_eval(m.group(0).split('=', 1)[1].strip()), m.group(0)


def card_date(title):
    """The meeting date from a card title, e.g. 'Feb. 5th, 2026 ...'."""
    m = re.match(r'([A-Z][a-z]{2})\.? (\d+)[a-z]{0,2},? (\d{4})', title)
    if not m:
        return None
    return '%s-%02d-%02d' % (m.group(3), MONTHS[m.group(1)], int(m.group(2)))


def esc(t):
    if '"' in t or '\\' in t:
        sys.exit('cell holds a quote or backslash, which build.py cannot take: %r' % t)
    return t.replace('&', '&amp;').replace("'", '&rsquo;')


def toks(t):
    """Alphanumeric content tokens; punctuation and markup discarded."""
    raw = html.unescape(re.sub(r'<[^>]+>', ' ', t))
    return collections.Counter(
        w for w in (re.sub(r'[^0-9A-Za-z]', '', x).lower() for x in raw.split()) if w)


def wrap(key, body):
    """One CIVIC_AGENDAS entry, wrapped to the data block's 99-byte lines."""
    out, line = [' "%s":' % key], ''
    for w in body.split(' '):
        cand = (line + ' ' + w) if line else w
        if len(('  "%s "' % cand).encode()) > 99 and line:
            out.append('  "%s "' % line)
            line = w
        else:
            line = cand
    out.append('  "%s",' % line)
    return '\n'.join(out)


# -- CivicClerk ---------------------------------------------------------------

def get(url, binary=False):
    req = urllib.request.Request(url, headers={'User-Agent': UA,
                                               'Accept': '*/*' if binary else 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return data if binary else json.loads(data)


def events(category, start, end):
    """Every event of this category in [start, end), following the page cap."""
    flt = ("categoryName eq '%s' and startDateTime ge %sT00:00:00Z "
           "and startDateTime lt %sT00:00:00Z" % (category.replace("'", "''"), start, end))
    out, skip = [], 0
    while True:
        url = '%s/Events?%s' % (API, urllib.parse.urlencode(
            {'$filter': flt, '$count': 'true', '$top': 100,
             '$orderby': 'startDateTime', '$skip': skip}))
        page = get(url)
        got = page.get('value', [])
        out += got
        if not got or len(out) >= int(page.get('@odata.count', len(out))):
            return out
        skip += len(got)


def agenda_files(event):
    return [f for f in (event.get('publishedFiles') or []) if f.get('type') == 'Agenda']


def pdf_bytes(file_id):
    return get('%s/Meetings/GetMeetingFileStream(fileId=%d,plainText=false)' % (API, file_id),
               binary=True)


# -- the PDF ------------------------------------------------------------------

def tables(pdf_path):
    """Every ruled table in the file, as (header, rows). Rows are 3-tuples."""
    import fitz
    doc = fitz.open(pdf_path)
    found, header = [], None
    clean = lambda c: re.sub(r'\s+', ' ', (c or '').replace('\n', ' ')).strip()
    for page in doc:
        for t in page.find_tables(strategy='lines').tables:
            data = [[clean(c) for c in row] for row in t.extract()]
            if not data:
                continue
            first = ' '.join(data[0]).lower()
            if 'article' in first and ('sponsor' in first or 'description' in first):
                header, body = data[0], data[1:]
            elif header and len(data[0]) == len(header):
                body = data                    # the table going on over a page break
            else:
                continue
            rows = [tuple(r[:3]) for r in body
                    if len(r) >= 3 and any(r) and not ' '.join(r).lower().startswith('article primary')]
            found.append((header, rows))
    doc.close()
    if not found:
        return None, []
    return found[0][0], fold(sum((f[1] for f in found), []))


def fold(rows):
    """Fold a continuation row — blank Article cell — into the row above it."""
    out = []
    for r in rows:
        if not r[0].strip() and out:
            prev = list(out[-1])
            for i in (1, 2):
                if r[i].strip():
                    prev[i] = (prev[i] + ' ' + r[i]).strip()
            out[-1] = tuple(prev)
        else:
            out.append(r)
    return out


def pick(candidates, stored, workdir):
    """The posting whose PDF is this agenda: the shortest plausible one.

    Scoring alone picks an Agenda Packet, whose first pages are the agenda and
    whose remaining hundred are not, so score only to rule out the unrelated.
    """
    import fitz
    want = shingles(stored)
    best = []
    for file_id in candidates:
        path = os.path.join(workdir, '%d.pdf' % file_id)
        if not os.path.exists(path):
            open(path, 'wb').write(pdf_bytes(file_id))
        doc = fitz.open(path)
        text = '\n'.join(p.get_text() for p in doc)
        pages = doc.page_count
        doc.close()
        cover = len(want & shingles(text)) / max(1, len(want))
        if cover >= 0.20:
            best.append((pages, file_id, path, cover))
    if not best:
        return None, None, 0.0
    best.sort()
    _, file_id, path, cover = best[0]
    return file_id, path, cover


def shingles(text, n=6):
    w = re.sub(r'[^a-z0-9 ]', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', text)).lower()).split()
    return {' '.join(w[i:i + n]) for i in range(len(w) - n + 1)}


# -- rebuilding ---------------------------------------------------------------

def rebuild(vid, stored, rows):
    """The agenda with its flattened table replaced by a nested list."""
    body = ''.join('<li>Article %s &ndash; %s (%s)</li>' % (esc(a), esc(d), esc(s))
                   for a, s, d in rows)
    i = 0
    while True:
        j = stored.index('<li>', i)
        end = stored.index('</li>', j)
        if HDR.search(stored[j:end]):
            break
        i = end + 5
    lead = HDR.split(stored[j + 4:end])[0].strip()

    # How far the table actually runs. A stray list marker can push the rest of
    # it into a nested list inside this item, or into the next item along with
    # whatever that item was supposed to say.
    seg_end = end + 5
    if '<ol>' in stored[j:end]:
        seg_end = stored.index('</ol></li>', j) + len('</ol></li>')
    want = collections.Counter()
    for r in rows:
        want += toks(' '.join(r))
    # A recovered article number is by definition absent from the stored text,
    # so looking for it would walk this search off the end of the agenda.
    want -= collections.Counter(RECOVERED.get(vid, {}))
    tail = ''
    while (want - toks(stored[j:seg_end])) and '<li>' in stored[seg_end:]:
        seg_end = stored.index('</li>', stored.index('<li>', seg_end)) + 5
        item = RESTORED_ITEMS.get(vid)
        if item and item in stored[j:seg_end]:
            tail = '<li>%s</li>' % item
    new = stored[:j] + '<li>%s<ol>%s</ol></li>%s' % (lead, body, tail) + stored[seg_end:]

    n = len(rows)
    lhs = toks(new) - collections.Counter({'article': n})
    rhs = (toks(stored) - collections.Counter({'article': 1, 'primary': 1,
                                               'description': 1, 'sponsor': 1})
           + collections.Counter(RECOVERED.get(vid, {})))
    if lhs != rhs:
        sys.exit('%s: the rebuild is not a re-ordering of the posting.\n'
                 '  gained: %r\n  lost:   %r\n'
                 'If the gain is an article number the stored text dropped, add it to '
                 'RECOVERED; otherwise the extraction is wrong.'
                 % (vid, dict(lhs - rhs), dict(rhs - lhs)))
    if new.count('<li>') != new.count('</li>') or new.count('<ol>') != new.count('</ol>'):
        sys.exit('%s: unbalanced list tags after rebuild' % vid)
    return new


# -- commands -----------------------------------------------------------------

def scan(agendas, boards):
    where = {v: (b, y, t) for b, ys in boards.items() for y, ms in ys.items() for v, t, _ in ms}
    hits = [k for k, v in agendas.items() if HDR.search(v)]
    if not hits:
        print('No stored agenda holds a flattened table.')
        return
    print('%d stored agenda(s) hold a flattened table:\n' % len(hits))
    for k in hits:
        board, year, title = where.get(k, ('(not on a board list)', '', ''))
        size = max((len(li) for li in re.findall(r'<li>(.*?)</li>', agendas[k], re.S)
                    if HDR.search(li)), default=0)
        print('  %-12s %-34s %-44s %5d chars' % (k, html.unescape(board)[:34], title[:44], size))
    print('\nRebuild them with --board/--year, or --id.')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--scan', action='store_true',
                    help='list stored agendas holding a flattened table; touches nothing')
    ap.add_argument('--board', help='board name as CIVIC_BOARDS spells it')
    ap.add_argument('--year', type=int, help='restrict to one year')
    ap.add_argument('--id', nargs='*', default=[], help='specific video ids')
    ap.add_argument('--category', help='CivicClerk categoryName, if it differs from --board')
    ap.add_argument('--apply', action='store_true', help='write the rebuilt entries into build.py')
    ap.add_argument('--workdir', default=os.path.join(HERE, '.agenda-pdfs'),
                    help='where downloaded PDFs are kept')
    args = ap.parse_args()

    src = open(BUILD, encoding='utf-8').read()
    agendas, block = literal(src, 'CIVIC_AGENDAS')
    boards, _ = literal(src, 'CIVIC_BOARDS')

    if args.scan or not (args.board or args.id):
        return scan(agendas, boards)

    targets = []
    if args.board:
        key = next((b for b in boards if html.unescape(b) == html.unescape(args.board)), None)
        if key is None:
            sys.exit('no such board: %s\n  %s' % (args.board,
                                                  '\n  '.join(sorted(html.unescape(b) for b in boards))))
        for year, meetings in sorted(boards[key].items()):
            if args.year and year != args.year:
                continue
            targets += [(v, t, year) for v, t, _ in meetings]
        category = args.category or html.unescape(key)
    else:
        where = {v: (b, y, t) for b, ys in boards.items() for y, ms in ys.items() for v, t, _ in ms}
        targets = [(v, where[v][2], where[v][1]) for v in args.id if v in where]
        category = args.category or html.unescape(where[targets[0][0]][0])

    todo = [(v, t, y) for v, t, y in targets if v in agendas and HDR.search(agendas[v])]
    if not todo:
        print('Nothing to do: no stored agenda in that scope holds a flattened table.')
        return
    print('%d agenda(s) to rebuild, category %r\n' % (len(todo), category))

    os.makedirs(args.workdir, exist_ok=True)
    dates = sorted({card_date(t) for _, t, _ in todo if card_date(t)})
    found = {}
    for ev in events(category, min(dates), max(dates)[:8] + '%02d' % (int(max(dates)[8:]) + 1)):
        for f in agenda_files(ev):
            found.setdefault(ev['startDateTime'][:10], []).append(f['fileId'])

    rebuilt, skipped = {}, []
    for vid, title, year in todo:
        date = card_date(title)
        cands = found.get(date, [])
        if not cands:
            skipped.append((vid, title, 'no CivicClerk posting on %s' % date))
            continue
        file_id, path, cover = pick(cands, agendas[vid], args.workdir)
        if not path:
            skipped.append((vid, title, 'no posting on %s matches the stored agenda' % date))
            continue
        header, rows = tables(path)
        if not rows:
            skipped.append((vid, title, 'PDF file%d holds no ruled table' % file_id))
            continue
        shape = tuple(h.strip().lower() for h in header)
        if shape != KNOWN_HEADER:
            skipped.append((vid, title, 'unfamiliar table header %r — ask before rendering' % (header,)))
            continue
        rebuilt[vid] = rebuild(vid, agendas[vid], rows)
        note = ''
        if vid in RECOVERED:
            note = '  [recovered article %s]' % ','.join(RECOVERED[vid])
        elif vid in RESTORED_ITEMS:
            note = '  [restored agenda item: %s]' % RESTORED_ITEMS[vid]
        print('  %-12s %s  file%-6d %2d rows%s' % (vid, date, file_id, len(rows), note))

    for vid, title, why in skipped:
        print('  %-12s SKIPPED — %s' % (vid, why))
    if not rebuilt:
        return
    print('\n%d agenda(s) rebuilt, %d rows.' % (len(rebuilt), sum(
        len(re.findall(r'<li>Article ', v)) for v in rebuilt.values())))

    if not args.apply:
        print('Nothing written. Re-run with --apply, or paste these entries:\n')
        for vid, value in rebuilt.items():
            print(wrap(vid, value))
        return

    block2 = block
    for vid, value in rebuilt.items():
        pat = re.compile(r'\n "%s":\n(?:  "[^"\n]*"\n)*  "[^"\n]*",\n' % re.escape(vid))
        hit = pat.search(block2)
        if not hit:
            sys.exit('%s: could not locate its entry to replace' % vid)
        block2 = block2[:hit.start()] + '\n' + wrap(vid, value) + '\n' + block2[hit.end():]

    check = ast.literal_eval(block2.split('=', 1)[1].strip())
    if list(check) != list(agendas) or len(check) != len(agendas):
        sys.exit('the entry set or its order changed')
    for k in agendas:
        if check[k] != rebuilt.get(k, agendas[k]):
            sys.exit('value mismatch on %s' % k)
    before = sum(1 for l in block.split('\n') if len(l.encode()) > 99)
    after = sum(1 for l in block2.split('\n') if len(l.encode()) > 99)
    if after != before:
        sys.exit('over-long lines %d -> %d; the wrapper is wrong' % (before, after))

    shutil.copy2(BUILD, BUILD + '.bak-agenda-tables')
    open(BUILD, 'w', encoding='utf-8').write(src.replace(block, block2))
    print('\nWritten to build.py (previous copy at build.py.bak-agenda-tables).')
    print('ASSET_VER must not move — this is a content change. Now run: python3 build.py')


if __name__ == '__main__':
    main()
