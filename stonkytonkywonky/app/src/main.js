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
  $("#asof").textContent = `Each stock's price-to-earnings compared with its own past · data as of ${data.as_of} · ${state.rows.length} stocks`;
  renderTable();
  const params = new URLSearchParams(location.search);
  const wanted = params.get("t");
  const first = state.rows.find((r) => r.ticker === wanted) || visibleRows()[0];
  if (first) await select(first.ticker);
  if (params.get("view") === "list") setExpanded(true);
}

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
  const priced = rows.filter((r) => r.pe > 0);
  const firstOfCompany = new Map();
  for (const r of priced) if (!firstOfCompany.has(r.company || r.ticker)) firstOfCompany.set(r.company || r.ticker, r);
  const pool = [...firstOfCompany.values()];
  const vsAll = positions(priced, "pe", true);

  for (const r of priced) {
    const g = r.growth;
    r.peg = g != null && g >= PEG_GROWTH_MIN ? r.pe / (Math.min(g, PEG_GROWTH_CAP) * 100) : null;
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
    const val = el("td");
    val.append(zoneBadge(zoneOf(r.sig3)));
    if (r.mainKey && r.mainKey !== MAIN_WINDOW) {
      val.append(el("span", { class: "short-hist", title: `Only ${spanOf(r.mainKey)} of usable history` }, ` (${r.mainKey})`));
    }
    tr.append(
      tick,
      scoreTd,
      relTd,
      val,
      el("td", { class: "num" }, r.pe == null || r.pe <= 0 ? "n/m" : fmt(r.pe)),
      el("td", { class: "num xcol" }, r.trailing_pe == null ? "n/m" : fmt(r.trailing_pe)),
      el("td", { class: "num" }, pct(r.growth, 0)),
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

async function select(ticker) {
  state.selected = ticker;
  const url = new URL(location.href);
  url.searchParams.set("t", ticker);
  history.replaceState(null, "", url);
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
    say(`You pay ${fmt(row.pe)}× the profit analysts expect over the next 12 months. ${vs}`);
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
  }[row.b_grade] || ["Recorded history only.", "Real data has been recorded since 2026-09-24; the picture sharpens as it builds up."];
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
      ? `P/E ÷ growth = ${fmt(row.peg, 2)} (growth ${pct(row.growth, 0)}, counted up to +50%)`
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
  ["Level", "× profit", "Price now", "In a year"].forEach((h, i) => head.append(el("th", i ? { class: "num" } : {}, h)));
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
    `"In a year" assumes profit per share grows from today's forecast (${fmt(row.eps, 2)}) to analysts' forecast for next financial year (${fmt(row.fy1_eps ?? row.eps, 2)}) and the stock is valued the same way.`));
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
  stat("Expected profit per share, next 12 months", fmt(row.eps, 2), "Analysts' average forecast (consensus NTM EPS)");
  stat("Price ÷ expected profit", row.pe == null || row.pe <= 0 ? "n/m" : `${fmt(row.pe)}×`, "Forward P/E");
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
    { title: "Expected profit per share, next 12 months (analyst consensus)", values: s.eps, digits: 2 },
    { title: `Price ÷ expected profit, with its normal range over ${row.mainKey ? spanOf(row.mainKey) : "the last 3 years"}`, values: s.pe, digits: 1, band: c ? [c.levels["-1"], c.levels["0"], c.levels["1"]] : null },
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

function lineChart(box, s, { title, values, digits, band }) {
  const W = 800, H = 180, L = 52, R = 12, T = 8, B = 24;
  const wrap = el("div", { class: "chart" });
  wrap.append(el("h4", {}, title));
  const root = svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": title });
  wrap.append(root);
  box.append(wrap);

  const t0 = dayNum(s.dates[0]), t1 = dayNum(s.dates[s.dates.length - 1]) || t0 + 1;
  const nums = values.filter((v) => v != null && Number.isFinite(v));
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
  let d = "", pen = false;
  values.forEach((v, i) => {
    if (v == null || !Number.isFinite(v)) { pen = false; return; }
    d += `${pen ? "L" : "M"}${xOf(i).toFixed(1)},${yOf(v).toFixed(1)}`;
    pen = true;
  });
  root.append(svg("path", { class: "series", d }));
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
