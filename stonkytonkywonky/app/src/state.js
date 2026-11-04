// Pure readings of the nightly data: no DOM, so the app and scripts/snapshot.mjs share them.
// The snapshot is what "What changed" on the Signals tab compares day to day.

const fx = (v, d) => (v == null || !Number.isFinite(v) ? "n/a" : v.toFixed(d));

// Consecutive sessions the last value kept moving the same way.
function streak(xs) {
  const n = xs.length;
  if (n < 2) return { dir: 0, days: 0 };
  const dir = Math.sign(xs[n - 1] - xs[n - 2]);
  let days = 0;
  for (let i = n - 1; i > 0 && Math.sign(xs[i] - xs[i - 1]) === dir && dir !== 0; i--) days++;
  return { dir, days };
}

/** NYSE McClellan Summation Index: headline, level and the lines that explain it. */
export function breadthState(b) {
  const n = b.dates.length - 1;
  const v = b.nysi[n], rsi = b.rsi[n], rsiPrev = b.rsi[n - 1];
  const bull = b.macd[n] > b.signal[n];
  const rising = b.osc[n] > 0;
  const run = streak(b.nysi);
  const head = rising && bull
    ? v < 0 ? "Breadth turning up from a washout" : "Breadth broad and improving"
    : !rising && !bull
      ? v > 0 ? "Breadth rolling over from strength" : "Breadth weak and still falling"
      : "Breadth turning, not confirmed";
  const level = rising && bull ? "good" : !rising && !bull ? "bad" : "na";
  const lines = [];
  lines.push([`The summation index is at ${fx(v, 0)} and has ${run.dir > 0 ? "risen" : "fallen"} ${run.days} session${run.days === 1 ? "" : "s"} in a row. ` +
    (rising ? "More NYSE stocks are rising than its recent average, so breadth is improving." : "Fewer NYSE stocks are rising than its recent average, so breadth is weakening.") +
    ` ${v < 0 ? "Below zero: over the last couple of months most stocks have lagged." : "Above zero: most stocks have been taking part."}`]);
  if (rsi != null) lines.push([`RSI of the index ${fx(rsi, 0)} (${rsi < 30 ? "oversold" : rsi > 70 ? "overbought" : "neutral"}), ${rsi > rsiPrev ? "turning higher" : "still falling"}.`]);
  const lc = b.last_cross;
  lines.push([`MACD is ${bull ? "above" : "below"} its signal line` + (lc ? `; the last cross was ${lc.dir === "bull" ? "bullish" : "bearish"} on ${lc.date}.` : ".") +
    (Math.abs(b.macd[n] - b.signal[n]) < 2 ? " The two lines are nearly touching, so a cross is close." : "")]);
  if (rising && bull && v < 0) lines.push(["This is the classic early buy signal for the broad market. It fails often on the first hook; trust it after a few weeks of follow-through.", "note-line"]);
  if (b.official) lines.push([`StockCharts' official $NYSI: ${fx(b.official.nysi, 1)} on ${b.official.date}${b.official.rsi != null ? `, RSI ${fx(b.official.rsi, 1)}` : ""}. Our line is counted from ${b.advances[n] + b.declines[n] + (b.unchanged?.[n] ?? 0)} NYSE issues and set to the official level, so day-to-day moves can differ slightly.`, "note-line"]);
  const means = {
    "Breadth turning up from a washout": "most stocks are starting to rise again after a sell-off, which has backed buying the dip",
    "Breadth broad and improving": "the rally has support from most stocks, not just a few",
    "Breadth rolling over from strength": "fewer stocks are joining in, so rallies get fragile",
    "Breadth weak and still falling": "most stocks are still falling; wait for breadth to turn before buying broadly",
  }[head] ?? "turning but not confirmed";
  return { head, level, value: v, lines, means };
}

/** The Nasdaq fear state: VXN above 30, QQQ 10% below its six-month high, estimates up more than 3%. */
export function nasdaqFear(n) {
  const k = n?.current?.checks;
  if (!k) return null;
  const state = k.vxn && k.dd && k.rev ? "all three hold" : k.rev && (k.vxn || k.dd) ? "close" : !k.rev && (k.vxn || k.dd) ? "fear without rising estimates" : "no fear state";
  return { state, k, c: n.current, g: n.groups.find((x) => x.period.startsWith("2010") && x.estimates === "rising") };
}

export function fundingState(p) {
  const sp = p.sofr.spread_bp, top = p.range[1];
  return sp >= 10 || p.sofr.p99 > top + 0.15 || p.srf.max_30_bn > 10 ? "stressed" : sp > 0 ? "tight" : "easy";
}

export const bondHedge = (corr) => (corr == null ? null : corr > 0.15 ? "not hedging" : corr > 0 ? "barely hedging" : "hedging");

export const rotationOn = (r) => !!r && r.current.gap > 6 && r.current.rest > 0;

/** Change over `days` calendar days from the last value of a dated series. */
export function backChange(ser, days) {
  const n = ser.values.length - 1;
  if (n < 1) return null;
  const t = Date.parse(ser.dates[n]) - days * 864e5;
  let v = null;
  for (let i = 0; i <= n && Date.parse(ser.dates[i]) <= t; i++) v = ser.values[i];
  return v ? ser.values[n] / v - 1 : null;
}
export const trend = (v) => (v == null ? null : v > 0.02 ? "rising" : v < -0.02 ? "falling" : "flat");

export function discountState(s) {
  return s.pct_3y >= 80 ? "wide" : s.pct_3y <= 20 ? "narrow" : "normal";
}

export function positioningState(P) {
  const sp = P?.cftc?.["13874+"];
  if (!sp) return null;
  const hf = sp.pct_2y.leveraged, am = sp.pct_2y.asset_managers;
  const state = hf < 30 && am < 30 ? "everyone light" : hf > 70 && am > 70 ? "everyone long" : hf < 30 && am > 50 ? "fast money light" : "no extreme";
  return { state, hf, am, margin: P.margin_debt?.pct_all ?? null };
}

export const JUDGE_STATE = { buy: "Buyable", care: "Buyable with care", wait: "Not buyable yet", none: "No dip" };
export const cheapHolding = (ranking) => (ranking?.rows ?? []).filter((r) => r.signal === "CHEAP, estimates holding").map((r) => r.ticker).sort();

/** One flat record per data day: what "What changed" diffs. Values are short words, not numbers. */
export function snapshot(D) {
  const items = {};
  const put = (key, label, value) => { if (value != null) items[key] = { label, value: String(value) }; };
  const J = D.dipjudge;
  for (const t of ["ndx", "sox"]) if (J?.[t]) put(`dip.${t}`, `${J[t].label} dip verdict`, JUDGE_STATE[J[t].level] ?? J[t].level);
  for (const b of J?.ndx?.brakes ?? []) if (b.counted && b.on != null) put(`brake.${b.key}`, `Brake: ${b.name.toLowerCase()}`, b.on ? "on" : "off");
  for (const s of J?.ndx?.supports ?? []) if (s.on != null) put(`tail.${s.key}`, `Tailwind: ${s.name.toLowerCase()}`, s.on ? "on" : "off");
  const m = D.highlow?.dip?.market;
  if (m) put("spx.washout", "S&P 500 washout score", { washout: "washout", deep: "deep dip", dip: "pullback", none: "no dip" }[m.level] ?? m.level);
  if (D.breadth) put("breadth", "Breadth", breadthState(D.breadth).head.replace(/^Breadth /, ""));
  const nf = nasdaqFear(D.fear?.nasdaq);
  if (nf) put("fear.nasdaq", "Nasdaq fear with rising estimates", nf.state);
  if (D.fear?.rotation) put("rotation", "Rotation out of AI", rotationOn(D.fear.rotation) ? "on" : "off");
  if (D.fear?.plumbing) put("funding", "Funding", fundingState(D.fear.plumbing));
  const y = D.fear?.rates?.corr?.by_year?.[String(new Date(D.fear?.generated ?? Date.now()).getFullYear())];
  if (y != null) put("bonds", "Bonds against stocks", bondHedge(y));
  const ps = positioningState(D.positioning);
  if (ps) put("positioning", "Futures positioning", ps.state);
  const mem = D.industry?.memory;
  if (mem?.dxi) put("dram", "DRAM spot, 4 weeks", trend(backChange(mem.dxi, 28)));
  if (mem?.nand) put("nand", "NAND wafers, 4 weeks", trend(backChange(mem.nand, 28)));
  for (const it of D.discounts?.items ?? []) put(`disc.${it.kind}`, `${it.name}: discount`, discountState(it.stats));
  return { date: D.ranking?.as_of ?? D.dipjudge?.as_of ?? null, items, cheap: cheapHolding(D.ranking) };
}

/** What moved between two snapshots. */
export function diff(prev, now) {
  const flips = [];
  for (const [k, v] of Object.entries(now.items)) {
    const p = prev.items[k];
    if (p && p.value !== v.value) flips.push({ key: k, label: v.label, from: p.value, to: v.value });
  }
  const before = new Set(prev.cheap ?? []), after = new Set(now.cheap ?? []);
  return { flips, added: [...after].filter((t) => !before.has(t)), dropped: [...before].filter((t) => !after.has(t)) };
}

