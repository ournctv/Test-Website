#!/usr/bin/env python3
"""Turn a Town Meeting warrant PDF into the HTML literal that build.py holds.

    python3 tools/warrant-to-html.py WARRANT.pdf --name TM_WARRANT_2027 > out.py

Paste the result into build.py beside TM_WARRANT_2026 and add the meeting's
video id to CIVIC_DOCS. Nothing else has to change: the button, the overlay and
the styling are already there.

Why this exists rather than a copy and paste of the PDF's text. The Town marks
proposed bylaw edits by drawing rectangles rather than by styling the text -- a
grey box behind new language, a hairline through language to be struck. Any
ordinary text extraction loses both and welds the old wording to the new; "as
measured by the exterior interior faces of the exterior walls" is one real line
of the 2026 warrant. So every character is tested against its own page's
rectangles and comes out as <del> or <ins>. Character rather than word
granularity because several of the edits turn on a single mark: the warrant
deletes a period and adds a semicolon in the same breath.

The other thing that has to survive is shape. The bylaw lists hang their
wrapped lines off a marker in a narrow left column, and the compensation
schedules are real grids. Both arrive from the PDF as cells sharing a baseline,
so one pass handles them: a row with one cell is prose, a row with more is a
table row, and a prose line sitting wholly inside one of that table's columns
is that cell going on.

Some of the Town's warrants are photocopies rather than born-digital PDFs:
every page one 300 dpi image with an OCR layer under it, and not a rectangle
in the file. scanned() spots that and the wash behind new language is then
measured off the pixels instead, which is worth knowing about, because a
rectangle test run over a scan reports a warrant that amends nothing. Such a
warrant's OCR also loses an opening bracket or quote that begins a line; the
ink is still in the image and Shading.opener() puts it back. Strikeouts are
the limit of this: on a scan a rule through a word is just more ink, so if a
scanned warrant does propose deletions they will come through as ordinary
text. Both of the warrants read this way propose none.

Check the output before pasting it. The page geometry below -- the footer
band, the text column's edges -- is the 2026 warrant's, and a differently
typeset year may need it adjusted.

Requires PyMuPDF (`pip3 install pymupdf`). It is not needed to build the site,
only to read a new warrant.
"""
import argparse
import re
import statistics

import fitz

# The text column, in points. The running footer is found rather than assumed:
# the 2026 warrant's sat in the bottom 55pt and the 2025 one's reaches 57pt
# higher, and a band guessed from one of them silently keeps "Page 137 Town of
# Nantucket 2025 Annual Town Meeting Warrant" in the middle of an article.
TEXT_LEFT, TEXT_RIGHT = 71.0, 540.0

# Reading a scan. A photocopied warrant holds no rectangles at all, so the
# wash behind new language has to be measured off the page image instead. On
# the November 2025 Special Town Meeting warrant a washed background reads 212
# and bare paper 255, which leaves the line between them wide. The median of
# the background is the statistic to take: the wash is shorter than the line's
# bounding box, so there is always white above and below it, and ink only
# darkens, so neither the lightest nor the darkest pixel says anything.
SHADE_MAX, SHADE_ZOOM = 235, 3.0

# The same scan's OCR drops an opening bracket or quote that begins a line --
# "(Brian Borgeson, et al)" comes through without its bracket, ten times over
# the document. The glyph is still in the image, so it is restored from the
# ink standing to the left of the first character the OCR did find, rather
# than guessed at from the punctuation that balances. Which glyph it was is
# its height: a bracket runs nearly the whole line, a quote sits in the top
# fifth of it.
INK_DARK, LEFT_PAD = 128, 7.0

ENT = (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"))
SMART = {"‘": "&rsquo;", "’": "&rsquo;", "“": "&ldquo;",
         "”": "&rdquo;", "–": "&ndash;", "—": "&mdash;",
         "…": "&hellip;", " ": " ", "•": "&bull;",
         "▪": "&bull;", "ﬁ": "fi", "ﬂ": "fl"}

ARTICLE = re.compile(r"^ARTICLE\s+\d+[A-Z]?$")
PAREN = re.compile(r"^\(.+\)$")
SPLIT = re.compile(r"[0-9A-Za-z]-$")
LOOSE = re.compile("(?<=[A-Za-z])\u2019 (?=s\\b)")
SEAM = re.compile(r"</(ins|del)>( ?)<\1>")


# ---------------------------------------------------------------- reading

def marks(page):
    """The page's highlight boxes and strikeout hairlines.

    Both have to be picked out of the rest of the page furniture. A warrant
    with real tables draws their rules as filled rectangles too: the 2025 one
    has 1,828 black slivers no wider than a point (the vertical borders) and
    530 white blocks the width of a column (the cell fills). So a highlight is
    a box with an actual colour -- lighter than black, darker than white --
    and a strike has to be wide enough to cross a word. Whether either one
    lands on any text is settled later, by where it sits.
    """
    strikes, boxes = [], []
    for item in page.get_drawings():
        if item["type"] != "f":
            continue
        r = fitz.Rect(item["rect"])
        fill = item["fill"]
        if r.height < 2 and r.width > 2:
            strikes.append(r)
        elif 8 < r.height < 50 and r.width > 2 and fill and 0.4 <= min(fill) < 0.97:
            boxes.append(r)
    return strikes, boxes


def scanned(doc):
    """Whether this warrant is a photocopy rather than a born-digital PDF.

    Every page one full-page image and not a drawing in the file. Both of the
    Annual Town Meeting warrants fail the first half of that at the first
    page; the Special Town Meeting one passes on all thirteen. It matters
    because marks() then has nothing to find and would report a warrant with
    no amendments at all, which is exactly the silence worth avoiding.
    """
    return not any(page.get_drawings() for page in doc) and \
        all(page.get_images() for page in doc)


class Shading(object):
    """A scanned page's grey wash, standing in for marks()' rectangles."""

    def __init__(self, page, zoom=SHADE_ZOOM):
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom),
                              colorspace=fitz.csGRAY)
        self.z, self.w, self.h = zoom, pix.width, pix.height
        self.buf = pix.samples

    def _column(self, x0, x1, y0, y1, keep):
        a, b = int(x0 * self.z), max(int(x1 * self.z), int(x0 * self.z) + 1)
        a, b = max(a, 0), min(b, self.w)
        out = []
        for py in range(max(int(y0 * self.z), 0), min(int(y1 * self.z), self.h)):
            row = self.buf[py * self.w:(py + 1) * self.w]
            out += [(py / self.z, v) for v in row[a:b] if keep(v)]
        return out

    def boxed(self, bbox, band):
        """Whether the paper behind one glyph is washed.

        The glyph's own x-range, read over the whole line's height so that a
        letter filling its cell still has background to sample. Ink is thrown
        away before the median is taken.
        """
        vals = [v for _, v in
                self._column(bbox[0], bbox[2], band[1], band[3], lambda v: v > 190)]
        return bool(vals) and statistics.median(vals) < SHADE_MAX

    def inked(self, bbox):
        """Whether anything is printed left of the line's first character.

        A dropped bracket is still in the image, so this is where one would
        be. It is only ever a hint: a scanned table prints its rules, so
        every cell has ink to its left, and the scan speckles the margin as
        well. restore_openers() decides from the punctuation; this says where
        the missing glyph can have stood.
        """
        x0, y0, _, y1 = bbox
        ink = self._column(x0 - LEFT_PAD, x0, y0, y1, lambda v: v < INK_DARK)
        return len(ink) > 24


def running_band(doc):
    """The y above which the repeated page furniture sits.

    A running footer is a line near the bottom that says the same thing page
    after page, once its page number is taken out. Anything at or below the
    highest one is dropped.
    """
    from collections import Counter
    seen, lowest = Counter(), {}
    for page in doc:
        edge = page.rect.height * 0.85
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                top = line["bbox"][1]
                if top < edge:
                    continue
                text = "".join(s["text"] for s in line["spans"])
                key = re.sub(r"[\divxlc]+", "#", text.strip().lower())
                if not key:
                    continue
                seen[key] += 1
                lowest[key] = min(lowest.get(key, top), top)
    if not doc.page_count:
        return 0.0
    repeats = [lowest[k] for k, n in seen.items() if n >= doc.page_count * 0.4]
    return min(repeats) - 1 if repeats else doc[0].rect.height


def state(bbox, strikes, boxes, shade=None, band=None):
    x0, y0, x1, y1 = bbox
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    # a strike crosses the middle of the glyph; an underline would sit at or
    # below y1, so the band stops well above the baseline
    struck = any(s.x0 - 0.5 <= cx <= s.x1 + 0.5
                 and y0 + 0.2 * (y1 - y0) <= s.y0 <= y0 + 0.8 * (y1 - y0)
                 for s in strikes)
    if shade is not None:
        boxed = shade.boxed(bbox, band)
    else:
        boxed = any(b.x0 - 0.5 <= cx <= b.x1 + 0.5 and b.y0 - 2 <= cy <= b.y1 + 2
                    for b in boxes)
    return "del" if struck else "ins" if boxed else ""


def read(path):
    """Every line of every page, as runs of plain, struck and new text."""
    doc = fitz.open(path)
    foot = running_band(doc)
    scan = scanned(doc)
    pages = []
    for page in doc:
        strikes, boxes = marks(page)
        shade = Shading(page) if scan else None
        lines = []
        for block in page.get_text("rawdict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                if line["bbox"][1] >= foot:
                    continue
                runs, cur, kind = [], "", None
                for span in line["spans"]:
                    for ch in span["chars"]:
                        k = state(ch["bbox"], strikes, boxes, shade,
                                  line["bbox"])
                        # a space between two runs of one kind belongs to that
                        # run, so "fully enclosed" stays one strike
                        if ch["c"] == " " and kind is not None:
                            cur += " "
                            continue
                        if k != kind:
                            if cur:
                                runs.append([kind or "", cur])
                            cur, kind = "", k
                        cur += ch["c"]
                if cur:
                    runs.append([kind or "", cur])
                if "".join(t for _, t in runs).strip():
                    lines.append({"runs": runs,
                                  "x": round(line["bbox"][0], 1),
                                  "x1": round(line["bbox"][2], 1),
                                  "y": round(line["bbox"][1], 1),
                                  "ink": shade.inked(line["bbox"])
                                  if shade is not None else False})
        pages.append(lines)
    if scan:
        restore_openers(pages)
        close_possessives(pages)
    return pages


def close_possessives(pages):
    """Close up the space a scan's OCR leaves inside a possessive.

    "Nantucket' s original renting" is the reading; "Nantucket's original
    renting" is what the page says, four lines above where it says it
    properly. Only a lone "s" is closed up: a closing quote can be followed
    by a word, but never by a word one letter long.
    """
    for page in pages:
        for line in page:
            for run in line["runs"]:
                run[1] = LOOSE.sub("’", run[1])
    return pages


def restore_openers(pages):
    """Put back the brackets and quotes a scan's OCR dropped at a line start.

    Ink in the margin says a glyph went missing but not which one, and it
    says it far too often: a scanned table prints its rules, so every cell
    has ink to its left. The punctuation is what settles it. A ")" with
    nothing open before it, or a closing quote that never opened, is an
    opener the OCR lost, and it belongs at the front of the last inked line
    at or before the mark -- the bracket of "(It is the intent of this bylaw"
    closes two lines further on. A line that only looked damaged is never
    chosen, because nothing went unbalanced for it to repair.
    """
    lines = [ln for page in pages for ln in page]
    shuts = {")": "(", "”": "“"}
    depth = {"(": 0, "“": 0}
    home = None
    for n, ln in enumerate(lines):
        if ln["ink"]:
            home = n
        for ch in "".join(t for _, t in ln["runs"]):
            if ch in depth:
                depth[ch] += 1
            elif ch in shuts:
                shut = shuts[ch]
                if depth[shut]:
                    depth[shut] -= 1
                    continue
                # nothing opened this one, so its opener was lost. Stay near:
                # a mark reaches back over the rest of its own sentence, not
                # over the page.
                at = lines[home] if home is not None and n - home < 4 else ln
                at["runs"][0][1] = shut + at["runs"][0][1]
                home = None
    return pages


# ---------------------------------------------------------------- writing

def esc(t):
    for a, b in ENT:
        t = t.replace(a, b)
    for a, b in SMART.items():
        t = t.replace(a, b)
    # The warrant is mostly typeset with curly quotes but drops into straight
    # ones about twenty times. None may stay straight: the blocks are stored in
    # build.py as single-quoted literals carrying double-quoted class
    # attributes, so a bare quote of either kind would break the file.
    out = []
    for j, c in enumerate(t):
        if c == "'":
            out.append("&rsquo;")
        elif c == '"':
            before = t[j - 1] if j else " "
            out.append("&ldquo;" if before.isspace() or before == "(" else "&rdquo;")
        elif ord(c) < 127:
            out.append(c)
        else:
            out.append("&#%d;" % ord(c))
    return "".join(out)


def runs_html(runs):
    out = []
    for kind, text in runs:
        t = esc(text)
        out.append(t if not kind or not t.strip() else "<%s>%s</%s>" % (kind, t, kind))
    return "".join(out)


def knit(parts):
    """Join the lines of a paragraph, honouring a word broken at a hyphen.

    A line ends in a hyphen because the word was split there -- a break at a
    space leaves no hyphen behind -- so the next line carries straight on.
    Otherwise the warrant comes out saying "non- substantive" and "One- half".
    Tags can stand between the hyphen and the end of a piece, so they are
    looked through; a dash is an entity by this point and does not count.

    A splitting hyphen follows a letter or a digit. The one in the General
    Court's ":-", which the warrant uses whenever it amends a statute by
    striking out words, does not, and the space after it is real.
    """
    out = ""
    for part in parts:
        if out and not SPLIT.search(re.sub(r"<[^>]+>", "", out).rstrip()):
            out += " "
        out += part
        # New or struck language that runs on over a line break is one run,
        # not two: left as two, the space between them is unmarked and the
        # grey behind a highlighted paragraph comes out in stripes.
        out = SEAM.sub(lambda m: m.group(2), out)
    return out.strip()


def flat(runs):
    return "".join(t for _, t in runs).strip()


def allcaps(text):
    letters = [c for c in text if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters)


def centred(cell):
    """A line standing on its own in the middle of the column.

    Equal margins alone is not enough: a long indented line of body text
    happens to sit mid-column too, and one bylaw heading was read as centred
    and broken off its own second line that way. A real centred line also has
    a wide margin to its left.
    """
    left, right = cell["x"] - TEXT_LEFT, TEXT_RIGHT - cell["x1"]
    return left > 40 and abs(left - right) < 14


def columns(block):
    """Column x-ranges for a run of table rows.

    Grouped by left edge, then adjacent groups are merged where their cells
    share a right edge instead: the schedules right-align their money, so
    "$600.00" and "Up to $80.00" start in different places and end in the same
    one. Overlap alone cannot be the test -- one long label in the first column
    would otherwise swallow the second.
    """
    cells = sorted((c for b in block for c in b["cells"]), key=lambda c: c["x"])
    groups = []
    for c in cells:
        if groups and c["x"] - groups[-1][0]["x"] < 6:
            groups[-1].append(c)
        else:
            groups.append([c])
    merged = True
    while merged and len(groups) > 1:
        merged = False
        for j in range(len(groups) - 1):
            both = groups[j] + groups[j + 1]
            ends = [c["x1"] for c in both]
            if max(ends) - min(ends) < 8:
                groups[j:j + 2] = [both]
                merged = True
                break
    return [[min(c["x"] for c in g), max(c["x1"] for c in g)] for g in groups]


def column_of(cell, cols):
    mid = (cell["x"] + cell["x1"]) / 2
    for j, (a, b) in enumerate(cols):
        if a - 1 <= mid <= b + 1:
            return j
    return min(range(len(cols)), key=lambda j: abs(cols[j][0] - cell["x"]))


def body_html(pages):
    """The warrant as a list of top-level HTML blocks."""
    # The cover and the address page are centred lines, not prose: they keep
    # their own line breaks rather than being flowed into paragraphs.
    cover = ["<p>%s</p>" % runs_html(ln["runs"]).strip()
             for p in pages[:2] for ln in sorted(p, key=lambda l: l["y"])]

    rows = []
    for pno, page in enumerate(pages[2:], start=2):
        by_y = {}
        for ln in page:
            key = next((k for k in by_y if abs(k - ln["y"]) < 3), ln["y"])
            by_y.setdefault(key, []).append(ln)
        for y in sorted(by_y):
            rows.append({"page": pno, "y": y,
                         "cells": sorted(by_y[y], key=lambda c: c["x"])})

    html = ['<header class="warrant-doc__cover">%s</header>' % "".join(cover)]
    para, para_x, prev_y, prev_page = [], None, None, None
    i = 0

    def flush():
        if para:
            html.append("<p>%s</p>" % knit(para))
            del para[:]

    while i < len(rows):
        row = rows[i]
        cells = row["cells"]
        # A blank line in the PDF shows up as a jump in baseline pitch, which
        # runs 13.5 to 14.3 inside a paragraph and 16 or more between them. A
        # page break says nothing either way: paragraphs run across pages.
        gap = None if prev_y is None or row["page"] != prev_page else row["y"] - prev_y

        if len(cells) == 1:
            cell = cells[0]
            text = flat(cell["runs"])
            if ARTICLE.match(text):
                flush()
                # The article's subject follows in parentheses, and seventeen
                # of the 2026 warrant's run to a second or third line, so read
                # on until the bracket closes rather than taking one line.
                sub, k = "", i + 1
                while k < len(rows) and len(rows[k]["cells"]) == 1 and k - i <= 4:
                    nxt = flat(rows[k]["cells"][0]["runs"])
                    if not sub and not nxt.startswith("("):
                        break
                    sub = knit([sub, nxt])
                    k += 1
                    if sub.endswith(")"):
                        break
                if PAREN.match(sub):
                    i = k - 1
                else:
                    sub = ""
                html.append('<h3 class="warrant-doc__art">%s%s</h3>'
                            % (esc(text), "<span>%s</span>" % esc(sub) if sub else ""))
                prev_y, prev_page = row["y"], row["page"]
                i += 1
                continue

            # the sponsor line that closes an article. It names whoever moved
            # the article, so it reads as a name and not as a sentence: the
            # Use Chart's "(Legend: "Y" = Permitted by right; ...)" stands
            # alone in brackets in the same way and is not one.
            if PAREN.match(text) and len(text) < 120 and cell["x"] < 110 \
                    and not set(":;=") & set(text) \
                    and (gap is None or gap > 15):
                flush()
                html.append('<p class="warrant-doc__by">%s</p>' % runs_html(cell["runs"]))
                prev_y, prev_page = row["y"], row["page"]
                i += 1
                continue

            caps = centred(cell) and allcaps(text)
            # The bylaw articles put a defined term in capitals on its own line
            # and run the definition straight on underneath with no blank line,
            # which would otherwise read as one paragraph beginning in shouted
            # capitals. The stormwater article alone has sixty of them. A run
            # of capitalised lines is the heading; the comma test keeps the
            # list of FIRM map panel numbers out of it.
            term = []
            if not caps and allcaps(text) and len(text) <= 60 and not text.endswith(","):
                k = i
                while k < len(rows) and len(rows[k]["cells"]) == 1:
                    t = flat(rows[k]["cells"][0]["runs"])
                    c = rows[k]["cells"][0]
                    if not (allcaps(t) and len(t) <= 60 and not t.endswith(",")
                            and abs(c["x"] - cell["x"]) < 4
                            and rows[k]["page"] == row["page"]
                            and (k == i or rows[k]["y"] - rows[k - 1]["y"] < 15)):
                        break
                    term.append(rows[k])
                    k += 1
                nxt = rows[k] if k < len(rows) else None
                if not (nxt and len(nxt["cells"]) == 1
                        and nxt["page"] == row["page"]
                        and abs(nxt["cells"][0]["x"] - cell["x"]) < 4
                        and nxt["y"] - rows[k - 1]["y"] < 15
                        and not allcaps(flat(nxt["cells"][0]["runs"]))):
                    term = []
            if term:
                flush()
                html.append('<p class="warrant-doc__term">%s</p>'
                            % " ".join(runs_html(r["cells"][0]["runs"]).strip()
                                       for r in term))
                prev_y, prev_page = term[-1]["y"], term[-1]["page"]
                i += len(term)
                continue

            # Indentation alone does not start a paragraph: an article opens
            # with a first-line indent, and the bylaw lists hang their wrapped
            # lines in the other direction. Only a blank line does -- except
            # across a page break, where there is no pitch to read and the
            # indent is all there is to go on.
            if para and (caps or (gap is None and abs(cell["x"] - para_x) > 4)
                         or (gap is not None and gap > 15)):
                flush()
            if not para:
                para_x = cell["x"]
            para.append(runs_html(cell["runs"]).strip())
            if caps:
                flush()
            prev_y, prev_page = row["y"], row["page"]
            i += 1
            continue

        flush()
        block = []
        while i < len(rows):
            r = rows[i]
            if len(r["cells"]) > 1:
                block.append(r)
                prev_y, prev_page = r["y"], r["page"]
                i += 1
                continue
            # A single line goes on with the cell above it only if it sits
            # wholly inside one column. A line that spans several -- the
            # sentence that follows the table, say -- ends the block instead.
            c = r["cells"][0]
            cols = columns(block)
            j = column_of(c, cols)
            if c["x"] >= cols[j][0] - 1 and c["x1"] <= cols[j][1] + 1 \
                    and r["page"] == prev_page and r["y"] - prev_y < 15:
                block[-1]["cells"].append(c)
                prev_y, prev_page = r["y"], r["page"]
                i += 1
                continue
            break

        cols = columns(block)
        grid = []
        for b in block:
            slots = [[] for _ in cols]
            for c in b["cells"]:
                slots[column_of(c, cols)].append(runs_html(c["runs"]).strip())
            grid.append([" ".join(s) for s in slots])
        # a column empty the whole way down is an artefact of the clustering,
        # not a column of the table
        keep = [j for j in range(len(cols)) if any(r[j] for r in grid)]
        # The scroll box is for the phone: a five-column schedule cannot be
        # squeezed into 350px, and without it the whole document scrolls
        # sideways and takes the prose with it.
        html.append('<div class="warrant-doc__scroll">'
                    '<table class="warrant-doc__grid">%s</table></div>'
                    % "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % r[j] for j in keep)
                              for r in grid))

    flush()
    return html


def literal(name, blocks, width=98, indent=1):
    """The blocks as build.py holds them: one implicitly joined string.

    Lines break after a space or after a tag and keep the break character, so
    the fragments concatenate back to exactly what went in -- which the caller
    checks before printing.
    """
    out = ["%s = (" % name]
    for block in blocks:
        room = width - indent - 2
        line = ""
        for piece in re.split(r"(?<= )|(?<=>)", block):
            if line and len(line) + len(piece) > room:
                out.append(" " * indent + "'%s'" % line)
                line = piece
            else:
                line += piece
        if line:
            out.append(" " * indent + "'%s'" % line)
    out.append(")")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--name", default="TM_WARRANT",
                    help="the constant to define (default: TM_WARRANT)")
    ap.add_argument("--html", action="store_true",
                    help="print the HTML itself instead of the Python literal")
    args = ap.parse_args()

    pages = read(args.pdf)
    blocks = body_html(pages)
    if args.html:
        print("\n".join(blocks))
        return

    text = literal(args.name, blocks)
    # The literal has to rebuild the HTML byte for byte -- a dropped space
    # would be invisible in the output and wrong on the page.
    ns = {}
    exec(text, ns)
    if ns[args.name] != "".join(blocks):
        raise SystemExit("the wrapped literal does not match the HTML it came from")
    print(text, end="")


if __name__ == "__main__":
    main()
