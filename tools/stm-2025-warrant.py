#!/usr/bin/env python3
"""Build TM_WARRANT_STM_2025 from the Special Town Meeting warrant PDF.

    python3 tools/stm-2025-warrant.py WARRANT.pdf > out.py

warrant-to-html.py does all the reading. This wrapper exists for one block of
that warrant it cannot assemble: the Use Chart's header. Twenty district names
are set sideways down twenty narrow columns, so each arrives as three or four
separate lines -- "R-", "10", "R-", "10", "L", "DR", "10" is one column -- and
the row grouping, which reads a shared baseline as a row, scatters them across
a grid of empty cells. Fixing that in the tool would mean changing how every
warrant's tables are built, to the risk of the two that already come out
right, for a chart that appears once.

So the header and the two row labels are named here, read off the artwork at
eight to fourteen times. Nothing else is: the twenty Y and N values in each
row, and whether each one is new language, are taken from what the tool
measured on the page, and the script refuses to run if what it finds there is
not the chart it expects.

The underlining under both row labels is not carried, here or anywhere else:
on a scan a rule under a word is just more ink. Both articles say that new
language is the highlighted language, and that is what survives.
"""
import argparse
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# The Use Chart's columns, in the order the page sets them. DR-10 is the
# page's own spelling; every other warrant writes that district SR-10.
DISTRICTS = ["R-1 SR-1", "ROH SOH", "R-5 R-5L", "R-10 R-10L DR-10",
             "R-20 SR-20", "R-40", "CDT", "CMI", "CN", "CTEC", "CI", "RC",
             "RC-2", "V-R", "LUG-1", "LUG-2", "LUG-3", "MMD", "VN", "VTEC"]

# The chart's own rows, and the state of each label. The Short-Term row's
# label is the one part of either row the page does not highlight.
ROWS = [("Short-Term Rental (STR)", False), ("Long-Term Rental (LTR)", True)]

CELL = re.compile(r"<td>(?:<ins>(.)</ins>|(.))</td>")


def load():
    path = os.path.join(HERE, "warrant-to-html.py")
    spec = importlib.util.spec_from_file_location("warrant_to_html", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def chart_at(blocks):
    """Where the scattered Use Chart starts, and the rows of values in it.

    The chart is the only table in the warrant holding single letters, so it
    is found by its values rather than by counting blocks, and the run it
    covers ends at the label that closes it.
    """
    rows, start, end = [], None, None
    for i, block in enumerate(blocks):
        cells = CELL.findall(block)
        if len(cells) == len(DISTRICTS) and \
                all((a or b) in "YN" for a, b in cells):
            rows.append([(a or b, bool(a)) for a, b in cells])
            if start is None:
                # the scattered header sits in the block above the first row
                start = i - 3
        elif rows and "(LTR)" in block:
            end = i
            break
    if len(rows) != len(ROWS) or start is None or end is None:
        raise SystemExit("this does not look like the Special Town Meeting "
                         "warrant: found %d value rows" % len(rows))
    if [v for v, _ in rows[0]].count("N") != 1:
        raise SystemExit("the Short-Term row should prohibit exactly one "
                         "district")
    if not all(new for row in rows for _, new in row):
        raise SystemExit("the chart's values should all be new language")
    return start, end, rows


def table(rows):
    out = ["<tr><td>Use</td>%s</tr>"
           % "".join("<td>%s</td>" % d for d in DISTRICTS)]
    for (label, new), row in zip(ROWS, rows):
        head = "<ins>%s</ins>" % label if new else label
        out.append("<tr><td>%s</td>%s</tr>"
                   % (head, "".join("<td><ins>%s</ins></td>" % v
                                    for v, _ in row)))
    return ('<div class="warrant-doc__scroll">'
            '<table class="warrant-doc__grid">%s</table></div>'
            % "".join(out))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse
                                 .RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--name", default="TM_WARRANT_STM_2025")
    ap.add_argument("--html", action="store_true")
    args = ap.parse_args()

    mod = load()
    blocks = mod.body_html(mod.read(args.pdf))
    start, end, rows = chart_at(blocks)
    blocks[start:end + 1] = [table(rows)]

    if args.html:
        print("\n".join(blocks))
        return
    text = mod.literal(args.name, blocks)
    ns = {}
    exec(text, ns)
    if ns[args.name] != "".join(blocks):
        raise SystemExit("the wrapped literal does not match its HTML")
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
