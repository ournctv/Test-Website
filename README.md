# Nantucket Community Television — Website

A static website. No framework, no database, no install step beyond Python.
To go live, upload this whole folder to any web host.

## Important: the HTML files are generated

Every `.html` file here is written by `build.py`. **Editing them directly does
nothing** — your changes are overwritten the next time the site is built.

To change anything:

1. Edit `build.py` (content, page structure), `styles.css` (appearance), or
   `site.js` (navigation, footer, interactive bits).
2. Run the build:

   ```
   python3 build.py
   ```

   It prints "Wrote 26 pages".

3. Open `index.html` in your browser and hard refresh (**Cmd+Option+E**, then
   reload) to get past Safari's cache.

If you changed `styles.css`, `site.js`, or anything in `assets/`, also bump
`ASSET_VER` near the top of `build.py` — that's what forces browsers to pick up
the new files.

## What's in this folder

```
build.py        Generates every page. Content and page structure live here.
styles.css      All styling. Colors are in the :root block at the top.
site.js         Navigation, footer, calendar, scroll reveals, year pickers.
assets/         Logos, thumbnails, banners, favicon.
tools/          Helper scripts. fetch-video.py pulls YouTube titles and
                descriptions in the format build.py expects.
CLAUDE.md       Conventions and gotchas — read this before making changes.
*.html          Generated. Do not edit.
```

## Common edits

**Navigation menu** — the `NAV` list at the top of `site.js`. Defined once,
applies to all 26 pages.

**Colors** — the `:root` block at the top of `styles.css`. Change a value there
and it updates everywhere.

**Contact details** — in `build.py` for the Hours & Contact page, and in the
footer builder in `site.js`.

**Adding videos to a partner page** — see CLAUDE.md, which documents the two
page templates and the metadata structures.

## Previewing locally

Opening `index.html` straight from the folder works — there are no module
scripts, `fetch()` calls, or absolute paths. Stay online so Google Fonts and
YouTube thumbnails load.

For something closer to a real server:

```
python3 -m http.server 8000
```

then visit `http://localhost:8000`.
