#!/usr/bin/env python3
"""Fetch YouTube metadata and emit it in build.py's house format.

Pulls titles and descriptions straight from YouTube via yt-dlp, cleans them,
escapes them to HTML entities, and wraps them to match the surrounding code —
so the output pastes directly into build.py with no hand-editing.

This exists because text copy-pasted from a YouTube page arrives damaged:
mojibake, mismatched quotes, redirect-wrapped links, doubled spaces. See the
"Text pasted from YouTube arrives damaged" section of CLAUDE.md. Fetching the
metadata programmatically avoids that whole class of error.

USAGE

    python3 tools/fetch-video.py ID [ID ...]        # flat list format
    python3 tools/fetch-video.py --format atheneum ID [ID ...]
    python3 tools/fetch-video.py --playlist URL     # whole channel/playlist
    python3 tools/fetch-video.py --paras 1 ID       # first paragraph only
    python3 tools/fetch-video.py --strip-urls ID    # drop bare URLs

Accepts bare 11-character video IDs or full YouTube URLs.

OUTPUT FORMATS

  flat (default) — for DREAMLAND_*, LLNF_*, and other (id, title, desc) lists:

     ("Y7uc7bBXpNM", "Dreamland Conversations: Welcome to Your Mind, Night 1",
      "This video is the first night of two nights ..."),

  atheneum — for the ATHENEUM_TITLES dict:

     "lHf2a9xX3Uk": (
       "2013 Constance Laibe Hays Memorial Lecture: Janny Scott",
       "Journalist Janny Scott discusses ..."),

ALWAYS PROOFREAD THE OUTPUT before committing it. This script fixes mechanical
damage; it cannot catch a misspelled surname or a wrong book title. Several
real errors in this site's copy were caught by reading carefully.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import urllib.parse

WRAP = 100  # matches the widest description lines already in build.py


# ---------------------------------------------------------------- yt-dlp
INSTALL_HINT = "  See: https://github.com/yt-dlp/yt-dlp/releases"


def find_ytdlp(explicit=None):
    """Locate yt-dlp, preferring an explicit path, then the user-local install."""
    if explicit:
        path = shutil.which(explicit) or (
            explicit if os.access(explicit, os.X_OK) else None)
        if not path:
            sys.exit("Not an executable yt-dlp: %s\n%s" % (explicit, INSTALL_HINT))
        return path
    for cand in (os.path.expanduser("~/.local/bin/yt-dlp"), "yt-dlp"):
        path = shutil.which(cand) or (
            cand if os.access(cand, os.X_OK) else None)
        if path:
            return path
    sys.exit(
        "yt-dlp not found. Install it, or pass its path with --ytdlp.\n" + INSTALL_HINT
    )


def fetch(ytdlp, url):
    """Return yt-dlp's JSON metadata for one video, or None on failure."""
    proc = subprocess.run(
        [ytdlp, "--skip-download", "--no-warnings", "--dump-json", url],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        err = (proc.stderr or "").strip().splitlines()
        sys.stderr.write("  ! failed: %s\n" % (err[-1] if err else "unknown error"))
        return None
    return json.loads(proc.stdout)


def playlist_ids(ytdlp, url):
    """Return every video id in a playlist or channel, in order."""
    proc = subprocess.run(
        [ytdlp, "--skip-download", "--no-warnings", "--flat-playlist",
         "--print", "%(id)s", url],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        sys.exit("Could not read playlist: %s" % (proc.stderr or "").strip())
    return [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]


# ---------------------------------------------------------------- cleaning
def fix_mojibake(s):
    """Repair UTF-8 that was decoded as Latin-1 ('â€™' -> "'", 'Ã ' -> 'à').

    Only applied when the round-trip succeeds and actually changes something,
    so correctly-encoded text is left alone.
    """
    if not any(marker in s for marker in ("Ã", "â€", "Â")):
        return s
    # cp1252 first: the curly-quote damage ('â€™') contains '€', which has no
    # Latin-1 encoding, so a latin-1 round-trip would raise and repair nothing.
    for codec in ("cp1252", "latin-1"):
        try:
            return s.encode(codec).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
    return s


def unwrap_redirects(s):
    """Replace YouTube redirect wrappers with the URL they point at.

    youtube.com/redirect?event=...&q=https%3A%2F%2Fexample.com -> https://example.com
    """
    def repl(m):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(m.group(0)).query).get("q")
        return urllib.parse.unquote(q[0]) if q else m.group(0)

    return re.sub(r"https?://(?:www\.)?youtube\.com/redirect\?[^\s]+", repl, s)


def to_entities(s):
    """Convert text to the HTML entities build.py uses.

    '&' is escaped FIRST — otherwise it would mangle the entities added after.
    """
    s = s.replace("&", "&amp;")
    # Curly characters that may already be present in the source text.
    for ch, ent in (("’", "&rsquo;"), ("‘", "&lsquo;"),
                    ("“", "&ldquo;"), ("”", "&rdquo;"),
                    ("–", "&ndash;"), ("—", "&mdash;"),
                    ("…", "&hellip;"), (" ", " ")):
        s = s.replace(ch, ent)
    # Straight apostrophe -> right single quote (the common case in prose).
    s = s.replace("'", "&rsquo;")
    # Straight double quotes -> paired curly quotes, alternating open/close.
    out, open_q = [], True
    for ch in s:
        if ch == '"':
            out.append("&ldquo;" if open_q else "&rdquo;")
            open_q = not open_q
        else:
            out.append(ch)
    s = "".join(out)
    # '--' used as a dash, and '...' as an ellipsis.
    s = re.sub(r"(?<=\w)\s*--\s*(?=\w)", " &mdash; ", s)
    s = s.replace("...", "&hellip;")
    return s


# Invisible characters that ride along in pasted YouTube metadata: zero-width
# space/non-joiner/joiner, word joiner, BOM, and the LTR/RTL marks. They render
# as nothing but break string comparisons and leave stray bytes in the HTML.
ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿‎‏"))


def clean(s, paras=None, strip_urls=False):
    """Run the full cleaning pipeline over a description or title."""
    s = fix_mojibake(s)
    s = s.translate(ZERO_WIDTH)
    s = unwrap_redirects(s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    if paras:
        blocks = [b for b in re.split(r"\n\s*\n", s) if b.strip()]
        s = "\n\n".join(blocks[:paras])
    if strip_urls:
        s = re.sub(r"https?://\S+", "", s)
    s = re.sub(r"\s+", " ", s).strip()      # collapse newlines and doubled spaces
    s = to_entities(s)
    s = re.sub(r"  +", " ", s).strip()
    return s


# ---------------------------------------------------------------- formatting
def quoted_block(text, indent, last_suffix):
    """Wrap text into adjacent Python string literals, one per line.

    Python concatenates adjacent literals automatically, which is how the
    long descriptions in build.py are written.
    """
    pad = " " * indent
    # Room for the two quotes and a trailing space, less whatever closes the
    # final line (")," ) — otherwise that last line overruns WRAP.
    room = WRAP - indent - 3 - len(last_suffix)
    # break_on_hyphens=False: each continuation line gets a trailing space, so
    # splitting "Co-Founder" across lines would silently render as "Co- Founder".
    # break_long_words=False keeps a long URL or entity intact rather than cut.
    lines = textwrap.wrap(text, room, break_on_hyphens=False,
                          break_long_words=False) or [""]
    out = []
    for i, ln in enumerate(lines):
        last = i == len(lines) - 1
        body = ln if last else ln + " "
        out.append('%s"%s"%s' % (pad, body, last_suffix if last else ""))
    return out


# Flagged inline so an empty description can never be pasted in unnoticed —
# doing so would silently wipe a hand-written one already in build.py.
TODO = "  # TODO no description on YouTube — write one by hand"


def fmt_flat(vid, title, desc):
    head = ' ("%s", "%s",' % (vid, title)
    return "\n".join([head] + quoted_block(desc, 2, ")," + (TODO if not desc else "")))


def fmt_atheneum(vid, title, desc):
    head = ' "%s": (' % vid
    body = ['   "%s",' % title]
    return "\n".join([head] + body + quoted_block(desc, 3, ")," + (TODO if not desc else "")))


# ---------------------------------------------------------------- main
ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def as_url(token):
    """Accept a bare video id or any YouTube URL."""
    if ID_RE.match(token):
        return "https://www.youtube.com/watch?v=%s" % token
    return token


def main():
    ap = argparse.ArgumentParser(
        description="Fetch YouTube metadata in build.py's house format.")
    ap.add_argument("ids", nargs="*", metavar="ID",
                    help="video ids or URLs")
    ap.add_argument("--format", choices=("flat", "atheneum"), default="flat",
                    help="output shape (default: flat)")
    ap.add_argument("--playlist", metavar="URL",
                    help="fetch every video in a playlist or channel")
    ap.add_argument("--paras", type=int, metavar="N",
                    help="keep only the first N paragraphs of the description")
    ap.add_argument("--strip-urls", action="store_true",
                    help="remove bare URLs from descriptions")
    ap.add_argument("--ytdlp", metavar="PATH", help="path to the yt-dlp binary")
    ap.add_argument("--meta", metavar="FILE",
                    help="also write 'id<TAB>year<TAB>width<TAB>height' per "
                         "video to FILE — the year for grouping a long section "
                         "(see program_group), the dimensions for spotting "
                         "vertical/Shorts video")
    # About one YouTube id in nine begins with "-", which argparse reads as an
    # option and then rejects, along with every argument after it. Take those
    # back from the unknown pile; anything else unknown is still an error.
    args, unknown = ap.parse_known_args()
    stray = [a for a in unknown if ID_RE.match(a.lstrip())]
    bad = [a for a in unknown if a not in stray]
    if bad:
        ap.error("unrecognized arguments: %s" % " ".join(bad))

    ytdlp = find_ytdlp(args.ytdlp)

    ids = list(args.ids) + stray
    if args.playlist:
        sys.stderr.write("Reading playlist ...\n")
        ids = playlist_ids(ytdlp, args.playlist) + ids
    if not ids:
        ap.error("give at least one video id, or --playlist URL")

    fmt = fmt_flat if args.format == "flat" else fmt_atheneum
    blocks, failed, empty, rows = [], [], [], []

    for i, token in enumerate(ids, 1):
        sys.stderr.write("[%d/%d] %s\n" % (i, len(ids), token))
        meta = fetch(ytdlp, as_url(token))
        if not meta:
            failed.append(token)
            continue
        vid = meta.get("id") or token
        title = clean(meta.get("title") or "")
        desc = clean(meta.get("description") or "",
                     paras=args.paras, strip_urls=args.strip_urls)
        if not desc:
            empty.append(vid)
        blocks.append(fmt(vid, title, desc))
        if args.meta:
            # upload_date is YYYYMMDD; the year is all a year-grouped section needs.
            rows.append((vid, (meta.get("upload_date") or "")[:4],
                         meta.get("width"), meta.get("height")))

    if blocks:
        print("\n".join(blocks))

    if args.meta:
        with open(args.meta, "w", encoding="utf-8") as fh:
            for vid, yr, w, h in rows:
                fh.write("%s\t%s\t%s\t%s\n" % (vid, yr, w or "", h or ""))
        sys.stderr.write("Wrote %d meta rows to %s\n" % (len(rows), args.meta))

    sys.stderr.write("\nDone: %d of %d.\n" % (len(blocks), len(ids)))
    if failed:
        sys.stderr.write("Failed: %s\n" % ", ".join(failed))
    if empty:
        sys.stderr.write(
            "No description on YouTube (marked TODO in the output): %s\n"
            "  Do not paste these over descriptions already written by hand.\n"
            % ", ".join(empty))
    sys.stderr.write("Proofread before pasting into build.py.\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
