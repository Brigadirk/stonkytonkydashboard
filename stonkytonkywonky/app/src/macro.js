// Macro: the brakes on buying a dip (bond volatility, funding, rates, credit, oil), then a price board.
import { $, el, fmt, pct, dayNum, isoOf, hlPct, psOrd, sgn, ok, hzSigned, pageBox } from "./core.js";
import { psChart } from "./charts.js";
import { topCard, nowLine, section, table, scroll, chips, psCell } from "./ui.js";
import { fundingState, bondHedge } from "./state.js";

export const SOURCES = ["dipjudge", "fear", "markets", "industry"];
const MACRO = ["bonds", "credit", "oil", "rates", "recession"];
const MK_RANGES = [[365, "1 year"], [730, "2 years"], [null, "5 years"]];
const mk = { sel: "DGS10", range: 365, port: "Strait of Hormuz" };
let D = null;
const year = () => String(new Date().getFullYear());

export function signal(Dx) {
  const bs = (Dx.dipjudge?.ndx?.brakes ?? []).filter((b) => MACRO.includes(b.key));
  const on = bs.filter((b) => b.on && b.counted);
  const p = Dx.fear?.plumbing, r = Dx.fear?.rates;
  const fs = p ? fundingState(p) : null;
  const hedge = bondHedge(r?.corr?.by_year?.[year()]);
  const names = on.map((b) => b.name.toLowerCase());
  const tailText = `${fs ? `funding ${fs}` : ""}${hedge ? `${fs ? "; " : ""}bonds ${hedge} stocks` : ""}`;
  const level = on.length >= 2 || fs === "stressed" ? "bad" : on.length === 1 ? "care" : "good";
  const means = on.length
    ? `Dips are less reliable buys while ${names.join(" and ")} ${on.length > 1 ? "are" : "is"} on: past Nasdaq dips with ${names[0]} on were higher three months later ${hlPct(on[0].when_on.up3m)} of the time, against ${hlPct(on[0].when_off.up3m)} with it off.`
    : "None of the macro brakes is on: in this setting dips have been good buys.";
  const ls = [];
  if (r) {
    ls.push(`MOVE ${fmt(r.move.value, 0)} (${psOrd(r.move.pct_1y)} percentile of the year); 10-year yield ${fmt(r.ten.value, 2)}% (${fmt(r.ten.ago_3m, 2)}% three months ago).`);
    ls.push(`Stock-bond correlation ${sgn(r.corr.by_year[year()], 2)} this year: ${hedge === "hedging" ? "bonds are hedging stocks" : hedge === "barely hedging" ? "bonds barely hedge stocks" : "bonds are not hedging stocks; a rates shock hits both"}. QQQ ${sgn(r.beta.now_6m, 2)}% per +10 bp on the 10-year.`);
  }
  if (p) ls.push(`Funding ${fs}: SOFR ${sgn(p.sofr.spread_bp, 0)} bp against interest on reserves, reverse repo buffer ${fmt(p.rrp.value_bn, 0)} billion.`);
  const S = Object.fromEntries((Dx.markets?.series ?? []).map((s) => [s.id, s]));
  const hy = S.BAMLH0A0HYM2;
  if (hy) ls.push(`High-yield spread ${hy.last.toFixed(2)}%, ${hzSigned(hy.chg["1m"] * 100, 0)} bp in a month (${psOrd(hy.pct_5y)} percentile of 5 years).`);
  const h = (Dx.industry?.shipping || []).find((x) => x.name === "Strait of Hormuz");
  if (h) ls.push(`Strait of Hormuz: ${h.now.n_tanker.toFixed(1)} tankers a day with their transponder on, against ${h.before.n_tanker.toFixed(1)} before ${Dx.industry.war_start}.`);
  const big = (Dx.markets?.series ?? []).filter((s) => s.chg["1w"] != null && s.unit !== "%").sort((a, b) => Math.abs(b.chg["1w"]) - Math.abs(a.chg["1w"])).slice(0, 4);
  if (big.length) ls.push(`Biggest moves this week: ${big.map((s) => `${s.name} ${pct(s.chg["1w"], 1)}`).join(", ")}.`);
  return { area: "Macro", level, state: on.length ? `${on.length} brake${on.length > 1 ? "s" : ""} on` : "No brakes on",
    short: `${on.length ? `${names.join(", ")} on` : "No macro brake on"}${tailText ? `; ${tailText}` : ""}.`,
    means, reading: bs.map((b) => `${ok(!b.on)} ${(b.now ?? b.name).replace(/ \(brake:.*\)$/, "")}${b.counted ? "" : " (does not count)"}`).join(" · "), lines: ls };
}

function fearRates(r) {
  const sec = section("Rates as a source of volatility", "MOVE: implied volatility of Treasury options, in basis points a year (median about 80; 2022 averaged 120); divide by 16 for a typical day. Stock-bond correlation: daily S&P 500 (SPY) against long Treasuries (TLT); negative means bonds hedge stocks, as from 2002 to 2021; positive means both fall together, so risk-parity and balanced funds cut both. Rate sensitivity: how much QQQ moves for each 10 bp rise in the 10-year yield, from a regression over the last six months.");
  const c = r.corr, b = r.beta, y = year();
  const hedge = bondHedge(c.by_year[y]);
  const v = el("div", { class: "v-lines" });
  v.append(nowLine(r.move.value >= 110 ? "bad" : hedge === "not hedging" ? "care" : "good", r.move.value >= 110 ? "Bond stress" : hedge === "not hedging" ? "Bonds not hedging" : "Calm",
    `MOVE ${fmt(r.move.value, 0)} (${fmt(r.move.ago_3m, 0)} three months ago, ${psOrd(r.move.pct_1y)} percentile of the year). 10-year yield ${fmt(r.ten.value, 2)}% (${fmt(r.ten.ago_3m, 2)}% three months ago).`));
  v.append(el("p", {}, `Stock-bond correlation ${sgn(c.now_3m, 2)} over three months, ${sgn(c.by_year[y], 2)} this year: ${hedge === "not hedging" ? "bonds are not hedging stocks; a rates shock hits both" : hedge === "barely hedging" ? "bonds barely hedge stocks" : "bonds are hedging stocks"}.`));
  v.append(el("p", {}, `QQQ ${sgn(b.now_6m, 2)}% for each +10 bp on the 10-year (six months), ${sgn(b.by_year[y], 2)}% this year: ${b.now_6m < -0.3 ? "tech is trading on rates; rising yields are a headwind" : b.now_6m > 0.3 ? "yields and tech rise together, on growth" : "little link between yields and tech right now"}.`));
  sec.append(v);
  psChart(sec, c.chart, { title: "Stock-bond correlation, three-month rolling (above 0: bonds do not hedge)", values: c.chart.values, digits: 1, band: [0, 0, 0] }, (i) => `${c.chart.dates[i]}: ${sgn(c.chart.values[i], 2)}`);
  psChart(sec, b.chart, { title: "QQQ % move per +10 bp on the 10-year, six-month rolling", values: b.chart.values, digits: 1, band: [0, 0, 0] }, (i) => `${b.chart.dates[i]}: ${sgn(b.chart.values[i], 2)}%`);
  return sec;
}

function fearPlumbing(p) {
  const sec = section("Funding plumbing", `Overnight funding of leverage. SOFR (the repo rate, NY Fed) against interest on reserves (IORB; ${p.iorb_note}): above it means banks are not lending reserves freely. The reverse repo facility was the buffer that let Treasury bills be sold without draining bank reserves; the standing repo facility is the Fed's emergency tap. Reserves: Fed H.4.1, weekly. TGA: the Treasury's cash at the Fed (Daily Treasury Statement); when it rises, reserves fall.`);
  const sp = p.sofr.spread_bp, top = p.range[1], fs = fundingState(p);
  const v = el("div", { class: "v-lines" });
  v.append(nowLine(fs === "stressed" ? "bad" : fs === "tight" ? "care" : "good", fs === "stressed" ? "Stressed" : fs === "tight" ? "Tight" : "Easy",
    `SOFR ${fmt(p.sofr.value, 2)}% on ${p.sofr.date} (${p.sofr.volume_bn.toLocaleString("en")} billion), ${sgn(sp, 0)} bp against IORB ${fmt(p.iorb, 2)}%; top 1% of trades at ${fmt(p.sofr.p99, 2)}% against a range top of ${fmt(top, 2)}%.`));
  v.append(el("p", {}, `Buffers: reverse repo ${fmt(p.rrp.value_bn, 0)} billion (over 2,000 billion in 2022); standing repo facility at most ${fmt(p.srf.max_30_bn, 1)} billion a day over the last 30 operations.` +
    (p.reserves ? ` Reserves ${p.reserves.value_bn.toLocaleString("en")} billion (week to ${p.reserves.week}${p.reserves.change_bn != null ? `, ${sgn(p.reserves.change_bn, 0)}` : ""}).` : "") +
    (p.tga ? ` TGA ${p.tga.value_bn.toLocaleString("en")} billion (${p.tga.date}).` : "")));
  v.append(el("p", { class: fs === "stressed" ? "pattern yes" : "" }, fs === "stressed" ? "Funding is stressed: leverage gets squeezed and forced selling can follow. The Fed usually steps in fast; its intervention has often marked lows."
    : fs === "tight" ? "Tight but working: repo trades above the Fed's floor and the buffer is thin, so there is little slack if a rates shock hits; the Fed's tap is barely used." : "Funding is easy: no pressure from the plumbing."));
  sec.append(v);
  const s = p.sofr_chart;
  psChart(sec, s, { title: "SOFR (solid) and its top 1% of trades (dashed), bp above IORB; line at 0", values: s.spread, extra: s.p99, digits: 0, band: [0, 0, 0] }, (i) => `${s.dates[i]}: SOFR ${sgn(s.spread[i], 0)} bp, top 1% ${sgn(s.p99[i], 0)} bp`);
  if (p.tga) psChart(sec, p.tga.chart, { title: "Treasury cash at the Fed (TGA), billions of dollars", values: p.tga.chart.values, digits: 0 }, (i) => `${p.tga.chart.dates[i]}: ${fmt(p.tga.chart.values[i], 0)} billion`);
  return sec;
}

// ---------- prices: rates and credit as brakes, the rest as a board ----------

const mkYield = (s) => s.unit === "%";
function mkLevel(s, v) {
  if (v == null) return "n/a";
  if (mkYield(s)) return `${v.toFixed(2)}%`;
  const a = Math.abs(v);
  return a >= 1000 ? Math.round(v).toLocaleString("en-US") : a >= 10 ? v.toFixed(2) : v.toFixed(4);
}
// Prices move in percent, yields and spreads in basis points. Up isn't good or bad for a
// yield or a spread, so those stay uncoloured.
function mkChange(s, v) {
  if (v == null) return el("td", { class: "num muted" }, "n/a");
  if (mkYield(s)) return el("td", { class: "num" }, `${hzSigned(v * 100, 0)} bp`);
  return el("td", { class: `num ret ${v >= 0 ? "pos" : "neg"}` }, pct(v, 1));
}

function board(d, title, groups, help, now) {
  const sec = section(title, help, { id: `mk-${groups[0]}` });
  if (now) { const v = el("div", { class: "v-lines" }); v.append(now); sec.append(v); }
  const rows = d.series.filter((s) => groups.includes(s.group));
  const cur = rows.find((s) => s.id === mk.sel);
  if (cur) {
    sec.append(chips(MK_RANGES, mk.range, (r) => { mk.range = r; render(D); }));
    const h = cur.history;
    const from = mk.range ? isoOf(dayNum(h.dates[h.dates.length - 1]) - mk.range) : "";
    const i0 = Math.max(0, h.dates.findIndex((x) => x >= from));
    const s = { dates: h.dates.slice(i0) };
    const vals = h.values.slice(i0);
    psChart(sec, s, { title: `${cur.name}${cur.note ? ` (${cur.note})` : ""}`, values: vals, digits: mkYield(cur) ? 2 : Math.abs(cur.last) >= 100 ? 0 : 2 }, (i) => `${s.dates[i]}: ${mkLevel(cur, vals[i])}`);
  }
  const t = table([["Market"], ["Last", "Latest close"], ["1d"], ["1w"], ["1m"], ["3m"], ["YTD", "Since the last close of last year"], ["1y"],
    ["From high", "Below the 1-year high"], ["1y pct", "Where today sits in the last year's range of closes, 0–100"], ["5y pct", "The same over 5 years"]], { cls: "ps-table mk-table" });
  for (const g of groups) {
    const rs = rows.filter((s) => s.group === g);
    if (!rs.length) continue;
    if (groups.length > 1) {
      const gh = el("tr", { class: "ps-group" });
      gh.append(el("td", { colspan: "11" }, d.groups[g]));
      t.tBodies[0].append(gh);
    }
    for (const s of rs) {
      const tr = el("tr", { class: s.id === mk.sel ? "ps-sel" : "" });
      const name = el("td");
      name.append(el("strong", {}, s.name), el("span", { class: "name" }, s.note || s.id));
      tr.append(name, el("td", { class: "num" }, mkLevel(s, s.last)));
      for (const k of ["1d", "1w", "1m", "3m", "ytd", "1y"]) tr.append(mkChange(s, s.chg[k]));
      tr.append(psCell(s.from_high, { pctFmt: true, lo: -0.2 }), psCell(s.pct_1y, { digits: 0, hi: 95, lo: 5 }), psCell(s.pct_5y, { digits: 0, hi: 95, lo: 5 }));
      tr.addEventListener("click", () => {
        mk.sel = s.id;
        render(D);
        $(`#mk-${groups[0]}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
      t.tBodies[0].append(tr);
    }
  }
  sec.append(scroll(t));
  return sec;
}

function shipping(ind) {
  const sec = section("Oil shipping through the chokepoints", `Ships counted from their AIS positions by IMF PortWatch, 7-day averages; about a week behind. "Before" is the year up to ${ind.war_start}, when Hormuz traffic collapsed. Tanker capacity is deadweight tonnage, closer to barrels than a ship count.`);
  const h = (ind.shipping || []).find((x) => x.name === "Strait of Hormuz");
  if (h) {
    const v = el("div", { class: "v-lines" });
    const ch = h.before.n_tanker ? h.now.n_tanker / h.before.n_tanker - 1 : null;
    v.append(nowLine(ch != null && ch < -0.5 ? "bad" : "na", ch != null && ch < -0.5 ? "Disrupted" : "", `Strait of Hormuz: ${h.now.n_tanker.toFixed(1)} tankers a day with their transponder on in the week to ${h.date}, against ${h.before.n_tanker.toFixed(1)} in the year before ${ind.war_start}. Dark tankers aren't in this count; satellite trackers see several times more.`));
    sec.append(v);
  }
  sec.append(el("p", { class: "help ind-warn" }, "Read the level with care: ships that switch their transponder off are not counted, and in a war zone many tankers do. For Hormuz, satellite-based trackers (Windward, Kpler) counted roughly 15–40 transits a day in late September 2026, about a third of them dark, against ~2 here. The timing and direction of changes are reliable; the size of the drop is overstated."));
  const t = table([["Chokepoint"], ["Tankers a day", "Last 7 days"], ["Before", "Year before the war"], ["Change"], ["All ships a day"], ["Before"], ["Tanker capacity, kt a day"], ["Before"]]);
  for (const c of ind.shipping || []) {
    const tr = el("tr", { class: c.name === mk.port ? "ps-sel" : "" });
    const chg = c.before.n_tanker ? c.now.n_tanker / c.before.n_tanker - 1 : null;
    tr.append(el("td", {}, c.name), el("td", { class: "num" }, c.now.n_tanker.toFixed(1)), el("td", { class: "num" }, c.before.n_tanker.toFixed(1)),
      el("td", { class: `num ret ${chg == null ? "" : chg >= 0 ? "pos" : "neg"}` }, chg == null ? "n/a" : pct(chg, 1)),
      el("td", { class: "num" }, c.now.n_total.toFixed(1)), el("td", { class: "num" }, c.before.n_total.toFixed(1)),
      el("td", { class: "num" }, (c.now.capacity_tanker / 1000).toFixed(0)), el("td", { class: "num" }, (c.before.capacity_tanker / 1000).toFixed(0)));
    tr.addEventListener("click", () => { mk.port = c.name; render(D); });
    t.tBodies[0].append(tr);
  }
  sec.append(scroll(t));
  const port = (ind.shipping || []).find((x) => x.name === mk.port);
  if (port) {
    const h2 = port.history;
    const from = isoOf(dayNum(h2.dates[h2.dates.length - 1]) - 730);
    const i0 = Math.max(0, h2.dates.findIndex((x) => x >= from));
    const s = { dates: h2.dates.slice(i0) }, tankers = h2.tankers.slice(i0), ships = h2.ships.slice(i0);
    psChart(sec, s, { title: `${port.name}: tankers a day (solid) and all ships (dashed), 7-day average, 2 years`, values: tankers, extra: ships, digits: 0 }, (i) => `${s.dates[i]}: ${tankers[i]} tankers, ${ships[i]} ships`);
  }
  return sec;
}

export function render(Dx) {
  D = Dx;
  const box = pageBox();
  box.replaceChildren(topCard(signal(D), SOURCES));
  if (D.fear?.rates) box.append(fearRates(D.fear.rates));
  if (D.fear?.plumbing) box.append(fearPlumbing(D.fear.plumbing));
  const d = D.markets;
  if (d) {
    const S = Object.fromEntries(d.series.map((s) => [s.id, s]));
    const hy = S.BAMLH0A0HYM2, real = S.DFII10;
    const wide = hy && hy.chg["3m"] != null && hy.chg["3m"] >= 0.0075;
    box.append(board(d, "Rates and credit spreads", ["rates", "credit"], "FRED: Treasury yields, Fed funds and ICE BofA credit spreads (German and Japanese 10-year are monthly). Changes in basis points. Click a row for its chart.",
      hy ? nowLine(wide ? "bad" : "na", wide ? "Widening" : "", `High-yield spread ${hy.last.toFixed(2)}%, ${hzSigned(hy.chg["1m"] * 100, 0)} bp in a month, ${psOrd(hy.pct_5y)} percentile of 5 years${real ? `; 10-year real yield ${real.last.toFixed(2)}% (${psOrd(real.pct_5y)} percentile)` : ""}.`) : null));
  }
  if (D.industry?.shipping) box.append(shipping(D.industry));
  if (d) {
    const highs = d.series.filter((s) => s.pct_1y >= 97 && !["rates", "credit"].includes(s.group)).map((s) => s.name);
    const failed = d.failed?.length ? ` Not updated this time: ${d.failed.join(", ")}.` : "";
    box.append(board(d, "Price board", ["us", "world", "fx", "commodities", "crypto"], `Yahoo closes: indexes, currencies, futures, crypto. Click a row for its chart.${failed}`,
      nowLine("na", "", highs.length ? `At or near a 1-year high: ${highs.join(", ")}.` : "Nothing at a 1-year high.")));
  }
}

