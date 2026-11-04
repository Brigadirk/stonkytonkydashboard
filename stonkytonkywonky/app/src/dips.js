// Dips: is this dip buyable? One verdict (dipjudge.json) on top; the inputs behind it fold below:
// brakes, analogs, the Nasdaq fear state, the S&P washout score, sectors, breadth, highs and lows.
import { el, fmt, pct, dayNum, hlPct, psOrd, sgn, ok, lower1, hzSigned, pageBox } from "./core.js";
import { psChart, linkCharts } from "./charts.js";
import { topCard, nowLine, lines, section, table, scroll, chips } from "./ui.js";
import { breadthState, nasdaqFear, JUDGE_STATE } from "./state.js";

export const SOURCES = ["dipjudge", "highlow", "fear", "breadth"];
const LEVEL = { buy: "good", care: "care", wait: "bad", none: "na" };
const JUDGE_T = { ndx: "Nasdaq-100", sox: "Chips (SOX)" };
const HL_RANGES = [[365, "1 year"], [1826, "5 years"], [null, "Since 1991"]];
const BREADTH_RANGES = [[183, "6M"], [365, "1Y"], [null, "All"]];
const hl = { range: 1826, open: null, sector: null, judgeT: "ndx", breadth: 365 };
let D = null;

const jStats = (s) => (s?.days ? `${hlPct(s.up3m)} up · ${hlPct(s.bad10)} fell 10% more` : "n/a");

// ---------- the verdict ----------

function fearLine(f) {
  if (!f) return null;
  const { c, k, g, state } = f;
  const checks = `VXN ${fmt(c.vxn, 1)} ${ok(k.vxn)} · QQQ ${sgn(c.dd, 1)}% from its six-month high ${ok(k.dd)} · estimates ${sgn(c.rev, 1)}% in 3 months ${ok(k.rev)}`;
  const then = g ? `since 2010 (outside 2022) QQQ was higher 3 months later on ${hlPct(g["3m"].up)} of such days, after a median further dip of ${sgn(g.further_drop.median, 1)}%` : "";
  const say = state === "all three hold" ? `all three hold: ${then}.` : state === "close" ? `close to the state where ${then}.`
    : state === "fear without rising estimates" ? "fear without rising estimates, the weaker setup (2008, 2022)." : "no fear state, so no timing edge from it.";
  return `Nasdaq fear: ${checks}: ${say}`;
}

function washoutLine(H) {
  const m = H?.dip?.market, base = H?.baseline;
  if (!m) return null;
  const cell = m.cells.find((c) => c.level === m.level && c.regime === m.regime);
  const lv = { washout: "washout", deep: "deep dip", dip: "pullback", none: "no dip" }[m.level] ?? m.level;
  const inDip = ["washout", "deep", "dip"].includes(m.level);
  const sectors = H.dip.sectors.filter((s) => s.score >= 60).map((s) => s.etf);
  return `S&P 500 washout score ${fmt(m.score, 0)}/100 (${lv})` + (cell && inDip
    ? `: in this zone the S&P rose a median ${pct(cell.med_3m, 1)} over 3 months, against ${pct(base.med_3m, 1)} on an ordinary day.`
    : ": no timing edge from it.") + (sectors.length ? ` Sectors in a dip: ${sectors.join(", ")}.` : "");
}

export function signal(Dx) {
  const J = Dx.dipjudge, jn = J?.ndx, js = J?.sox;
  if (!jn) return { area: "Dips", level: "na", state: "No verdict", short: "The dip verdict is missing tonight.", means: "The dip verdict is missing tonight.", lines: [washoutLine(Dx.highlow)].filter(Boolean) };
  const on = jn.brakes.filter((b) => b.on && b.counted).map((b) => b.name.toLowerCase());
  const tail = jn.supports?.find((s) => s.on && s.counted);
  const brakeText = on.length ? `brake${on.length > 1 ? "s" : ""} on: ${on.join(", ")}` : "no brakes on";
  const short = jn.in_dip
    ? `Nasdaq-100 ${pct(jn.dd, 0)} from its high; ${brakeText}${tail ? "; tailwind: tech cheap with estimates holding" : ""}.`
    : `Nasdaq-100 ${pct(jn.dd, 0)} from its high: no dip to judge.`;
  const r = jn.row, ts = jn.tail_split;
  let means = "No dip on the Nasdaq-100, so nothing to judge. The washout score and breadth below say how stretched the market is.";
  if (jn.in_dip && r?.days) {
    means = `Past Nasdaq dips in this state were higher three months later ${hlPct(r.up3m)} of the time; ${hlPct(r.bad10)} first fell 10% more.`;
    if (tail && ts?.with?.days) means += ` With tech this cheap: ${hlPct(ts.with.up3m)} higher and ${hlPct(ts.with.bad10)} fell 10% more (${ts.with.episodes} episodes).`;
  }
  const ls = [];
  if (js) ls.push(`Chips (SOX) ${pct(js.dd, 0)} from its high: ${lower1(js.verdict)}${js.reliable ? "" : " A weak guide for chips: the brakes have not separated their dips."}`);
  const f = fearLine(nasdaqFear(Dx.fear?.nasdaq));
  if (f) ls.push(f);
  const w = washoutLine(Dx.highlow);
  if (w) ls.push(w);
  if (Dx.breadth) { const b = breadthState(Dx.breadth); ls.push(`${b.head}: ${b.means}.`); }
  if (Dx.highlow) { const h = hlRead(Dx.highlow); ls.push(`${h.head}. ${h.lines[1]}`); }
  if (jn.analogs_up3m != null) ls.push(`The ${jn.analogs.length} closest past dips to today were higher three months later ${hlPct(jn.analogs_up3m)} of the time (median ${pct(jn.analogs_med3m, 1)}).`);
  ls.push([jn.reliable
    ? `How much to trust it: dips with no brake on were higher three months later ${hlPct(jn.combo[0].up3m)} of the time, against ${hlPct(jn.combo[2].up3m)} with two or more. The brakes were chosen on this same history, so the gap flatters them somewhat.`
    : "How much to trust it: little; these brakes have not separated good dips from bad ones.", "note-line"]);
  return { area: "Dips", level: LEVEL[jn.level] ?? "na", state: JUDGE_STATE[jn.level] ?? jn.level, short, means, lines: ls };
}

// ---------- brakes and analogs ----------

function judgeSection(J) {
  const t = hl.judgeT, j = J[t];
  const sec = section("Brakes and tailwind", `A dip day: ${j.label} at least ${Math.round(-100 * j.cut)}% below its 52-week high. A brake is a condition under which past dips were worse buys, a tailwind one under which they were better (valuation breadth: the share of the coverage list's tech names whose forward P/E is in the bottom 16% of their own three years with estimates not lower than three months earlier, from reconstructed estimates on today's names since 2006). A brake counts toward the verdict only if dips with it on did at least 5 points worse over three months (greyed rows do not count for this index). Thresholds are round numbers set by hand, not fitted. Up: share of dip days higher three months later; fell 10% more: lowest close in the next three months at least 10% lower. Days within one episode overlap. Fear itself is not a brake: the VXN level barely separated good dips from bad ones.`);
  const on = j.brakes.filter((b) => b.on && b.counted);
  const tail = (j.supports ?? []).filter((s) => s.on && s.counted);
  const v = el("div", { class: "v-lines" });
  v.append(nowLine(LEVEL[j.level], on.length ? `${on.length} on` : "None on", `${j.label}: ${on.length ? on.map((b) => b.now).join("; ") : "no brake on"}${tail.length ? `. Tailwind on: ${tail[0].now}` : ""}.`));
  sec.append(v);
  sec.append(chips(Object.entries(JUDGE_T), t, (k) => { hl.judgeT = k; render(D); }));
  const t1 = table(["Condition", "Now", "Line", "On?", "Past dips with it on", "with it off", "Since"], { numFrom: 4, cls: "ps-table wrap" });
  const row = (b, kind) => {
    const tr = el("tr", { class: b.counted ? "" : "cp-uncertain" });
    const [now, line] = (b.now ?? "n/a").split(/ \((?:brake|tailwind): /);
    tr.append(el("td", {}, kind === "tail" ? `${b.name} (tailwind)` : b.name), el("td", {}, now), el("td", { class: "muted" }, line ? line.replace(/\)$/, "") : ""),
      el("td", { class: b.on && b.counted ? (kind === "tail" ? "ps-cold" : "ps-hot") : "" }, b.on == null ? "n/a" : b.on ? "on" : "off"),
      el("td", { class: "num" }, jStats(b.when_on)), el("td", { class: "num" }, jStats(b.when_off)), el("td", { class: "num" }, b.since ?? "n/a"));
    t1.tBodies[0].append(tr);
  };
  j.brakes.forEach((b) => row(b, "brake"));
  (j.supports ?? []).forEach((b) => row(b, "tail"));
  sec.append(scroll(t1));
  if (j.in_dip && j.tail_split?.with?.days && j.tail_split?.without?.days) {
    const ts = j.tail_split;
    sec.append(el("p", {}, `Valuation breadth in today's brake state since 2006: dips with the tailwind were higher three months later ${hlPct(ts.with.up3m)} of the time and ${hlPct(ts.with.bad10)} fell 10% more (${ts.with.episodes} episodes), against ${hlPct(ts.without.up3m)} and ${hlPct(ts.without.bad10)} without (${ts.without.episodes}).`));
  }
  sec.append(el("h4", {}, "By number of brakes on"));
  const t2 = table(["Brakes on", "Days (episodes)", "Up 3m", "Median 3m", "Up 12m", "Fell 10% more", "Up 3m before 2010", "Up 3m 2010 on"]);
  for (const c of j.combo) {
    const now = j.in_dip && c.brakes === j.row?.brakes;
    const tr = el("tr", { class: now ? "ps-sel" : "" });
    tr.append(el("td", {}, c.brakes + (now ? " (now)" : "")), ...[`${c.days} (${c.episodes})`, hlPct(c.up3m), pct(c.med3m, 1), hlPct(c.up12m), hlPct(c.bad10),
      hlPct(c["before 2010"].up3m), hlPct(c["2010 on"].up3m)].map((x) => el("td", { class: "num" }, x)));
    t2.tBodies[0].append(tr);
  }
  sec.append(scroll(t2));
  return sec;
}

function analogSection(J) {
  const j = J[hl.judgeT];
  const sec = section("Closest past dips", `Nearest past dip days to today for ${j.label} on ${j.analog_features.length} standardized features (drawdown, trend, RSI, fear, estimates, forward P/E, bond volatility, rates, credit, oil, financial conditions, jobless claims, breadth, margin debt, stock-bond correlation), one per episode; features missing in early years are skipped. Estimates start in 2005. Follows the index chosen under Brakes and tailwind.`);
  const up = j.analogs_up3m;
  const v = el("div", { class: "v-lines" });
  v.append(nowLine(up == null ? "na" : up >= 0.75 ? "good" : up >= 0.5 ? "care" : "bad", up == null ? "" : `${hlPct(up)} up`,
    `The ${j.analogs.length} closest past dips to today: higher three months later ${hlPct(up)} of the time, median ${pct(j.analogs_med3m, 1)}.`));
  sec.append(v);
  const t3 = table(["Date", "From high", "VXN", "Estimates 3m", "Brakes", "1 month", "3 months", "12 months", "Lowest in 3m"]);
  for (const a of j.analogs) {
    const tr = el("tr");
    tr.append(el("td", {}, a.date), ...[pct(a.dd, 0), fmt(a.vxn, 0), a.est3m == null ? "n/a" : `${hzSigned(a.est3m, 1)}%`, a.fails ?? "n/a",
      pct(a.r1m, 0), pct(a.r3m, 0), pct(a.r12m, 0), pct(a.low3m, 0)].map((x) => el("td", { class: "num" }, String(x))));
    t3.tBodies[0].append(tr);
  }
  sec.append(scroll(t3));
  return sec;
}

// ---------- Nasdaq fear with rising estimates (fear.json) ----------

const upMed = (h) => (h?.n ? `${hlPct(h.up)} · ${sgn(h.median, 1)}%` : "n/a");

function fearNasdaq(n) {
  const f = nasdaqFear(n), { c, k } = f;
  const sec = section("Nasdaq: fear with rising estimates", "Days since mid-2006 when Nasdaq volatility (VXN) closed above 30 and the Nasdaq-100 ETF (QQQ) stood at least 10% below its six-month high, split by whether Nasdaq-100 forward earnings estimates rose more than 3% over the previous three months. Estimates: today's members summed from the reconstructed consensus (method B) at today's share counts, so before about 2015 the list carries survivorship bias; B moves once a quarter, so it reacts late to a sudden shock (it still showed rising estimates in March 2020). Days inside one episode overlap: about 15 independent episodes in all. Up · median: share of days QQQ was higher that much later, and the median change. Further drop: the lowest QQQ close in the next three months against that day.");
  const v = el("div", { class: "v-lines" });
  const lv = f.state === "all three hold" ? "good" : f.state === "close" ? "care" : f.state.startsWith("fear without") ? "bad" : "na";
  v.append(nowLine(lv, f.state === "all three hold" ? "All three hold" : f.state === "close" ? "Close" : f.state.startsWith("fear without") ? "Estimates not rising" : "No fear state",
    `Now (${c.date}): VXN ${fmt(c.vxn, 1)} ${ok(k.vxn)} · QQQ ${sgn(c.dd, 1)}% from its six-month high ${ok(k.dd)} · estimates ${sgn(c.rev, 1)}% in three months ${ok(k.rev)} · forward P/E ${fmt(c.pe, 1)} (${c.coverage} members, ${c.pe_date}).`));
  const g = f.g;
  const hist = g ? `since 2010, outside 2022, QQQ was higher a month later on ${hlPct(g["1m"].up)} of such days, three months later on ${hlPct(g["3m"].up)} and a year later on ${hlPct(g["12m"].up)}, after a median further drop of ${sgn(g.further_drop.median, 1)}% (worst ${sgn(g.further_drop.worst, 0)}%)` : "";
  const missing = [!k.vxn && "VXN is not above 30", !k.dd && "QQQ is not yet 10% below its high"].filter(Boolean).join(" and ");
  const verdict = f.state === "all three hold" ? `${hist[0].toUpperCase()}${hist.slice(1)}. A good setup to buy in steps; expect more swings for a few weeks.`
    : f.state === "close" ? `Close: ${missing}. When all three held, ${hist}.`
      : f.state.startsWith("fear without") ? "Fear without rising estimates: the weaker column below (2008, 2022). Wait for estimates to turn up."
        : "No fear state on the Nasdaq right now: this history gives no timing edge.";
  v.append(el("p", {}, verdict));
  v.append(el("p", { class: "note-line" }, "The exceptions: November 2007 (estimates still rising before the recession, −42% a year later) and 2022 (estimates stalling at 25–30 times earnings). The risk to watch is estimates that stop rising, not the VXN."));
  sec.append(v);
  const t = table(["Period", "Estimates", "Days (episodes)", "1 month", "3 months", "12 months", "Further drop (median · worst)"], { numFrom: 2 });
  for (const x of n.groups) {
    const tr = el("tr", { class: x.estimates === "rising" ? "" : "cp-uncertain" });
    tr.append(el("td", {}, x.period), el("td", {}, x.estimates), ...[`${x.days} (${x.episodes})`, upMed(x["1m"]), upMed(x["3m"]), upMed(x["12m"]),
      x.further_drop ? `${sgn(x.further_drop.median, 1)}% · ${sgn(x.further_drop.worst, 0)}%` : "n/a"].map((y) => el("td", { class: "num" }, y)));
    t.tBodies[0].append(tr);
  }
  sec.append(scroll(t));
  const ch = n.chart, s = { dates: ch.dates };
  const readout = (i) => `${s.dates[i]}: VXN ${fmt(ch.vxn[i], 1)}, QQQ ${sgn(ch.dd[i], 1)}% from its high, estimates ${sgn(ch.rev[i], 1)}% in three months`;
  linkCharts([
    psChart(sec, s, { title: "VXN (solid) and how far QQQ is below its six-month high, % (dashed); line at 30", values: ch.vxn, extra: ch.dd.map((x) => (x == null ? null : -x)), digits: 0, band: [30, 30, 30] }, readout),
    psChart(sec, s, { title: "Nasdaq-100 forward estimates, change over three months, % (line at +3)", values: ch.rev, digits: 0, band: [3, 3, 3] }, readout),
  ], readout, s.dates.length - 1);
  sec.append(el("h4", {}, "Every episode"));
  const et = table(["Episode", "Days", "Forward P/E", "Estimates 3m", "QQQ 1m", "3m", "12m", "Further drop"]);
  for (const e of [...n.episodes].reverse()) {
    const tr = el("tr", { class: e.rev != null && e.rev > 3 ? "" : "cp-uncertain" });
    tr.append(el("td", {}, e.start === e.end ? e.start : `${e.start} to ${e.end}`), ...[e.days, fmt(e.pe, 1), `${sgn(e.rev, 1)}%`,
      ...["1m", "3m", "12m"].map((h) => (e[h] == null ? "n/a" : `${sgn(e[h], 0)}%`)), e.further_drop == null ? "n/a" : `${sgn(e.further_drop, 0)}%`].map((y) => el("td", { class: "num" }, String(y))));
    et.tBodies[0].append(tr);
  }
  sec.append(scroll(et));
  return sec;
}

// ---------- S&P 500 and sector washout scores (highlow.json) ----------

const DIP_LEVEL = { washout: "Washout (90+)", deep: "Deep (80–90)", dip: "Pullback (60–80)", none: "Normal (under 60)" };
const DIP_REGIME = {
  up: "S&P above its 200-day",
  down: "Below its 200-day, credit calm",
  knife: "Below its 200-day, credit widening (falling knife)",
};
const DIP_VERDICT = {
  beaten: ["Washed out after a bad year", "Score 85+ and down 20% or more over 12 months. Historically beat the S&P 500 over the next year, in both halves of the record: the one sector setup with an edge."],
  with_market: ["Selling with the whole market", "Score 85+ while the market score is 80+. Buy the market rather than the sector: it did about the same as the S&P 500."],
  alone: ["Sold off on its own", "Score 85+ while the market is calm. Sectors trend, so a sell-off of its own has tended to keep lagging the S&P 500."],
  dip: ["Pullback", "Score 60–85. No edge over the S&P 500 on its own."],
  none: ["No dip", "Score under 60."],
};
const dipClass = (lv) => (lv === "washout" ? "ps-cold" : lv === "deep" ? "dip-deep" : "");
const level = (v) => (v == null ? null : v >= 90 ? "washout" : v >= 80 ? "deep" : v >= 60 ? "dip" : "none");

function dipMarket(dip) {
  const m = dip.market, all = m.all;
  const sec = section("S&P 500 washout score", "How washed out the market is, 0–100: the average percentile of five oversold measures, each ranked only against its own past (no hindsight). Share of stocks above their 50-day and 200-day average, most new 52-week lows on one day in 10 sessions, VIX against its one-year median, the S&P 500 below its 20-day average. The table shows what the S&P 500 (SPY, with dividends) did afterwards, by score and by trend and credit: a falling knife is the S&P under its 200-day while the Baa corporate spread widened more than 0.25 points in three months.");
  const cell = m.cells.find((c) => c.regime === m.regime && c.level === m.level);
  const v = el("div", { class: "v-lines" });
  v.append(nowLine(m.level === "washout" || m.level === "deep" ? "good" : m.level === "dip" ? "care" : "na", `${fmt(m.score, 0)}/100`,
    `${DIP_LEVEL[m.level]} · ${DIP_REGIME[m.regime]}.` + (cell ? ` In this state the S&P 500 did ${pct(cell.med_3m, 1)} over 3 months and ${pct(cell.med_12m, 1)} over 12 (up ${Math.round(cell.up_12m * 100)}% of the time; ${cell.days} days), against ${pct(all.med_12m, 1)} on any day.` : "")));
  sec.append(v);
  sec.append(el("p", { class: "help keep" }, `S&P ${pct(m.spx_vs_200, 1)} against its 200-day; Baa spread ${fmt(m.baa, 2)} (${m.baa_chg_3m >= 0 ? "+" : ""}${fmt(m.baa_chg_3m, 2)} in 3 months).`));
  const comps = { above50: "Stocks above 50-day", above200: "Stocks above 200-day", lows10: "Most new lows in a day, 10 sessions", fear: "VIX vs its 1-year median", stretch: "S&P vs its 20-day average" };
  const show = { above50: (x) => hlPct(-x), above200: (x) => hlPct(-x), lows10: (x) => `${fmt(x * 100, 1)}%`, fear: (x) => `${fmt(x, 2)}×`, stretch: (x) => pct(-x, 1) };
  const cl = el("div", { class: "dip-comps" });
  for (const [k, label] of Object.entries(comps)) {
    const c = m.components[k];
    const row = el("div", { class: "dip-comp" });
    const barBox = el("div", { class: "dip-cbar" });
    const fill = el("div");
    fill.style.width = `${c.pct ?? 0}%`;
    barBox.append(fill);
    row.append(el("span", {}, label), el("span", { class: "num" }, show[k](c.value)), barBox, el("span", { class: "num" }, psOrd(c.pct)));
    cl.append(row);
  }
  sec.append(cl);
  const t = table(["Trend and credit", "Score", "Days", "1 month", "3 months", "12 months", "12m, 1993–2008", "12m, 2009–", "Worst in 3 months"], { numFrom: 2 });
  const c2 = (x, up) => (x == null ? "n/a" : up == null ? pct(x, 1) : `${pct(x, 1)} (${Math.round(up * 100)})`);
  const better = (x) => (x == null ? "" : x > all.med_12m * 1.25 ? "ps-cold" : x < all.med_12m * 0.75 ? "ps-hot" : "");
  for (const c of m.cells) {
    const tr = el("tr", { class: c.regime === m.regime && c.level === m.level ? "ps-sel" : "" });
    tr.append(el("td", {}, DIP_REGIME[c.regime]), el("td", {}, DIP_LEVEL[c.level]), el("td", { class: "num" }, String(c.days)),
      el("td", { class: "num" }, c2(c.med_1m, c.up_1m)), el("td", { class: "num" }, c2(c.med_3m, c.up_3m)),
      el("td", { class: `num ${better(c.med_12m)}` }, c2(c.med_12m, c.up_12m)),
      el("td", { class: `num ${better(c.early_12m)}` }, c2(c.early_12m)), el("td", { class: `num ${better(c.late_12m)}` }, c2(c.late_12m)),
      el("td", { class: "num" }, pct(c.pain3m, 1)));
    t.tBodies[0].append(tr);
  }
  const btr = el("tr", { class: "hl-base" });
  btr.append(el("td", {}, "Any day (baseline)"), el("td"), el("td", { class: "num" }, String(all.days)), el("td", { class: "num" }, c2(all.med_1m, all.up_1m)),
    el("td", { class: "num" }, c2(all.med_3m, all.up_3m)), el("td", { class: "num" }, c2(all.med_12m, all.up_12m)),
    el("td", { class: "num" }, c2(all.early_12m)), el("td", { class: "num" }, c2(all.late_12m)), el("td", { class: "num" }, pct(all.pain3m, 1)));
  t.tBodies[0].append(btr);
  sec.append(scroll(t));
  sec.append(el("p", { class: "help" }, "Days, not events: neighbouring days overlap, so a row of 300 days may be a handful of sell-offs. Read across both halves of the record; a row that only worked after 2009 leans on the Fed rescuing every dip."));
  const s = m.history, hs = { dates: s.dates.slice(-2520) };
  const sh = s.score.slice(-2520), px = s.spx.slice(-2520);
  const readout = (i) => `${hs.dates[i]}: score ${fmt(sh[i], 0)} · S&P 500 ${fmt(px[i], 0)}`;
  linkCharts([
    psChart(sec, hs, { title: "Washout score, last 10 years (shaded 80–90; above 90 is a washout)", values: sh, digits: 0, band: [80, 90, 90] }, readout),
    psChart(sec, hs, { title: "S&P 500", values: px, digits: 0 }, readout),
  ], readout, hs.dates.length - 1);
  return sec;
}

function dipSectors(dip) {
  const sec = section("Sector washouts", "The same idea within each sector: share of its S&P 1500 members above their 50-day and 200-day average, most new lows in a day over 10 sessions, its equal-weighted index below its 20-day average. Returns are the SPDR sector ETFs (SMH for semiconductors) with dividends, against SPY. A washed-out sector is not on its own a buy: what matters is why it is washed out. Click a sector for its history.");
  const rows = [...dip.sectors].sort((a, b) => b.score - a.score);
  const edge = rows.filter((x) => x.verdict === "beaten").map((x) => x.sector);
  const dipped = rows.filter((x) => x.score >= 60);
  const v = el("div", { class: "v-lines" });
  v.append(nowLine(edge.length ? "good" : "na", edge.length ? "Setup with an edge" : dipped.length ? `${dipped.length} in a dip` : "None in a dip",
    edge.length ? `Washed out after a bad year: ${edge.join(", ")}.` : dipped.length ? `${dipped.map((x) => `${x.sector} ${fmt(x.score, 0)}`).join(", ")}; none washed out after a bad year, the one setup with an edge.` : "No sector scores 60 or more."));
  sec.append(v);
  const t = table(["Sector", "Score", "Above 50-day", "Above 200-day", "1 month", "12 months", "Setup"]);
  for (const x of rows) {
    const tr = el("tr", { class: `hl-row ${hl.sector === x.sector ? "ps-sel" : ""}` });
    const name = el("td", {}, x.sector);
    name.append(el("span", { class: "name" }, `${x.etf} · ${x.members} stocks`));
    tr.append(name, el("td", { class: `num ${dipClass(level(x.score))}` }, fmt(x.score, 0)),
      el("td", { class: "num" }, hlPct(x.above50)), el("td", { class: "num" }, hlPct(x.above200)),
      el("td", { class: "num" }, pct(x.chg_1m, 1)), el("td", { class: "num" }, pct(x.mom12, 0)),
      el("td", { title: DIP_VERDICT[x.verdict][1] }, DIP_VERDICT[x.verdict][0]));
    tr.addEventListener("click", () => { hl.sector = hl.sector === x.sector ? null : x.sector; render(D); });
    t.tBodies[0].append(tr);
  }
  sec.append(scroll(t));
  sec.append(el("h4", {}, "What each setup did afterwards (all sectors pooled, 1999–)"));
  const vt = table(["Setup", "Days", "ETF, 12 months", "vs S&P, 3 months", "vs S&P, 12 months", "vs S&P 12m, 1999–2008", "vs S&P 12m, 2009–"]);
  const sign = (x) => (x == null ? "" : x > 0.02 ? "ps-cold" : x < -0.01 ? "ps-hot" : "");
  for (const x of dip.sector_verdicts) {
    const tr = el("tr");
    const name = el("td", {}, DIP_VERDICT[x.verdict][0]);
    name.append(el("span", { class: "name dip-why" }, DIP_VERDICT[x.verdict][1]));
    tr.append(name, el("td", { class: "num" }, String(x.days)), el("td", { class: "num" }, pct(x.med_12m, 1)),
      el("td", { class: `num ${sign(x.rel_3m)}` }, pct(x.rel_3m, 1)),
      el("td", { class: `num ${sign(x.rel_12m)}` }, `${pct(x.rel_12m, 1)} (${Math.round(x.beat_12m * 100)})`),
      el("td", { class: `num ${sign(x.early_12m)}` }, pct(x.early_12m, 1)), el("td", { class: `num ${sign(x.late_12m)}` }, pct(x.late_12m, 1)));
    vt.tBodies[0].append(tr);
  }
  sec.append(scroll(vt));
  sec.append(el("p", { class: "help" }, "Median return over the S&P 500 (share of days the sector beat it in brackets). Sector ETFs start in December 1998; XLRE in 2015, XLC in 2018."));
  const x = dip.sectors.find((s) => s.sector === hl.sector);
  if (x) {
    const h = x.history, s = { dates: h.dates };
    const readout = (i) => `${s.dates[i]}: score ${fmt(h.score[i], 0)} · ${x.etf} ${fmt(h.price[i], 2)}`;
    linkCharts([
      psChart(sec, s, { title: `${x.sector}: washout score, last 5 years (shaded 85–100)`, values: h.score, digits: 0, band: [85, 85, 100] }, readout),
      psChart(sec, s, { title: `${x.etf}, with dividends`, values: h.price, digits: 0 }, readout),
    ], readout, s.dates.length - 1);
  }
  return sec;
}

// ---------- breadth (breadth.json, NYSE McClellan Summation Index) ----------

function breadthSection(b) {
  const st = breadthState(b);
  const sec = section("Breadth", "NYSE McClellan Summation Index (ratio-adjusted): advances minus declines per 1000 NYSE issues, smoothed (19- and 39-day) and summed. Rising: breadth improving. The RSI and MACD are taken of the index itself.");
  const v = el("div", { class: "v-lines" });
  v.append(nowLine(st.level, st.head.replace(/^Breadth /, ""), `${st.lines[0][0]}`));
  for (const [t, cls] of st.lines.slice(1)) v.append(el("p", { class: cls ?? "" }, t));
  sec.append(v);
  sec.append(chips(BREADTH_RANGES, hl.breadth, (r) => { hl.breadth = r; render(D); }));
  let from = 0;
  if (hl.breadth) {
    const last = dayNum(b.dates[b.dates.length - 1]);
    from = Math.max(0, b.dates.findIndex((d) => dayNum(d) >= last - hl.breadth));
  }
  const s = Object.fromEntries(Object.entries(b).map(([k, x]) => [k, Array.isArray(x) ? x.slice(from) : x]));
  const readout = (i) => `${s.dates[i]}: NYSI ${fmt(s.nysi[i], 0)} · RSI ${fmt(s.rsi[i], 0)} · MACD ${fmt(s.macd[i] - s.signal[i], 1)} vs signal · ${s.advances[i]} up, ${s.declines[i]} down`;
  linkCharts([
    psChart(sec, s, { title: "Summation index (zero line dashed)", values: s.nysi, digits: 0, band: [0, 0, 0] }, readout),
    psChart(sec, s, { title: "MACD of the index (solid) and its signal line (dashed)", values: s.macd, extra: s.signal, digits: 0, band: [0, 0, 0] }, readout),
    psChart(sec, s, { title: "RSI of the index, 14 days (shaded 30–70)", values: s.rsi, digits: 0, band: [30, 50, 70] }, readout),
  ], readout, s.dates.length - 1);
  return sec;
}

// ---------- new highs and lows (highlow.json) ----------

function hlRead(d) {
  const L = d.latest, now = d.study.filter((r) => r.now);
  const total = L.nh + L.nl;
  const narrow = L.dd > -0.03 && (L.above200 < 0.5 || L.hp10 < 0.5);
  const washout = now.some((r) => ["washout30", "washout15", "hp10_10", "above200_20", "vix35", "vix_fading"].includes(r.key));
  const head = washout ? "Highs and lows: washout, historically a time to buy" : narrow ? "Highs and lows: index near its high, most stocks not" : "Highs and lows: no extreme either way";
  const ls = [
    `${d.as_of}: ${L.nh} of ${L.n} stocks made a new 52-week high and ${L.nl} a new low (${total ? hlPct(L.nh / total) : "n/a"} highs). Over the last 10 sessions highs were ${hlPct(L.hp10)} of the total, lower than on ${100 - Math.round(L.hp10_pct)}% of days since 1991.`,
    `${hlPct(L.above200)} of stocks are above their 200-day average (${psOrd(L.above200_pct)} percentile); the S&P 500 is ${L.dd > -0.005 ? "at its high" : `${pct(-L.dd, 1).replace("+", "")} below its high`}, VIX ${fmt(L.vix, 1)}.`,
  ];
  if (now.length) ls.push(`Active now: ${now.map((r) => r.label.split(":")[0].toLowerCase()).join("; ")}.`);
  return { head, level: washout ? "good" : narrow ? "bad" : "na", lines: ls, narrow, washout };
}

function hlBoard(d) {
  const r = hlRead(d);
  const sec = section("New highs and lows today", "S&P 500, 400 and 600 stocks whose high (low) today beat every high (low) of the past year. The small number counts how many of the last 21 sessions made a new high (low): a high count is a stock trending steadily, 1 is a fresh breakout. Hover a ticker for its name, industry and today's move.");
  const v = el("div", { class: "v-lines" });
  v.append(nowLine(r.level, r.washout ? "Washout" : r.narrow ? "Narrow" : "No extreme", r.lines[0]));
  for (const t of r.lines.slice(1)) v.append(el("p", {}, t));
  if (r.narrow) v.append(el("p", { class: "note-line" }, "A narrow market: the index is carried by a few large stocks while the typical stock lags. Afterwards the S&P 500 did worse than usual on average (12 months: about +6% against +12% on all days), but the spread was wide: 1999, 2007 and 2021 went badly, 1996, 2017 and 2024 well. It is a caution, not a sell signal."));
  if (r.washout) v.append(el("p", { class: "note-line" }, "Capitulation readings have been the best times to buy in this record. Returns were strongest a year out; the first month is often still rough."));
  sec.append(v);
  const { highs, lows } = d.today;
  const total = highs.length + lows.length;
  const bar = el("div", { class: "hl-bar" });
  const labels = el("div", { class: "hl-bar-labels" });
  labels.append(el("span", { class: "hl-hi-text" }, `New highs ${total ? hlPct(highs.length / total) : "n/a"} (${highs.length})`),
    el("span", { class: "hl-lo-text" }, `New lows ${total ? hlPct(lows.length / total) : "n/a"} (${lows.length})`));
  const track = el("div", { class: "hl-track" });
  const g = el("div", { class: "hl-g" });
  g.style.width = `${total ? (100 * highs.length) / total : 50}%`;
  track.append(g);
  bar.append(labels, track);
  sec.append(bar);
  const cols = el("div", { class: "hl-cols" });
  for (const [side, list] of [["hi", highs], ["lo", lows]]) {
    const col = el("div", { class: "hl-col" });
    const groups = new Map();
    for (const x of list) {
      if (!groups.has(x.sector)) groups.set(x.sector, []);
      groups.get(x.sector).push(x);
    }
    const ordered = [...groups.entries()].sort((a, b) => b[1].length - a[1].length);
    if (!ordered.length) col.append(el("p", { class: "help keep" }, side === "hi" ? "No new highs." : "No new lows."));
    for (const [sector, xs] of ordered) {
      xs.sort((a, b) => b.hits - a.hits);
      const box = el("div", { class: "hl-group" });
      const h = el("div", { class: "hl-group-head" });
      h.append(el("span", {}, sector), el("span", { class: `hl-n hl-${side}-text` }, `${xs.length}`));
      box.append(h);
      const cs = el("div", { class: "hl-chips" });
      for (const x of xs) {
        const c = el("span", { class: `hl-chip hl-${side}`, title: `${x.name} · ${x.industry} · ${pct(x.chg, 1)} today · ${x.hits} new ${side === "hi" ? "highs" : "lows"} in 21 sessions` });
        c.append(document.createTextNode(x.s), el("small", {}, String(x.hits)));
        cs.append(c);
      }
      box.append(cs);
      col.append(box);
    }
    cols.append(col);
  }
  sec.append(cols);
  return sec;
}

// What the S&P 500 did after each signal: one event per signal at most every 60 sessions.
function hlStudy(d) {
  const sec = section("Signal record since 1991", "S&P 500 return after each highs-and-lows signal since 1991, median over the events (share of events that ended higher in brackets). A signal counts again only after 60 quiet sessions, so one sell-off is one event. \"Worst in 3 months\" is the median lowest close within three months, the pain before the payoff. Sorted by the 12-month return. Click a row for its dates. Today's members only: delisted losers are missing from the past, so the breadth levels run high; the index returns are real.");
  const active = d.study.filter((r) => r.now);
  const v = el("div", { class: "v-lines" });
  v.append(nowLine(active.length ? "good" : "na", active.length ? `${active.length} active` : "None active", active.length ? `Active now: ${active.map((r) => r.label.split(":")[0].toLowerCase()).join("; ")}.` : "No highs-and-lows signal is active today."));
  sec.append(v);
  const H = ["1m", "3m", "6m", "12m"];
  const t = table(["Signal", "Events", "1 month", "3 months", "6 months", "12 months", "Worst in 3 months", "Last seen"], { cls: "ps-table hl-study" });
  const cell = (m, up) => (m == null ? "n/a" : `${pct(m, 1)} (${Math.round(up * 100)})`);
  const base = d.baseline;
  const better = (r, k) => (r["med_" + k] == null ? "" : r["med_" + k] > base["med_" + k] * 1.25 ? "ps-cold" : r["med_" + k] < base["med_" + k] * 0.75 ? "ps-hot" : "");
  for (const r of [...d.study].sort((a, b) => (b.med_12m ?? -1) - (a.med_12m ?? -1))) {
    const tr = el("tr", { class: `${r.now ? "ps-sel" : ""} hl-row` });
    const name = el("td", {}, r.label);
    if (r.now) name.append(el("span", { class: "hl-now" }, "now"));
    tr.append(name, el("td", { class: "num" }, String(r.events)));
    for (const k of H) tr.append(el("td", { class: `num ${better(r, k)}` }, cell(r["med_" + k], r["up_" + k])));
    tr.append(el("td", { class: "num" }, pct(r.pain3m, 1)), el("td", { class: "num" }, r.last ?? "never"));
    tr.addEventListener("click", () => { hl.open = hl.open === r.key ? null : r.key; render(D); });
    t.tBodies[0].append(tr);
    if (hl.open === r.key) {
      const dr = el("tr", { class: "hl-dates" });
      dr.append(el("td", { colspan: "8" }, `Events: ${r.dates.join(", ")}`));
      t.tBodies[0].append(dr);
    }
  }
  const btr = el("tr", { class: "hl-base" });
  btr.append(el("td", {}, "Any day (baseline)"), el("td", { class: "num" }, ""));
  for (const k of H) btr.append(el("td", { class: "num" }, cell(base["med_" + k], base["up_" + k])));
  btr.append(el("td", { class: "num" }, pct(base.pain3m, 1)), el("td", { class: "num" }, ""));
  t.tBodies[0].append(btr);
  sec.append(scroll(t));
  sec.append(el("p", { class: "help" }, "Blue: at least a quarter better than the baseline; amber: at least a quarter worse. The washout signals rest on 5 to 22 events each, so one or two years (2008, 2020) can swing a median."));
  return sec;
}

function hlHistory(d) {
  const sec = section("History");
  sec.append(chips(HL_RANGES, hl.range, (r) => { hl.range = r; render(D); }));
  const h = d.history;
  let from = 0;
  if (hl.range) {
    const last = dayNum(h.dates[h.dates.length - 1]);
    from = Math.max(0, h.dates.findIndex((x) => dayNum(x) >= last - hl.range));
  }
  const s = Object.fromEntries(Object.entries(h).map(([k, x]) => [k, x.slice(from)]));
  const readout = (i) => `${s.dates[i]}: S&P 500 ${fmt(s.spx[i], 0)} (${pct(s.dd[i], 1)} from high) · ${s.nh[i]} highs, ${s.nl[i]} lows · 10-day share of highs ${hlPct(s.hp10[i])} · ${hlPct(s.above200[i])} above 200-day · VIX ${fmt(s.vix[i], 1)}`;
  linkCharts([
    psChart(sec, s, { title: "S&P 500", values: s.spx, digits: 0 }, readout),
    psChart(sec, s, { title: "Share of highs over 10 sessions, % (shaded 10–50; under 10 is a washout)", values: s.hp10.map((x) => (x == null ? null : x * 100)), digits: 0, band: [10, 50, 50] }, readout),
    psChart(sec, s, { title: "Stocks above their 200-day average, % (shaded 20–50)", values: s.above200.map((x) => (x == null ? null : x * 100)), digits: 0, band: [20, 50, 50] }, readout),
    psChart(sec, s, { title: "New highs (solid) and new lows (dashed), number of stocks", values: s.nh, extra: s.nl, digits: 0 }, readout),
  ], readout, s.dates.length - 1);
  return sec;
}

export function render(Dx) {
  D = Dx;
  const box = pageBox();
  box.replaceChildren(topCard(signal(D), SOURCES));
  if (D.dipjudge?.ndx) box.append(judgeSection(D.dipjudge), analogSection(D.dipjudge));
  if (D.fear?.nasdaq) box.append(fearNasdaq(D.fear.nasdaq));
  if (D.highlow?.dip) box.append(dipMarket(D.highlow.dip), dipSectors(D.highlow.dip));
  if (D.breadth) box.append(breadthSection(D.breadth));
  if (D.highlow) box.append(hlBoard(D.highlow), hlStudy(D.highlow), hlHistory(D.highlow));
}
