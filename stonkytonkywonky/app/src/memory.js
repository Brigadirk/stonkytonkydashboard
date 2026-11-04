// Memory & GPUs: memory spot prices against the makers' promises, GPU rental, and the Korean discounts.
import { el, fmt, pct, dayNum, isoOf, pageBox } from "./core.js";
import { psChart } from "./charts.js";
import { topCard, nowLine, section, table, scroll, chips } from "./ui.js";
import { backChange, trend, discountState } from "./state.js";

export const SOURCES = ["industry", "discounts"];
let DD = null;

const ind = { mem: "DRAM chips|DDR5 16Gb (2Gx8) 4800/5600", gpu: "H100 SXM", range: 730, dc: 1095 };
const IND_RANGES = [[365, "1 year"], [730, "2 years"], [null, "All"]];
const IND_MEM_ORDER = ["DRAM chips", "DRAM modules", "GDDR", "NAND wafers", "NAND chips", "Memory cards"];

function indSlice(dates, ...cols) {
  const from = ind.range ? isoOf(dayNum(dates[dates.length - 1]) - ind.range) : "";
  const i0 = Math.max(0, dates.findIndex((x) => x >= from));
  return [{ dates: dates.slice(i0) }, ...cols.map((c) => c && c.slice(i0))];
}

const indRanges = () => chips(IND_RANGES, ind.range, (r) => { ind.range = r; render(DD); });

function indTable(cols) {
  const t = el("table", { class: "ps-table" });
  t.append(el("thead"), el("tbody"));
  const hr = el("tr");
  cols.forEach(([c, tip], i) => hr.append(el("th", { class: i ? "num" : "", title: tip || "" }, c)));
  t.tHead.append(hr);
  return t;
}
const indScroll = (t) => { const s = el("div", { class: "ps-scroll" }); s.append(t); return s; };
const indChg = (v) => (v == null ? el("td", { class: "num muted" }, "n/a") : el("td", { class: `num ret ${v >= 0 ? "pos" : "neg"}` }, pct(v, 1)));

// DRAM against NAND spot, and what the memory makers committed to on their last calls.
function indCycle(d) {
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "Memory cycle: the makers' promises and the prices that test them"));
  sec.append(el("p", { class: "help" }, `In the 2018 and 2021 tops, spot prices turned down at or before the stocks. DRAM: DRAMeXchange's DXI index (daily). NAND: our index of the TLC wafer spot prices (${(d.memory?.nand?.items || []).join(", ")}), weekly; wafers are what module and SSD makers buy, a small market that moves first. Both set to 100 at the start of the range shown. The promises are hand-entered from the calls and updated after each print.`));
  const x = d.memory?.dxi, nd = d.memory?.nand;
  const lines = el("div", { class: "v-lines" });
  const back = (ser, days) => {
    const n = ser.values.length - 1, t = isoOf(dayNum(ser.dates[n]) - days);
    const v = at(ser.dates, ser.values, t);
    return v ? ser.values[n] / v - 1 : null;
  };
  const at = (ds, vs, day) => { let b = null; for (let i = 0; i < ds.length && ds[i] <= day; i++) b = vs[i]; return b; };
  if (x?.values.length && nd?.values.length) {
    const d4 = back(x, 28), n4 = back(nd, 28), n13 = back(nd, 91);
    const nm = Math.max(...nd.values), off = nd.values.at(-1) / nm - 1;
    const both = d4 < -0.02 && n4 < -0.02, one = d4 < -0.02 || n4 < -0.02;
    lines.append(nowLine(both ? "bad" : one ? "care" : d4 > 0.02 ? "good" : "na", both ? "Both falling" : one ? `${d4 < -0.02 ? "DRAM" : "NAND"} falling` : d4 > 0.02 ? "Still rising" : "Flat", `DRAM spot ${pct(d4, 1)} in 4 weeks, ${pct(back(x, 91), 0)} in 3 months. NAND wafers ${pct(n4, 1)} in 4 weeks, ${pct(n13, 0)} in 3 months, ${pct(off, 0)} from their high.`));
    lines.append(el("p", {}, d4 < -0.02 && n4 < -0.02 ? "Both falling: the pattern that preceded the 2018 and 2021 tops. Take the top case seriously." :
      d4 < -0.02 || n4 < -0.02 ? `${d4 < -0.02 ? "DRAM" : "NAND"} spot is falling while the other holds: an early warning for the names most exposed to it${n4 < -0.02 ? " (SanDisk, Kioxia)" : ""}.` :
      Math.abs(n4) <= 0.02 && d4 > 0.02 ? "DRAM still rising, NAND flat: the shortage is intact in DRAM; NAND has stopped tightening. Watch SanDisk and Kioxia first." :
      "Spot prices still rising: no sign yet of the turn that marked earlier tops."));
    const [s] = indSlice(nd.dates);
    const dv = s.dates.map((t) => at(x.dates, x.values, t));
    const i0 = dv.findIndex((v) => v != null);
    if (i0 >= 0) {
      const nv = nd.values.slice(nd.values.length - s.dates.length);
      const b1 = dv[i0], b2 = nv[i0];
      const dn = dv.map((v, i) => (i < i0 || v == null ? null : (100 * v) / b1)), nn = nv.map((v, i) => (i < i0 ? null : (100 * v) / b2));
      sec.append(lines);
      psChart(sec, s, { title: "Spot prices, start of range = 100: DRAM (solid), NAND wafers (dashed)", values: dn, extra: nn, digits: 0 },
        (i) => `${s.dates[i]}: DRAM ${dn[i] == null ? "n/a" : fmt(dn[i], 0)} · NAND ${nn[i] == null ? "n/a" : fmt(nn[i], 0)}`);
    } else sec.append(lines);
  }
  const cp = d.checkpoints?.items;
  if (cp?.length) {
    const t = indTable([["Company"], ["What they committed to"], ["Test"], ["When", "The print that tests it"], ["Status"]]);
    for (const c of cp) {
      const tr = el("tr");
      tr.append(el("td", {}, c.company), el("td", { title: `${c.source}, ${c.said_on}` }, c.said), el("td", {}, c.test), el("td", { class: "num" }, c.check_at),
        el("td", { class: `num ${c.status === "broken" ? "ret neg" : c.status === "held" ? "ret pos" : ""}` }, c.result ? `${c.status}: ${c.result}` : c.status));
      t.tBodies[0].append(tr);
    }
    sec.append(indScroll(t));
  }
  return sec;
}

export function render(Dx) {
  DD = Dx;
  const d = Dx.industry;
  const box = pageBox();
  box.replaceChildren(topCard(signal(Dx), SOURCES), indRanges());
  if (d.memory) box.append(indCycle(d));

  // Memory spot prices
  const ms = el("section", { class: "hz-sec" });
  ms.append(el("h3", {}, "Memory spot prices"));
  ms.append(el("p", { class: "help" }, "DRAMeXchange spot prices in US dollars, session average. Spot is the small, fast market that turns before contract prices do; DRAM chips update daily, the others weekly. History before October 2026 is rebuilt from archived copies of the page, so it has gaps."));
  const dd5 = (d.memory?.items || []).find((x) => x.item.startsWith("DDR5 16Gb") && x.item.includes("4800"));
  if (dd5) {
    const m1 = dd5.chg["1m"];
    const mv = el("div", { class: "v-lines" });
    mv.append(nowLine(m1 == null ? "na" : m1 > 0.02 ? "good" : m1 < -0.02 ? "bad" : "na", m1 == null ? "" : `${pct(m1, 0)} in a month`, `DDR5 16Gb spot $${dd5.last.toFixed(2)} on ${dd5.date}${dd5.chg["1y"] != null ? `, ${pct(dd5.chg["1y"], 0)} in a year` : ""}.`));
    ms.append(mv);
  }
  const mt = indTable([["Item"], ["Price", "Session average, US$"], ["1w"], ["1m"], ["3m"], ["1y"], ["Date", "Last update"]]);
  const items = (d.memory?.items || []).slice().sort((a, b) => IND_MEM_ORDER.indexOf(a.section) - IND_MEM_ORDER.indexOf(b.section) || a.item.localeCompare(b.item));
  let lastSec = null;
  for (const m of items) {
    if (m.section !== lastSec) {
      lastSec = m.section;
      const gh = el("tr", { class: "ps-group" });
      gh.append(el("td", { colspan: "7" }, m.section));
      mt.tBodies[0].append(gh);
    }
    const key = `${m.section}|${m.item}`;
    const tr = el("tr", { class: key === ind.mem ? "ps-sel" : "" });
    tr.append(el("td", {}, m.item), el("td", { class: "num" }, m.last.toFixed(2)));
    for (const k of ["1w", "1m", "3m", "1y"]) tr.append(indChg(m.chg[k]));
    tr.append(el("td", { class: "num" }, m.date));
    tr.addEventListener("click", () => { ind.mem = key; render(DD); });
    mt.tBodies[0].append(tr);
  }
  ms.append(indScroll(mt));
  const mem = items.find((m) => `${m.section}|${m.item}` === ind.mem) || items[0];
  if (mem && mem.history.dates.length > 1) {
    const [s, v] = indSlice(mem.history.dates, mem.history.values);
    psChart(ms, s, { title: `${mem.item} (${mem.section}), US$`, values: v, digits: 2 }, (i) => `${s.dates[i]}: $${v[i].toFixed(2)}`);
  }
  box.append(ms);

  // GPU rental
  const gs = el("section", { class: "hz-sec" });
  gs.append(el("h3", {}, "GPU rental prices"));
  gs.append(el("p", { class: "help" }, "vast.ai marketplace, on-demand offers that are free right now, per GPU-hour. A spot market of mostly smaller hosts, cheaper than the big clouds; the trend matters more than the level. Fewer free offers means tighter supply. Recorded nightly from 19 October 2026."));
  const h100 = (d.gpu || []).find((x) => x.gpu === "H100 SXM");
  if (h100) {
    const m1 = h100.chg["1m"];
    const gv = el("div", { class: "v-lines" });
    gv.append(nowLine(m1 == null ? "na" : m1 < -0.05 ? "bad" : "na", m1 == null ? "" : `${pct(m1, 0)} in a month`, `H100 SXM: median $${h100.median.toFixed(2)} per GPU-hour, ${h100.offers} offers free right now.`));
    gs.append(gv);
  }
  const gt = indTable([["GPU"], ["Median $/h"], ["Cheapest quarter", "25th percentile"], ["Cheapest"], ["Free offers"], ["Free GPUs"], ["1w"], ["1m"]]);
  for (const g of d.gpu || []) {
    const tr = el("tr", { class: g.gpu === ind.gpu ? "ps-sel" : "" });
    tr.append(el("td", {}, g.gpu), el("td", { class: "num" }, g.median.toFixed(2)), el("td", { class: "num" }, g.p25.toFixed(2)), el("td", { class: "num" }, g.min.toFixed(2)),
      el("td", { class: "num" }, String(g.offers)), el("td", { class: "num" }, String(g.gpus)), indChg(g.chg["1w"]), indChg(g.chg["1m"]));
    tr.addEventListener("click", () => { ind.gpu = g.gpu; render(DD); });
    gt.tBodies[0].append(tr);
  }
  gs.append(indScroll(gt));
  const gpu = (d.gpu || []).find((g) => g.gpu === ind.gpu);
  if (gpu && gpu.history.dates.length > 1) {
    const [s, v] = indSlice(gpu.history.dates, gpu.history.values);
    psChart(gs, s, { title: `${gpu.gpu}: median $ per GPU-hour`, values: v, digits: 2 }, (i) => `${s.dates[i]}: $${v[i].toFixed(2)}`);
  }
  box.append(gs);
  if (Dx.discounts) box.append(discounts(Dx.discounts));
  const failed = d.failed?.length ? ` Not updated this time: ${d.failed.join(", ")}.` : "";
  box.append(el("p", { class: "help" }, `Click a row for its chart. Sources: DRAMeXchange (TrendForce), vast.ai, KRX prices for the discounts.${failed}`));
}

// ---------- Korean discounts: holding companies and preferred shares against what they track ----------

const DC_RANGES = [[365, "1Y"], [1095, "3Y"], [1826, "5Y"], [0, "All"]];
const dcPts = (v) => (v == null ? "n/a" : `${v >= 0 ? "+" : "−"}${Math.abs(v * 100).toFixed(1)} pts`);
const krw = (v) => (v >= 1e12 ? `₩${(v / 1e12).toFixed(1)}trn` : `₩${Math.round(v).toLocaleString("en")}`);
const DC_SAY = { wide: "Wide against its last 3 years: the cheap end of its range.", narrow: "Narrow against its last 3 years: little left of the usual discount.", normal: "Inside its usual range of the last 3 years." };
const dcLine = (it) => `${it.name}: ${(it.stats.last * 100).toFixed(1)}% discount on ${it.stats.date}, against a median of ${(it.stats.median_3y * 100).toFixed(1)}% over 3 years (wider than on ${Math.round(it.stats.pct_3y)}% of days). ${DC_SAY[discountState(it.stats)]}`;

function discounts(d) {
  const sec = section("Korean discounts", "Stocks that are mostly a claim on another stock, and how far below that stock they trade. Discount = 1 − (what the market pays for the derivative ÷ what the underlying stock is worth). A wider discount than usual makes the derivative the cheaper way to own the same thing; it can stay wide for years, so read it against its own history.", { id: "discounts" });
  const v = el("div", { class: "v-lines" });
  const wide = d.items.filter((it) => discountState(it.stats) === "wide");
  v.append(nowLine(wide.length ? "good" : "na", wide.length ? "Wide" : "Normal", d.items.map(dcLine).join(" ")));
  sec.append(v);
  sec.append(chips(DC_RANGES, ind.dc, (r) => { ind.dc = r; render(DD); }));
  for (const it of d.items) {
    const s = it.stats, lt = it.latest;
    sec.append(el("h4", {}, it.name));
    const what = it.kind === "holding"
      ? `${it.holdco_name} is worth ${krw(lt.holdco_cap)} (${lt.holdco_shares.toLocaleString("en")} shares at ${krw(lt.holdco_price)}); its ${it.stakes.map((x) => `${(x.shares / 1e6).toFixed(1)}m ${x.name} shares`).join(" and ")} are worth ${krw(lt.stake_value)}.`
      : `Preferred ${krw(lt.pref_price)} against common ${krw(lt.common_price)}.`;
    sec.append(el("p", { class: "help" }, `${what} ${it.note}`));
    const t = table([["Discount now"], ["1m", "Change in discount points; negative = narrowing"], ["3m"], ["1y"], ["Median 1y"], ["Median 3y"], ["Median, all", "Since the first date in the chart"], ["Range", "Narrowest to widest"], ["Percentile 3y", "Share of days in 3 years with a narrower discount"]], { numFrom: 0 });
    const tr = el("tr");
    const chg = (x) => el("td", { class: `num ret ${x == null ? "" : x <= 0 ? "neg" : "pos"}` }, dcPts(x));
    tr.append(el("td", { class: "num" }, `${(s.last * 100).toFixed(1)}%`), chg(s.chg_1m), chg(s.chg_3m), chg(s.chg_1y),
      el("td", { class: "num" }, `${(s.median_1y * 100).toFixed(1)}%`), el("td", { class: "num" }, `${(s.median_3y * 100).toFixed(1)}%`),
      el("td", { class: "num" }, `${(s.median_all * 100).toFixed(1)}%`), el("td", { class: "num" }, `${(s.min * 100).toFixed(0)}–${(s.max * 100).toFixed(0)}%`),
      el("td", { class: "num" }, `${Math.round(s.pct_3y)}th`));
    t.tBodies[0].append(tr);
    sec.append(scroll(t));
    const h = it.history;
    const from = ind.dc ? isoOf(dayNum(h.dates[h.dates.length - 1]) - ind.dc) : "";
    const i0 = Math.max(0, h.dates.findIndex((x) => x >= from));
    const sl = { dates: h.dates.slice(i0) };
    const vals = h.values.slice(i0).map((x) => x * 100);
    const m3 = s.median_3y * 100;
    psChart(sec, sl, { title: `${it.name}: discount, % (dashed: 3-year median ${m3.toFixed(1)}%)`, values: vals, extra: vals.map(() => m3), digits: 0 }, (i) => `${sl.dates[i]}: ${vals[i].toFixed(1)}% discount`);
  }
  return sec;
}


export function signal(Dx) {
  const mem = Dx.industry?.memory, x = mem?.dxi;
  const w4 = x ? backChange(x, 28) : null, w13 = x ? backChange(x, 91) : null;
  const n4 = mem?.nand ? backChange(mem.nand, 28) : null;
  const tr = trend(w4);
  const nandNote = n4 == null ? "" : n4 < -0.02 ? " NAND wafer prices are falling: SanDisk and Kioxia feel it first." : n4 <= 0.02 ? " NAND wafer prices have stopped rising: the NAND names (SanDisk, Kioxia) lose their tailwind first." : "";
  const ls = [];
  const dd5 = (mem?.items || []).find((y) => y.item.startsWith("DDR5 16Gb") && y.item.includes("4800"));
  if (dd5) ls.push(`DDR5 16Gb spot $${dd5.last.toFixed(2)} on ${dd5.date}${dd5.chg["1m"] != null ? `, ${pct(dd5.chg["1m"], 1)} in a month` : ""}${dd5.chg["1y"] != null ? `, ${pct(dd5.chg["1y"], 0)} in a year` : ""}.`);
  const h100 = (Dx.industry?.gpu || []).find((g) => g.gpu === "H100 SXM");
  if (h100) ls.push(`H100 SXM rental on vast.ai: median $${h100.median.toFixed(2)} per GPU-hour, ${h100.offers} offers free right now.`);
  for (const it of Dx.discounts?.items ?? []) ls.push(dcLine(it));
  return { area: "Memory & GPUs", level: tr === "rising" ? "good" : tr === "falling" ? "bad" : "care", state: tr === "rising" ? "DRAM rising" : tr === "falling" ? "DRAM falling" : "DRAM flat",
    short: `DRAM spot ${pct(w4, 1)} in 4 weeks${n4 != null ? `, NAND wafers ${pct(n4, 1)}` : ""}.${nandNote ? ` NAND ${n4 < -0.02 ? "falling" : "flat"}: SanDisk and Kioxia first.` : ""}`,
    means: (tr === "rising" ? "DRAM prices still rising: memory earnings estimates should keep going up." : tr === "falling" ? "DRAM prices falling: estimate cuts for memory names are likely next." : "DRAM prices flattening: estimates may stall.") + nandNote,
    reading: `DRAM spot index ${pct(w4, 1)} in 4 weeks, ${pct(w13, 0)} in 3 months${n4 != null ? `; NAND wafers ${pct(n4, 1)} in 4 weeks` : ""}.`, lines: ls };
}

// Shown as their own line on Signals: the cheaper way to own SK hynix and Samsung.
export function discountSignal(Dx) {
  const items = Dx.discounts.items;
  const wide = items.filter((it) => discountState(it.stats) === "wide"), narrow = items.filter((it) => discountState(it.stats) === "narrow");
  return { area: "Korean discounts", level: wide.length ? "good" : "na", state: wide.length ? "Wide" : narrow.length === items.length ? "Narrow" : "Normal",
    short: items.map((it) => `${it.name.split(" vs ")[0]} ${(it.stats.last * 100).toFixed(1)}% (${Math.round(it.stats.pct_3y)}th pct of 3 years)`).join(" · "),
    means: wide.length ? `A cheaper way in: ${wide.map((it) => it.name).join(", ")} trades wider than usual.` : "No extra bargain in the holding company or the preferred shares now.", anchor: "discounts" };
}
