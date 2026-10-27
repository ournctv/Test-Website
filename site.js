/* =====================================================================
   Nantucket Community Television — site.js
   ---------------------------------------------------------------------
   Builds the navigation bar and footer on every page, so you only edit
   them HERE (once) instead of in 12 separate files.

   TO ADD / RENAME / REORDER A NAV LINK: edit the NAV array just below.
   Each top-level item with `children` becomes a dropdown.
   `href:null` means the item is a dropdown trigger only (not a link).
   `external:true` opens the link in a new tab — use it for anything that
   leaves this site, like the Donate form.
   ===================================================================== */

const NAV = [
  { label: "About", href: null, children: [
      { label: "Staff &amp; Board", href: "about-staff.html" },
      { label: "Hours & Contact", href: "about-hours-contact.html" },
  ]},
  { label: "Watch", href: null, children: [
      { label: "Live TV", href: "https://u.peg.tv/s/afezr0", external: true },
      { label: "Nantucket Civic TV",        href: "videos-civic.html" },
      { label: "Nantucket Life",            href: "videos-nantucket-life.html" },
      { label: "Nantucket Sports Connection", href: "videos-sports-connection.html" },
      { label: "Nonprofit Videos",          href: "videos-partner-programs.html" },
      { label: "School Videos",             href: "videos-school.html" },
      { label: "Past TV Shows",            href: "videos-past-shows.html" },
  ]},
  { label: "Shorts Fest",   href: "events-shorts-fest.html" },
  { label: "New Moon Fest", href: "events-new-moon-fest.html" },
  { label: "Free Services", href: "create.html" },
  { label: "Donate", href: "https://donate.stripe.com/7sYbJ0dFD8IVd7k9XQ0VO07", external: true },
];

const PAGE = (document.body.dataset.page || "").toLowerCase();

/* ---------- build nav ---------- */
function buildNav(){
  const mount = document.getElementById("site-nav");
  if(!mount) return;

  const chev = '<span class="chev" aria-hidden="true"></span>';
  let items = "";

  NAV.forEach(item=>{
    if(item.children){
      const childCurrent = item.children.some(c=>c.href===PAGE);
      const links = item.children.map(c=>{
        const cur = c.href===PAGE ? " is-current" : "";
        const ext = c.external ? ' target="_blank" rel="noopener"' : "";
        return `<a class="${cur.trim()}" href="${c.href}"${ext}>${c.label}</a>`;
      }).join("");
      items += `
        <div class="nav__item">
          <button class="nav__link${childCurrent?" is-current":""}" aria-haspopup="true" aria-expanded="false">
            ${item.label}${chev}
          </button>
          <div class="nav__panel">${links}</div>
        </div>`;
    } else {
      const cur = item.href===PAGE ? " is-current" : "";
      const ext = item.external ? ' target="_blank" rel="noopener"' : "";
      items += `
        <div class="nav__item">
          <a class="nav__link${cur}" href="${item.href}"${ext}>${item.label}</a>
        </div>`;
    }
  });

  // Search sits at the end of the menu row, which puts it in the top right
  // corner on a wide screen; on mobile the menu becomes a column and `order`
  // lifts it to the top of it. It is a plain GET form, so it works without
  // JavaScript and from a file:// preview.
  const search = `
      <form class="nav__search" role="search" action="search.html">
        <input class="nav__search-input" type="search" name="q" placeholder="Search videos"
               aria-label="Search videos" autocomplete="off" spellcheck="false">
        <button class="nav__search-btn" type="submit" aria-label="Search">
          <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor"
               stroke-width="2.2" stroke-linecap="round">
            <circle cx="11" cy="11" r="7"></circle><path d="M20 20l-3.6-3.6"></path>
          </svg>
        </button>
      </form>`;

  mount.className = "nav";
  mount.innerHTML = `
    <div class="wrap">
      <a class="nav__brand" href="index.html" aria-label="Nantucket Community Television — home">
        <img src="assets/NCTV_Full_Name.webp" alt="Nantucket Community TV — Civic + HD · Channels 8 | 1072">
      </a>
      <button class="nav__burger" aria-label="Menu" aria-expanded="false">
        <span></span><span></span><span></span>
      </button>
      <nav class="nav__menu" aria-label="Primary">${items}${search}</nav>
    </div>`;

  wireNav(mount);
}

function wireNav(nav){
  const burger = nav.querySelector(".nav__burger");
  burger.addEventListener("click", ()=>{
    const open = nav.classList.toggle("is-open");
    burger.setAttribute("aria-expanded", open);
  });

  const items = [...nav.querySelectorAll(".nav__item")];
  const mobile = ()=> window.matchMedia("(max-width:1100px)").matches;

  items.forEach(item=>{
    const trigger = item.querySelector(".nav__link");
    const hasPanel = item.querySelector(".nav__panel");
    if(!hasPanel) return;

    // On desktop, hover + keyboard focus open the panel via CSS — the click
    // just shouldn't navigate. On mobile, click toggles the accordion.
    trigger.addEventListener("click",(e)=>{
      e.preventDefault();
      if(!mobile()) return;               // desktop handled by CSS hover/focus
      const open = item.classList.contains("open");
      items.forEach(i=>{
        i.classList.remove("open");
        const t=i.querySelector(".nav__link"); if(t) t.setAttribute("aria-expanded","false");
      });
      if(!open){ item.classList.add("open"); trigger.setAttribute("aria-expanded","true"); }
    });
  });

  // close dropdowns when clicking outside
  document.addEventListener("click",(e)=>{
    if(!nav.contains(e.target)){
      items.forEach(i=>i.classList.remove("open"));
    }
  });
  // esc closes everything
  document.addEventListener("keydown",(e)=>{
    if(e.key==="Escape"){
      items.forEach(i=>i.classList.remove("open"));
      nav.classList.remove("is-open");
      burger.setAttribute("aria-expanded","false");
    }
  });
}

/* ---------- build footer ---------- */
function buildFooter(){
  const mount = document.getElementById("site-footer");
  if(!mount) return;
  mount.className = "footer";
  mount.innerHTML = `
    <div class="wrap">
      <div class="footer__top">
        <p class="footer__addr">
          Nantucket Community Television<br>
          9 Bayberry Court<br>
          Nantucket, MA 02554<br><br>
          <a href="mailto:info@ournctv.org">info@ournctv.org</a><br>
          <a href="tel:+15089015499">508-901-5499</a>
        </p>
        <span class="footer__brand">
          <img src="assets/nctv-logo-whitetext.webp" alt="NCTV — Nantucket Community Television">
        </span>
      </div>
      <div class="footer__bar">
        <span>© ${new Date().getFullYear()} Nantucket Community Television</span>
        <span>TV CHANNELS: CIVIC 8 &amp; HD 1072 · NANTUCKET, MA</span>
      </div>
    </div>`;
}

/* ---------- interactive month calendar (home) ---------- */
function initCalendar(){
  const cal = document.getElementById("nctvCalendar");
  if(!cal) return;
  const months = [...cal.querySelectorAll(".calendar__month")];
  const grids  = [...cal.querySelectorAll(".calendar__grid")];
  const hint   = cal.querySelector("[data-calendar-hint]");

  months.forEach(btn=>{
    btn.addEventListener("click",()=>{
      const m = btn.dataset.month;
      const isActive = btn.classList.contains("is-active");
      months.forEach(b=>b.classList.remove("is-active"));
      grids.forEach(g=>{ g.hidden = true; });
      if(hint) hint.hidden = true;
      if(!isActive){
        btn.classList.add("is-active");
        const grid = grids.find(g=>g.dataset.month===m);
        if(grid) grid.hidden = false;
      } else if(hint){
        hint.hidden = false;   // toggled the active month off again
      }
    });
  });
}

/* ---------- scroll reveal ---------- */
function initReveal(){
  const els = document.querySelectorAll("[data-reveal]");
  if(!("IntersectionObserver" in window) ||
     window.matchMedia("(prefers-reduced-motion:reduce)").matches){
    els.forEach(el=>el.classList.add("in")); return;
  }
  const io = new IntersectionObserver((entries)=>{
    entries.forEach(en=>{ if(en.isIntersecting){ en.target.classList.add("in");
      io.unobserve(en.target);} });
  },{rootMargin:"0px 0px -8% 0px",threshold:.12});
  els.forEach(el=>io.observe(el));
}

/* ---------- New Moon Fest: Official Film Selections movie picker ---------- */
function initMoviePicker(){
  /* Scope on the row of film buttons and the panels beside it, not on the
     wrapper. The New Moon Fest years were <details class="pastsel__year">
     until 2026-10-18 and are now panels of a year picker; keying off the
     structure instead of that class survives the change. */
  document.querySelectorAll(".pastsel__movies").forEach(function(row){
    var group = row.parentElement;
    var btns = row.querySelectorAll(".movie-btn");
    var panels = group.querySelectorAll(".movie-panel");
    btns.forEach(function(btn){
      btn.addEventListener("click",function(){
        var slug = btn.getAttribute("data-movie");
        var target = group.querySelector('.movie-panel[data-movie="'+slug+'"]');
        var wasActive = btn.classList.contains("is-active");
        btns.forEach(function(b){ b.classList.remove("is-active"); });
        panels.forEach(function(p){ p.hidden = true; });
        if(!wasActive && target){ btn.classList.add("is-active"); target.hidden = false; }
      });
    });
  });
}

/* ---------- Atheneum: year picker for lecture archives ----------
   Like the movie picker above, but one year is always selected: clicking the
   active year again leaves it open rather than collapsing to nothing. */
/* ---------- committee picker ----------
   The civic archive asks for a board before it asks for a year, so this is the
   outer twin of initYearPicker: same toggle, one level up. Its classes are
   deliberately distinct from the year picker's -- a nested .yearpick would
   otherwise be swept up by that function's descendant lookup.

   The reader's year and quarter follow them from board to board. Asked for on
   2026-10-11: picking a new board used to drop you back to no year and no
   quarter, so comparing the same months across two boards meant three clicks
   each way. The choice is remembered here, in memory only, so a page refresh
   starts over -- also asked for.

   Only the civic page has a board picker, and .yearpick is shared with the
   partner and school pages, which open on a year chosen in the markup. So
   everything below is scoped to .boardpick and is inert everywhere else. */
var civicPick = { year: null, quarter: null };

/* Clearing a level still clears every level below it. The difference is that a
   level is now re-selected from civicPick straight afterwards, when the board
   or year the reader moved to happens to offer what they had chosen. */
function clearPicks(root, btnSel, panelSel){
  root.querySelectorAll(btnSel).forEach(function(b){
    b.classList.remove("is-active");
    if(!b.disabled) b.setAttribute("aria-pressed", "false");
  });
  root.querySelectorAll(panelSel).forEach(function(p){ p.hidden = true; });
}

function initQuarterPicker(){
  document.querySelectorAll(".quarterpick").forEach(function(pick){
    var btns   = pick.querySelectorAll(".quarter-btn");
    var panels = pick.querySelectorAll(".quarter-panel");
    btns.forEach(function(btn){
      if(btn.disabled) return;
      btn.addEventListener("click", function(){
        var want = btn.getAttribute("data-quarter");
        if(pick.closest(".boardpick")) civicPick.quarter = want;
        btns.forEach(function(b){
          var on = b === btn;
          b.classList.toggle("is-active", on);
          if(!b.disabled) b.setAttribute("aria-pressed", on ? "true" : "false");
        });
        panels.forEach(function(p){
          p.hidden = p.getAttribute("data-quarter") !== want;
        });
      });
    });
  });
}

/* Re-select the remembered quarter inside a year panel that has just opened.
   An empty quarter is rendered disabled and gets no panel at all, so a board
   that simply has no meetings that quarter leaves the row unselected -- and
   civicPick keeps the value, ready for the next board that does have it. */
function restoreQuarter(yearPanel){
  var qp = yearPanel.querySelector(".quarterpick");
  if(!qp) return;
  clearPicks(qp, ".quarter-btn", ".quarter-panel");
  if(civicPick.quarter === null) return;
  var btn   = qp.querySelector('.quarter-btn[data-quarter="' + civicPick.quarter + '"]');
  var panel = qp.querySelector('.quarter-panel[data-quarter="' + civicPick.quarter + '"]');
  if(!btn || btn.disabled || !panel) return;
  btn.classList.add("is-active");
  btn.setAttribute("aria-pressed", "true");
  panel.hidden = false;
}

/* The same, one level up, for a board panel that has just opened. A board whose
   archive does not reach the remembered year has no button to press, so it
   opens on no year, exactly as it did before. */
function restoreYear(boardPanel){
  var yp = boardPanel.querySelector(".yearpick");
  if(!yp) return;
  clearPicks(yp, ".year-btn", ".year-panel");
  clearPicks(yp, ".quarter-btn", ".quarter-panel");
  if(civicPick.year === null) return;
  var btn   = yp.querySelector('.year-btn[data-year="' + civicPick.year + '"]');
  var panel = yp.querySelector('.year-panel[data-year="' + civicPick.year + '"]');
  if(!btn || !panel) return;
  btn.classList.add("is-active");
  btn.setAttribute("aria-pressed", "true");
  panel.hidden = false;
  restoreQuarter(panel);
}

function initBoardPicker(){
  document.querySelectorAll(".boardpick").forEach(function(pick){
    var btns   = pick.querySelectorAll(".board-btn");
    var panels = pick.querySelectorAll(".board-panel");
    btns.forEach(function(btn){
      btn.addEventListener("click", function(){
        var want = btn.getAttribute("data-board");
        var open = !btn.classList.contains("is-active");
        btns.forEach(function(b){
          var on = (b === btn) && open;
          b.classList.toggle("is-active", on);
          b.setAttribute("aria-pressed", on ? "true" : "false");
        });
        panels.forEach(function(p){
          var mine = p.getAttribute("data-board") === want;
          p.hidden = !(mine && open);
          if(p.hidden){
            clearPicks(p, ".year-btn", ".year-panel");
            clearPicks(p, ".quarter-btn", ".quarter-panel");
          } else {
            restoreYear(p);
          }
        });
      });
    });
  });
}

/* ---------- sport picker (NSC archive) ----------
   The outer level of the Sports Connection archive: pick a sport, then a
   school year, then the games. Shaped like initBoardPicker but with none of
   its remembered state -- there is no third level here to restore, and the
   class is its own so the civic picker's logic stays out of it. */
/* ---------- Past TV Shows: sortable columns ----------
   Show Name sorts alphabetically, the two date columns chronologically. Every
   sortable cell carries data-sort: the name lowercased, and dates as ISO, whole
   or partial. ISO sorts correctly as plain text, so no date parsing is needed
   here. Clicking the column already sorted reverses it. A row with nothing in
   that column sits at the bottom either way -- flipping the direction should
   not push the blanks to the top. */
function initShowsTable(){
  document.querySelectorAll(".shows__table").forEach(function(table){
    var tbody = table.querySelector("tbody");
    if(!tbody) return;
    var heads = table.querySelectorAll("thead th[aria-sort]");
    heads.forEach(function(th){
      var btn = th.querySelector(".shows__sort");
      if(!btn) return;
      btn.addEventListener("click", function(){
        var idx = th.cellIndex;
        var dir = th.getAttribute("aria-sort") === "ascending" ? "descending" : "ascending";
        heads.forEach(function(h){ h.setAttribute("aria-sort", "none"); });
        th.setAttribute("aria-sort", dir);
        var key = function(row){
          var c = row.cells[idx];
          if(!c) return "";
          // An empty data-sort means "no value here", so it has to win over the
          // cell's text -- otherwise a blank date sorts as its em dash and the
          // blanks climb to the top when the order is reversed.
          var v = c.hasAttribute("data-sort") ? c.getAttribute("data-sort") : c.textContent;
          return (v || "").trim().toLowerCase();
        };
        // A show and its episode panel are two rows but one unit: sort the
        // show rows and carry each panel along, or the panels end up under
        // whichever show happens to land above them.
        var pairs = Array.prototype.slice.call(tbody.rows)
          .filter(function(r){ return !r.classList.contains("shows__panel"); })
          .map(function(r){
            var n = r.nextElementSibling;
            return [r, (n && n.classList.contains("shows__panel")) ? n : null];
          });
        // Ties fall back to the show name, which is always column 0.
        var nameKey = function(row){
          var c = row.cells[0];
          if(!c) return "";
          var v = c.hasAttribute("data-sort") ? c.getAttribute("data-sort") : c.textContent;
          return (v || "").trim().toLowerCase();
        };
        var rows = pairs.map(function(pr){ return pr[0]; });
        rows.sort(function(a, b){
          var x = key(a), y = key(b);
          if(!x) return y ? 1 : 0;      // blanks last, whichever way the column runs
          if(!y) return -1;
          if(x !== y) return (x < y ? -1 : 1) * (dir === "ascending" ? 1 : -1);
          // Equal in this column -- two shows of one genre, or one year. Order
          // them by name, A-Z either way, so the grouping stays readable.
          var nx = nameKey(a), ny = nameKey(b);
          return nx === ny ? 0 : (nx < ny ? -1 : 1);
        });
        var panelOf = new Map(pairs);
        rows.forEach(function(r){
          tbody.appendChild(r);
          var pnl = panelOf.get(r);
          if(pnl) tbody.appendChild(pnl);
        });
      });
    });

    // 2. clicking a show name opens its episodes, one show at a time
    tbody.querySelectorAll(".shows__name").forEach(function(btn){
      btn.addEventListener("click", function(){
        var row = btn.closest("tr");
        var panel = row.nextElementSibling;
        if(!panel || !panel.classList.contains("shows__panel")) return;
        var opening = panel.hidden;
        tbody.querySelectorAll(".shows__panel").forEach(function(p){
          if(!p.hidden){ clearPicks(p, ".year-btn", ".year-panel"); }
          p.hidden = true;
        });
        tbody.querySelectorAll(".shows__name").forEach(function(b){
          b.setAttribute("aria-expanded", "false");
        });
        if(opening){
          panel.hidden = false;
          btn.setAttribute("aria-expanded", "true");
        }
        clampDescriptions(panel);
      });
    });
  });
}

/* ---------- Instagram reels ----------
   Hiding an <iframe> does not stop it: a cross-origin embed keeps playing, and
   its sound keeps coming, from a card that has been collapsed or a panel that
   has been switched away from. Instagram exposes no player API we can call
   from here, so the frame is unloaded instead -- its src is parked on data-src
   and put back when it is next shown. Unloading also frees the player rather
   than leaving it running out of sight. */
function stopReels(root){
  (root || document).querySelectorAll("iframe.reel").forEach(function(f){
    var src = f.getAttribute("src");
    if(src){ f.dataset.src = src; f.removeAttribute("src"); }
  });
}
function startReels(root){
  (root || document).querySelectorAll("iframe.reel").forEach(function(f){
    // Only load one the reader can actually see. Any hidden ancestor counts --
    // its own card may be collapsed, or the school year or sport above it may
    // be shut. Restoring regardless would fetch the embed, and hand Instagram
    // a visit, for a reel nobody is looking at.
    if(f.closest("[hidden]")) return;
    if(!f.getAttribute("src") && f.dataset.src) f.setAttribute("src", f.dataset.src);
  });
}

function initSportPicker(){
  document.querySelectorAll(".sportpick").forEach(function(pick){
    var btns   = pick.querySelectorAll(".sport-btn");
    var panels = pick.querySelectorAll(".sport-panel");
    btns.forEach(function(btn){
      btn.addEventListener("click", function(){
        var want = btn.getAttribute("data-sport");
        var open = !btn.classList.contains("is-active");
        btns.forEach(function(b){
          var on = (b === btn) && open;
          b.classList.toggle("is-active", on);
          b.setAttribute("aria-pressed", on ? "true" : "false");
        });
        panels.forEach(function(p){
          var mine = p.getAttribute("data-sport") === want;
          p.hidden = !(mine && open);
          if(p.hidden){ clearPicks(p, ".year-btn", ".year-panel"); stopReels(p); }
          else startReels(p);
        });
      });
    });
  });
}

/* Photo lightbox for the Shorts Fest gallery.

   The overlay is built on the first click rather than shipped in every page,
   and the large file is only fetched at that point -- the grid carries the
   small copies, so opening the gallery costs a few hundred KB and a full-size
   photo is loaded only when somebody actually asks for one. */
function initPhotoLightbox(){
  var box = null, lastFocus = null;

  function build(){
    box = document.createElement("div");
    box.className = "lightbox";
    box.hidden = true;
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.setAttribute("aria-label", "Photo viewer");
    box.innerHTML =
      '<button type="button" class="lightbox__close" aria-label="Close photo">\u00d7</button>' +
      '<figure class="lightbox__fig">' +
        '<img class="lightbox__img" alt="">' +
        '<figcaption class="lightbox__credit"></figcaption>' +
      '</figure>';
    // Anything that is not the photo itself, or a link in its caption, closes
    // the viewer. Testing for `e.target === box` was not enough: the <figure>
    // stretches to the full width of the overlay, so a portrait photo had
    // roughly 300px of figure down either side where a click hit the figure
    // and nothing happened. Asking what was clicked, rather than where, keeps
    // this right however the layout changes.
    box.addEventListener("click", function(e){
      if(e.target.closest(".lightbox__img, .lightbox__credit a")) return;
      closeBox();
    });
    document.body.appendChild(box);
  }

  function openBox(item){
    if(!box) build();
    lastFocus = document.activeElement;
    var thumb = item.querySelector("img");
    var img = box.querySelector(".lightbox__img");
    img.src = item.getAttribute("data-full");
    img.alt = thumb ? thumb.alt : "";
    // Reuse the credit already rendered above the grid rather than repeating
    // it in a data attribute: the two can then never disagree, and a year
    // published without a credit simply shows none here either.
    var panel  = item.closest(".year-panel");
    var credit = panel && panel.querySelector(".photo-credit");
    var slot   = box.querySelector(".lightbox__credit");
    slot.innerHTML = credit ? credit.innerHTML : "";
    slot.hidden = !credit;
    box.hidden = false;
    document.body.classList.add("is-lightboxed");
    box.querySelector(".lightbox__close").focus();
  }

  function closeBox(){
    if(!box || box.hidden) return;
    box.hidden = true;
    // Drop the source so the next open cannot flash the previous photo.
    box.querySelector(".lightbox__img").removeAttribute("src");
    document.body.classList.remove("is-lightboxed");
    if(lastFocus && document.contains(lastFocus)) lastFocus.focus();
  }

  document.addEventListener("click", function(e){
    var item = e.target.closest(".photo-grid__item");
    if(!item) return;
    openBox(item);
  });

  document.addEventListener("keydown", function(e){
    if(!box || box.hidden) return;
    if(e.key === "Escape"){ closeBox(); return; }
    // Keep Tab inside the overlay. There are now two stops -- the close
    // button and the credit's prints link -- so it cycles rather than pinning.
    if(e.key === "Tab"){
      var stops = box.querySelectorAll("button, a[href]");
      if(!stops.length) return;
      var first = stops[0], last = stops[stops.length - 1], at = document.activeElement;
      if(e.shiftKey && (at === first || !box.contains(at))){
        e.preventDefault(); last.focus();
      } else if(!e.shiftKey && (at === last || !box.contains(at))){
        e.preventDefault(); first.focus();
      }
    }
  });
}

function initYearPicker(){
  document.querySelectorAll(".yearpick").forEach(function(pick){
    // Scoped to THIS picker's own buttons and panels. The NHA's "Browse by
    // Topic" buttons open panels that hold year pickers of their own, so a
    // plain querySelectorAll would hand the outer picker the inner one's
    // buttons and hide its panels on every click. Everywhere else nothing
    // nests and the filter changes nothing.
    var own    = function(el){ return el.closest(".yearpick") === pick; };
    var btns   = Array.prototype.filter.call(pick.querySelectorAll(".year-btn"), own);
    var panels = Array.prototype.filter.call(pick.querySelectorAll(".year-panel"), own);
    btns.forEach(function(btn){
      btn.addEventListener("click",function(){
        var yr = btn.getAttribute("data-year");
        var civic = !!pick.closest(".boardpick");
        // A picker marked --toggle shuts when its open year is clicked again.
        // Every other one keeps a year open once chosen, which is what the
        // lecture and meeting archives want: collapsing to nothing there would
        // just look like the page had lost its contents.
        var shut = pick.classList.contains("yearpick--toggle") &&
                   btn.classList.contains("is-active");
        if(civic) civicPick.year = yr;
        btns.forEach(function(b){
          var on = (b === btn) && !shut;
          b.classList.toggle("is-active", on);
          b.setAttribute("aria-pressed", on ? "true" : "false");
        });
        panels.forEach(function(p){
          p.hidden = shut || p.getAttribute("data-year") !== yr;
          if(p.hidden){ clearPicks(p, ".quarter-btn", ".quarter-panel"); stopReels(p); }
          else { startReels(p); if(civic) restoreQuarter(p); }
        });
      });
    });
  });
}

/* ---------- YouTube thumbnail fallback ----------
   Older uploads have no maxresdefault image. YouTube answers those requests
   with a 404 whose BODY is a valid 120x90 grey placeholder, so the browser
   decodes it and fires "load" — an onerror handler never runs. Detect the
   placeholder by its size and swap in hqdefault (480x360), which always
   exists. The swapped URL no longer matches, so this cannot loop. */
function initThumbFallback(){
  document.querySelectorAll(".watch-episode__thumb img").forEach(function(img){
    function check(){
      var m = img.src.match(/\/vi\/([A-Za-z0-9_-]{11})\/maxresdefault\.jpg/);
      if(m && img.naturalWidth && img.naturalWidth <= 120){
        img.src = "https://img.youtube.com/vi/" + m[1] + "/hqdefault.jpg";
      }
    }
    if(img.complete) check(); else img.addEventListener("load", check);
  });
}

/* ---------- long description toggles ----------
   A description running past ten lines collapses, with "Click to See More" on
   the eleventh. The ten-line limit lives in CSS (-webkit-line-clamp) so it
   reflows with the window; this only works out which descriptions actually
   overflow and wires up their control.

   A description inside a closed <details> or a hidden year panel measures zero
   height, so the test has to run again whenever one of those is revealed.
   Already-measured descriptions carry data-clamp so the work happens once. */
function clampDescriptions(root){
  (root || document).querySelectorAll(".watch-episode__desc").forEach(function(p){
    if(p.dataset.clamp || !p.textContent.trim()) return;
    if(!p.offsetParent && p.offsetHeight === 0) return;   // still hidden
    p.dataset.clamp = "done";
    p.classList.add("is-clamped");
    if(p.scrollHeight <= p.clientHeight + 1){             // fits in ten lines
      p.classList.remove("is-clamped");
      return;
    }
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "watch-episode__more";
    btn.textContent = "Click to See More";
    btn.setAttribute("aria-expanded", "false");
    btn.addEventListener("click", function(){
      var clamped = p.classList.toggle("is-clamped");
      btn.textContent = clamped ? "Click to See More" : "Click to See Less";
      btn.setAttribute("aria-expanded", clamped ? "false" : "true");
    });
    p.insertAdjacentElement("afterend", btn);
  });
}

/* ---------- agenda toggles ----------
   Some School Committee and Civic TV cards carry the meeting's posted agenda
   alongside the description. The button swaps one for the other in place and
   renames itself, so a reader can always get back to the description. Nothing
   is fetched: both blocks ship in the page, which keeps the control working
   offline and makes the agenda findable by an in-page search even before it is
   shown. */
function initAgendaToggles(){
  document.querySelectorAll(".watch-episode__agenda-btn").forEach(function(btn){
    if(btn.dataset.wired) return;
    btn.dataset.wired = "1";
    // the button sits beside the thumbnail, the description in the other
    // column, so scope the lookup to the whole card rather than either column
    var card    = btn.closest(".watch-episode");
    var desc    = card.querySelector(".watch-episode__desc");
    var agenda  = card.querySelector(".watch-episode__agenda");
    if(!agenda) return;
    var label   = btn.dataset.label || "Meeting Agenda";
    // A card marked data-title-moves drops its title below the buttons while
    // the panel is open, so a tall panel (an Instagram reel) starts level with
    // the thumbnail rather than under a heading. The title is moved rather
    // than duplicated: two copies would read twice to a screen reader, and
    // the columns are separate elements, so CSS order cannot do it.
    var moveTitle = card.hasAttribute("data-title-moves");
    var title   = card.querySelector(".watch-episode__title");
    var media   = card.querySelector(".watch-episode__media");
    var text    = card.querySelector(".watch-episode__text");
    btn.addEventListener("click", function(){
      var showing = agenda.hasAttribute("hidden");
      agenda.toggleAttribute("hidden", !showing);
      if(showing) startReels(agenda); else stopReels(agenda);
      if(moveTitle && title && media && text){
        if(showing) media.appendChild(title);
        else text.insertBefore(title, text.firstChild);
      }
      btn.textContent = showing ? "Hide " + label : label;
      btn.setAttribute("aria-expanded", showing ? "true" : "false");
      // a card with an agenda but no description has nothing to swap out: the
      // agenda just opens and closes under the title
      if(!desc) return;
      desc.toggleAttribute("hidden", showing);
      // the "Click to See More" control, if this description grew one
      var more = desc.nextElementSibling;
      if(more && more.classList.contains("watch-episode__more"))
        more.toggleAttribute("hidden", showing);
      btn.textContent = showing ? "Show Description" : label;
    });
  });
}

/* ---------- document overlay ----------
   A card can offer a whole document instead of a posted agenda -- a Town
   Meeting warrant, 84 articles of it for 2026 and 104 for 2025. An agenda
   swaps itself for the description in place, which is right for a page of
   bullet points and wrong for tens of thousands of words: everything below
   the card would be pushed off the screen. So this one opens over the page.

   The documents sit together in one hidden block near the foot of the page,
   not inside the cards, because a warrant belongs to every sitting of its
   Town Meeting and the button only names it. The one that is opened is moved
   into the overlay and handed back on close rather than copied, so the page
   holds one of it and an in-page search never finds the same sentence twice.
   Nothing is fetched: it ships with the page, the way the agendas do. */
function initDocModal(){
  var box = null, home = null, body = null, lastFocus = null;

  function build(){
    box = document.createElement("div");
    box.className = "docmodal";
    box.hidden = true;
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.innerHTML =
      '<div class="docmodal__panel">' +
        '<div class="docmodal__bar">' +
          '<h2 class="docmodal__title"></h2>' +
          '<button type="button" class="docmodal__close">Close</button>' +
        '</div>' +
        '<div class="docmodal__body"></div>' +
      '</div>';
    // Anything outside the panel closes it. Asking what was clicked rather
    // than where keeps this right however the panel is laid out.
    box.addEventListener("click", function(e){
      if(!e.target.closest(".docmodal__panel") || e.target.closest(".docmodal__close"))
        closeBox();
    });
    document.body.appendChild(box);
  }

  function openBox(btn){
    // The document is not in the card. One warrant belongs to every card for
    // its Town Meeting, so it ships once per page and the button names it.
    var doc = document.getElementById(btn.dataset.doc);
    if(!doc) return;
    if(!box) build();
    lastFocus = document.activeElement;
    home = doc.parentNode;
    body = box.querySelector(".docmodal__body");
    body.appendChild(doc);
    var title = btn.getAttribute("data-doc-title") || btn.textContent;
    box.querySelector(".docmodal__title").textContent = title;
    box.setAttribute("aria-label", title);
    box.hidden = false;
    document.body.classList.add("is-docopen");
    body.scrollTop = 0;
    box.querySelector(".docmodal__close").focus();
  }

  function closeBox(){
    if(!box || box.hidden) return;
    // Hand the document back before hiding, so the card is whole again even
    // if the overlay is never opened a second time.
    if(home && body && body.firstElementChild) home.appendChild(body.firstElementChild);
    box.hidden = true;
    document.body.classList.remove("is-docopen");
    if(lastFocus && document.contains(lastFocus)) lastFocus.focus();
  }

  document.addEventListener("click", function(e){
    var btn = e.target.closest(".watch-episode__doc-btn");
    if(!btn) return;
    openBox(btn);
  });

  document.addEventListener("keydown", function(e){
    if(!box || box.hidden) return;
    if(e.key === "Escape"){ closeBox(); return; }
    // Keep Tab inside the overlay. The warrant has no links of its own, so in
    // practice this pins focus to the close button.
    if(e.key === "Tab"){
      var stops = box.querySelectorAll("button, a[href]");
      if(!stops.length) return;
      var first = stops[0], last = stops[stops.length - 1], at = document.activeElement;
      if(e.shiftKey && (at === first || !box.contains(at))){
        e.preventDefault(); last.focus();
      } else if(!e.shiftKey && (at === last || !box.contains(at))){
        e.preventDefault(); first.focus();
      }
    }
  });
}

document.addEventListener("DOMContentLoaded",()=>{
  buildNav();
  buildFooter();
  initCalendar();
  initReveal();
  initMoviePicker();
  initShowsTable();
  initSportPicker();
  initYearPicker();
  initPhotoLightbox();
  initBoardPicker();
  initQuarterPicker();
  initThumbFallback();
  clampDescriptions();
  initAgendaToggles();
  initDocModal();
  // Measure again as sections and panels are revealed. The civic page nests
  // three pickers -- board, then year, then quarter -- and a card has no
  // measurable height until the innermost panel is showing, so every level
  // re-runs. These listeners are registered after the pickers' own, so the
  // panel is already visible by the time the measuring happens.
  document.querySelectorAll("details.dl-group").forEach(function(d){
    d.addEventListener("toggle", function(){ if(d.open) clampDescriptions(d); });
  });
  document.querySelectorAll(".sport-btn, .board-btn, .year-btn, .quarter-btn").forEach(function(b){
    b.addEventListener("click", function(){
      clampDescriptions(b.closest(".sportpick, .boardpick, .yearpick, .quarterpick"));
    });
  });
});
