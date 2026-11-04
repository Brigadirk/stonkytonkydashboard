// Positioning: who is already leaning which way, and who could still sell.
import { el, fmt, pct, hlPct, psOrd, sgn, hzSigned, pageBox } from "./core.js";
import { psChart } from "./charts.js";
import { topCard, nowLine, section, psCell } from "./ui.js";
import { positioningState, rotationOn } from "./state.js";

export const SOURCES = ["positioning", "korea_margin", "fear"];
let D = null;

const PS_GROUPS = { memory: "Memory", "ai-infra": "AI infrastructure", neocloud: "Neoclouds", megacap: "Megacaps", crowding: "Old crowding watchlist", market: "Index and macro ETFs" };
const PS_SIDES = { leveraged: "Hedge funds (leveraged funds)", asset_managers: "Asset managers", dealers: "Dealers" };
const ps = { contract: "20974+", group: "all", sv: "QQQ" };

export function signal(Dx) {
  const P = Dx.positioning, st = positioningState(P);
  if (!st) return { area: "Positioning", level: "na", state: "No data", short: "No positioning data tonight.", means: "No positioning data tonight." };
  const means = {
    "fast money light": "Hedge funds have already sold; the selling that is left would come from slower long-only funds. Less fuel for a crash than it feels, but not a washout either.",
    "everyone light": "Everyone is already light: contrarian bullish.",
    "everyone long": "Everyone is long: a shakeout would hit hard.",
    "no extreme": "No positioning extreme.",
  }[st.state] + (st.margin >= 95 ? " Margin debt is at a record, so falls can be sped up by forced selling." : "");
  const rot = rotationOn(Dx.fear?.rotation);
  const level = st.state === "everyone light" ? "good" : st.state === "everyone long" ? "bad" : st.margin >= 95 || rot ? "care" : "na";
  const label = { "fast money light": "Fast money light", "everyone light": "Everyone light", "everyone long": "Everyone long", "no extreme": "No extreme" }[st.state];
  return { area: "Positioning", level, state: label,
    short: `Hedge funds ${psOrd(st.hf)} percentile in S&P futures, asset managers ${psOrd(st.am)}; margin debt ${psOrd(st.margin)} percentile${rot ? "; a rotation out of AI is on" : ""}.`,
    means, lines: [...psSummary({ ...P, korea: Dx.korea_margin }), ...(rot ? [["A rotation out of AI and momentum is on: pods cutting their crowded longs. See the last section.", ""]] : [])] };
}

// The detail lines of the top card.
function psSummary(d) {
  const ls = [];
  const say = (text, cls = "") => ls.push([text, cls]);
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
  const k = d.korea?.latest;
  if (k) say(`Korean retail leverage: ${fmt(k.kospi_margin_tn, 1)} trillion won of margin loans in Kospi stocks, ${pct(k.margin_chg_1w, 1)} in a week and ${pct(k.from_peak, 0)} from the ${k.peak_date} record, while the Kospi is ${pct(k.kospi_from_peak_date, 0)} since then. ` +
    (k.margin_chg_1w <= -0.04 ? "Loans are being cut fast: margin calls are forcing sales." : k.margin_chg_1w >= 0.02 ? "Loans are growing again: retail is buying with borrowed money." : "Loans are roughly steady."));
  say("Light positioning is fuel, not a trigger: it says how hard prices can move once selling stops, not when.", "note-line");
  return ls;
}

export function render(Dx) {
  D = Dx;
  const d = { ...Dx.positioning, korea: Dx.korea_margin, fear: Dx.fear };
  const box = pageBox();
  box.replaceChildren(topCard(signal(Dx), SOURCES));

  // Futures by trader type
  const fut = el("section", { class: "hz-sec" });
  fut.append(el("h3", {}, "Index futures by trader type"));
  fut.append(el("p", { class: "help" }, "CFTC Traders in Financial Futures, weekly (Tuesday positions, published Friday). Net long minus short as a share of open interest; the percentile compares it with the last two years."));
  const sp = d.cftc["13874+"], nq = d.cftc["20974+"], pst = positioningState(d);
  if (sp && nq) {
    const fv = el("div", { class: "v-lines" });
    fv.append(nowLine(pst.state === "everyone light" ? "good" : pst.state === "everyone long" ? "bad" : "na", pst.state[0].toUpperCase() + pst.state.slice(1),
      `S&P futures: hedge funds at the ${psOrd(sp.pct_2y.leveraged)} percentile of two years, asset managers the ${psOrd(sp.pct_2y.asset_managers)}; Nasdaq futures ${psOrd(nq.pct_2y.leveraged)} and ${psOrd(nq.pct_2y.asset_managers)} (${sp.report_date}).`));
    fut.append(fv);
  }
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
    tr.addEventListener("click", () => { ps.contract = code; render(D); });
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
  const vix = d.volatility.indices.VIX, vxn0 = d.volatility.indices.VXN;
  if (vix && vxn0) {
    const hot = vxn0.pct_1y >= 80;
    const vv = el("div", { class: "v-lines" });
    vv.append(nowLine(hot ? "care" : "na", hot ? "Fear high" : "", `VIX ${fmt(vix.value, 1)} (${psOrd(vix.pct_1y)} percentile of the year), VXN ${fmt(vxn0.value, 1)} (${psOrd(vxn0.pct_1y)}); ${hzSigned(vxn0.change_5d, 1)} in 5 days.`));
    vol.append(vv);
  }
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
    psChart(vol, s, { title: "Nasdaq-100 volatility (VXN), last two years", values: vxn.history.values, digits: 0 }, (i) => `${s.dates[i]}: VXN ${fmt(vxn.history.values[i], 1)}`);
  }
  box.append(vol);

  // Margin debt
  const md = d.margin_debt;
  if (md) {
    const sec = el("section", { class: "hz-sec" });
    sec.append(el("h3", {}, "Margin debt"));
    sec.append(el("p", { class: "help" }, "FINRA customer debit balances, monthly, in billions of dollars. Borrowed money in the market; it turns into forced selling when prices fall far enough."));
    const mv = el("div", { class: "v-lines" });
    mv.append(nowLine(md.pct_all >= 95 ? "care" : "na", md.pct_all >= 99 ? "Record" : md.pct_all >= 95 ? "High" : "", `${fmt(md.debit_billions, 0)} billion dollars in ${md.month}, ${pct(md.yoy, 0)} on a year earlier, ${psOrd(md.pct_all)} percentile of its history.`));
    sec.append(mv);
    const s = { dates: md.history.months.map((m) => `${m}-01`) };
    psChart(sec, s, { title: "Margin debt, last five years (billions of dollars)", values: md.history.values, digits: 0 }, (i) => `${md.history.months[i]}: ${fmt(md.history.values[i], 0)} billion`);
    box.append(sec);
  }

  if (d.korea) box.append(psKorea(d.korea));

  // Stocks
  const st = el("section", { class: "hz-sec" });
  st.append(el("h3", {}, "Stocks: long and short crowding"));
  st.append(el("p", { class: "help" }, "Long side: the model's long-crowding score leans on momentum ranks, so read it next to the moves measured in each stock's own volatility (σ), its distance above the 200-day average in σ, and how closely it trades with GVIP, Goldman's basket of hedge funds' favourite longs. Short side: days to cover, borrow fee and the change in short interest. Orange marks a stretched reading, blue a washed-out one."));
  const top = (k) => [...d.stocks].filter((r) => r.scores?.[k] != null).sort((a, b) => b.scores[k] - a.scores[k]).slice(0, 4).map((r) => r.symbol);
  const sv0 = el("div", { class: "v-lines" });
  sv0.append(nowLine("na", "", `Most crowded long: ${top("long_crowding").join(", ")}. Most crowded short: ${top("short_crowding").join(", ")}.`));
  st.append(sv0);
  const chips = el("div", { class: "ranges" });
  for (const [k, label] of [["all", "All"], ...Object.entries(PS_GROUPS)]) {
    const b = el("button", { class: "chip", "aria-pressed": String(ps.group === k) }, label);
    b.addEventListener("click", () => { ps.group = k; render(D); });
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
    const tr = el("tr", { class: r.symbol === ps.sv ? "ps-sel" : "" });
    if (d.short_volume?.[r.symbol]) tr.addEventListener("click", () => { ps.sv = r.symbol; render(D); document.getElementById("ps-sv")?.scrollIntoView({ block: "start" }); });
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
  const sv = d.short_volume?.[ps.sv];
  if (sv) box.append(psShortVolume(ps.sv, sv));
  if (d.fear?.rotation) box.append(fearRotation(d.fear.rotation));
  box.append(el("p", { class: "help" }, "Sources: CFTC, Cboe, FINRA (short interest twice a month, margin debt monthly), OCC stock loans, IBKR borrow file, Yahoo prices. Every figure is a proxy for positioning; nobody publishes the real books."));
}

// Korean retail margin loans: the leverage behind Samsung and Hynix, and how fast it is being cut.
function psKorea(k) {
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "Korean retail margin"));
  sec.append(el("p", { class: "help" }, "KOFIA, daily, one business day behind, by settlement date. Margin loans are money Korean investors borrowed from brokers to buy stocks; deposits are the cash they hold at brokers. Margin per Kospi point divides Kospi margin loans (billions of won) by the index: it rises when prices fall faster than loans, meaning the holders left are more leveraged. Forced selling ends when loans stop falling."));
  const L = k.latest, h = k.history, n = h.dates.length - 1;
  const kv = el("div", { class: "v-lines" });
  sec.append(kv);
  kv.append(nowLine(L.margin_chg_1w <= -0.04 ? "bad" : L.margin_chg_1w >= 0.02 ? "care" : "na", L.margin_chg_1w <= -0.04 ? "Being cut" : L.margin_chg_1w >= 0.02 ? "Growing" : "Steady", `${k.as_of}: Kospi margin loans ${fmt(L.kospi_margin_tn, 1)} trillion won (${pct(L.margin_chg_1w, 1)} in a week, ${pct(L.margin_chg_1m, 1)} in a month, ${pct(L.from_peak, 0)} from the ${fmt(L.peak_tn, 1)} trillion record on ${L.peak_date}); Kosdaq ${fmt(L.kosdaq_margin_tn, 1)} trillion; deposits ${fmt(L.deposits_tn, 0)} trillion (${pct(L.deposits_chg_1m, 0)} in a month). Margin per Kospi point ${fmt(L.ratio, 2)}, ${psOrd(L.ratio_pct)} percentile since 2023.`));
  const s = { dates: h.dates };
  const readout = (i) => `${s.dates[i]}: Kospi margin ${fmt(h.kospi_margin_tn[i], 1)}tn, Kosdaq ${fmt(h.kosdaq_margin_tn[i], 1)}tn · deposits ${fmt(h.deposits_tn[i], 0)}tn · Kospi ${h.kospi[i] == null ? "n/a" : fmt(h.kospi[i], 0)} · per point ${h.ratio[i] == null ? "n/a" : fmt(h.ratio[i], 2)}`;
  const charts = [
    psChart(sec, s, { title: "Margin loans, trillions of won: Kospi stocks (solid), Kosdaq (dashed)", values: h.kospi_margin_tn, extra: h.kosdaq_margin_tn, digits: 0 }, readout),
    psChart(sec, s, { title: "Kospi", values: h.kospi, digits: 0 }, readout),
    psChart(sec, s, { title: "Margin per Kospi point, 5-day average (leverage against the market's size)", values: h.ratio, digits: 1 }, readout),
    psChart(sec, s, { title: "Investor cash at brokers, trillions of won", values: h.deposits_tn, digits: 0 }, readout),
  ];
  for (const ch of charts) ch.onMove((i) => charts.forEach((c) => {
    c.cross(i);
    c.wrap.querySelector(".ps-readout").textContent = readout(i ?? n);
  }));
  return sec;
}

// Daily short-sale volume: the raw count people chart, next to the share of volume it is.
function psShortVolume(symbol, sv) {
  const sec = el("section", { class: "hz-sec", id: "ps-sv" });
  sec.append(el("h3", {}, `Short-sale volume: ${symbol}`));
  sec.append(el("p", { class: "help" }, "FINRA's daily count of shares sold short on its reporting venues. Most of it is market makers and ETF dealers selling short to fill buy orders and covering within hours, so the raw count rises and falls with total volume. A spike in the count is mostly a high-volume day; the share of volume sold short shows whether shorts were unusually heavy. Real short positions are in short interest and stock loans above. Click a stock in the table to switch."));
  const n = sv.dates.length - 1;
  const share = (v) => (v == null ? "n/a" : `${Math.round(v * 100)}%`);
  const lo = sv.share_mean - sv.share_sd, hi = sv.share_mean + sv.share_sd;
  const x = (i) => (sv.ema_m[i] ? sv.short_m[i] / sv.ema_m[i] : null);
  const where = (v) => (v > hi ? "above its usual range" : v < lo ? "below its usual range" : "inside its usual range");
  const svl = el("div", { class: "v-lines" });
  sec.append(svl);
  svl.append(nowLine(sv.share[n] > hi ? "care" : "na", sv.share[n] > hi ? "Heavy shorting" : "", `Last session (${sv.dates[n]}): ${fmt(sv.short_m[n], 1)} million shares sold short, ${fmt(x(n), 1)}× its 20-day average; ${share(sv.share[n])} of volume, ${where(sv.share[n])} (${share(lo)}–${share(hi)} over two years).`));
  const s = { dates: sv.dates };
  const readout = (i) => `${s.dates[i]}: ${fmt(sv.short_m[i], 1)}M short (${fmt(x(i), 1)}× average) · ${share(sv.share[i])} of volume · close ${sv.close[i] == null ? "n/a" : fmt(sv.close[i], 2)}`;
  const charts = [
    psChart(sec, s, { title: "Shares sold short a day, millions (solid), and its 20-day average (dashed)", values: sv.short_m, extra: sv.ema_m, digits: 0 }, readout),
    psChart(sec, s, { title: "Share of volume sold short, % (band: two-year average ± 1 sd)", values: sv.share.map((v) => v * 100), digits: 0, band: [lo * 100, sv.share_mean * 100, hi * 100] }, readout),
    psChart(sec, s, { title: `${symbol} price`, values: sv.close, digits: 0 }, readout),
  ];
  // Move one crosshair, move all three.
  for (const ch of charts) ch.onMove((i) => charts.forEach((c) => {
    c.cross(i);
    c.wrap.querySelector(".ps-readout").textContent = readout(i ?? n);
  }));
  return sec;
}

function fearRotation(r) {
  const c = r.current;
  const sec = section("Rotation out of AI and momentum unwinds", "The unloved sectors (homebuilders XHB, retail XRT, health care XLV, utilities XLU, financials XLF, regional banks KRE, staples XLP; equal weight) against chips (SMH) and the Nasdaq (QQQ) over 10 trading days, and the momentum factor (MTUM) against the S&P 500. A rotation day: the unloved sectors up and ahead by more than 6 points. Mostly it is multi-manager pods cutting risk: they sell their crowded longs and buy back their shorts, which are by definition the stocks nobody owns. Chips after: from the day the gap peaked.");
  const lines = el("div", { class: "v-lines" });
  const on = rotationOn(r);
  lines.append(nowLine(on ? "care" : "na", on ? "On" : "Off", `Last 10 days (to ${c.date}): unloved sectors ${sgn(c.rest, 1)}%, chips ${sgn(c.smh, 1)}%, gap ${sgn(c.gap, 1)} points; momentum ${sgn(c.mom, 1)} points against the S&P 500.`));
  const years = Object.entries(r.per_year), thisYear = String(new Date().getFullYear());
  const now = r.per_year[thisYear] ?? 0;
  const busier = years.filter(([y, n]) => y !== thisYear && n > now).map(([y]) => y);
  lines.append(el("p", {}, `Rotation days this year: ${now}${busier.length ? `; more only in ${busier.join(", ")}` : ", the most in the data since 2000"}. One rotation is usually a pause; rotations that keep coming back, as in 2000, are the warning.`));
  const done = r.episodes.filter((e) => e["3m"] != null);
  if (on && done.length) {
    const up = done.filter((e) => e["3m"] > 0).length;
    const drops = done.map((e) => e.further_drop).sort((a, b) => a - b);
    lines.append(el("p", { class: "pattern yes" }, `A rotation is on. In the last ${done.length} finished episodes chips fell a median further ${sgn(drops[Math.floor(drops.length / 2)], 0)}% within a month, and were higher three months later in ${up} of them. Test: chips should make a new high before the next rotation.`));
  }
  sec.append(lines);
  const s = { dates: r.chart.dates };
  psChart(sec, s, { title: "Unloved sectors minus chips and Nasdaq, 10 days, points (solid); momentum minus S&P 500 (dashed); line at 6", values: r.chart.gap, extra: r.chart.mom, digits: 0, band: [6, 6, 6] },
    (i) => `${s.dates[i]}: gap ${sgn(r.chart.gap[i], 1)}, momentum ${sgn(r.chart.mom[i], 1)}`);
  const t = el("table", { class: "ps-table" });
  t.append(el("thead"), el("tbody"));
  const hr = el("tr");
  ["Episode", "Unloved", "Chips", "Momentum", "Chips further drop (1m)", "Chips 1m", "3m", "12m"].forEach((h, i) => hr.append(el("th", { class: i ? "num" : "" }, h)));
  t.tHead.append(hr);
  for (const e of [...r.episodes].reverse()) {
    const tr = el("tr");
    tr.append(el("td", {}, e.start === e.end ? e.start : `${e.start} to ${e.end}`), ...[`${sgn(e.rest, 1)}%`, `${sgn(e.smh, 1)}%`, e.mom == null ? "n/a" : sgn(e.mom, 1),
      `${sgn(e.further_drop, 0)}%`, ...["1m", "3m", "12m"].map((h) => (e[h] == null ? "n/a" : `${sgn(e[h], 0)}%`))].map((v) => el("td", { class: "num" }, v)));
    t.tBodies[0].append(tr);
  }
  const sc = el("div", { class: "ps-scroll" });
  sc.append(t);
  sec.append(sc);
  return sec;
}
