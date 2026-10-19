const SVG = "http://www.w3.org/2000/svg";
const DAY = 864e5;

// Time windows whose forward P/E range each stock is compared against.
const WINDOWS = [
  { key: "90d", days: 90, label: "Last 90 days" },
  { key: "180d", days: 180, label: "Last 6 months" },
  { key: "1Y", days: 365, label: "Last year" },
  { key: "2Y", days: 730, label: "Last 2 years" },
  { key: "3Y", days: 1095, label: "Last 3 years" },
  { key: "4Y", days: 1461, label: "Last 4 years" },
  { key: "5Y", days: 1826, label: "Last 5 years" },
];
const MAIN_WINDOW = "3Y"; // the window the list and the verdict use
// Recent listings and newly profitable companies lack 3 years; judge them on the longest window they have.
const FALLBACK = ["3Y", "2Y", "1Y", "180d", "90d"];

// Seven valuation zones on the σ-equivalent scale (levels are read off percentiles).
const ZONES = [
  { key: "c3", upTo: -2, label: "Extremely cheap", side: "cheap" },
  { key: "c2", upTo: -1.5, label: "Very cheap", side: "cheap" },
  { key: "c1", upTo: -1, label: "Cheap", side: "cheap" },
  { key: "n", upTo: 1, label: "Normal", side: "normal" },
  { key: "e1", upTo: 1.5, label: "Expensive", side: "rich" },
  { key: "e2", upTo: 2, label: "Very expensive", side: "rich" },
  { key: "e3", upTo: Infinity, label: "Extremely expensive", side: "rich" },
];
const LEVELS = ["2", "1.5", "1", "0", "-1", "-1.5", "-2"];
const LEVEL_NAME = {
  "2": "Extremely expensive above",
  "1.5": "Very expensive above",
  "1": "Expensive above",
  "0": "Typical",
  "-1": "Cheap below",
  "-1.5": "Very cheap below",
  "-2": "Extremely cheap below",
};

// Direction of analysts' forecast for next financial year over the last 90 days.
const REVS = {
  up2: { icon: "↑↑", label: "Rising steadily", short: "Keeps rising", tone: "up" },
  up1: { icon: "↑", label: "Rising", short: "Rising", tone: "up" },
  flat: { icon: "→", label: "Flat", short: "Flat", tone: "flat" },
  down1: { icon: "↓", label: "Falling", short: "Falling", tone: "down" },
  down2: { icon: "↓↓", label: "Falling steadily", short: "Keeps falling", tone: "down" },
};

// Combined ranking: each criterion is the stock's position among all stocks (100 = best),
// so outliers like +400% growth can't dominate; the score is the plain average.
const CRITERIA = [
  { key: "rel", better: "high", label: "Cheap compared with other stocks", explain: (r) => `${r.rel.toFixed(0)}/100 on the "vs others" score` },
  { key: "growth", better: "high", label: "Expected profit growth", explain: (r) => `${pct(r.growth, 0)} next 12 months vs last 12` },
  { key: "rev90", better: "high", label: "Forecasts being raised", explain: (r) => `next-year forecast ${pct(r.rev90)} in 90 days` },
  { key: "r_mid", better: "high", label: "Upside if valued at its typical level", explain: (r) => `${pct(r.r_mid, 0)} in a year` },
];

const RANGES = [
  { label: "1Y", days: 365 },
  { label: "3Y", days: 1095 },
  { label: "5Y", days: 1826 },
  { label: "All", days: null },
];

const state = {
  rows: [],
  query: "",
  sort: { key: "score", dir: -1 },
  selected: null,
  window: MAIN_WINDOW,
  range: 1095,
  expanded: false,
};
const $ = (sel) => document.querySelector(sel);

function el(tag, attrs = {}, text) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (text !== undefined) node.textContent = text;
  return node;
}
function svg(tag, attrs = {}) {
  const node = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
}
const fmt = (v, d = 1) => (v == null || !Number.isFinite(v) ? "n/a" : v.toFixed(d));
const pct = (v, d = 1) => (v == null ? "n/a" : `${v >= 0 ? "+" : ""}${(v * 100).toFixed(d)}%`);
const money = (v, ccy) => (v == null || !Number.isFinite(v) ? "n/a" : `${v >= 1000 ? v.toFixed(0) : v.toFixed(2)} ${ccy || ""}`.trim());
const dayNum = (iso) => Math.round(Date.parse(iso) / DAY);
const isoOf = (n) => new Date(n * DAY).toISOString().slice(0, 10);
const zoneOf = (sigma) => (sigma == null ? null : ZONES.find((z) => sigma <= z.upTo));
const windowOf = (key) => WINDOWS.find((w) => w.key === key);
const spanOf = (key) => windowOf(key).label.replace(/^Last /, "the last ").replace("the last year", "the last year");

function ordinal(n) {
  const tail = n % 100 >= 11 && n % 100 <= 13 ? "th" : ["th", "st", "nd", "rd"][n % 10] || "th";
  return `${n}${tail}`;
}

function revBadge(rv, short = false) {
  const info = rv ? REVS[rv.category] : null;
  const span = el("span", { class: `rev rev-${info ? info.tone : "na"}` });
  if (!info) {
    span.textContent = "n/a";
    return span;
  }
  span.append(el("span", { class: "rev-icon", "aria-hidden": "true" }, info.icon), document.createTextNode(short ? info.short : info.label));
  return span;
}

function zoneBadge(zone, big = false) {
  const span = el("span", { class: `zone zone-${zone ? zone.key : "na"}${big ? " big" : ""}` });
  span.append(el("span", { class: "dot", "aria-hidden": "true" }), document.createTextNode(zone ? zone.label : "No history yet"));
  return span;
}

async function load() {
  const res = await fetch("data/ranking.json", { cache: "no-store" });
  const data = await res.json();
  const rows = data.rows
    .filter((r) => !r.missing)
    .map((r) => ({
      ...r,
      mainKey: FALLBACK.find((k) => r.corridors?.[k]) ?? null,
    }))
    .map((r) => ({
      ...r,
      sig3: r.corridors?.[r.mainKey]?.sigma ?? null,
      pctMain: r.corridors?.[r.mainKey]?.pct ?? null,
      ...targets(r),
      rev90: r.revisions?.change_90d ?? null,
    }));
  state.rows = scoreRows(rows);
  state.asof = `Each stock's price-to-earnings compared with its own past · data as of ${data.as_of} · ${state.rows.length} stocks`;
  $("#asof").textContent = state.asof;
  renderTable();
  const params = new URLSearchParams(location.search);
  const wanted = params.get("t");
  const first = state.rows.find((r) => r.ticker === wanted) || visibleRows()[0];
  const page = wanted === BREADTH ? "breadth" : params.get("page"); // old links used t=$NYSI
  if (first) await select(first.ticker, { keepPage: PAGES[page] });
  if (params.get("view") === "list") setExpanded(true);
  if (PAGES[page]) await showPage(page);
}

// ---------- sections: valuation is the list and detail; the others get the full width ----------

const PAGES = {
  valuation: null,
  breadth: () => showBreadth(),
  positioning: () => showPositioning(),
  horizon: () => showHorizon(),
};

async function showPage(name) {
  if (!(name in PAGES)) name = "valuation";
  const onValuation = name === "valuation";
  document.querySelectorAll(".tab").forEach((t) => {
    if (t.dataset.page === name) t.setAttribute("aria-current", "page");
    else t.removeAttribute("aria-current");
  });
  $("main.layout").hidden = !onValuation;
  $("#valuation-controls").hidden = !onValuation;
  $("#foot").hidden = !onValuation;
  $("#page").hidden = onValuation;
  $("#asof").textContent = PAGE_SUBS[name] ?? state.asof ?? "";
  const url = new URL(location.href);
  if (onValuation) url.searchParams.delete("page");
  else {
    url.searchParams.set("page", name);
    url.searchParams.delete("t");
  }
  history.replaceState(null, "", url);
  if (!onValuation) await PAGES[name]();
}
const pageBox = () => $("#pagebody");
const PAGE_SUBS = {
  breadth: "How many NYSE stocks take part in the move",
  positioning: "Who is already leaning which way",
  horizon: "What the market is waiting for, and how far it has run ahead",
};

// ---------- list ----------

// ---------- cheap compared with other stocks ----------

const PEG_GROWTH_CAP = 0.5; // one-year rebounds from near-zero profit would otherwise look endlessly cheap
const PEG_GROWTH_MIN = 0.03;
const MIN_PEERS = 5;

/** Percentile position (0–100) of each row's value among `pool`; `low` means lower is better. */
function positions(pool, key, low) {
  const sorted = [...pool].sort((a, b) => a[key] - b[key]);
  const out = new Map();
  sorted.forEach((r, i) => {
    const up = sorted.length > 1 ? (i / (sorted.length - 1)) * 100 : 50;
    out.set(r.ticker, low ? 100 - up : up);
  });
  return out;
}

/**
 * "Cheap vs others", 0–100 (100 = cheapest): the average of forward P/E against all stocks,
 * forward P/E against industry peers (sector when the industry is too small), and
 * P/E relative to growth (PEG). Share classes after the first don't count as extra peers.
 */
function addRelative(rows) {
  // Sales-valued loss-makers carry P/S in `pe`; comparing that with other stocks' P/E would be nonsense.
  const priced = rows.filter((r) => r.pe > 0 && r.metric !== "ps");
  const firstOfCompany = new Map();
  for (const r of priced) if (!firstOfCompany.has(r.company || r.ticker)) firstOfCompany.set(r.company || r.ticker, r);
  const pool = [...firstOfCompany.values()];
  const vsAll = positions(priced, "pe", true);

  for (const r of priced) {
    const g = r.growth;
    r.peg = g != null && g >= PEG_GROWTH_MIN ? r.pe / (Math.min(g, PEG_GROWTH_CAP) * 100) : null;
    // The usual PEG, shown in the list; only the ranking uses the capped version above.
    r.pegRaw = g != null && g > 0 ? r.pe / (g * 100) : null;
  }
  const vsPeg = positions(priced.filter((r) => r.peg != null), "peg", true);

  const groups = new Map();
  for (const r of pool) {
    for (const [level, name] of [["industry", r.industry], ["sector", r.sector]]) {
      if (!name) continue;
      const k = `${level}:${name}`;
      if (!groups.has(k)) groups.set(k, []);
      groups.get(k).push(r);
    }
  }
  for (const r of priced) {
    const ind = groups.get(`industry:${r.industry}`) || [];
    const sec = groups.get(`sector:${r.sector}`) || [];
    const [level, peers] = ind.length >= MIN_PEERS ? ["industry", ind] : sec.length >= MIN_PEERS ? ["sector", sec] : [null, []];
    let vsPeers = null;
    if (level) {
      const withSelf = peers.some((p) => p.ticker === r.ticker) ? peers : [...peers, r];
      vsPeers = positions(withSelf, "pe", true).get(r.ticker);
      r.peerGroup = { level, name: level === "industry" ? r.industry : r.sector, size: peers.length,
        cheaper: withSelf.filter((p) => p.pe > r.pe).length, median: median(peers.map((p) => p.pe)) };
    }
    r.relParts = { all: vsAll.get(r.ticker), peers: vsPeers, peg: vsPeg.get(r.ticker) ?? null };
    const have = Object.values(r.relParts).filter((v) => v != null);
    r.rel = have.reduce((a, b) => a + b, 0) / have.length;
  }
}

function median(xs) {
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

function scoreRows(rows) {
  addRelative(rows);
  const valid = {
    rel: (r) => r.rel != null,
    growth: (r) => r.growth != null,
    rev90: (r) => r.rev90 != null,
    r_mid: (r) => r.r_mid != null,
  };
  const ranks = {};
  for (const c of CRITERIA) {
    const pool = rows.filter(valid[c.key]).sort((a, b) => a[c.key] - b[c.key]);
    ranks[c.key] = new Map(pool.map((r, i) => {
      const up = pool.length > 1 ? (i / (pool.length - 1)) * 100 : 50;
      return [r.ticker, c.better === "low" ? 100 - up : up];
    }));
  }
  // One company, one ranking slot: of several share classes, only the cheapest (lowest P/E) is ranked.
  const cheapest = new Map();
  for (const r of rows) {
    const k = r.company || r.ticker;
    const best = cheapest.get(k);
    if (r.pe > 0 && (!best || r.pe < best.pe)) cheapest.set(k, r);
  }
  const scored = rows.map((r) => {
    const parts = Object.fromEntries(CRITERIA.map((c) => [c.key, ranks[c.key].get(r.ticker) ?? null]));
    const have = Object.values(parts).filter((v) => v != null);
    const best = cheapest.get(r.company || r.ticker);
    const rankedVia = best && best.ticker !== r.ticker ? best.ticker : null;
    const score = !rankedVia && have.length >= 3 ? have.reduce((a, b) => a + b, 0) / have.length : null;
    return { ...r, parts, score, rankedVia };
  });
  const ordered = scored.filter((r) => r.score != null).sort((a, b) => b.score - a.score);
  ordered.forEach((r, i) => (r.rank = i + 1));
  return Object.assign(scored, { rankedOf: ordered.length });
}

/** Price in a year at the −1σ, median and +1σ P/E of the stock's main window, and the return from today. */
function targets(r) {
  const c = r.corridors?.[r.mainKey];
  if (!c || !(r.eps > 0) || !r.price) return {};
  const eps1 = epsAhead(r, 365);
  const at = (k) => c.levels[k] * eps1;
  const t_lo = at("-1"), t_mid = at("0"), t_hi = at("1");
  return {
    t_lo, t_mid, t_hi,
    r_lo: t_lo / r.price - 1,
    r_mid: t_mid / r.price - 1,
    r_hi: t_hi / r.price - 1,
  };
}

function retCell(v) {
  return el("td", { class: `num xcol ret ${v == null ? "" : v >= 0 ? "pos" : "neg"}` }, v == null ? "n/a" : pct(v, 0));
}

function visibleRows() {
  const q = state.query.trim().toLowerCase();
  const { key, dir } = state.sort;
  return state.rows
    .filter((r) => !q || r.ticker.toLowerCase().includes(q) || (r.name || "").toLowerCase().includes(q))
    .sort((a, b) => {
      const av = a[key], bv = b[key];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      return (typeof av === "string" ? av.localeCompare(bv) : av - bv) * dir;
    });
}

function renderTable() {
  const tbody = $("#table tbody");
  tbody.replaceChildren();
  for (const r of visibleRows()) {
    const tr = el("tr", { "aria-selected": String(r.ticker === state.selected), tabindex: "0" });
    const tick = el("td");
    tick.append(el("strong", {}, r.ticker), el("span", { class: "name" }, r.name || ""));
    const scoreTd = el("td", { class: "num score", title: r.rankedVia ? `Ranked via ${r.rankedVia}` : "" },
      r.rankedVia ? `→ ${r.rankedVia}` : r.score == null ? "n/a" : r.score.toFixed(0));
    const relTd = el("td", { class: "num", title: "Cheap compared with other stocks, 0–100 (100 = cheapest)" },
      r.rel == null ? "n/a" : r.rel.toFixed(0));
    const val = el("td", { class: "val" });
    val.append(zoneBadge(zoneOf(r.sig3)));
    if (r.mainKey && r.mainKey !== MAIN_WINDOW) {
      val.append(el("span", { class: "short-hist", title: `Only ${spanOf(r.mainKey)} of usable history` }, ` (${r.mainKey})`));
    }
    tr.append(
      tick,
      scoreTd,
      relTd,
      val,
      r.metric === "ps"
        ? el("td", { class: "num ps", title: "Loss-making: valued on sales. Trailing price ÷ sales; forward P/S in the panel" }, `P/S ${fmt(r.pe, 2)}`)
        : el("td", { class: "num" }, r.pe == null || r.pe <= 0 ? "n/m" : fmt(r.pe)),
      el("td", { class: "num xcol" }, r.trailing_pe == null ? "n/m" : fmt(r.trailing_pe)),
      el("td", { class: "num" }, pct(r.growth, 0)),
      el("td", { class: "num", title: r.pegRaw == null ? "Growth is zero or negative, so PEG has no meaning" : "" },
        r.pegRaw == null ? "n/m" : fmt(r.pegRaw, 2)),
      (() => { const td = el("td"); td.append(revBadge(r.revisions, true)); return td; })(),
      el("td", { class: "num xcol" }, r.pctMain == null ? "n/a" : ordinal(Math.round(r.pctMain))),
      el("td", { class: "num xcol" }, money(r.price, r.currency)),
      el("td", { class: "num xcol group-start" }, money(r.t_lo, "")),
      retCell(r.r_lo),
      el("td", { class: "num xcol group-start" }, money(r.t_mid, "")),
      retCell(r.r_mid),
      el("td", { class: "num xcol group-start" }, money(r.t_hi, "")),
      retCell(r.r_hi),
    );
    tr.onclick = () => {
      if (state.expanded) setExpanded(false);
      select(r.ticker);
    };
    tr.onkeydown = (e) => e.key === "Enter" && select(r.ticker);
    tbody.append(tr);
  }
  document.querySelectorAll("#table th[data-sort]").forEach((th) => {
    const key = th.dataset.sort;
    th.setAttribute("aria-sort", key === state.sort.key ? (state.sort.dir > 0 ? "ascending" : "descending") : "none");
    th.onclick = () => {
      state.sort = { key, dir: state.sort.key === key ? -state.sort.dir : 1 };
      renderTable();
    };
  });
}

async function select(ticker, { keepPage = false } = {}) {
  state.selected = ticker;
  if (!keepPage) {
    const url = new URL(location.href);
    url.searchParams.set("t", ticker);
    history.replaceState(null, "", url);
  }
  renderTable();
  const row = state.rows.find((r) => r.ticker === ticker);
  let series = null;
  try {
    const res = await fetch(`data/series/${encodeURIComponent(ticker)}.json`, { cache: "no-store" });
    if (res.ok) series = await res.json();
  } catch {
    series = null;
  }
  renderDetail(row, series);
}

// ---------- detail ----------

function renderDetail(row, series) {
  const box = $("#detail");
  box.replaceChildren();
  const head = el("div", { class: "d-head" });
  head.append(el("h2", {}, `${row.name || row.ticker}`), el("div", { class: "d-sub" }, `${row.ticker} · ${money(row.price, row.currency)} · data as of ${row.as_of}`));
  box.append(head, verdictCard(row), scoreCard(row), relativeCard(row));

  if (row.pe == null || row.pe <= 0) {
    box.append(el("p", { class: "plain" }, "This company is expected to lose money over the next 12 months, so its price can't be compared with its earnings. There is nothing to rank."));
    box.append(detailsSection(row, series));
    return;
  }
  if (!row.corridors?.[state.window] && row.mainKey) state.window = row.mainKey;
  box.append(gaugeSection(row));
  if (row.revisions) box.append(revisionSection(row));
  if (row.analysts) box.append(analystSection(row));
  if (series && series.dates.length > 1 && row.corridors?.[state.window]) {
    box.append(priceSection(row, series));
  }
  box.append(detailsSection(row, series));
}

function verdictCard(row) {
  const main = row.corridors?.[row.mainKey];
  const span = row.mainKey ? spanOf(row.mainKey) : "the last 3 years";
  const zone = zoneOf(main?.sigma);
  const card = el("section", { class: `verdict side-${zone ? zone.side : "na"}` });
  card.append(zoneBadge(zone, true));

  const lines = el("div", { class: "v-lines" });
  const say = (text, cls = "") => lines.append(el("p", { class: cls }, text));
  const name = row.name || row.ticker;

  if (row.pe == null || row.pe <= 0) {
    say(`${name} is expected to make a loss, so this screen has no view on it.`);
  } else if (!main) {
    say(`${name} doesn't have enough history yet to say whether it's cheap or expensive. The app records new data every weekday, so this fills in over time.`);
  } else {
    const p = Math.round(main.pct);
    const vs = p < 1
      ? `That's the cheapest it has been in ${span}.`
      : p > 99
        ? `That's the most expensive it has been in ${span}.`
        : p <= 50
          ? `That's cheaper than on ${100 - p}% of trading days in ${span}.`
          : `That's more expensive than on ${p}% of trading days in ${span}.`;
    if (row.metric === "ps") {
      say(`${name} is loss-making, so it's valued on sales instead of profit. You pay ${fmt(row.pe, 2)}× its sales over the last 12 months` +
        `${row.ps_forward ? ` (${fmt(row.ps_forward, 2)}× the sales ${row.rev_analysts || "the"} analysts expect over the next 12)` : ""}. ${vs}`);
      say("Sales multiples fall naturally as a young company grows, so a low reading against its own past is weaker evidence than a low P/E would be.", "note-line");
    } else {
      say(`You pay ${fmt(row.pe)}× the profit analysts expect over the next 12 months. ${vs}`);
    }
    if (row.mainKey !== MAIN_WINDOW) {
      say(`Note: there's only ${span} of usable history (recent listing, or profits only recently turned positive), so this compares with a shorter past than usual.`, "note-line");
    }
  }

  const rv = row.revisions;
  const cat = rv?.category;
  const moved = rv ? `${pct(rv.change_90d)} in 90 days` : "";
  if (cat === "up2") {
    say(`Analysts keep raising their profit forecast for next year: ${moved}, up at every check along the way.`);
  } else if (cat === "up1") {
    say(`Analysts have raised their profit forecast for next year (${moved}).`);
  } else if (cat === "flat") {
    say(`Analysts' profit forecast for next year has held steady (${moved}).`);
  } else if (cat === "down1" || cat === "down2") {
    say(`⚠ Analysts ${cat === "down2" ? "keep cutting" : "have cut"} their profit forecast for next year (${moved}). A stock that looks cheap while forecasts fall is often a trap.`, "warn-line");
  }

  const trust = {
    good: ["Reliable history.", "The past valuations used here were checked against real data and match closely."],
    caution: ["Roughly reliable history.", "The past valuations used here are reconstructed and can be 15–35% off. Treat the verdict as approximate."],
    biased: ["Unreliable history for this stock.", "Profit forecasts jumped after the fact, so the past looks cheaper than it really was and today looks more expensive than it is."],
  }[row.b_grade] || (row.metric === "ps"
    ? ["History from reported sales.", "Past multiples use revenue as actually reported at the time, so there is no look-ahead."]
    : ["Recorded history only.", "Real data has been recorded since 2026-09-24; the picture sharpens as it builds up."]);
  const t = el("p", { class: "trust" });
  t.append(el("strong", {}, trust[0] + " "), document.createTextNode(trust[1]));
  lines.append(t);

  if (zone && zone.side === "cheap") {
    const text = cat === "up2"
      ? ["yes", "✓✓ Strongest pattern: cheap against its own past, and analysts keep raising forecasts."]
      : cat === "down1" || cat === "down2"
        ? ["no", "✗ Cheap, but forecasts are falling: doesn't match the strategy's pattern."]
        : ["yes", "✓ Matches the strategy's pattern: cheap against its own past, and forecasts holding up."];
    lines.append(el("p", { class: `pattern ${text[0]}` }, text[1]));
  } else if (zone && zone.side === "rich") {
    lines.append(el("p", { class: "pattern no" }, "Expensive against its own past: the strategy would take profits here, not buy."));
  }
  card.append(lines);
  return card;
}

function scoreCard(row) {
  const sec = el("section", { class: "scorecard" });
  if (row.rankedVia) {
    sec.append(el("h3", {}, "Combined ranking"));
    sec.append(el("p", { class: "help" }, `Not ranked separately: this is another share class of the same company, with the same profit forecasts. The cheaper class, ${row.rankedVia}, carries the company's ranking.`));
    return sec;
  }
  if (row.score == null) {
    sec.append(el("h3", {}, "Combined ranking"));
    sec.append(el("p", { class: "help" }, "Not ranked: needs at least three of the four measures (usually because the company is loss-making or too new)."));
    return sec;
  }
  const top = el("div", { class: "sc-top" });
  top.append(
    el("span", { class: "sc-rank" }, `#${row.rank}`),
    el("span", { class: "sc-of" }, ` of ${state.rows.rankedOf} ranked stocks`),
    el("span", { class: "sc-score" }, `score ${row.score.toFixed(0)}/100`),
  );
  sec.append(el("h3", {}, "Combined ranking"), top);
  sec.append(el("p", { class: "help" }, "Four measures, each scored by where this stock stands among all the others (100 = best in the list, 50 = middle). The score is their average."));
  for (const c of CRITERIA) {
    const v = row.parts[c.key];
    const line = el("div", { class: "sc-row" });
    line.append(el("span", { class: "sc-label" }, c.label));
    const bar = el("span", { class: "sc-bar" });
    if (v != null) bar.append(el("span", { class: "sc-fill", style: `width:${Math.max(v, 2)}%` }));
    line.append(bar);
    line.append(el("span", { class: "sc-val" }, v == null ? "no data" : `${v.toFixed(0)} · ${c.explain(row)}`));
    sec.append(line);
  }
  if (row.b_grade === "biased") {
    sec.append(el("p", { class: "help" }, "⚠ This stock's history is unreliable, so its 'typical level' (and the upside measure) is distorted."));
  }
  return sec;
}

function relativeCard(row) {
  const sec = el("section", { class: "scorecard" });
  sec.append(el("h3", {}, "Cheap compared with other stocks"));
  if (row.rel == null) {
    sec.append(el("p", { class: "help" }, "No comparison: the company is expected to make a loss, so it has no P/E."));
    return sec;
  }
  const top = el("div", { class: "sc-top" });
  top.append(el("span", { class: "sc-rank" }, `${row.rel.toFixed(0)}`), el("span", { class: "sc-of" }, "/100 (100 = cheapest in the list)"));
  sec.append(top);
  sec.append(el("p", { class: "help" }, "The section above compares the stock with its own past. This one compares it with other companies today."));
  const pg = row.peerGroup;
  const lines = [
    ["Against all stocks", row.relParts.all, `forward P/E ${fmt(row.pe)}× vs a list median of ${fmt(median(state.rows.filter((r) => r.pe > 0).map((r) => r.pe)))}×`],
    ["Against its peers", row.relParts.peers, pg
      ? `cheaper than ${pg.cheaper} of ${pg.size} ${pg.name} ${pg.level === "sector" ? "sector " : ""}stocks (their median ${fmt(pg.median)}×)`
      : "too few similar companies in the list to compare"],
    ["For its growth (PEG)", row.relParts.peg, row.peg != null
      ? `PEG ${fmt(row.pegRaw, 2)}${row.growth > PEG_GROWTH_CAP ? `; ranked on ${fmt(row.peg, 2)}, with growth counted up to +50%` : ""}`
      : "expected growth below +3%, so growth doesn't justify the price"],
  ];
  for (const [label, v, why] of lines) {
    const line = el("div", { class: "sc-row" });
    line.append(el("span", { class: "sc-label" }, label));
    const bar = el("span", { class: "sc-bar" });
    if (v != null) bar.append(el("span", { class: "sc-fill", style: `width:${Math.max(v, 2)}%` }));
    line.append(bar, el("span", { class: "sc-val" }, v == null ? why : `${v.toFixed(0)} · ${why}`));
    sec.append(line);
  }
  return sec;
}

function gaugeSection(row) {
  const sec = el("section", { class: "gauges" });
  sec.append(el("h3", {}, "How cheap or expensive, by time window"));
  sec.append(el("p", { class: "help" }, "Each bar is the range of prices-to-earnings this stock traded at over that period. The dot is today. Click a row to see it on the price chart."));

  const scale = el("div", { class: "g-scale", "aria-hidden": "true" });
  scale.append(el("span", {}, "cheaper"), el("span", {}, "normal"), el("span", {}, "more expensive"));
  sec.append(scale);

  const lo = -2.5, hi = 2.5;
  const at = (s) => ((Math.max(lo, Math.min(hi, s)) - lo) / (hi - lo)) * 100;
  for (const w of WINDOWS) {
    const c = row.corridors?.[w.key];
    const btn = el("button", { class: `g-row${state.window === w.key ? " on" : ""}`, "aria-pressed": String(state.window === w.key) });
    btn.append(el("span", { class: "g-label" }, w.label));
    const bar = el("span", { class: "g-bar" });
    let edge = lo;
    for (const z of ZONES) {
      const end = Math.min(z.upTo, hi);
      bar.append(el("span", { class: `g-seg zone-${z.key}`, style: `left:${at(edge)}%;width:${at(end) - at(edge)}%` }));
      edge = end;
    }
    if (c) bar.append(el("span", { class: "g-dot", style: `left:${at(c.sigma)}%`, title: `Today: ${zoneOf(c.sigma).label}` }));
    btn.append(bar);
    const zone = c ? zoneOf(c.sigma) : null;
    const txt = el("span", { class: "g-text" });
    if (c) {
      const p = Math.round(c.pct);
      const where = p < 1 ? "cheapest in this period" : p > 99 ? "priciest in this period"
        : p <= 50 ? `cheaper than ${100 - p}% of days` : `pricier than ${p}% of days`;
      txt.append(el("strong", {}, zone.label), el("span", { class: "g-pct" }, ` · ${where}`));
    } else {
      txt.append(el("span", { class: "muted" }, "not enough history"));
    }
    btn.append(txt);
    if (c) btn.onclick = () => {
      state.window = w.key;
      rerender();
    };
    else btn.disabled = true;
    sec.append(btn);
  }
  return sec;
}

function revisionSection(row) {
  const rv = row.revisions;
  const info = REVS[rv.category];
  const sec = el("section", { class: "revs" });
  sec.append(el("h3", {}, "Are analysts raising or cutting their forecasts?"));
  sec.append(el("p", { class: "help" }, "Analysts' average forecast of profit per share for the company's next financial year, as it stood at each point over the last 90 days. Forecasts that keep rising often keep pushing the price up."));

  const top = el("div", { class: "rev-top" });
  const badge = revBadge(rv);
  badge.classList.add("big");
  top.append(badge, el("span", { class: "muted" }, `${pct(rv.change_90d)} over 90 days`));
  sec.append(top);

  // Five points: 90, 60, 30, 7 days ago and today.
  const W = 800, H = 120, L = 58, R = 16, T = 14, B = 24;
  const root = svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Next-year profit forecast over the last 90 days" });
  const vals = rv.points.map((p) => p.eps);
  let lo = Math.min(...vals), hi = Math.max(...vals);
  const pad = (hi - lo) * 0.25 || Math.abs(hi) * 0.02 || 1;
  lo -= pad; hi += pad;
  const xOf = (daysAgo) => L + ((90 - daysAgo) / 90) * (W - L - R);
  const yOf = (v) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);
  const grid = svg("g", { class: "grid" });
  for (const v of [lo + pad, hi - pad]) {
    grid.append(svg("line", { x1: L, x2: W - R, y1: yOf(v), y2: yOf(v) }));
    const lab = svg("text", { x: L - 6, y: yOf(v) + 4, "text-anchor": "end", class: "tick" });
    lab.textContent = v.toFixed(2);
    grid.append(lab);
  }
  for (const p of rv.points.filter((q) => q.days_ago !== 7)) {
    const lab = svg("text", { x: xOf(p.days_ago), y: H - 6, "text-anchor": p.days_ago === 90 ? "start" : p.days_ago === 0 ? "end" : "middle", class: "tick" });
    lab.textContent = p.days_ago === 0 ? "today" : `${p.days_ago}d ago`;
    grid.append(lab);
  }
  root.append(grid);
  root.append(svg("path", { class: `rev-line rev-${info.tone}`, d: rv.points.map((p, i) => `${i ? "L" : "M"}${xOf(p.days_ago).toFixed(1)},${yOf(p.eps).toFixed(1)}`).join("") }));
  for (const p of rv.points) {
    const c = svg("circle", { class: `rev-pt rev-${info.tone}`, cx: xOf(p.days_ago), cy: yOf(p.eps), r: 5 });
    const t = svg("title");
    t.textContent = `${p.days_ago === 0 ? "Today" : `${p.days_ago} days ago`}: ${p.eps.toFixed(2)}`;
    c.append(t);
    root.append(c);
  }
  const holder = el("div", { class: "chart" });
  holder.append(root);
  sec.append(holder);

  if (rv.up_30d != null && rv.down_30d != null) {
    sec.append(el("p", { class: "help" }, `Last 30 days, roughly: ${rv.up_30d} analyst revisions up, ${rv.down_30d} down (Yahoo's counts are approximate).`));
  }
  return sec;
}

// The earlier project stored some firms by short lowercase keys.
const FIRM_NAMES = { mirae: "Mirae Asset", hana: "Hana Securities", meritz: "Meritz Securities", kb: "KB Securities",
  nh: "NH Investment", hyundai: "Hyundai Motor Securities", samsung: "Samsung Securities", kiwoom: "Kiwoom", daishin: "Daishin" };
const firmName = (f) => FIRM_NAMES[(f || "").toLowerCase()] || f || "?";

function analystSection(row) {
  const a = row.analysts;
  const [y0, y1] = a.years;
  const sec = el("section", { class: "analysts" });
  sec.append(el("h3", {}, "What individual analysts forecast"));
  const named = a.reports.filter((r) => r.kind === "analyst" && r.eps[y1] != null);
  const c1 = a.consensus[y1];
  if (named.length && c1) {
    const vals = named.map((r) => r.eps[y1]);
    const avg = vals.reduce((x, y) => x + y, 0) / vals.length;
    sec.append(el("p", { class: "help" },
      `${named.length} analyst report${named.length > 1 ? "s" : ""} from the last two years. For ${y1}, they average ` +
      `${money(avg, "")} per share (${pct(avg / c1 - 1)} vs the consensus of ${money(c1, "")}` +
      `${a.consensus_analysts ? `, ${a.consensus_analysts} analysts` : ""}), ranging from ${money(Math.min(...vals), "")} to ${money(Math.max(...vals), "")}.`));
  }
  const wrap = el("div", { class: "ladder" });
  const t = el("table");
  const head = el("tr");
  ["Analyst", "Report", `${y1} EPS`, "vs consensus"].forEach((h, i) => head.append(el("th", i >= 2 ? { class: "num" } : {}, h)));
  t.append(head);
  const cons = el("tr", { class: "lvl-mid" });
  cons.append(el("td", {}, `Consensus${a.consensus_analysts ? ` · ${a.consensus_analysts} analysts` : ""}`), el("td", {}, "today"),
    el("td", { class: "num" }, money(c1, "")), el("td", { class: "num" }, "—"));
  t.append(cons);
  for (const r of a.reports) {
    const tr = el("tr");
    const who = el("td");
    const firm = /^https?:/.test(r.source_url)
      ? el("a", { href: r.source_url, target: "_blank", rel: "noopener", title: "Open the report (PDF)" }, firmName(r.firm))
      : el("strong", {}, firmName(r.firm));
    who.append(firm, el("span", { class: "name" }, r.kind === "consensus" ? "published consensus" : r.analyst));
    if (r.status === "needs_review") who.append(el("span", { class: "review", title: "A figure could not be matched in the report text" }, " ⚠"));
    const age = r.age_days < 60 ? `${r.age_days}d ago` : `${Math.round(r.age_days / 30)}mo ago`;
    const when = el("td", {}, r.date);
    when.append(el("span", { class: `name${r.age_days > 180 ? " stale" : ""}` }, age));
    const vs = r.vs_consensus;
    tr.append(who, when,
      (() => {
        const td = el("td", { class: "num" }, money(r.eps[y1], ""));
        if (r.gaap) td.append(el("span", { class: "gaap", title: "GAAP/reported EPS; the consensus is adjusted, so the gap is not like for like" }, " GAAP"));
        return td;
      })(),
      el("td", { class: `num ret ${vs == null ? "" : vs >= 0 ? "pos" : "neg"}` }, vs == null ? "" : pct(vs)));
    t.append(tr);
  }
  wrap.append(t);
  sec.append(wrap);
  sec.append(el("p", { class: "help" }, "From broker reports: imported from the earlier dashboard project, collected nightly (Morningstar via Firstrade, Korean brokers via Telegram) or dropped into the inbox. Per share on today's share count, in the price currency."));
  return sec;
}

function rerender() {
  const row = state.rows.find((r) => r.ticker === state.selected);
  fetch(`data/series/${encodeURIComponent(row.ticker)}.json`, { cache: "force-cache" })
    .then((r) => (r.ok ? r.json() : null))
    .then((series) => renderDetail(row, series))
    .catch(() => renderDetail(row, null));
}

/** EPS from today's NTM, moving linearly to next fiscal year's consensus over 365 days. */
function epsAhead(row, k) {
  const target = row.fy1_eps != null && row.fy1_eps > 0 ? row.fy1_eps : row.eps;
  return row.eps + (target - row.eps) * (k / 365);
}

function priceSection(row, series) {
  const w = windowOf(state.window);
  const c = row.corridors[state.window];
  const sec = el("section", { class: "price-sec" });
  sec.append(el("h3", {}, `Price against its usual valuation, ${w.label.toLowerCase()} and one year ahead`));

  const chips = el("div", { class: "ranges", role: "group", "aria-label": "Time window" });
  for (const x of WINDOWS) {
    const b = el("button", { class: "chip", "aria-pressed": String(state.window === x.key) }, x.key);
    if (!row.corridors?.[x.key]) b.disabled = true;
    b.onclick = () => {
      state.window = x.key;
      rerender();
    };
    chips.append(b);
  }
  sec.append(chips);
  sec.append(el("p", { class: "help" },
    "The coloured bands show where the price would be if the stock were valued the way it usually was in this window. " +
    "Grey is its normal range, blue is cheap, red is expensive. The shaded area on the right projects this a year ahead, using analysts' forecasts for next year."));

  priceChart(sec, row, series, c, w.days);
  sec.append(ladder(row, c));
  return sec;
}

function priceChart(sec, row, series, c, days) {
  const W = 800, H = 280, L = 58, R = 12, T = 10, B = 24;
  const holder = el("div", { class: "chart" });
  const root = svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Price with valuation bands" });
  holder.append(root);
  sec.append(holder);

  const today = dayNum(series.dates[series.dates.length - 1]);
  const startDay = today - Math.max(days, 180);
  const endDay = today + 365;
  const hist = series.dates.map((d, i) => ({ day: dayNum(d), price: series.price[i], eps: series.eps[i] }))
    .filter((p) => p.day >= startDay);
  const ahead = [];
  for (let k = 7; k <= 365; k += 7) ahead.push({ day: today + k, eps: epsAhead(row, k) });
  const pts = [...hist.filter((h) => h.eps > 0), ...ahead].map((h) => ({
    day: h.day,
    lv: Object.fromEntries(LEVELS.map((k) => [k, c.levels[k] * h.eps])),
  }));

  const ys = [...hist.map((h) => h.price), ...pts.flatMap((q) => [q.lv["-2"], q.lv["2"]])].filter((v) => v != null && Number.isFinite(v));
  let lo = Math.min(...ys), hi = Math.max(...ys);
  const pad = (hi - lo) * 0.06 || 1;
  lo = Math.max(0, lo - pad);
  hi += pad;
  const xOf = (day) => L + ((day - startDay) / (endDay - startDay)) * (W - L - R);
  const yOf = (v) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);

  const grid = svg("g", { class: "grid" });
  for (let k = 0; k <= 4; k++) {
    const v = lo + ((hi - lo) * k) / 4;
    grid.append(svg("line", { x1: L, x2: W - R, y1: yOf(v), y2: yOf(v) }));
    const lab = svg("text", { x: L - 6, y: yOf(v) + 4, "text-anchor": "end", class: "tick" });
    lab.textContent = v >= 100 ? v.toFixed(0) : v.toFixed(2);
    grid.append(lab);
  }
  for (const [day, anchor, text] of [[startDay, "start", isoOf(startDay)], [today, "middle", "today"], [endDay, "end", isoOf(endDay)]]) {
    const lab = svg("text", { x: xOf(day), y: H - 6, "text-anchor": anchor, class: "tick" });
    lab.textContent = text;
    grid.append(lab);
  }
  root.append(grid);

  const clipId = `clip-${Math.random().toString(36).slice(2)}`;
  const defs = svg("defs");
  const clip = svg("clipPath", { id: clipId });
  clip.append(svg("rect", { x: L, y: T, width: W - L - R, height: H - T - B }));
  defs.append(clip);
  root.append(defs);
  root.append(svg("rect", { class: "future", x: xOf(today), y: T, width: xOf(endDay) - xOf(today), height: H - T - B }));
  const plot = svg("g", { "clip-path": `url(#${clipId})` });

  const areaBetween = (a, b, cls) => {
    const top = pts.map((q, i) => `${i ? "L" : "M"}${xOf(q.day).toFixed(1)},${yOf(q.lv[b]).toFixed(1)}`).join("");
    const bottom = [...pts].reverse().map((q) => `L${xOf(q.day).toFixed(1)},${yOf(q.lv[a]).toFixed(1)}`).join("");
    plot.append(svg("path", { class: `zband ${cls}`, d: `${top}${bottom}Z` }));
  };
  areaBetween("-2", "-1.5", "zone-c2");
  areaBetween("-1.5", "-1", "zone-c1");
  areaBetween("-1", "1", "zone-n");
  areaBetween("1", "1.5", "zone-e1");
  areaBetween("1.5", "2", "zone-e2");
  plot.append(svg("path", { class: "zmid", d: pts.map((q, i) => `${i ? "L" : "M"}${xOf(q.day).toFixed(1)},${yOf(q.lv["0"]).toFixed(1)}`).join("") }));

  let d = "", pen = false;
  for (const h of hist) {
    if (h.price == null) { pen = false; continue; }
    d += `${pen ? "L" : "M"}${xOf(h.day).toFixed(1)},${yOf(h.price).toFixed(1)}`;
    pen = true;
  }
  plot.append(svg("path", { class: "price", d }));
  root.append(plot);
  root.append(svg("line", { class: "todayline", x1: xOf(today), x2: xOf(today), y1: T, y2: H - B }));
  if (row.price) root.append(svg("circle", { class: "today-dot", cx: xOf(today), cy: yOf(row.price), r: 4 }));

  const legend = el("div", { class: "legend" });
  const key = (cls, text) => {
    const k = el("span", { class: "key" });
    k.append(el("span", { class: `sw ${cls}`, "aria-hidden": "true" }), document.createTextNode(text));
    legend.append(k);
  };
  key("sw-price", "Price");
  key("zone-n", "Normal");
  key("zone-c1", "Cheap");
  key("zone-c2", "Very cheap");
  key("zone-e1", "Expensive");
  key("zone-e2", "Very expensive");
  key("sw-mid", "Typical");
  holder.prepend(legend);

  const tip = el("div", { class: "tip", hidden: "" });
  holder.append(tip);
  const cross = svg("line", { class: "cross", y1: T, y2: H - B, visibility: "hidden" });
  root.append(cross);
  const hit = svg("rect", { class: "hit", x: L, y: T, width: W - L - R, height: H - T - B });
  root.append(hit);
  const nearest = (arr, day) => arr.reduce((best, q) => (Math.abs(q.day - day) < Math.abs(best.day - day) ? q : best), arr[0]);
  hit.addEventListener("pointermove", (e) => {
    const r = root.getBoundingClientRect();
    const day = Math.round(startDay + ((((e.clientX - r.left) / r.width) * W - L) / (W - L - R)) * (endDay - startDay));
    cross.setAttribute("x1", xOf(day));
    cross.setAttribute("x2", xOf(day));
    cross.setAttribute("visibility", "visible");
    const lines = [el("div", { class: "tip-date" }, isoOf(day) + (day > today ? " (projected)" : ""))];
    if (day <= today && hist.length) lines.push(el("div", {}, `Price ${money(nearest(hist, day).price, row.currency)}`));
    const q = pts.length ? nearest(pts, day) : null;
    if (q && Math.abs(q.day - day) <= 10) {
      lines.push(el("div", {}, `Normal ${money(q.lv["-1"], "")}–${money(q.lv["1"], "")}`));
      lines.push(el("div", {}, `Typical ${money(q.lv["0"], "")}`));
      lines.push(el("div", {}, `Very cheap below ${money(q.lv["-1.5"], "")}`));
    }
    tip.replaceChildren(...lines);
    tip.hidden = false;
    const x = xOf(day) * (holder.clientWidth / W);
    tip.style.left = `${Math.min(Math.max(x + 12, 0), holder.clientWidth - 190)}px`;
    tip.style.top = "40px";
  });
  hit.addEventListener("pointerleave", () => {
    cross.setAttribute("visibility", "hidden");
    tip.hidden = true;
  });
}

function ladder(row, c) {
  const wrap = el("div", { class: "ladder" });
  wrap.append(el("h4", {}, "What price would each level mean?"));
  const t = el("table");
  const head = el("tr");
  ["Level", row.metric === "ps" ? "× sales" : "× profit", "Price now", "In a year"].forEach((h, i) => head.append(el("th", i ? { class: "num" } : {}, h)));
  t.append(head);
  const eps1 = epsAhead(row, 365);
  let placed = false;
  const youAreHere = () => {
    const tr = el("tr", { class: "here" });
    tr.append(
      el("td", {}, "▶ Today"),
      el("td", { class: "num" }, `${fmt(row.pe)}×`),
      el("td", { class: "num" }, money(row.price, row.currency)),
      el("td", { class: "num" }, ""),
    );
    t.append(tr);
    placed = true;
  };
  for (const k of LEVELS) {
    const pe = c.levels[k];
    if (!placed && row.pe >= pe) youAreHere();
    const tr = el("tr", { class: `lvl-${k === "0" ? "mid" : Number(k) > 0 ? "rich" : "cheap"}` });
    tr.append(
      el("td", {}, LEVEL_NAME[k]),
      el("td", { class: "num" }, `${fmt(pe)}×`),
      el("td", { class: "num" }, money(pe * row.eps, "")),
      el("td", { class: "num" }, money(pe * eps1, "")),
    );
    t.append(tr);
  }
  if (!placed) youAreHere();
  wrap.append(t);
  wrap.append(el("p", { class: "help" },
    row.metric === "ps"
      ? `"In a year" assumes sales per share grow from the last 12 months (${fmt(row.eps, 2)}) to what analysts expect over the next 12 (${fmt(row.fy1_eps ?? row.eps, 2)}) and the stock is valued at the same multiple of sales.`
      : `"In a year" assumes profit per share grows from today's forecast (${fmt(row.eps, 2)}) to analysts' forecast for next financial year (${fmt(row.fy1_eps ?? row.eps, 2)}) and the stock is valued the same way.`));
  return wrap;
}

function detailsSection(row, series) {
  const d = el("details", { class: "more" });
  d.append(el("summary", {}, "More detail: the numbers, charts and the historical test"));

  const stats = el("div", { class: "stats" });
  const stat = (k, v, help) => {
    const s = el("div", { class: "stat", title: help });
    s.append(el("div", { class: "k" }, k), el("div", { class: "v" }, v));
    stats.append(s);
  };
  if (row.metric === "ps") {
    stat("Sales per share, last 12 months", fmt(row.eps, 2), "Reported revenue per share, in the price currency");
    stat("Price ÷ sales, last 12 months", `${fmt(row.pe, 2)}×`, "Trailing P/S");
    stat("Price ÷ expected sales, next 12 months", row.ps_forward ? `${fmt(row.ps_forward, 2)}×` : "n/a",
      `Forward P/S on ${row.rev_analysts || "?"} analysts' revenue consensus`);
    if (row.shares_source && !row.shares_source.startsWith("yahoo")) stat("Share count", "override", row.shares_source);
  } else {
    stat("Expected profit per share, next 12 months", fmt(row.eps, 2), "Analysts' average forecast (consensus NTM EPS)");
    stat("Price ÷ expected profit", row.pe == null || row.pe <= 0 ? "n/m" : `${fmt(row.pe)}×`, "Forward P/E");
  }
  stat("Price ÷ last 12 months' profit", row.trailing_pe == null ? "n/m" : `${fmt(row.trailing_pe)}×`, "Trailing P/E on the same (adjusted) basis as the forecasts");
  stat("Expected profit growth", pct(row.growth, 0), "Next 12 months' forecast against the last 12 months' reported profit");
  stat("Forecast change, next year, 90 days", pct(row.fy1_revision_90d), "How analysts' forecast for next financial year moved in 90 days");
  d.append(stats);

  if (series && series.dates.length > 1) {
    const ranges = el("div", { class: "ranges", role: "group", "aria-label": "Time range" });
    for (const r of RANGES) {
      const b = el("button", { class: "chip", "aria-pressed": String(state.range === r.days) }, r.label);
      b.onclick = () => {
        state.range = r.days;
        renderDetail(row, series);
        $("#detail details.more").open = true;
      };
      ranges.append(b);
    }
    d.append(ranges);
    smallCharts(d, row, series);
  }

  const past = row.past;
  if (past && past.scored_days) {
    const wrap = el("div", { class: "past" });
    wrap.append(el("h4", {}, "Historical test: what happened after the stock looked cheap or expensive"));
    wrap.append(el("p", { class: "help" }, "Average price change after each day the stock was cheap (bottom sixth of its 3-year range) or expensive (top sixth), next to the average after any day. Reconstructed history flatters these numbers."));
    const t = el("table");
    const head = el("tr");
    ["After", "Any day", "After cheap", "After expensive"].forEach((h, i) => head.append(el("th", i ? { class: "num" } : {}, h)));
    t.append(head);
    for (const [h, s] of Object.entries(past.horizons)) {
      const tr = el("tr");
      tr.append(el("td", {}, `${Math.round(Number(h) / 21)} months`));
      tr.append(el("td", { class: "num" }, pct(s.all_avg)));
      const cheap = el("td", { class: "num" }, `${pct(s.cheap_avg)} (${s.cheap_n} days)`);
      if (s.cheap_avg != null && s.all_avg != null && s.cheap_avg > s.all_avg) cheap.classList.add("better");
      tr.append(cheap, el("td", { class: "num" }, `${pct(s.expensive_avg)} (${s.expensive_n} days)`));
      t.append(tr);
    }
    wrap.append(t);
    d.append(wrap);
  }
  if (row.warnings?.length) {
    const ul = el("ul", { class: "warn" });
    row.warnings.forEach((w) => ul.append(el("li", {}, w)));
    d.append(ul);
  }
  return d;
}

function sliceRange(series) {
  if (!state.range) return series;
  const last = dayNum(series.dates[series.dates.length - 1]);
  const i = series.dates.findIndex((d) => dayNum(d) >= last - state.range);
  const from = i < 0 ? 0 : i;
  return Object.fromEntries(Object.entries(series).map(([k, v]) => [k, v.slice(from)]));
}

function smallCharts(box, row, full) {
  const s = sliceRange(full);
  const c = row.corridors?.[row.mainKey];
  const charts = [
    row.metric === "ps"
      ? { title: "Sales per share, last 12 months (as reported at the time)", values: s.eps, digits: 2 }
      : { title: "Expected profit per share, next 12 months (analyst consensus)", values: s.eps, digits: 2 },
    { title: `Price ÷ ${row.metric === "ps" ? "sales" : "expected profit"}, with its normal range over ${row.mainKey ? spanOf(row.mainKey) : "the last 3 years"}`,
      values: s.pe, digits: row.metric === "ps" ? 2 : 1, band: c ? [c.levels["-1"], c.levels["0"], c.levels["1"]] : null },
  ].map((spec) => lineChart(box, s, spec));
  const holder = charts[1].wrap;
  const tip = el("div", { class: "tip", hidden: "" });
  holder.append(tip);
  const move = (idx) => {
    for (const ch of charts) ch.cross(idx);
    if (idx == null) {
      tip.hidden = true;
      return;
    }
    tip.hidden = false;
    tip.replaceChildren(
      el("div", { class: "tip-date" }, s.dates[idx]),
      el("div", {}, `Price ${money(s.price[idx], row.currency)}`),
      el("div", {}, `Expected profit ${fmt(s.eps[idx], 2)}`),
      el("div", {}, `Price ÷ profit ${s.pe[idx] == null ? "n/m" : fmt(s.pe[idx])}×`),
    );
    const x = charts[1].xOf(idx) * (holder.clientWidth / 800);
    tip.style.left = `${Math.min(Math.max(x + 12, 0), holder.clientWidth - 150)}px`;
    tip.style.top = "28px";
  };
  charts.forEach((ch) => ch.onMove(move));
}

function lineChart(box, s, { title, values, digits, band, extra }) {
  const W = 800, H = 180, L = 52, R = 12, T = 8, B = 24;
  const wrap = el("div", { class: "chart" });
  wrap.append(el("h4", {}, title));
  const root = svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": title });
  wrap.append(root);
  box.append(wrap);

  const t0 = dayNum(s.dates[0]), t1 = dayNum(s.dates[s.dates.length - 1]) || t0 + 1;
  const nums = values.concat(extra || []).filter((v) => v != null && Number.isFinite(v));
  if (band) nums.push(band[0], band[2]);
  let lo = nums.length ? Math.min(...nums) : 0, hi = nums.length ? Math.max(...nums) : 1;
  if (lo === hi) { lo -= 1; hi += 1; }
  const pad = (hi - lo) * 0.08;
  lo -= pad; hi += pad;
  const xOf = (i) => L + ((dayNum(s.dates[i]) - t0) / (t1 - t0 || 1)) * (W - L - R);
  const yOf = (v) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);

  const grid = svg("g", { class: "grid" });
  for (let k = 0; k <= 4; k++) {
    const v = lo + ((hi - lo) * k) / 4;
    grid.append(svg("line", { x1: L, x2: W - R, y1: yOf(v), y2: yOf(v) }));
    const lab = svg("text", { x: L - 6, y: yOf(v) + 4, "text-anchor": "end", class: "tick" });
    lab.textContent = v.toFixed(digits);
    grid.append(lab);
  }
  for (const f of [0, 0.5, 1]) {
    const i = Math.round(f * (s.dates.length - 1));
    const lab = svg("text", { x: xOf(i), y: H - 6, "text-anchor": f === 0 ? "start" : f === 1 ? "end" : "middle", class: "tick" });
    lab.textContent = s.dates[i];
    grid.append(lab);
  }
  root.append(grid);
  if (band && band[0] != null && band[2] != null) {
    root.append(svg("rect", { class: "band", x: L, width: W - L - R, y: yOf(band[2]), height: yOf(band[0]) - yOf(band[2]) }));
    root.append(svg("line", { class: "mean", x1: L, x2: W - R, y1: yOf(band[1]), y2: yOf(band[1]) }));
  }
  const path = (vals) => {
    let d = "", pen = false;
    vals.forEach((v, i) => {
      if (v == null || !Number.isFinite(v)) { pen = false; return; }
      d += `${pen ? "L" : "M"}${xOf(i).toFixed(1)},${yOf(v).toFixed(1)}`;
      pen = true;
    });
    return d;
  };
  if (extra) root.append(svg("path", { class: "series extra", d: path(extra) }));
  root.append(svg("path", { class: "series", d: path(values) }));
  const cross = svg("line", { class: "cross", y1: T, y2: H - B, visibility: "hidden" });
  root.append(cross);
  const hit = svg("rect", { class: "hit", x: L, y: T, width: W - L - R, height: H - T - B });
  root.append(hit);

  let handler = () => {};
  const idxAt = (evt) => {
    const r = root.getBoundingClientRect();
    const x = ((evt.clientX - r.left) / r.width) * W;
    const t = t0 + ((x - L) / (W - L - R)) * (t1 - t0);
    let a = 0, b = s.dates.length - 1;
    while (b - a > 1) {
      const m = (a + b) >> 1;
      if (dayNum(s.dates[m]) < t) a = m; else b = m;
    }
    return Math.abs(dayNum(s.dates[a]) - t) < Math.abs(dayNum(s.dates[b]) - t) ? a : b;
  };
  hit.addEventListener("pointermove", (e) => handler(idxAt(e)));
  hit.addEventListener("pointerleave", () => handler(null));
  return {
    wrap,
    xOf,
    onMove: (fn) => (handler = fn),
    cross: (idx) => {
      if (idx == null) return cross.setAttribute("visibility", "hidden");
      cross.setAttribute("x1", xOf(idx));
      cross.setAttribute("x2", xOf(idx));
      cross.setAttribute("visibility", "visible");
    },
  };
}

// ---------- market breadth (NYSE McClellan Summation Index) ----------

const BREADTH = "$NYSI";
const BREADTH_RANGES = [
  { label: "6M", days: 183 },
  { label: "1Y", days: 365 },
  { label: "All", days: null },
];
let breadthRange = 365;

async function showBreadth() {
  const box = pageBox();
  try {
    const res = await fetch("data/breadth.json", { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    renderBreadth(await res.json());
  } catch {
    box.replaceChildren(el("p", { class: "empty" }, "No breadth data yet. It is computed each weekday night after the US close."));
  }
}

// Consecutive sessions the last value kept moving the same way.
function streak(xs) {
  const n = xs.length;
  if (n < 2) return { dir: 0, days: 0 };
  const dir = Math.sign(xs[n - 1] - xs[n - 2]);
  let days = 0;
  for (let i = n - 1; i > 0 && Math.sign(xs[i] - xs[i - 1]) === dir && dir !== 0; i--) days++;
  return { dir, days };
}

function breadthCard(b) {
  const n = b.dates.length - 1;
  const v = b.nysi[n], rsi = b.rsi[n], rsiPrev = b.rsi[n - 1];
  const bull = b.macd[n] > b.signal[n];
  const rising = b.osc[n] > 0;
  const run = streak(b.nysi);
  const side = rising && bull ? "cheap" : !rising && !bull ? "rich" : "na";
  const card = el("section", { class: `verdict side-${side}` });
  const head = rising && bull
    ? v < 0 ? "Breadth turning up from a washout" : "Breadth broad and improving"
    : !rising && !bull
      ? v > 0 ? "Breadth rolling over from strength" : "Breadth weak and still falling"
      : "Breadth turning, not confirmed";
  card.append(el("h3", {}, head));
  const lines = el("div", { class: "v-lines" });
  const say = (text, cls = "") => lines.append(el("p", { class: cls }, text));

  say(`The summation index is at ${fmt(v, 0)} and has ${run.dir > 0 ? "risen" : "fallen"} ${run.days} session${run.days === 1 ? "" : "s"} in a row. ` +
    (rising ? "More NYSE stocks are rising than its recent average, so breadth is improving." : "Fewer NYSE stocks are rising than its recent average, so breadth is weakening.") +
    ` ${v < 0 ? "Below zero: over the last couple of months most stocks have lagged." : "Above zero: most stocks have been taking part."}`);
  if (rsi != null) {
    const zone = rsi < 30 ? "oversold" : rsi > 70 ? "overbought" : "neutral";
    say(`RSI of the index ${fmt(rsi, 0)} (${zone}), ${rsi > rsiPrev ? "turning higher" : "still falling"}.`);
  }
  const lc = b.last_cross;
  say(`MACD is ${bull ? "above" : "below"} its signal line` +
    (lc ? `; the last cross was ${lc.dir === "bull" ? "bullish" : "bearish"} on ${lc.date}.` : ".") +
    (Math.abs(b.macd[n] - b.signal[n]) < 2 ? " The two lines are nearly touching, so a cross is close." : ""));
  if (rising && bull && v < 0) {
    say("This is the classic early buy signal for the broad market. It fails often on the first hook; trust it after a few weeks of follow-through.", "note-line");
  }
  if (b.official) {
    say(`StockCharts' official $NYSI: ${fmt(b.official.nysi, 1)} on ${b.official.date}` +
      `${b.official.rsi != null ? `, RSI ${fmt(b.official.rsi, 1)}` : ""}. Our line is counted from ${b.advances[n] + b.declines[n] + (b.unchanged?.[n] ?? 0)} NYSE issues and set to the official level, so day-to-day moves can differ slightly.`, "note-line");
  }
  card.append(lines);
  return card;
}

function renderBreadth(b) {
  const box = pageBox();
  box.replaceChildren();
  const head = el("div", { class: "d-head" });
  head.append(el("h2", {}, "Market breadth"), el("div", { class: "d-sub" }, `NYSE McClellan Summation Index (ratio-adjusted) · data as of ${b.as_of}`));
  box.append(head, breadthCard(b));

  const sec = el("section");
  sec.append(el("h3", {}, "History"));
  sec.append(el("p", { class: "help" }, "Advances minus declines per 1000 NYSE issues, smoothed (19- and 39-day) and summed. Rising: breadth improving. The RSI and MACD below are taken of the index itself."));
  const ranges = el("div", { class: "ranges" });
  for (const r of BREADTH_RANGES) {
    const b2 = el("button", { class: "chip", "aria-pressed": String(breadthRange === r.days) }, r.label);
    b2.addEventListener("click", () => { breadthRange = r.days; renderBreadth(b); });
    ranges.append(b2);
  }
  sec.append(ranges);
  box.append(sec);

  let from = 0;
  if (breadthRange) {
    const last = dayNum(b.dates[b.dates.length - 1]);
    from = Math.max(0, b.dates.findIndex((d) => dayNum(d) >= last - breadthRange));
  }
  const s = Object.fromEntries(Object.entries(b).map(([k, v]) => [k, Array.isArray(v) ? v.slice(from) : v]));
  const charts = [
    lineChart(sec, s, { title: "Summation index (zero line dashed)", values: s.nysi, digits: 0, band: [0, 0, 0] }),
    lineChart(sec, s, { title: "MACD of the index (solid) and its signal line (dashed)", values: s.macd, extra: s.signal, digits: 0, band: [0, 0, 0] }),
    lineChart(sec, s, { title: "RSI of the index, 14 days (shaded 30–70)", values: s.rsi, digits: 0, band: [30, 50, 70] }),
  ];
  const holder = charts[0].wrap;
  const tip = el("div", { class: "tip", hidden: "" });
  holder.append(tip);
  const move = (idx) => {
    for (const ch of charts) ch.cross(idx);
    if (idx == null) { tip.hidden = true; return; }
    tip.hidden = false;
    tip.replaceChildren(
      el("div", { class: "tip-date" }, s.dates[idx]),
      el("div", {}, `NYSI ${fmt(s.nysi[idx], 0)}`),
      el("div", {}, `RSI ${fmt(s.rsi[idx], 0)} · MACD ${fmt(s.macd[idx] - s.signal[idx], 1)} vs signal`),
      el("div", {}, `${s.advances[idx]} up · ${s.declines[idx]} down`),
    );
    const x = charts[0].xOf(idx) * (holder.clientWidth / 800);
    tip.style.left = `${Math.min(Math.max(x + 12, 0), holder.clientWidth - 170)}px`;
    tip.style.top = "28px";
  };
  charts.forEach((ch) => ch.onMove(move));
}

// ---------- horizon: what the market is waiting for ----------

const HZ_RANGES = [
  { label: "2 weeks", days: 14 },
  { label: "1 month", days: 31 },
  { label: "All", days: null },
];
const HZ_THEMES = { rates: "Rates", oil: "Oil and the Gulf", geopolitics: "Geopolitics", growth: "Growth", politics: "Politics" };
const HZ_WEEKDAY = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const HZ_MONTH = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const hz = { range: 31, all: false };

async function showHorizon() {
  const box = pageBox();
  try {
    const res = await fetch("data/horizon.json", { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    renderHorizon(await res.json());
  } catch {
    box.replaceChildren(el("p", { class: "empty" }, "No horizon data yet. It is collected each weekday night after the US close."));
  }
}

const hzDate = (iso) => {
  const d = new Date(`${iso}T12:00:00Z`);
  return `${HZ_WEEKDAY[d.getUTCDay()]} ${d.getUTCDate()} ${HZ_MONTH[d.getUTCMonth()]}`;
};
const hzIn = (iso, asOf) => {
  const n = dayNum(iso) - dayNum(asOf);
  return n === 0 ? "today" : n === 1 ? "tomorrow" : `in ${n} days`;
};
const hzPct = (p) => `${Math.round(p * 100)}%`;
const hzPts = (now, past) => (past == null ? null : Math.round((now - past) * 100));
const hzSigned = (v, d = 0) => `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(d)}`;

function hzImpact(n) {
  return el("span", { class: "hz-impact", title: `Impact on an AI and memory book: ${n} of 3`, "aria-label": `impact ${n} of 3` }, "●".repeat(n) + "○".repeat(3 - n));
}

function hzExpect(x) {
  if (x.median != null) {
    const v = x.unit === "k" ? `${Math.round(x.median)}k`
      : x.unit === "%" ? `${x.signed === false ? x.median.toFixed(2) : hzSigned(x.median, 2)}%` : fmt(x.median, 2);
    return `${x.name}: market median ${v}`;
  }
  if (x.outcomes) return `${x.outcomes.map(([t, p]) => `${t} ${hzPct(p)}`).join(" · ")}`;
  if (x.text) return `${x.name} ${x.text}`;
  return null;
}

function hzTags(tags) {
  const box = el("div", { class: "hz-tags" });
  for (const t of tags || []) box.append(el("p", { class: `hz-tag tag-${t.key}` }, t.text));
  return box;
}

function hzEvent(ev, asOf) {
  const li = el("li", { class: "hz-ev" });
  const when = el("div", { class: "hz-when" });
  when.append(el("div", { class: "hz-day" }, hzDate(ev.date)), el("div", { class: "muted" }, hzIn(ev.date, asOf)));
  const body = el("div", { class: "hz-body" });
  const title = el("div", { class: "hz-title" });
  title.append(el("strong", {}, ev.name), hzImpact(ev.impact));
  const meta = [ev.time, ev.period, ev.company && ev.company !== ev.name ? ev.company : null].filter(Boolean).join(" · ");
  if (meta) title.append(el("span", { class: "muted" }, meta));
  body.append(title);
  for (const x of ev.expect || []) {
    const t = hzExpect(x);
    if (t) body.append(el("div", { class: "hz-expect" }, t));
  }
  if (ev.note) body.append(el("div", { class: "hz-note" }, ev.note));
  body.append(hzTags(ev.tags));
  const nums = el("div", { class: "hz-nums" });
  const via = ev.asset && ev.ticker !== ev.asset ? ` (${ev.asset})` : "";
  if (ev.implied) nums.append(el("div", {}, `Options: ±${(ev.implied.move * 100).toFixed(1)}%${via} by ${ev.implied.expiry.slice(5)}`));
  if (ev.runup) {
    const r = ev.runup;
    nums.append(el("div", { class: r.r20 >= 0 ? "ret pos" : "ret neg" }, `20d ${pct(r.r20, 0)}${r.z20 != null ? ` (${hzSigned(r.z20, 1)}σ)` : ""}${via && !ev.implied ? via : ""}`));
  }
  li.append(when, body, nums);
  return li;
}

// One probability as a 90-day line on a fixed 0–100% scale, so a move looks as big as it is.
function hzSpark(hist) {
  const w = 120, h = 30;
  const s = svg("svg", { viewBox: `0 0 ${w} ${h}`, class: "hz-spark", "aria-hidden": "true" });
  s.append(svg("line", { x1: 0, x2: w, y1: h / 2, y2: h / 2, class: "hz-mid" }));
  if (hist && hist.length > 1) {
    const d = hist.map(([, p], i) => `${i ? "L" : "M"}${((i / (hist.length - 1)) * w).toFixed(1)},${((1 - p) * (h - 2) + 1).toFixed(1)}`).join("");
    s.append(svg("path", { d, class: "hz-line" }));
  }
  return s;
}

function hzChange(o, past, label) {
  const v = hzPts(o.p, past);
  if (v == null) return el("span", { class: "hz-chg muted" }, `${label} n/a`);
  const helps = o.good_if === "yes" ? v > 0 : o.good_if === "no" ? v < 0 : null;
  const cls = v === 0 || helps == null ? "muted" : helps ? "ret pos" : "ret neg";
  return el("span", { class: `hz-chg ${cls}` }, `${label} ${hzSigned(v)}`);
}

function hzMarket(m) {
  const card = el("article", { class: "hz-mkt" });
  const head = el("div", { class: "hz-title" });
  head.append(el("strong", {}, m.title), hzImpact(m.impact));
  const link = el("a", { href: m.url, target: "_blank", rel: "noopener", class: "muted" }, "Polymarket ↗");
  head.append(link);
  card.append(head);
  if (m.note) card.append(el("div", { class: "hz-note" }, m.note));
  for (const o of m.outcomes) {
    const row = el("div", { class: "hz-out" });
    const lone = m.outcomes.length === 1;
    const name = el("div", { class: "hz-oname" }, lone ? "" : o.label);
    if (o.good_if === "yes" || o.good_if === "no") {
      name.append(el("span", { class: "muted" }, `${lone ? "" : " · "}good for the book if ${o.good_if}`));
    }
    const chg = el("div", { class: "hz-chgs" });
    chg.append(hzChange(o, o.p1, "1d"), hzChange(o, o.p7, "7d"), hzChange(o, o.p30, "30d"));
    row.append(name, el("div", { class: "hz-p" }, hzPct(o.p)), hzSpark(o.hist), chg);
    card.append(row);
    if (o.tags?.length) card.append(hzTags(o.tags));
  }
  return card;
}

function hzSummary(d, events) {
  const card = el("section", { class: "verdict" });
  card.append(el("h3", {}, "What the market is waiting for"));
  const lines = el("div", { class: "v-lines" });
  const say = (text, cls = "") => lines.append(el("p", { class: cls }, text));
  const soon = events.filter((e) => e.impact >= 3 && dayNum(e.date) - dayNum(d.as_of) <= 14);
  if (soon.length) say(`Next two weeks: ${soon.length} high-impact date${soon.length === 1 ? "" : "s"}: ${soon.map((e) => `${e.name.replace(" results", "")} (${hzDate(e.date)})`).join(", ")}.`);

  const moves = [];
  for (const m of d.markets) for (const o of m.outcomes) {
    const v = hzPts(o.p, o.p7);
    if (v != null && Math.abs(v) >= 5) moves.push({ m, o, v });
  }
  moves.sort((a, b) => Math.abs(b.v) - Math.abs(a.v));
  if (moves.length) {
    say(`Biggest shifts this week: ${moves.slice(0, 3).map(({ m, o, v }) => `${m.title}${m.outcomes.length > 1 ? ` (${o.label})` : ""} ${hzSigned(v)} points to ${hzPct(o.p)}`).join("; ")}.`);
  }
  const tails = [], upside = [];
  for (const m of d.markets) for (const o of m.outcomes) for (const t of o.tags || []) {
    const name = `${m.title}${m.outcomes.length > 1 ? ` (${o.label})` : ""} ${hzPct(o.p)}`;
    if (t.key === "tail-bad" && m.impact >= 2) tails.push(name);
    if (t.key === "tail-good" && m.impact >= 2) upside.push(name);
  }
  if (upside.length) say(`Cheap upside the market doubts: ${upside.slice(0, 4).join("; ")}.`);
  if (tails.length) say(`Tail risks it dismisses: ${tails.slice(0, 4).join("; ")}.`);
  const a = d.assets || {};
  const tone = ["SPY", "QQQ", "SMH"].filter((k) => a[k]).map((k) => `${k} ${pct(a[k].r20, 0)} in 20 days, ${pct(a[k].from_high, 0)} from its high`);
  if (tone.length) say(`So far: ${tone.join(" · ")}.`, "note-line");
  say("Read the tags as questions, not calls: a priced-in outcome moves prices most when it fails to happen, and a date the market has front-run often reverses on the day.", "note-line");
  card.append(lines);
  return card;
}

function renderHorizon(d) {
  const box = pageBox();
  box.replaceChildren();
  const head = el("div", { class: "d-head" });
  head.append(el("h2", {}, "Horizon"), el("div", { class: "d-sub" }, `What the market is waiting for, how likely it is, and how far it has run ahead · data as of ${d.as_of}`));

  const shown = d.scheduled.filter((e) => (hz.all || e.impact >= 2) && (!hz.range || dayNum(e.date) - dayNum(d.as_of) <= hz.range));
  box.append(head, hzSummary(d, d.scheduled.filter((e) => e.impact >= 2)));

  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "Dated events"));
  sec.append(el("p", { class: "help" }, "These will happen; the question is the outcome. Macro expectations come from Kalshi's traded ranges, the options figure is the at-the-money straddle to the first expiry after the date (the move the options market prices in), and 20d is how far the exposed asset has run into it, in its own volatility units."));
  const ctl = el("div", { class: "ranges" });
  for (const r of HZ_RANGES) {
    const b = el("button", { class: "chip", "aria-pressed": String(hz.range === r.days) }, r.label);
    b.addEventListener("click", () => { hz.range = r.days; renderHorizon(d); });
    ctl.append(b);
  }
  const allBtn = el("button", { class: "chip", "aria-pressed": String(hz.all) }, "Every stock I track");
  allBtn.addEventListener("click", () => { hz.all = !hz.all; renderHorizon(d); });
  ctl.append(allBtn);
  sec.append(ctl);
  const list = el("ol", { class: "hz-list" });
  for (const ev of shown) list.append(hzEvent(ev, d.as_of));
  if (!shown.length) list.append(el("li", { class: "muted" }, "Nothing in this window."));
  sec.append(list);
  box.append(sec);

  const sec2 = el("section", { class: "hz-sec" });
  sec2.append(el("h3", {}, "Could happen"));
  sec2.append(el("p", { class: "help" }, "Prices on Polymarket read as probabilities. The changes are in percentage points; green means the move helps a long AI and memory book. The line is the last 90 days on a 0–100% scale, with 50% marked."));
  const order = Object.keys(HZ_THEMES);
  const themes = [...new Set(d.markets.map((m) => m.theme))].sort((a, b) => (order.indexOf(a) + 99) % 99 - (order.indexOf(b) + 99) % 99);
  for (const th of themes) {
    sec2.append(el("h4", {}, HZ_THEMES[th] || th));
    const grid = el("div", { class: "hz-grid" });
    for (const m of d.markets.filter((x) => x.theme === th)) grid.append(hzMarket(m));
    sec2.append(grid);
  }
  box.append(sec2);
  box.append(el("p", { class: "help" }, "Coming: positioning (who is already leaning which way) and sentiment, so each catalyst shows how crowded the bet on it is."));
}

// ---------- positioning: who is already leaning which way ----------

const PS_GROUPS = { memory: "Memory", "ai-infra": "AI infrastructure", neocloud: "Neoclouds", megacap: "Megacaps", crowding: "Old crowding watchlist", market: "Index and macro ETFs" };
const PS_SIDES = { leveraged: "Hedge funds (leveraged funds)", asset_managers: "Asset managers", dealers: "Dealers" };
const ps = { contract: "20974+", group: "all" };

async function showPositioning() {
  const box = pageBox();
  try {
    const res = await fetch("data/positioning.json", { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    renderPositioning(await res.json());
  } catch {
    box.replaceChildren(el("p", { class: "empty" }, "No positioning data yet. It is collected each weekday night after the US close."));
  }
}

const psOrd = (p) => (p == null ? "n/a" : ordinal(Math.round(p)));

// A chart with a one-line readout under its title that follows the pointer.
function psChart(box, s, opts, readout) {
  const ch = lineChart(box, s, opts);
  const line = el("div", { class: "help ps-readout" }, readout(s.dates.length - 1));
  ch.wrap.querySelector("h4").after(line);
  ch.onMove((i) => {
    ch.cross(i);
    line.textContent = readout(i ?? s.dates.length - 1);
  });
  return ch;
}

function psSummary(d) {
  const card = el("section", { class: "verdict" });
  card.append(el("h3", {}, "How the market is positioned"));
  const lines = el("div", { class: "v-lines" });
  const say = (text, cls = "") => lines.append(el("p", { class: cls }, text));
  const md = d.margin_debt;
  if (md) say(`Leverage: margin debt ${fmt(md.debit_billions / 1000, 2)} trillion dollars in ${md.month}, ${pct(md.yoy, 0)} on a year earlier, at the ${psOrd(md.pct_all)} percentile of its history${md.pct_all >= 99 ? " (a record or close to it)" : ""}.`);
  const sp = d.cftc["13874+"], nq = d.cftc["20974+"];
  if (sp && nq) {
    say(`Futures (${sp.report_date}): hedge funds are net ${sp.latest.leveraged < 0 ? "short" : "long"} S&P futures, ${psOrd(sp.pct_2y.leveraged)} percentile of two years, while asset managers sit at the ${psOrd(sp.pct_2y.asset_managers)}. ` +
      `In Nasdaq futures hedge funds are at the ${psOrd(nq.pct_2y.leveraged)} and asset managers at the ${psOrd(nq.pct_2y.asset_managers)}.` +
      (sp.pct_2y.asset_managers > 50 && sp.pct_2y.leveraged < 30 ? " Fast money is already light; real money still has length it could sell." : ""));
  }
  const v = d.volatility;
  const vix = v.indices.VIX, vxn = v.indices.VXN, skew = v.indices.SKEW;
  if (vix && vxn) say(`Fear: VIX ${fmt(vix.value, 1)} (${hzSigned(vix.change_5d, 1)} in 5 days, ${psOrd(vix.pct_1y)} percentile of the year), Nasdaq volatility ${fmt(vxn.value, 1)} (${hzSigned(vxn.change_5d, 1)}).`);
  const vn = v.vxn_vs_nasdaq;
  if (vn) {
    const fading = vn.qqq_down_days >= 3 && vn.qqq_down_vxn_down / vn.qqq_down_days >= 0.5;
    say(`Panic check: the Nasdaq fell on ${vn.qqq_down_days} of the last ${vn.sessions} sessions and its volatility fell on ${vn.qqq_down_vxn_down} of those days. ` +
      (fading ? "Volatility falling with prices: the selling is getting orderly, a classic sign a selloff is tiring."
        : vn.qqq_down_days >= 3 ? "Volatility still rises on down days: fear is building, no sign of exhaustion yet." : "Too few down days to read."),
      fading ? "pattern yes" : "");
  }
  if (skew && skew.pct_1y >= 90) say(`Tail hedging: SKEW at ${fmt(skew.value, 0)}, ${psOrd(skew.pct_1y)} percentile of the year. Investors are paying up for crash protection.`);
  if (v.term_ratio) say(`Short-term against 3-month VIX: ${fmt(v.term_ratio.value, 2)}${v.term_ratio.value >= 1 ? ", inverted: near-term stress is priced above later stress." : v.term_ratio.value >= 0.95 ? ", close to inverting." : ", normal upward slope."}`);
  const m = d.market?.scores;
  if (m) say(`Model scores (0–100): leverage ${fmt(m.gross_leverage, 0)}, systematic selling pressure ${fmt(m.systematic_selling, 0)}, liquidity fragility ${fmt(m.liquidity_fragility, 0)}, direction ${hzSigned(m.directional_exposure, 0)} (−100 short to +100 long).`, "note-line");
  say("Light positioning is fuel, not a trigger: it says how hard prices can move once selling stops, not when.", "note-line");
  card.append(lines);
  return card;
}

function psCell(v, { digits = 1, pctFmt = false, hi = null, lo = null } = {}) {
  const td = el("td", { class: "num" }, v == null ? "n/a" : pctFmt ? pct(v, 0) : fmt(v, digits));
  if (v != null && hi != null && v >= hi) td.classList.add("ps-hot");
  if (v != null && lo != null && v <= lo) td.classList.add("ps-cold");
  return td;
}

function renderPositioning(d) {
  const box = pageBox();
  box.replaceChildren();
  const head = el("div", { class: "d-head" });
  head.append(el("h2", {}, "Positioning"), el("div", { class: "d-sub" }, `Who is already leaning which way · prices as of ${d.as_of}`));
  box.append(head, psSummary(d));

  // Futures by trader type
  const fut = el("section", { class: "hz-sec" });
  fut.append(el("h3", {}, "Index futures by trader type"));
  fut.append(el("p", { class: "help" }, "CFTC Traders in Financial Futures, weekly (Tuesday positions, published Friday). Net long minus short as a share of open interest; the percentile compares it with the last two years."));
  const t = el("table", { class: "ps-table" });
  const hr = el("tr");
  ["Index", ...Object.values(PS_SIDES)].forEach((h, i) => hr.append(el("th", { class: i ? "num" : "" }, h)));
  t.append(el("thead"), el("tbody"));
  t.tHead.append(hr);
  for (const [code, c] of Object.entries(d.cftc)) {
    const tr = el("tr", { class: code === ps.contract ? "ps-sel" : "" });
    tr.append(el("td", {}, c.name));
    for (const k of Object.keys(PS_SIDES)) {
      tr.append(el("td", { class: "num" }, `${hzSigned(c.latest[k], 1)}% · ${psOrd(c.pct_2y[k])}`));
    }
    tr.addEventListener("click", () => { ps.contract = code; renderPositioning(d); });
    t.tBodies[0].append(tr);
  }
  const fs = el("div", { class: "ps-scroll" });
  fs.append(t);
  fut.append(fs);
  const c = d.cftc[ps.contract];
  if (c) {
    const s = { dates: c.history.dates };
    psChart(fut, s, { title: `${c.name}: hedge funds (solid) and asset managers (dashed), % of open interest`, values: c.history.leveraged, extra: c.history.asset_managers, digits: 0, band: [0, 0, 0] },
      (i) => `${s.dates[i]}: hedge funds ${hzSigned(c.history.leveraged[i], 1)}%, asset managers ${hzSigned(c.history.asset_managers[i], 1)}%, dealers ${hzSigned(c.history.dealers[i], 1)}%`);
  }
  box.append(fut);

  // Volatility complex
  const vol = el("section", { class: "hz-sec" });
  vol.append(el("h3", {}, "Volatility and hedging"));
  vol.append(el("p", { class: "help" }, "Cboe indices. The percentile compares today with the last year; high means more fear or more hedging than usual."));
  const vt = el("table", { class: "ps-table" });
  vt.append(el("thead"), el("tbody"));
  const vh = el("tr");
  ["Index", "Level", "1 day", "5 days", "Year pct"].forEach((h, i) => vh.append(el("th", { class: i ? "num" : "" }, h)));
  vt.tHead.append(vh);
  for (const k of ["VIX", "VXN", "VIX9D", "VIX3M", "VVIX", "SKEW", "OVX"]) {
    const x = d.volatility.indices[k];
    if (!x) continue;
    const tr = el("tr");
    tr.append(el("td", {}, x.name), psCell(x.value), psCell(x.change_1d, { hi: 2, lo: -2 }), psCell(x.change_5d, { hi: 3, lo: -3 }), psCell(x.pct_1y, { digits: 0, hi: 80, lo: 20 }));
    vt.tBodies[0].append(tr);
  }
  const vs = el("div", { class: "ps-scroll" });
  vs.append(vt);
  vol.append(vs);
  const vxn = d.volatility.indices.VXN;
  if (vxn) {
    const s = { dates: vxn.history.dates };
    psChart(vol, s, { title: "Nasdaq-100 volatility (VXN), last year", values: vxn.history.values, digits: 0 }, (i) => `${s.dates[i]}: VXN ${fmt(vxn.history.values[i], 1)}`);
  }
  box.append(vol);

  // Margin debt
  const md = d.margin_debt;
  if (md) {
    const sec = el("section", { class: "hz-sec" });
    sec.append(el("h3", {}, "Margin debt"));
    sec.append(el("p", { class: "help" }, "FINRA customer debit balances, monthly, in billions of dollars. Borrowed money in the market; it turns into forced selling when prices fall far enough."));
    const s = { dates: md.history.months.map((m) => `${m}-01`) };
    psChart(sec, s, { title: "Margin debt, last five years (billions of dollars)", values: md.history.values, digits: 0 }, (i) => `${md.history.months[i]}: ${fmt(md.history.values[i], 0)} billion`);
    box.append(sec);
  }

  // Stocks
  const st = el("section", { class: "hz-sec" });
  st.append(el("h3", {}, "Stocks: long and short crowding"));
  st.append(el("p", { class: "help" }, "Long side: the model's long-crowding score leans on momentum ranks, so read it next to the moves measured in each stock's own volatility (σ), its distance above the 200-day average in σ, and how closely it trades with GVIP, Goldman's basket of hedge funds' favourite longs. Short side: days to cover, borrow fee and the change in short interest. Orange marks a stretched reading, blue a washed-out one."));
  const chips = el("div", { class: "ranges" });
  for (const [k, label] of [["all", "All"], ...Object.entries(PS_GROUPS)]) {
    const b = el("button", { class: "chip", "aria-pressed": String(ps.group === k) }, label);
    b.addEventListener("click", () => { ps.group = k; renderPositioning(d); });
    chips.append(b);
  }
  st.append(chips);
  const tbl = el("table", { class: "ps-table ps-stocks" });
  tbl.append(el("thead"), el("tbody"));
  const sh = el("tr");
  [["Stock", ""], ["Long crowd", "Model long-crowding score, 0–100"], ["20d σ", "Last 20 sessions in units of the stock's own volatility"], ["6m σ", "Last 120 sessions in volatility units"],
    ["Above 200d", "Distance above the 200-day average, in volatility units"], ["From high", "Below the 1-year high"], ["Trades with crowd", "Correlation with GVIP over 60 sessions"],
    ["Short crowd", "Model short-crowding score, 0–100"], ["Days to cover", "Short interest ÷ average daily volume"], ["Borrow fee", "Annual % to borrow the shares (IBKR)"], ["SI change", "Change in short interest since the last report"]]
    .forEach(([h, tip], i) => sh.append(el("th", { class: i ? "num" : "", title: tip }, h)));
  tbl.tHead.append(sh);
  const order = Object.keys(PS_GROUPS);
  const rank = (g) => (order.includes(g) ? order.indexOf(g) : order.length);
  const rows = d.stocks.filter((r) => ps.group === "all" || r.group === ps.group)
    .sort((a, b) => rank(a.group) - rank(b.group) || a.symbol.localeCompare(b.symbol));
  let lastGroup = null;
  for (const r of rows) {
    if (ps.group === "all" && r.group !== lastGroup) {
      lastGroup = r.group;
      const gh = el("tr", { class: "ps-group" });
      gh.append(el("td", { colspan: "11" }, PS_GROUPS[r.group] || r.group || "Other"));
      tbl.tBodies[0].append(gh);
    }
    const p = r.price || {}, s = r.short_side || {};
    const tr = el("tr");
    const name = el("td");
    name.append(el("strong", {}, r.symbol), el("span", { class: "name" }, r.name || ""));
    tr.append(name,
      psCell(r.scores.long_crowding, { digits: 0, hi: 75, lo: 25 }),
      psCell(p.z_20d, { digits: 1, hi: 1.5, lo: -1.5 }),
      psCell(p.z_120d, { digits: 1, hi: 1.5, lo: -1.5 }),
      psCell(p.above_200d_sigma, { digits: 1, hi: 1.5, lo: -1.5 }),
      psCell(p.from_high, { pctFmt: true, lo: -0.3 }),
      psCell(p.corr_crowd_60d, { digits: 2, hi: 0.8 }),
      psCell(r.scores.short_crowding, { digits: 0, hi: 50 }),
      psCell(s.days_to_cover, { digits: 1, hi: 5 }),
      psCell(s.borrow_fee, { digits: 2, hi: 3 }),
      el("td", { class: "num" }, s.short_interest_change == null ? "n/a" : `${hzSigned(s.short_interest_change, 0)}%`));
    tbl.tBodies[0].append(tr);
  }
  st.append(el("div", { class: "ps-scroll" }, ""));
  st.lastChild.append(tbl);
  box.append(st);
  box.append(el("p", { class: "help" }, "Sources: CFTC, Cboe, FINRA (short interest twice a month, margin debt monthly), OCC stock loans, IBKR borrow file, Yahoo prices. Every figure is a proxy for positioning; nobody publishes the real books."));
}

document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => showPage(t.dataset.page)));

// The grouped header row wraps, so pin the sub-header just below its real height.
function pinSubHeader() {
  const h = $("#table thead tr").getBoundingClientRect().height;
  document.querySelectorAll("#table thead tr.sub th").forEach((th) => (th.style.top = `${h}px`));
}
window.addEventListener("resize", pinSubHeader);

function setExpanded(on) {
  state.expanded = on;
  $("main.layout").classList.toggle("expanded", on);
  pinSubHeader();
  const b = $("#expand");
  b.setAttribute("aria-pressed", String(on));
  b.textContent = on ? "⤡ Back to stock view" : "⤢ Expand list: 1-year price targets";
  const url = new URL(location.href);
  if (on) url.searchParams.set("view", "list");
  else url.searchParams.delete("view");
  history.replaceState(null, "", url);
}
$("#expand").addEventListener("click", () => setExpanded(!state.expanded));

$("#search").addEventListener("input", (e) => {
  state.query = e.target.value;
  renderTable();
});
load();
