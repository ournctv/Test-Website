# NCTV website — working notes

Static site for Nantucket Community Television. 33 HTML pages, no framework,
no build tooling beyond one Python script.

## How the site is built

`build.py` generates **every** `.html` file in this folder. `styles.css` and
`site.js` are edited by hand and loaded by all pages.

The nav bar and footer are **markup in every page**, emitted by `nav_html()`
and `footer_html()` in `build.py`. To add, rename or reorder a nav link, edit
the `NAV` list there, not `site.js` — which now only wires the behaviour, plus
one line that corrects the footer's copyright year if a visitor reads the page
in a later year than the one it was built in. Until 2026-10-28 `site.js` built
both with `innerHTML` on every page load.

`search.js` is hand-edited too, but loads only on `search.html`. Four more
files are **generated** by `build.py` alongside the pages — never edit them,
and never count them as pages:

| file | what it is |
|---|---|
| `search-index.js` | every video card on the site, for `search.html` |
| `sitemap.xml` | the 33 pages, for crawlers |
| `robots.txt` | points crawlers at the sitemap |
| `404.html` | shown for any address that does not exist |

**Never edit the generated `.html` files.** Any change there is destroyed on the
next build. Edit `build.py`, then run:

```
python3 build.py
```

It prints "Wrote 4 other files" and then "Wrote 33 pages". `OUT` is derived
from the script's own location, so it always writes beside `build.py`.

## The header is wider than the page

Every other row on the site keeps to the 1200px column (`.wrap`). The nav and
the status strip above it do not -- they span the window and keep only the
gutter, because the logo, six links and the search box do not fit in 1200px:
the logo was left less width than its artwork, kept drawing at full size
anyway, and the first link landed on top of the play button. Between 1101px
and 1200px even the full window is tight, so the header drops its gutter to
20px across that band.

The search box is the last item in the menu row and is nudged right by an
offset (`position:relative;left:...`), not a margin, so it sits 20px from the
window edge without moving the links beside it. **Anything else added to the
header has to come out of that same budget** -- check the gap between the logo
and the first link afterwards, at 1101px and at 1920px, not just at one width.

## Search

`search.html` searches every video on the site by title and by description.

`build_search_index()` in `build.py` runs **after** the pages are built and
reads them back: every `<article class="watch-episode">` on every page becomes
one record, `[youtube id, title, description, page index]`. It is written to
`search-index.js` as one assignment to `window.NCTV_SEARCH` — a plain script,
not JSON fetched at runtime, because the site has to work from `file://`. It is
about 2.1 MB, which is why only `search.html` loads it. Its `?v=` is a hash of
its own contents, not `ASSET_VER`, so a changed archive busts its own cache.

There are no placeholder partner pages left. All twenty have real
`.watch-episode` listings and are indexed; the Rossini Club was the last one,
built out on 2026-10-25. A page that shows `.video` cards titled "Video 1"
again would be a regression, not a page awaiting content.

`search.js` ranks the records. Two behaviours worth knowing before changing it:
a multi-word query returns only the videos matching **every** word (the best
available number of words, if none match all), and results are deduplicated by
YouTube id, because the NHA page cross-lists about forty of its talks under two
playlists on purpose.

**Everything on the page shares one global scope**, so `search.js` is wrapped in
an IIFE. It declared a bare `const PAGE` once and collided with a `PAGE` that
`site.js` declared at the time, which killed the whole script. `site.js` no
longer declares one, but the hazard is the shared scope, not that name.

## Cache busting — ASSET_VER

`ASSET_VER` near the top of `build.py` is appended to CSS, JS and image URLs as
`?v=NNN`. The site owner views the site in Safari, which caches aggressively.

**Bump it when you change `styles.css`, `site.js`, or any file in `assets/`.**
Do *not* bump it for changes that only affect generated HTML (text, titles,
descriptions) — the HTML isn't cached by that mechanism, so bumping is noise.

Read its current value from `build.py` — it changes several times in a working
session, so a number written here goes stale immediately.

## The site's address, and what a shared link looks like

`SITE_URL` near the top of `build.py` is the one place the live address is
written down: `https://www.ournctv.org`, which is what the homepage promo
announces. Every absolute URL on the site is derived from it — the
`rel="canonical"` link in each `<head>`, the Open Graph tags, `sitemap.xml`
and `robots.txt`. **If the site ends up on a different address, change that
one string.** Nothing else hard-codes it. `page_url()` turns a page name into
its address; `index.html` resolves to the bare root, so `/` and
`/index.html` never compete as two addresses for one page.

`META_DESC`, a few lines below it, holds the sentence Google prints under the
page title, one per page. **A page with no entry stops the build** — the
check sits just above the write loop and names the page. That is deliberate:
until 2026-10-28 all 33 pages shared one sentence, which made the Shorts Fest
page and the Civic TV page read identically in a search listing. The 20
partner pages are filled from `_PARTNER_ORGS` rather than written out
one by one.

The picture a shared link shows — on Facebook, Instagram, iMessage, WhatsApp
and X — is `assets/og-card.jpg`, built by `tools/og-card.py` from the
homepage hero photo at 1200x630 with the white NCTV mark over a scrim. It is
the one JPEG on a site that is otherwise WebP, because some scrapers still do
not read WebP. Re-run that script if the hero photo changes.

`404.html` is deliberately **not** in `files`: it is not part of the
navigation and does not belong in the sitemap, and GitHub Pages picks it up by
name. Because it is served for any missing address, including a deep one like
`/civic/2026/march`, every link in it is rewritten to start from the site root
after `shell()` builds it. An assertion fails the build if a relative URL
survives.

## Keyboard and screen-reader basics

Two things every page carries, both emitted by `shell()`:

- A **skip link** — the first thing the Tab key reaches, letting a keyboard
  visitor jump the nine nav links and the search box. It lands on the first
  element of the page body, which `shell()` gives `id="main" tabindex="-1"`.
  The `tabindex` is what actually moves the keyboard: without it the page
  scrolls but focus stays in the nav.
- **A placeholder control is `disabled`**, not merely dimmed. The pending
  "Meeting Agenda" buttons are the case to remember: `videos-civic.html`
  carries 2,243 of them, and until 2026-10-28 they were focusable buttons
  that announced as actionable and did nothing. Dimming a control in CSS does
  not take it out of the tab order.

## Banner videos

Three pages carry a looping video banner: the home page, Shorts Fest and New
Moon Fest. All three are **Vimeo background embeds**, named in `build.py` as
`BANNER_VIDEO` (home) and the first argument of `video_hero()` (the other
two). The value is a Vimeo id and its private hash, `"<id>:<hash>"` -- the two
halves of a Vimeo share link.

`background=1` gives autoplay, muted, looped, and **no player controls at
all**. `dnt=1` asks Vimeo not to track the visitor. Vimeo also serves the
video, so none of it rides on our own bandwidth -- which is why the
self-hosted files were removed again.

**Do not move these back to YouTube.** Its player paints a transport strip
over the banner -- a pause button, a mute button, and prev/next whenever the
embed is set to loop -- for roughly the first four seconds of *every* load.
`controls=0` does not suppress it, `youtube-nocookie` behaves the same, and
nothing on our side can cover it, because it is drawn inside the cross-origin
iframe, dead-centre, where it cannot even be cropped out. Frame.io is worse
still: its share links are review pages with permanent controls and a
timecode, and a Frame.io staffer has said embedding is unsupported and may
break at any time.

Two details the embed needs:

- **It letterboxes.** An iframe has no `object-fit`, so `styles.css` oversizes
  it past the hero on whichever axis is short and lets `.hero__media` clip it.
  The `cqw`/`cqh` rule measures the hero box itself and is what actually runs;
  the `vw`/`vh` pair above it is a fallback that assumes a viewport-sized hero,
  true of the home banner but not the shorter event ones.
- **The photo holds until real frames arrive**, via Vimeo's own postMessage
  protocol (`addEventListener` / `play`), used directly so we need not fetch
  `player.js` for one event. A timer backstops it.

`shell()` derives each page's preconnects from its own body -- Vimeo's two
hosts when the page holds a player embed, `img.youtube.com` when it holds a
thumbnail -- so the hosts can never drift from what the page actually loads,
and a page that uses neither pays for neither. Fonts are on every page and
stay in the markup. Do not hand-list a host here again: the previous pair
pointed at `www.youtube.com` and `i.ytimg.com`, and neither was ever fetched.

Two things live outside the repo and can bite: the Vimeo plan has to keep
`background=1` available, and each video's "where can this be embedded"
setting has to allow the live domain.

Self-hosted MP4 banners were built and measured first, then removed when
Vimeo was chosen; `tools/hero-video.py` went with them. The source videos are
on the owner's Desktop, outside the repo. If self-hosting is ever wanted
again, the encode settings that worked are in Claude's project memory.

## Page types

- **Standard pages** (home, staff, contact, classes, create) — built inline.
- **Channel pages** — Civic TV, Nantucket Life, Sports Connection.
- **Event pages** — Shorts Fest, New Moon Fest. Hand-built custom layouts;
  read the functions before editing.
- **Partner pages** — 20 in all: 15 with a tile in the grid (`PARTNERS`)
  and 5 reached only from elsewhere (`PAGE_ONLY_PARTNERS`, which is where the
  Community Foundation's four Initiative Funds sit).
  - **Every one of them is custom now.** All twenty are listed in
    `CUSTOM_PARTNER_PAGES` and built by `custom_partner_page()` further down
    the file, so the generic partner loop below that set has nothing left to
    build. It is kept for the next partner added tile-first. `video_page()`
    itself is still live — Civic TV and Sports Connection use it.
  - Entries in `PAGE_ONLY_PARTNERS` must be **string literals**: that list sits
    thousands of lines above where `CFN_PAGE` and the rest are defined.
  - **The logo grid is drawn alphabetically**, by the same `label_key()` the
    section headings use, so the order the list is written in does not matter
    (Frank, 2026-10-25). `partner_buttons()` does the sorting, and the home
    page draws the same grid, so both pages agree. The Community Foundation's
    four Initiative Fund logos, in the section below the grid, are sorted the
    same way by `cfn_funds_section()`.
- **School Videos** (`videos-school.html`) — one page covering several
  organizations. See "School Videos page specifics" below.

### Meeting titles

Every recorded-meeting title leads with its date in the School Committee's form:
abbreviated month with a period (May takes none), the day with its ordinal
suffix, then the year and the body, and no dash between them —
`Sep. 15th, 2026 School Committee`. The 2,732 Civic TV titles were converted to
this from `September 15, 2026 - School Committee` at the site owner's request.

Nothing parses these dates. A civic card's quarter comes from the third element
of its tuple in `CIVIC_BOARDS`, and the agendas and descriptions are keyed by
video id, so the format is display only — it also supplies each thumbnail's
`alt` text. Dates written inside an agenda or a description are the meeting
posting's own wording and are left long.

**Two boards have no quarter row.** Public Forums never had one. Annual/Special
Town Meeting lost its on 2026-10-27 at Frank's request: the meeting sits once a
year over two or three evenings, so every year drew four quarter buttons with
three greyed out. `CIVIC_NO_QUARTERS` in `build.py` names those boards and
`civic_board_picker()` puts the cards straight under the year, keeping their
agenda and warrant buttons. The month is still stored in every tuple — keep
filling it in, since a board can be taken back out of that set.

**Meetings are stored oldest-first and drawn newest-first.** `civic_year_cards()`
and `civic_forum_cards()` reverse the list as they render, so a quarter or a
forum year reads newest at the top; the School Committee list does the same
through `programs_section(..., newest_first=True)`. The reversal is deliberately
at render time and not in the data: new meetings are **appended** to the end of
a year's list, and storing them backwards would silently invert that for every
future addition. Keep appending. The hairline still falls between cards, since
`rule=(i != last)` is applied after the reversal.

The year and quarter buttons are not reversed — they stay oldest-left, by
request. Nantucket Government 101 is not a meeting list and keeps its own
order.

### Adding another custom partner page

`custom_partner_page()` takes a logo, mission text, website phrase, and a list
of `(section label, videos)` groups. ~10 lines. Add the page to
`_PARTNER_ORGS` as well, or the description check at the foot of `build.py`
stops the build. `videos` is one of four shapes:

- a flat list of `(video_id, title, description)` — Dreamland, Linda Loring
- a dict of `{year: [(video_id, title, description), ...]}` — Atheneum,
  Book Festival
- a `Subgroups([...])` list of `(label, videos)` pairs — no page uses it now
- a `Picker([...])` list of `(label, videos)` pairs — NHA

The dict form renders a row of year buttons (oldest left, newest right) with one
year's videos visible at a time, driven by `initYearPicker()` in `site.js`. A
year may be listed with an empty list to reserve its button before the videos
exist; the picker opens on the newest year that actually has any.

`Subgroups` nests one more level of accordions inside a section instead of
listing video cards. It nests arbitrarily deep, and `program_group()` styles
every level past the first with `dl-group--sub` (indented, one size down). The
NHA's two Browse lists were its only users until they became `Picker`s, so it
is live but unused — keep it for the next section that wants nested rows.

`Picker` holds the same `(label, videos)` pairs but draws the children as a
wrapping row of buttons over a single panel rather than a column of accordion
rows — see "NHA page specifics" below. Reach for it when a section has enough
children that a stack reads as a list to scroll past rather than a set of
choices to pick from. Nothing is open on load, and a second click on the open
button shuts it. A child may itself be any of the four shapes, so a `Picker`
panel can hold a year picker of its own; `initYearPicker()` scopes its buttons
and panels to one picker's own level so the two do not fight, and the
`.yearpick--labels` rules use child combinators for the same reason.

A group may carry a third element, `(label, videos, intro)`: a note set once at
the top of that section. It exists for text that would otherwise repeat on
every card inside it -- the Arts Council closes all four Emergence episodes
with the same paragraph about the series, so the paragraph is the section's
note and the cards carry only what differs. Prefer this to deleting a partner's
own wording.

**Section order is alphabetical and enforced in code.** `custom_partner_page()`
sorts the groups it is given by `label_key()`, so the order they are written in
does not matter and a section added later cannot land out of order (Frank,
2026-10-25 -- "Halloween Parade" had arrived after "Talk of the Town" on the
Chamber page). `label_key()` strips markup and entities, ignores leading
punctuation so `&rsquo;Sconset` files under S, ignores a leading "The" so
"The Cranberry Bogs" files under C, and case-folds. Only "The" is dropped --
no section starts with "A" or "An", and guessing at articles that are not
there would file a future section where nobody looks for it. Digits sort
before letters, so "50th Anniversary Video" leads the Land & Water Council
page. Only the top-level sections are sorted -- the children inside a
`Picker` or `Subgroups` keep their list order, some of them being
chronological.

A final `collapsible=False` argument renders the groups permanently open, with
a plain heading in place of the click-to-toggle summary. The Book Festival
archive uses it; nothing else does.

An empty group list is fine: `programs_section()` renders nothing at all rather
than a bare "Programs" heading over empty space, so a page can go up with its
banner and mission before any videos exist. The Civic League page is the
current example.

## Production credits

Most of the archive is NCTV's own work. A video made by an outside production
company carries that maker's credit **under its thumbnail** -- the site owner
calls these "tags" (the YP tag, the SP tag, the NM tag, the TN tag).

> **Never add a tag that was not asked for.** Standing rule, 2026-10-25: no NM,
> YP, SP or TN tag goes on a video unless the site owner names that video and
> that tag. Who made a video is a claim about someone else's work, and YouTube text,
> channel ownership and a run of similar videos are not evidence. When a video
> looks like it should carry one, say so and leave the card alone.

This is the settled placement, agreed 2026-10-25. It does not vary by company:

```
Video created by:  [mark]
click for website
```

Two right-aligned lines of mono text ending flush on the mark's left edge, the
square mark beside them at two text lines tall, the whole block right-justified
so the mark's right edge meets the thumbnail's. An inline version inside the
description was tried first and dropped.

Not every tag has all four parts. `credit_block(name, logo, url)` builds the
full one; a maker with no website loses the "click for website" line and nothing
in its block is clickable. `NM_CREDIT` is wording alone, `TN_CREDIT` is wording
plus mark. All of them use `.video-credit`, which is what puts a block under the
thumbnail at the right edge in the same face and size.

`credit_block(name, logo, url)` near `ASSET_VER` builds every one of them, and
`VIDEO_CREDITS` maps YouTube id -> block. A new video is one line; a new company
is a logo plus two. Keyed by id rather than set on the video's tuple, so a credit
follows its video onto every page that lists it -- several are cross-listed.

Four things to keep:

- **Only "click for website" is the link.** Not the wording above it, not the
  mark. The link needs its `aria-label` and the mark needs the company name as
  its `alt`, because the name appears nowhere else in the block.
- **Logos are 96px square WebP** in `assets/`, 2x the 46px they render at, with
  the original in `image-originals/`. A new logo means bumping `ASSET_VER`.
- **Remove any production credit already written into the description**, or the
  card says it twice. "60 Years of Conservation" carried "Produced by Dan
  Driscoll and September Productions" from the Foundation's own YouTube text.
- **Check YouTube's own description before crediting a video.** The same card
  was first going to be credited to the wrong company; the YouTube text caught
  it.

### The NM tag

Novation Media's is the one credit set by rule rather than one video at a time:
the NHA videos **posted to YouTube in 2024 or later** carry "Edited by Novation
Media" (Frank, 2026-10-25). The rule describes how the list was built; it is
not standing permission to extend it. `NM_VIDEOS` is a closed list of 77 ids,
and a newer NHA video does not join it without being asked for -- see the
standing rule above. It is the same block with the two parts it
has no use for removed -- there is no mark and no site, so no "click for
website" line -- and `NM_CREDIT` reuses `.video-credit` so the placement, face
and size match the other two exactly.

`NM_VIDEOS` near `ASSET_VER` holds the 77 ids, grouped by year, and is folded
into `VIDEO_CREDITS` after the hand-set entries so a video that names its own
production company keeps that block instead.

Two things to keep:

- **The cutoff is the upload date, not the event year.** The NHA's year buttons
  follow the event, so a 2023 lecture posted in 2024 is tagged and filed under
  2023. That is correct, not a bug. If asked to extend the list, read the dates
  off YouTube (`yt-dlp --print "%(id)s|%(upload_date)s"`) rather than guessing.
- **A video that names a different maker on its own card is left out.** Three
  are: the two "Nantucket About Town" episodes print "Edited by Andrew Daume"
  in their own description text, and `8NRGe4SHOcs` is Ric Burns's film. Flag
  cases like these rather than letting the date rule decide them.

### The TN tag

Nantucket Government 101 on the Civic TV page is the Town's own series, so every
video in it carries "Created by the Town of Nantucket's / Communications Office"
beside the Town seal, with nothing clickable -- the Town has no site the block
sends anyone to. It is the second rule-based tag, and the only one set off a
list rather than off ids: `VIDEO_CREDITS.update({vid: TN_CREDIT for vid, *_ in
GOVT101})` sits directly under `GOVT101`, so a department added there is
credited without a second edit. That is deliberate (the site owner was told);
it is the section's defining property, not a guess about someone else's work.

Two things it changed, both worth knowing before touching the Civic TV page:

- **Government 101 cards are `nl_episode()`, not `civic_card()`.** A tag is
  drawn by `nl_episode()`, which also puts the watch link under the description
  rather than under the thumbnail, which is where the tag goes. The site owner
  asked for exactly that layout on 2026-10-25, pointing at the Golf Club
  Foundation page. The section no longer carries the note that used to sit above
  its cards.
- **`AWARD_COLORS`, `trophy()` and `nl_episode()` now live beside
  `VIDEO_CREDITS`** near the top of the file. They were defined around line
  27400, but `videos_pages` is assembled around line 26480 and Government 101
  calls `nl_episode()` while it is being built, so the definitions had to come
  first. Nothing else moved and no other page's output changed.

## A document on a card — the Town Meeting warrants

A civic card normally offers its posted agenda, which the button swaps for the
description in place. Five cards offer a whole document instead — both
sittings of the 2025 Annual Town Meeting, both of the 2026, and the November
4, 2025 Special Town Meeting — whose buttons read **Warrant** and open that
meeting's warrant in an overlay (`initDocModal()` in `site.js`, `.docmodal` in
`styles.css`). In place would push every meeting below them off the screen;
the 2025 Annual alone is 104 articles and 70,000 words. Frank asked for 2026,
then 2025, then the Special on 2026-10-27; he explicitly did not want the PDFs
hosted. **A card can carry more than one**, and all five do: a second
button, **Summary**, opens the Town's list of how each article was disposed
of and by what vote. It is a six-document, ten-button page now, so neither
count is a check on the other.

`CIVIC_DOCS` in `build.py` maps a video id to a list of `(button label,
overlay heading, body html)`, and `civic_card()` checks it before it checks
`CIVIC_AGENDAS`, writing one button per entry in the order given. **Where the
button goes is a second decision.** A heading listed in `CIVIC_DOC_NOTES` is
written under the title instead, led by the line that dictionary gives it
(`.watch-episode__note`) — the summary reads *"To see the vote results,
please click this button:"*, which is Frank's wording. Everything else sits
in the actions row beside the watch link, which is `flex-wrap` and takes a
second button without crowding. The note is a `<p>` of its own and not a
`.watch-episode__desc`, so it is never clamped and never reaches the search
index. **The bodies are not in the cards.** `civic_doc_store()` emits each distinct document once,
hidden, at the foot of the Civic TV page, and each button names one with
`data-doc`; cards sharing a heading share the copy, because one warrant
governs every sitting of its meeting. A copy per card put the 2025 warrant
into the page twice at half a megabyte each. Nothing is fetched, so it works
offline, and nothing reaches the search index, which reads
`.watch-episode__desc` only. The three warrants and three summaries add
about 0.8 MB to `videos-civic.html`, which is 5.3 MB now.

The overlay **moves** the document into itself and hands it back on close, so
the page holds one copy and an in-page search never finds a sentence twice.

Six things about the warrant text itself:

- **It is extracted, never retyped, and the tool reads scans as well as
  born-digital files.** `tools/warrant-to-html.py` reads the PDF and writes
  the literal in the exact form `build.py` holds. Another year is one run of
  that tool plus one line in `CIVIC_DOCS` per sitting. **Check which kind of
  PDF it is**, because a scan is marked up a different way: the Special Town
  Meeting warrant is a photocopy — thirteen page images with an OCR layer
  under them and not one drawable rectangle in the file — so the
  box-and-hairline test below finds nothing. `scanned()` catches that case
  (no drawings anywhere, an image on every page) and `Shading` renders the
  page grey at 3x and takes the median of each character's own column
  instead, so the highlighting still comes out as `<ins>`. What cannot come
  out is `<del>`: on a scan a rule through a word is just more ink. **How
  good the copy is decides whether any of that works.** The first copy Frank
  had measured 245-253 under highlighted lines against 253-255 under plain
  ones, which overlap; the motions edition he sent later separates at 212
  against 255. `TM_WARRANT_STM_2025` is regenerated with
  `tools/stm-2025-warrant.py` rather than with the tool directly — that
  wrapper exists for one block, the Use Chart, whose twenty district names are
  set sideways down twenty narrow columns and arrive as a hundred loose
  fragments.
- **Two warrants are enough to show how much the typesetting varies.** The
  tool finds the running footer rather than assuming a band — 2026's sits in
  the bottom 44pt, 2025's reaches 68pt up — and it has to tell a highlight
  from the rest of the page furniture. 2025 draws its tables as filled
  rectangles: 1,828 black slivers a point wide for the borders and 530 white
  blocks the width of a column for the cells. **A highlight is a box with a
  real colour, lighter than black and darker than white.** Taking every box
  of about line height, which is what the first version did, marked 52 runs
  of the 2026 warrant as new language that the PDF does not highlight.
- **The Town marks bylaw edits by drawing rectangles, not by styling text** —
  a grey box behind new language, a hairline through language to be struck.
  Any ordinary text extraction loses both and welds the old wording to the
  new; "as measured by the exterior interior faces of the exterior walls" is
  one real line. The tool tests every character against its page's rectangles
  and emits `<del>` and `<ins>`. Every zoning article tells the reader that
  new language is highlighted and deleted language struck through, so the CSS
  has to keep looking like that.
- **A line break is not a word break, and not a tag break either.** The
  warrants hyphenate across lines, so joining the lines with a space wrote
  "non- substantive" and "Short- Term" into all three of them. `knit()` drops
  the space after a hyphen that follows a letter or digit — but not after
  the Massachusetts drafting idiom "words:- select" — and closes the
  `</ins><ins>` seam at each line end, which had been striping the highlights
  into bars.
- **A summary is not a warrant and is not read the same way.** The Town
  publishes its action summary as plain text, so there is nothing to measure
  and nothing to mark up. `tools/action-summary.py` turns it into a
  `TM_SUMMARY_*` literal: the lead, a `<p>` per paragraph of it, then one
  `<p>` per article with the title in `<strong>` and the result after it. It
  rewords nothing — the only repairs are the ones copying out of a PDF asks
  for, a vote rejoined across a page break and a space dropped before a colon
  or a period — and it refuses to run unless the articles number from 1
  without a gap and every one states a result. **Where a title ends is told,
  not guessed**, because the Town set all three meetings differently:
  `--split call` (the default) ends it where the call state begins, which is
  both Annual Town Meetings, and `--split line` gives the title the line to
  itself with the vote underneath, which is the 2025 Special. Guess wrong and
  a title swallows its vote or breaks mid-sentence, so read a new summary's
  output before shipping it. **An article with no call state at all is the
  Town's omission, not a parse failure** — 2025's Article 87 has none — and
  `call` then ends the title at its first sentence and says so on stderr.
- **The stored blocks carry no straight quotes of either kind.** They are
  single-quoted Python literals holding double-quoted class attributes, so the
  tool turns every `'` into `&rsquo;` and every `"` into `&ldquo;`/`&rdquo;`.
  The tool refuses to print a literal that does not rebuild its HTML byte for
  byte.

## Tables in a posted agenda

**Check every agenda for a table before storing it.** CivicClerk serves each
agenda two ways, and `CIVIC_AGENDAS` is built from the plain-text rendition,
which is fine until the agenda carries a table. Then it flattens the table into
one run-together list item **with the columns interleaved** -- wherever a cell
wraps to a second line, that line is emitted wherever it physically fell, which
drops it inside the neighboring cell:

```
35 Select Board for Zoning Map Change: RC-2 to CMI or CTEC - 43 Nobadeer
Planning Board Farm Road
```

is really article 35, sponsored by *Select Board for Planning Board*, to make a
*Zoning Map Change: RC-2 to CMI or CTEC - 43 Nobadeer Farm Road*. The words are
out of order, so splitting the stored string cannot repair it -- a regex just
produces tidy-looking rows holding the wrong text. **Read the PDF instead.**

`tools/agenda-tables.py` does it, and the tables are ruled, so it is geometry
rather than guesswork: vertical rules at x=95.6/145.0/235.0/561.4 and a
horizontal rule every ~25.3pt, the same in the 2025 and 2026 templates.

```
python3 tools/agenda-tables.py --scan                            # who is affected
python3 tools/agenda-tables.py --board "Finance Committee" --year 2026
python3 tools/agenda-tables.py --board "Finance Committee" --year 2026 --apply
```

Without `--apply` it prints the rebuilt entries to paste. With it, it writes
them and leaves `build.py.bak-agenda-tables`. **It is a content change, so
`ASSET_VER` must not move** -- the output is a nested `<ol>`, the vocabulary
`CIVIC_AGENDAS` already uses, and the stylesheet already draws level two
lower-alpha. 18 agendas and 188 article rows went through it on 2026-10-27/28;
no stored agenda holds a flattened table now.

Four things it handles that are not obvious:

- **A date can carry several postings, and CivicClerk labels Agenda Packets
  `type: Agenda` too.** March 4, 2025 offered a 2-page agenda and a 145-page
  packet; February 20 had four postings. Scoring the candidates against the
  stored text picks the *packet*, which contains the agenda plus everything
  else, so the script scores only to rule out the unrelated and then takes the
  shortest survivor.
- **A cell that overflows its ruled row gets its own ruled row**, with an empty
  Article cell -- `['', 'al', '']` is the tail of "et al". Those fold into the
  row above. Five of the eight 2026 agendas needed it and none of the ten 2025
  ones did, so a clean run proves nothing about the next.
- **A leading article number can be eaten as a list marker.** Where a row began
  a line, whatever built the stored HTML read the number as an ordered-list
  marker and consumed it. Both shapes are real: February 5, 2026 opened a
  spurious nested `<ol>` mid-table and lost article 1's number; March 10, 2026
  started a new sibling `<li>`, lost article 8's number, and that stray item
  then swallowed the real agenda item 8, "Committee Reports". So a rebuild can
  *gain* content. Each gain is declared in `RECOVERED` and asserted on rather
  than absorbed into a total -- on March 10 the arithmetic nets to zero, which
  is exactly how a real change hides.
- **The table can run past its own list item**, so the script walks forward
  until every cell token is accounted for. Replacing only the header's own item
  would leave half a table behind.

What makes it safe to run unattended is the token check: every word of every
extracted cell must already be in the stored text, allowing for the one literal
"Article" the template adds per row and the four scrambled header words it
drops. Passing proves the rebuild is a re-ordering of the posting and not a
paraphrase. It compares alphanumeric tokens only -- a raw word comparison trips
over the added dashes and brackets, and over `Owner&rsquo;s` in the stored text
against `Owner's` in the PDF. Replaying both runs through the script reproduces
the hand-made result byte for byte.

**An unfamiliar table header is reported, not rendered.** The row format --
`Article 8 &ndash; Appropriation: ... (Select Board)`, description first and
sponsor in brackets -- is Frank's choice for the one header seen so far. A
table with different columns stops and asks.

**Leave the postings' own inconsistencies alone.** The same petitioner appears
as both `Stephen Maury et al` and `Stephen Maury, et al` across agendas, and one
description carries literal asterisks (`*aka Van Gilder Avenue*`). House rule is
the posting's own capitalization and punctuation, so all of it stays.

## Atheneum page specifics

`ATHENEUM_SERIES` holds video IDs grouped by series then year.
`ATHENEUM_TITLES` maps video ID → `(title, description)`. All 66 videos are
populated. Any ID missing from `ATHENEUM_TITLES` falls back to a generated
"<series> <year>" label, so new videos can be added IDs-first and captioned later.

Title patterns, normalized per section — match them when adding videos:

| Section | Pattern |
|---|---|
| Geschke Lectures | `<Year> Geschke Lecture Series: <Speaker>, <Talk title>` |
| Dance Festival | `<Year> Nantucket Dance Festival <Event type>` |
| Summer Forum | `<Year> Nantucket Annual Summer Forum` |
| Constance Laibe Hays | `<Year> Constance Laibe Hays Memorial Lecture: <Speaker>` |
| One Book One Island | varied by design — genuinely different event types |

Where a title carried a date that appears nowhere else, the date was moved to
the head of the description as its own line (e.g. "July 30, 2018").

## Book Festival page specifics

`BOOKFEST_YEARS` maps year → list of `(id, title, description)`: 2017, 2018,
2019, 2022, 2023, 2024, 2025, 2026 — 183 videos. There is no 2020 or 2021
button because there was no festival those years. Built with
`collapsible=False`, so the archive is one static heading rather than a
toggle.

Two conventions to keep when adding videos:

- **Titles carry no year or festival prefix.** The videos arrived with six
  different ones ("NBF 2017:", "2022 BookFest -", "BookFest 2024:"); they were
  all stripped, since the year is already on the button above the card. Promo
  clips, whose whole title was the festival's name, became "Festival Promo".
- **Book titles are wrapped in `<cite>`**, which `styles.css` renders italic.
  `<cite>` rather than `<em>` because a screen reader gives `<em>` vocal
  stress, which is wrong for a title. Periodicals and films on that page are
  not yet marked up.

Descriptions were written from the videos' auto-captions, two sentences each.
Videos with no transcript, and all montage/promo clips, have none by request.

## NHA page specifics

The largest page on the site: 675 cards in a two-level accordion under
"Programs". The top level is All Lectures, Nantucket Documentaries, Historic
Films, and two `Picker` parents — "Browse by Topic" (16 children) and
"Browse by NHA Program" (9) — whose children are drawn as rows of buttons
(Frank, 2026-10-25) and are alphabetical. Three of those buttons open a panel
holding a year picker, so this is the one page where a `.yearpick` sits inside
a `.yearpick`. Two sort cases
worth knowing: &rsquo;Sconset files under S, the leading apostrophe being
punctuation rather than a letter, and the four `Symposium:` playlists sort
together under S, then by what follows the colon.

Not every NHA playlist is on the page. Webinars, Special Events and
Fundraisers, and About the NHA were excluded by request, not overlooked.

Things that were decided deliberately and should not be "fixed" without asking:

- **Dead videos are left out.** Private and unavailable IDs in the NHA's
  playlists are skipped rather than linked; the NHA clears them on their own
  account.
- **Vertical videos are left out.** Shorts are dropped by comparing yt-dlp's
  `width` and `height` — `fetch-video.py --meta FILE` writes both.
- **Cross-listed videos stay.** ~38 videos appear in two sections because the
  NHA files them in two playlists. This is intentional.
- **Historic Films is ordered by when the footage was shot, not by upload
  date, and is not grouped by year.** 41 of its 44 videos were uploaded in
  2011-2012 when the collection was digitized, so upload dates sort it into
  noise and year buttons would put nearly everything under two labels. The
  list runs 1920s to 1976 by shooting date, read from the titles and
  descriptions. See the comment above `NHA_FILMS` in `build.py` before
  re-sorting it — a naive "earliest year in the description" scan gets six
  entries wrong.

## School Videos page specifics

The only page that introduces more than one organization. The hero is the
district; each school below it gets an `org_banner()` — the same shape as a
page hero but shorter, flatter and with no visible title, since the school's
name is already in its logo. A visually hidden `<h2>` keeps the heading for
screen readers and the document outline. Each school's
`programs_section(..., heading=None)` drops the "Programs" head so it is not
repeated three times down the page.

`NPS_COMMITTEE` is keyed by **school year**, July to June, as strings
("School Yr 25-26") rather than the integer years every other section uses.
`program_group()` sorts and renders dict keys as-is, so string keys need no
code change.

Deliberate, and not to be "fixed":

- **Meetings that have not happened yet are excluded.** The playlist carries
  scheduled premieres months ahead; they are filtered on yt-dlp's
  `live_status == is_upcoming`.
- **Only the two most recent school years have descriptions.** These meetings
  run two to four hours each, and 145 older ones are deliberately blank rather
  than thin. The descriptions YouTube holds are the same boilerplate paragraph
  with a dead Zoom registration link on every meeting, so they were not kept.
- **Meetings are filed by the date in their own title**, not the upload date.
  One title is wrong at the source — "2/4/29" went up in February 2020 — and is
  corrected to 2020-02-04.

## Fetching video metadata

`tools/fetch-video.py` pulls titles and descriptions from YouTube via `yt-dlp`
and prints them in this file's house format — HTML entities already escaped,
wrapped to 100 columns. Paste the output straight into `build.py`.

Use it instead of copying text off a YouTube page. It removes the entire class
of damage described under "Text pasted from YouTube arrives damaged" below.

```
python3 tools/fetch-video.py ID [ID ...]                 # flat (id, title, desc) lists
python3 tools/fetch-video.py --format atheneum ID ...    # ATHENEUM_TITLES dict entries
python3 tools/fetch-video.py --playlist URL              # a whole channel or playlist
```

Three flags worth knowing: `--paras 1` keeps only the first paragraph (YouTube
descriptions usually trail off into boilerplate), `--strip-urls` drops bare
links, and `--meta FILE` writes `id<TAB>year<TAB>width<TAB>height` rows
alongside the output. `--meta` is how vertical videos and upload years are
found — `height > width` means a Short. Progress goes to stderr, so
`> out.txt` captures clean output only.

**Requires `yt-dlp`**, found at `~/.local/bin/yt-dlp` or anywhere on `PATH`
(override with `--ytdlp PATH`). It is not bundled; install the official binary
from <https://github.com/yt-dlp/yt-dlp/releases> if it's missing.

Three things to watch:

- **Playlists can list the same video several times.** The 2019 playlist had 65
  entries for 28 videos. Deduplicate before building a year, or the page repeats
  cards. `--playlist` does not deduplicate.
- **A video with no YouTube description yields `""`**, marked with an inline
  `# TODO` comment and listed on stderr. Several descriptions in `build.py` were
  written by hand and do not exist on YouTube — pasting over them loses real
  copy. Check the TODO lines before committing.
- **It fixes mechanical damage only.** A misspelled surname or a wrong book
  title still needs a human read. Proofread the output.

## Gotchas learned the hard way

**HTML inside a label breaks attributes.** The Summer Forum section label
contains a `<span>` for the co-sponsor note. Interpolating that into an
`aria-label` closed the attribute early and dumped markup onto the page as
visible text. `program_group()` strips tags with `re.sub(r"<[^>]+>", "", label)`
before using a label in an attribute. Do the same anywhere else.

**Text pasted from YouTube arrives damaged.** Recurring problems, all seen in
real copy: mojibake (`Ã ` for `à`, `â€™` for `'`) from UTF-8 read as cp1252;
quotes that open single and close double; YouTube redirect wrappers around links
(`youtube.com/redirect?event=video_description&redir_token=...`); timestamp links
wrapped around times like "9:30"; doubled spaces; invisible characters such as a
zero-width joiner at the end of a title (one real 2025 Book Festival title ends
in one) — they display as nothing but leave stray bytes in the HTML. Always read
pasted metadata before committing it — several real errors (a misspelled surname,
a missing verb, a wrong book title) were caught this way.

Don't paste by hand if you can avoid it — `tools/fetch-video.py` pulls the text
straight from YouTube already cleaned and escaped. See "Fetching video metadata"
above. (The mojibake is cp1252, not Latin-1: `â€™` contains `€`, which Latin-1
can't encode, so a Latin-1 round-trip repairs nothing.)

**YouTube thumbnails, and why `onerror` doesn't work.** `nl_episode()` falls
back to `img.youtube.com/vi/<id>/maxresdefault.jpg` when no local thumbnail is
given. Older uploads have no `maxresdefault`, and YouTube answers those with a
404 whose *body* is a valid 120x90 grey placeholder — so the browser decodes it
and fires `load`, not `error`, and an `onerror` handler never runs.
`initThumbFallback()` in `site.js` detects the placeholder by its width and
swaps in `hqdefault`, which always exists. This is automatic; nothing to do
when adding videos. Nantucket Life uses local thumbnails in `assets/`.

**Measuring anything inside a closed `<details>` returns zero.** The ten-line
description clamp (`clampDescriptions()` in `site.js`, "Click to See More")
can't tell whether text overflows until its section is actually visible, so it
re-runs on `<details>` toggle and on board-, year- and quarter-button clicks.
The Civic TV page needs all three: most of its cards sit three pickers deep
(two for the boards in `CIVIC_NO_QUARTERS`) and have no measurable height until
the innermost panel is showing. Anything else
that measures rendered height needs the same treatment. When checking this in a
browser pane, give the pane a real width first — a zero-width viewport reports
every description as overflowing.

**`yt-dlp --print` does not interpret `\t`.** `--print "%(id)s\t%(width)s"`
writes a literal backslash-t, not a tab, so `awk -F'\t'` sees one field and
silently reports nothing. This cost two debugging sessions: once parsing a
playlist list, once scanning for vertical videos, where it reported 0 of 13.
Use `fetch-video.py --meta` instead, which writes real tabs.

**`yt-dlp` inside a `while read` loop eats the loop's input.** It reads stdin,
so the loop consumes its own list and runs once. Redirect it: `yt-dlp ... </dev/null`.

**English captions are often under `en-orig`, not `en`.** On videos with
multiple audio tracks, YouTube names the original-language auto-captions
`en-orig` and publishes a plain `en` that is a *machine translation* of it.
`--sub-lang en` can miss the real track entirely and report a video as having
no captions when it has a half-megabyte transcript. Worse, when `en` does
download it reads like a bad translation — one School Committee meeting came
through calling a school "the Impedance school". Ask for both, original first:

```
yt-dlp --write-auto-subs --sub-lang "en-orig,en" --sub-format vtt ...
```

Check with `--list-subs` before concluding a video has no transcript; four
School Committee meetings were wrongly recorded as caption-less this way.

**Then pick the file by name, not by size.** Downloading both leaves two files
and the choice still has to be made. On 2026-10-11 a selection of `ls -S | head
-1` took the larger file, which for one video was the translation, and it
reached the point of being read before the giveaways showed up — "Office of
City Administration", "the Health Board", "a hardship discharge procedure",
"Congratulations" for hello. The site owner's rule since: **always `en-orig`,
never `en`.** The one exception is a video that has only `en` and no `en-orig`
— there the `en` track is the original recognition, not a translation.

**Use HTML entities** in titles and descriptions: `&amp;` `&rsquo;` `&ldquo;`
`&rdquo;` `&ndash;` `&mdash;` `&hellip;`. Unescaped `&` can break the page.

## Verifying a change

After rebuilding, it's worth checking:

- every referenced `assets/...` file exists
- every internal `href="*.html"` resolves
- no duplicate video IDs where they'd be unintended (note that a description
  can legitimately contain a `youtu.be/` link to another video — match on the
  card's own `watch-episode__link`, not on any URL in the page)
- the page parses (`html.parser.HTMLParser().feed(...)`)
- the build is idempotent: run it twice, compare `md5 -q` of a page
- the card count didn't change when it shouldn't have — reorganizing sections
  should move cards, never drop them

Note that a page can pass all of these and still render wrong — the `aria-label`
bug above did. **Look at the actual page in a browser.**

## Previewing

Open `index.html` directly in Safari (`file://` works — no server needed; no
module scripts, no `fetch()`, no absolute paths). Hard refresh with
**Cmd+Option+E, then reload**.

Stay online when previewing: fonts come from Google Fonts and some thumbnails
from YouTube.

For a closer match to production: `python3 -m http.server 8000`, then
`http://localhost:8000`.
