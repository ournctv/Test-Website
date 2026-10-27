/* =====================================================================
   Nantucket Community Television — search.js
   ---------------------------------------------------------------------
   Runs only on search.html. `search-index.js`, written by build.py, has
   already put every video on the site into window.NCTV_SEARCH as
   { pages: [[file, label], ...], videos: [[id, title, description, page]] }.

   Nothing here talks to a server: the whole archive is in memory, so a
   query is a scan over ~5,000 records, which is a few milliseconds.
   ===================================================================== */

(function(){
"use strict";

const MAX_RESULTS = 60;      // beyond this the list stops being a list
const SNIPPET = 260;         // characters of description shown per result

/* Field positions in a record. Wrapped in an IIFE, and named apart from
   site.js's own globals, because every script on the page shares one scope. */
const ID = 0, TITLE = 1, DESC = 2, PAGE = 3;

/* ---------- query ---------- */
function terms(q){
  return q.toLowerCase().split(/[^a-z0-9'&]+/i).filter(t => t.length > 1);
}

/* A whole word, or the start of one — "whal" should find "whaling", but
   "ale" should not. */
function wordish(hay, term){
  let from = 0;
  for(;;){
    const at = hay.indexOf(term, from);
    if(at < 0) return 0;
    const before = at === 0 ? " " : hay[at - 1];
    if(!/[a-z0-9]/.test(before)){
      const after = hay[at + term.length];
      return (after === undefined || !/[a-z0-9]/.test(after)) ? 2 : 1;  // whole word, or prefix
    }
    from = at + 1;
  }
}

function countOf(hay, term){
  let n = 0, from = 0, at;
  while((at = hay.indexOf(term, from)) >= 0 && n < 4){ n++; from = at + term.length; }
  return n;
}

/* Returns [points, terms matched]. Title matches beat description matches;
   how many of the query's words were found is weighed separately, by run(). */
function score(rec, ts, phrase){
  const title = rec._t, desc = rec._d;
  let total = 0, matched = 0;
  for(const t of ts){
    const inTitle = wordish(title, t);
    const inDesc  = wordish(desc, t);
    if(!inTitle && !inDesc) continue;
    matched++;
    if(inTitle) total += inTitle === 2 ? 12 : 7;
    if(inDesc)  total += (inDesc === 2 ? 4 : 2) + Math.min(countOf(desc, t) - 1, 3) * 0.6;
  }
  if(ts.length > 1 && matched){
    if(title.indexOf(phrase) >= 0) total += 20;
    else if(desc.indexOf(phrase) >= 0) total += 9;
  }
  return [total, matched];
}

/* ---------- rendering ---------- */
function escapeHtml(s){
  return s.replace(/[&<>"]/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;" }[c]));
}

/* Start the snippet at the first match rather than at the start of the
   description, so the reader can see why the video came back. */
function snippet(desc, lower, ts){
  if(!desc) return "";
  let first = -1;
  for(const t of ts){
    const at = lower.indexOf(t);
    if(at >= 0 && (first < 0 || at < first)) first = at;
  }
  let start = 0;
  if(first > SNIPPET * 0.4){
    start = desc.lastIndexOf(" ", first - 60);
    if(start < 0) start = first;
  }
  let cut = desc.slice(start, start + SNIPPET);
  if(start + SNIPPET < desc.length){
    const space = cut.lastIndexOf(" ");
    if(space > SNIPPET * 0.6) cut = cut.slice(0, space);
    cut += "…";
  }
  return (start > 0 ? "…" : "") + cut;
}

function highlight(text, ts){
  let out = escapeHtml(text);
  for(const t of ts){
    const safe = t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    out = out.replace(new RegExp("(^|[^a-z0-9])(" + safe + ")", "gi"), "$1<mark>$2</mark>");
  }
  return out;
}

function card(rec, pages, ts){
  const [file, label] = pages[rec[PAGE]];
  const watch = rec[ID]
    ? `<a class="watch-episode__link" href="https://youtu.be/${rec[ID]}" target="_blank" rel="noopener">Click Here to Watch</a>`
    : "";
  const thumb = rec[ID]
    ? `<div class="watch-episode__thumb">
         <img src="https://img.youtube.com/vi/${rec[ID]}/hqdefault.jpg" alt="${escapeHtml(rec[TITLE])}" loading="lazy">
       </div>`
    : "";
  const text = snippet(rec[DESC], rec._d, ts);
  return `<article class="watch-episode search-result">
      ${thumb}
      <div class="watch-episode__text">
        <h3 class="watch-episode__title">${highlight(rec[TITLE], ts)}</h3>
        ${text ? `<p class="watch-episode__desc">${highlight(text, ts)}</p>` : ""}
        <p class="search-result__where">On <a href="${file}">${escapeHtml(label)}</a></p>
        ${watch}
      </div>
    </article>`;
}

/* ---------- page ---------- */
function initSearch(){
  const input   = document.querySelector("[data-search-input]");
  const status  = document.querySelector("[data-search-status]");
  const results = document.querySelector("[data-search-results]");
  const data    = window.NCTV_SEARCH;
  if(!input || !results) return;

  if(!data){
    status.textContent = "The search index did not load. Please reload the page.";
    return;
  }

  // One lowercase copy of each record, made once, reused by every query.
  const recs = data.videos;
  recs.forEach(r => { r._t = r[TITLE].toLowerCase(); r._d = r[DESC].toLowerCase(); });

  const query = new URLSearchParams(location.search).get("q") || "";
  input.value = query;

  function run(q){
    const ts = terms(q);
    if(!ts.length){
      status.textContent = `Search ${recs.length.toLocaleString()} videos by title or description.`;
      results.innerHTML = "";
      return;
    }
    const phrase = ts.join(" ");
    const hits = [];
    let best = 0;
    for(const r of recs){
      const got = score(r, ts, phrase);
      if(!got[1]) continue;
      if(got[1] > best) best = got[1];
      hits.push([got[0], r, got[1]]);
    }
    // Someone who types three words wants the videos that have all three.
    // Records matching fewer are dropped rather than ranked below, so the
    // count means something; if nothing matches every word, the best
    // available number of words becomes the bar instead.
    const full = hits.filter(h => h[2] === best);
    full.sort((a, b) => b[0] - a[0]);

    // A few dozen videos are filed under two sections on purpose (the NHA
    // page cross-lists its talks). That is right on the page and wrong here,
    // so each video appears once, under its best-scoring entry.
    const seen = new Set();
    const found = full.filter(h => {
      const id = h[1][ID];
      if(!id || !seen.has(id)){ seen.add(id); return true; }
      return false;
    });

    if(!found.length){
      status.textContent = `No videos match “${q.trim()}”.`;
      results.innerHTML = `<p class="search-empty">Try a single word, or a name, or the subject of a meeting.</p>`;
      return;
    }
    const shown = found.slice(0, MAX_RESULTS);
    status.textContent = found.length > shown.length
      ? `${found.length.toLocaleString()} videos match “${q.trim()}”. Showing the closest ${shown.length}.`
      : `${found.length === 1 ? "One video matches" : found.length.toLocaleString() + " videos match"} “${q.trim()}”.`;
    results.innerHTML = shown.map(h => card(h[1], data.pages, ts)).join("");
  }

  run(query);

  // Typing re-runs the search in place; the form still works without JS and
  // for anyone arriving from the search box in the header.
  let timer;
  input.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const q = input.value;
      run(q);
      const url = q.trim() ? `?q=${encodeURIComponent(q.trim())}` : location.pathname;
      history.replaceState(null, "", url);
    }, 160);
  });
}

if(document.readyState === "loading"){
  document.addEventListener("DOMContentLoaded", initSearch);
}else{
  initSearch();
}

})();
