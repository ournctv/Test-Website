#!/usr/bin/env python3
"""Build a TM_SUMMARY_* literal from a Town Meeting action summary.

    python3 tools/action-summary.py SUMMARY.txt --name TM_SUMMARY_2026 \\
        [--split call|line] > out.py

The Town publishes, after a Town Meeting, a list of how every article was
disposed of and by what vote. It is plain text rather than a warrant, so
there is nothing to measure and nothing to mark up: a lead note, then one
entry per article.

Three meetings have been asked for and the Town set all three differently,
so --split says where an article's title ends rather than leaving it to be
guessed. In "call" (the default) the call state opens the result and the
title is whatever came before it: "Article 1: Receipt of Reports. (Not
Called) Adopted by ...", which is how both Annual Town Meetings read. In
"line" the title has the line to itself, call or no call, and the result
follows underneath, which is how the 2025 Special reads. Getting this wrong
is not subtle -- a title swallows its vote, or breaks in the middle of a
sentence -- so look at the output of a new summary before shipping it.

An article with no call state at all is the Town's omission, not a parse
failure: 2025's Article 87 has none. In "call" the script falls back to the
end of the title's first sentence and says on stderr that it did, so the
entry can be checked by eye.

The text is not reworded. The only repairs are the ones copying out of a PDF
makes: runs of whitespace collapse, which rejoins a vote broken across a page
break, and a space before a colon is dropped. Everything else -- names, the
Town's own capitals, "2/3rds", a dash where other entries have none -- is
left as the Town wrote it. The script refuses to run if the articles are not
numbered from 1 without a gap, or if an entry states no call.

Wrapping is `literal()` from warrant-to-html.py, so the output is in the form
build.py holds and rebuilds the HTML byte for byte.
"""
import argparse
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# The parenthesis that opens the result: "(Called)", "(Not Called)",
# "(Called, Call withdrawn)". A title's own parentheses -- "(ADU)",
# "(portion of)", "(NP&EDC)" -- do not match.
CALL = re.compile(r"\((?:Not )?Called[^)]*\)")


def load():
    path = os.path.join(HERE, "warrant-to-html.py")
    spec = importlib.util.spec_from_file_location("warrant_to_html", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def escape(text):
    """The entities the data blocks carry -- see the note at the top of build.py."""
    return (text.replace("&", "&amp;").replace("’", "&rsquo;")
                .replace("“", "&ldquo;").replace("”", "&rdquo;")
                .replace("–", "&ndash;").replace("—", "&mdash;"))


def tidy(text):
    """One line, and without the spacing a copy out of a PDF leaves behind."""
    return " ".join(text.split()).replace(" :", ":").replace(" .", ".")


def split_entry(n, entry, how):
    """An article's title and its result."""
    if how == "line":
        head, _, rest = entry.strip().partition("\n")
        return tidy(head), tidy(rest)

    flat = tidy(entry)
    at = CALL.search(flat)
    if at is not None:
        return flat[:at.start()].strip(), flat[at.start():].strip()

    # no call state at all -- the Town left it out. End the title at its
    # first sentence and say so, rather than guessing in silence.
    stop = flat.find(". ")
    if stop < 0:
        raise SystemExit("article %d states no call and no sentence to end "
                         "its title: %s" % (n, flat))
    sys.stderr.write("article %d states no call; title ended at %r\n"
                     % (n, flat[:stop + 1][-40:]))
    return flat[:stop + 1].strip(), flat[stop + 1:].strip()


def blocks_for(raw, how="call"):
    parts = re.split(r"(?=Article \d+:)", raw)
    lead, entries = parts[0], parts[1:]
    if not entries:
        raise SystemExit("no articles found: is this an action summary?")

    # The lead is prose and may run to several paragraphs -- what the
    # Moderator took up, which articles were called, the pot of uncalled
    # ones. A blank line separates them, as it does in the warrants.
    out = ["<p>%s</p>" % escape(tidy(para))
           for para in re.split(r"\n\s*\n", lead) if para.split()]
    for n, entry in enumerate(entries, 1):
        title, result = split_entry(n, entry, how)
        if not title.startswith("Article %d:" % n):
            raise SystemExit("article %d is out of order: %.48s" % (n, title))
        if not title[len("Article %d:" % n):].strip():
            raise SystemExit("article %d has no title: %s" % (n, title))
        if not result:
            raise SystemExit("article %d states no result: %s" % (n, title))
        out.append("<p><strong>%s</strong> %s</p>"
                   % (escape(title), escape(result)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse
                                 .RawDescriptionHelpFormatter)
    ap.add_argument("text")
    ap.add_argument("--name", default="TM_SUMMARY")
    ap.add_argument("--split", choices=("call", "line"), default="call",
                    help="where an article's title ends (default: call)")
    ap.add_argument("--html", action="store_true")
    args = ap.parse_args()

    blocks = blocks_for(open(args.text, encoding="utf-8").read(), args.split)
    if args.html:
        print("\n".join(blocks))
        return

    mod = load()
    text = mod.literal(args.name, blocks)
    ns = {}
    exec(text, ns)
    if ns[args.name] != "".join(blocks):
        raise SystemExit("the wrapped literal does not match its HTML")
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
