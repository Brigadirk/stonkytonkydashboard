// AI build-out: does the spending pay, who buys, who pays, and how fast demand grows.
import { el, svg, fmt, pct, dayNum, hlPct, DAY, pageBox } from "./core.js";
import { psChart } from "./charts.js";
import { topCard, nowLine, table, scroll } from "./ui.js";

export const SOURCES = ["compute"];
let DD = null;

const CP_MAKERS = { anthropic: "Anthropic", openai: "OpenAI", google: "Google", deepseek: "DeepSeek", "x-ai": "xAI", qwen: "Qwen (Alibaba)", "z-ai": "Z.ai", minimax: "MiniMax", xiaomi: "Xiaomi", tencent: "Tencent", stealth: "Stealth (unnamed)", "meta-llama": "Meta", mistralai: "Mistral", Others: "Others" };
const CP_CO = { MSFT: "Microsoft", GOOGL: "Alphabet", AMZN: "Amazon", META: "Meta", ORCL: "Oracle", CRWV: "CoreWeave" };
const cp = { range: null };
const tn = (v, d = 1) => (v == null ? "n/a" : `${fmt(v / 1e12, d)}T`);
const bn = (v, d = 0) => (v == null ? "n/a" : `${v < 0 ? "−" : ""}$${fmt(Math.abs(v), d)}bn`);
const growth = (a, b) => (a == null || b == null || !b ? null : a / b - 1);

// The detail lines of the top card.
function cpSummary(d) {
  const o = d.openrouter, s = d.sec;
  const n = o.weeks.length - (o.last_week_partial ? 2 : 1);
  const at = (k) => (n - k >= 0 ? o.total[n - k] : null);
  const share = (m, i) => (o.by_maker[m] ? o.by_maker[m][i] / o.total[i] : null);
  const qi = s.capex_total_bn.findLastIndex((v) => v != null);
  const ls = [];
  const say = (t, c = "") => ls.push([t, c]);
  say(`Tokens on OpenRouter, week of ${o.weeks[n]}: ${tn(o.total[n])}, ${pct(growth(at(0), at(4)), 0)} in 4 weeks, ${pct(growth(at(0), at(13)), 0)} in 13 weeks, ${n >= 52 ? `${pct(growth(at(0), at(52)), 0)} in a year` : `${pct(growth(at(0), o.total[0]), 0)} since ${o.weeks[0]}`}. Anthropic models ${hlPct(share("anthropic", n))} of them (${hlPct(share("anthropic", Math.max(0, n - 13)))} 13 weeks earlier).`);
  if (qi >= 0) say(`Capex of Microsoft, Alphabet, Amazon, Meta and Oracle: ${bn(s.capex_total_bn[qi])} in ${s.quarters[qi]}, ${pct(growth(s.capex_total_bn[qi], s.capex_total_bn[qi - 4]), 0)} on a year earlier: about ${bn(s.capex_total_bn[qi] * 4)} a year.`);
  const rpo = Object.entries(s.rpo).map(([t, r]) => [t, r.bn[r.bn.length - 1], r.dates[r.dates.length - 1]]);
  if (rpo.length) say(`Contracted, not yet billed revenue (remaining performance obligations): ${rpo.map(([t, v, dt]) => `${CP_CO[t]} ${bn(v)} (${dt})`).join(", ")}. Total ${bn(rpo.reduce((a, r) => a + r[1], 0))}.`);
  const latest = (series) => (d.disclosed.points ?? []).filter((p) => p.series === series).sort((a, b) => a.date.localeCompare(b.date)).pop();
  const ar = latest("anthropic_revenue_runrate"), or = latest("openai_revenue_runrate");
  if (ar && or) say(`Paid demand at the two biggest labs: Anthropic's revenue run-rate ${bn(ar.value)} (${ar.date}), OpenAI's ${bn(or.value)} (${or.date}). Anthropic's share of the two: ${hlPct(ar.value / (ar.value + or.value))}. Run-rates are the latest month × 12.`);
  const com = (d.disclosed.commitments ?? []).filter((c) => !/negotiation/i.test(c.counterparty));
  if (com.length && rpo.length) say(`Anthropic alone has committed ${d.disclosed.commitments_total_bn ? `more than ${bn(d.disclosed.commitments_total_bn)}` : `about ${bn(com.reduce((a, c) => a + c.amount_bn, 0))}`} to compute over the next decade, against ${bn(rpo.reduce((a, r) => a + r[1], 0))} of contracted backlog at the clouds above: a large slice of the industry's committed demand rests on a few labs.`);
  say("OpenRouter is a router for developers. It leans to cheap open models and misses most direct use of Claude, ChatGPT and Gemini, so read it for growth and for the price-sensitive end, not for market share.", "note-line");
  return ls;
}

function cpTokens(d) {
  const o = d.openrouter;
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "Tokens on OpenRouter, by model maker"));
  sec.append(el("p", { class: "help" }, "Weekly tokens processed through OpenRouter's API, from its public rankings. The latest week is still running and is left out. The table shows the six biggest makers."));
  const n = o.weeks.length - (o.last_week_partial ? 1 : 0);
  const g13 = o.total[n - 1] && o.total[n - 14] ? o.total[n - 1] / o.total[n - 14] - 1 : null;
  const tv = el("div", { class: "v-lines" });
  tv.append(nowLine(g13 == null ? "na" : g13 > 0.1 ? "good" : g13 < 0 ? "bad" : "care", g13 == null ? "" : `${pct(g13, 0)} in 13 weeks`, `Week of ${o.weeks[n - 1]}: ${tn(o.total[n - 1])} tokens.`));
  sec.append(tv);
  const s = { dates: o.weeks.slice(0, n) };
  const tot = o.total.slice(0, n);
  const sh = (m) => o.by_maker[m].slice(0, n).map((v, i) => (tot[i] ? (100 * v) / tot[i] : null));
  const readout = (i) => `${s.dates[i]}: ${tn(tot[i])} · Anthropic ${fmt(sh("anthropic")[i], 1)}% · OpenAI ${fmt(sh("openai")[i], 1)}% · Google ${fmt(sh("google")[i], 1)}%`;
  const charts = [
    psChart(sec, s, { title: "Tokens a week, trillions", values: tot.map((v) => v / 1e12), digits: 0 }, readout),
    psChart(sec, s, { title: "Share of tokens, %: Anthropic (solid), OpenAI (dashed)", values: sh("anthropic"), extra: sh("openai"), digits: 0 }, readout),
  ];
  for (const ch of charts) ch.onMove((i) => charts.forEach((c) => {
    c.cross(i);
    c.wrap.querySelector(".ps-readout").textContent = readout(i ?? s.dates.length - 1);
  }));
  const last = n - 1, then = Math.max(0, n - 14);
  const t = el("table", { class: "ps-table" });
  t.append(el("thead"), el("tbody"));
  const hr = el("tr");
  ["Model maker", `Week of ${o.weeks[last]}`, "Share", "Share 13 weeks earlier", "Tokens vs 13 weeks earlier"].forEach((h, i) => hr.append(el("th", { class: i ? "num" : "" }, h)));
  t.tHead.append(hr);
  const makers = Object.keys(o.by_maker).sort((a, b) => o.by_maker[b][last] - o.by_maker[a][last]).slice(0, 6);
  for (const m of makers) {
    const v = o.by_maker[m];
    if (!v[last] && !v[then]) continue;
    const tr = el("tr", { class: m === "anthropic" ? "ps-sel" : "" });
    tr.append(el("td", {}, CP_MAKERS[m] ?? m), el("td", { class: "num" }, tn(v[last])), el("td", { class: "num" }, hlPct(v[last] / o.total[last])),
      el("td", { class: "num" }, hlPct(v[then] / o.total[then])), el("td", { class: "num" }, v[then] ? pct(v[last] / v[then] - 1, 0) : "new"));
    t.tBodies[0].append(tr);
  }
  const sc = el("div", { class: "ps-scroll" });
  sc.append(t);
  sec.append(sc);
  return sec;
}

function cpCapex(d) {
  const s = d.sec;
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "Capex and backlog"));
  sec.append(el("p", { class: "help" }, "From the companies' SEC filings (XBRL), each quarter. Capex is cash spent on property and equipment; Microsoft's and Oracle's headline figures also count finance leases, so theirs here run lower. Quarters are calendar quarters (Microsoft's fiscal year ends in June, Oracle's in May). Remaining performance obligations are signed contracts not yet billed: for these companies mostly multi-year cloud and AI compute deals, so they show demand already committed for the next years. Amazon no longer reports its backlog in tagged form; Meta sells no cloud."));
  const k = s.quarters.length;
  const from = Math.max(0, k - 9);
  const qi = s.capex_total_bn.findLastIndex((v) => v != null);
  const cy = qi >= 4 ? growth(s.capex_total_bn[qi], s.capex_total_bn[qi - 4]) : null;
  const cv = el("div", { class: "v-lines" });
  cv.append(nowLine(cy == null ? "na" : cy > 0.3 ? "good" : cy < 0 ? "bad" : "care", cy == null ? "" : `${pct(cy, 0)} a year`, `Big-five capex ${bn(s.capex_total_bn[qi])} in ${s.quarters[qi]}, about ${bn(s.capex_total_bn[qi] * 4)} a year.`));
  sec.append(cv);
  const t = el("table", { class: "ps-table" });
  t.append(el("thead"), el("tbody"));
  const hr = el("tr");
  ["Capex, $bn", ...s.quarters.slice(from), "vs year before"].forEach((h, i) => hr.append(el("th", { class: i ? "num" : "" }, h)));
  t.tHead.append(hr);
  const addRow = (label, vals, cls = "") => {
    const tr = el("tr", { class: cls });
    tr.append(el("td", {}, label));
    for (let i = from; i < k; i++) tr.append(el("td", { class: "num" }, vals[i] == null ? "" : fmt(vals[i], 1)));
    const li = vals.findLastIndex((v) => v != null);
    tr.append(el("td", { class: "num" }, li >= 4 ? pct(growth(vals[li], vals[li - 4]), 0) : ""));
    t.tBodies[0].append(tr);
  };
  for (const [tk, vals] of Object.entries(s.capex_bn)) addRow(CP_CO[tk] ?? tk, vals);
  addRow("Big five (without CoreWeave)", s.capex_total_bn, "hl-base");
  const sc = el("div", { class: "ps-scroll" });
  sc.append(t);
  sec.append(sc);
  const qn = s.capex_total_bn.findLastIndex((v) => v != null) + 1;
  const qs = { dates: s.quarters.slice(0, qn).map((q) => `${q.slice(0, 4)}-${String(Number(q.slice(5)) * 3).padStart(2, "0")}-28`) };
  psChart(sec, qs, { title: "Big-five capex a quarter, $bn", values: s.capex_total_bn.slice(0, qn), digits: 0 }, (i) => `${s.quarters[i]}: ${bn(s.capex_total_bn[i])}${i >= 4 ? ` (${pct(growth(s.capex_total_bn[i], s.capex_total_bn[i - 4]), 0)} on a year earlier)` : ""}`);
  sec.append(el("h4", {}, "Contracted, not yet billed (remaining performance obligations)"));
  const rt = table(["Company", "Latest", "Date", "A year earlier", "Change"]);
  for (const [tk, r] of Object.entries(s.rpo)) {
    const i = r.bn.length - 1, j = i - 4;
    const tr = el("tr");
    tr.append(el("td", {}, CP_CO[tk]), el("td", { class: "num" }, bn(r.bn[i])), el("td", { class: "num" }, r.dates[i]),
      el("td", { class: "num" }, j >= 0 ? bn(r.bn[j]) : "n/a"), el("td", { class: "num" }, j >= 0 ? pct(growth(r.bn[i], r.bn[j]), 0) : "n/a"));
    rt.tBodies[0].append(tr);
  }
  sec.append(scroll(rt));
  return sec;
}

const cpQDate = (q) => `${q.slice(0, 4)}-${String(Number(q.slice(5)) * 3).padStart(2, "0")}-28`;
const cpLast = (vals) => vals.findLastIndex((v) => v != null);

// Does the spending earn money? Company-level cash and returns from SEC filings, cloud segment
// profit from the earnings releases. Every figure is trailing twelve months unless it says quarter.
function cpReturns(d) {
  const r = d.returns;
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "Does it pay? Returns on the build-out"));
  sec.append(el("p", { class: "help" }, "Company figures from SEC filings, trailing twelve months. Capex share: capex as a share of operating cash flow; above 100% the rest is borrowed or raised. Operating return: operating profit over average property and equipment (before tax). Incremental return: the extra operating profit of the last year divided by the property and equipment added the year before, since new data centres take about a year to earn. Amazon's capex is gross (its own free cash flow nets off incentives) and includes logistics; Microsoft's and Oracle's exclude finance leases. Cloud segments come from the earnings releases: Microsoft replaced its Intelligent Cloud segment with the broader Agents and Infra in fiscal 2027, so that line starts over."));
  const qs = r.quarters;
  const lines = el("div", { class: "v-lines" });
  const over = Object.entries(r.companies).filter(([, c]) => c.capex_ocf[cpLast(c.capex_ocf)] > 1).map(([tk]) => CP_CO[tk]);
  const ga = r.cloud.googl_cloud, aw = r.cloud.amzn_aws;
  const mg = (x) => x && x.margin[cpLast(x.margin)];
  lines.append(nowLine(over.length ? "care" : "good", over.length ? `${over.length} borrowing to build` : "Paid from cash",
    `${over.length ? `${over.join(" and ")} now spend more on capex than they make in operating cash flow; the rest pay from cash.` : "Every company pays its capex from operating cash flow."}${ga && aw ? ` Cloud margins: Google Cloud ${hlPct(mg(ga))}, AWS ${hlPct(mg(aw))}.` : ""}`));
  for (const s of Object.values(r.cloud)) {
    const i = cpLast(s.margin);
    if (i < 0) continue;
    const j = i - 4;
    const yoy = j >= 0 && s.rev_bn[j] ? `, ${pct(growth(s.rev_bn[i], s.rev_bn[j]), 0)} on a year earlier` : "";
    lines.append(el("p", {}, `${s.label} (${qs[i]}): revenue ${bn(s.rev_bn[i], 1)} in the quarter${yoy}, operating margin ${hlPct(s.margin[i])}${j >= 0 && s.margin[j] != null ? ` (${hlPct(s.margin[j])} a year earlier)` : ""}${s.oi_per_capex[i] != null ? `; ${fmt(100 * s.oi_per_capex[i], 0)}¢ of yearly operating profit per dollar of ${CP_CO[s.parent]}'s capex a year before` : ""}.`));
  }
  sec.append(lines);

  const t = el("table", { class: "ps-table" });
  t.append(el("thead"), el("tbody"));
  const hr = el("tr");
  ["Trailing 12 months", "Quarter", "Free cash flow", "Capex share", "a year earlier", "Depreciation / revenue", "a year earlier", "Operating return", "a year earlier", "Incremental return"]
    .forEach((h, k) => hr.append(el("th", { class: k ? "num" : "" }, h)));
  t.tHead.append(hr);
  for (const [tk, c] of Object.entries(r.companies)) {
    const i = cpLast(c.capex_ocf), j = i - 4;
    const tr = el("tr");
    tr.append(el("td", {}, CP_CO[tk]), el("td", { class: "num" }, qs[i]), el("td", { class: "num" }, bn(c.fcf_bn[i], 1)),
      ...[c.capex_ocf[i], c.capex_ocf[j], c.da_rev[i], c.da_rev[j], c.ret_ppe[i], c.ret_ppe[j], c.inc_ret[i]].map((v) => el("td", { class: "num" }, hlPct(v))));
    t.tBodies[0].append(tr);
  }
  const sc = el("div", { class: "ps-scroll" });
  sc.append(t);
  sec.append(sc);

  const n = qs.length;
  const s = { dates: qs.map(cpQDate) };
  const g = r.cloud.googl_cloud, a = r.cloud.amzn_aws;
  if (g && a) {
    const m = (x) => x.margin.map((v) => (v == null ? null : 100 * v));
    psChart(sec, s, { title: "Cloud operating margin, %: Google Cloud (solid), AWS (dashed)", values: m(g), extra: m(a), digits: 0 },
      (i) => `${qs[i]}: Google Cloud ${hlPct(g.margin[i])} on ${bn(g.rev_bn[i], 1)} · AWS ${hlPct(a.margin[i])} on ${bn(a.rev_bn[i], 1)}`);
  }
  const cs = r.companies;
  const pc = (tk, k) => cs[tk][k].map((v) => (v == null ? null : 100 * v));
  psChart(sec, s, { title: "Capex as % of operating cash flow: Alphabet (solid), Amazon (dashed)", values: pc("GOOGL", "capex_ocf"), extra: pc("AMZN", "capex_ocf"), digits: 0 },
    (i) => `${qs[i]}: ${Object.keys(cs).map((tk) => `${CP_CO[tk]} ${hlPct(cs[tk].capex_ocf[i])}`).join(" · ")}`);
  if (n && r.azure_rev_bn.some((v) => v != null)) {
    const i = cpLast(r.azure_rev_bn);
    sec.append(el("p", { class: "help keep" }, `Azure revenue, reported in dollars from fiscal 2027: ${bn(r.azure_rev_bn[i], 1)} in ${qs[i]}.`));
  }
  return sec;
}

// Who buys besides the hyperscalers: Nvidia's own split, the hyperscalers' Taiwanese server
// builders (monthly), and buyers outside that channel with revenue in their SEC filings.
function cpBuyers(d) {
  const b = d.buyers;
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "Who buys? Hyperscalers against everyone else"));
  sec.append(el("p", { class: "help" }, "Nvidia, from its CFO commentary: since fiscal 2027 it reports Hyperscale (public clouds and the largest consumer internet companies) against AI Clouds, Industrial & Enterprise (ACIE: neoclouds, sovereigns, enterprises, labs building their own). Earlier quarters only have the large cloud providers' approximate share of Data Center revenue (italic). In fiscal Q2 2027 Nvidia moved one customer from ACIE to Hyperscale and recast only the quarters in that report, so compare like with like (marked ✓). Quarters are labelled by the calendar quarter they mostly cover. The hyperscalers buy their servers directly from Taiwanese contract manufacturers (Quanta, Wiwynn, Wistron), whose revenue comes out monthly: an early read on the hyperscaler channel. Supermicro and CoreWeave stand for the buyers outside it."));
  const nv = b.nvidia;
  const lines = el("div", { class: "v-lines" });
  const last = nv[nv.length - 1];
  if (last) {
    const ago = nv.find((r) => r.label === `${Number(last.label.slice(0, 4)) - 1}${last.label.slice(4)}`);
    const same = ago && ago.current_basis === last.current_basis;
    lines.append(nowLine(same && last.acie_share > ago.acie_share ? "good" : "na", same && last.acie_share > ago.acie_share ? "Broadening" : "", `Nvidia ${last.label}: Hyperscale ${bn(last.hyperscale_bn, 1)}${same ? ` (${pct(growth(last.hyperscale_bn, ago.hyperscale_bn), 0)} on a year earlier)` : ""}, everyone else (ACIE) ${bn(last.acie_bn, 1)}${same ? ` (${pct(growth(last.acie_bn, ago.acie_bn), 0)})` : ""}: ${hlPct(last.acie_share)} of Data Center revenue${same ? `, against ${hlPct(ago.acie_share)} a year earlier` : ""}.`));
  }
  const o = b.odm;
  const oi = cpLast(o.yoy3);
  if (oi >= 0) lines.append(el("p", {}, `Hyperscaler server builders (Quanta, Wiwynn, Wistron): NT$${fmt(o.total_bn_twd[oi], 0)}bn in ${o.months[oi]}; the last three months ${pct(o.yoy3[oi], 0)} on a year earlier (${pct(o.yoy3[oi - 3], 0)} three months before).`));
  for (const x of Object.values(b.others)) {
    const i = cpLast(x.rev_bn);
    if (i >= 4) lines.append(el("p", {}, `${x.label}: revenue ${bn(x.rev_bn[i], 1)} in ${x.quarters[i]}, ${pct(growth(x.rev_bn[i], x.rev_bn[i - 4]), 0)} on a year earlier.`));
  }
  sec.append(lines);

  const t = el("table", { class: "ps-table" });
  t.append(el("thead"), el("tbody"));
  const hr = el("tr");
  ["Nvidia Data Center", "Hyperscale", "Everyone else (ACIE)", "ACIE share", "Comparable"].forEach((h, k) => hr.append(el("th", { class: k ? "num" : "" }, h)));
  t.tHead.append(hr);
  for (const r of nv.slice(-8)) {
    const tr = el("tr", { class: r.exact ? "" : "cp-uncertain" });
    tr.append(el("td", {}, r.label), el("td", { class: "num" }, bn(r.hyperscale_bn, 1)), el("td", { class: "num" }, bn(r.acie_bn, 1)),
      el("td", { class: "num" }, hlPct(r.acie_share)), el("td", { class: "num" }, r.current_basis ? "✓" : r.exact ? "old basis" : "approx."));
    t.tBodies[0].append(tr);
  }
  const sc = el("div", { class: "ps-scroll" });
  sc.append(t);
  sec.append(sc);

  if (o.months.length) {
    const from = o.months.findIndex((m) => m >= "2021-01");
    const s = { dates: o.months.slice(from).map((m) => `${m}-15`) };
    psChart(sec, s, { title: "Hyperscaler server builders: revenue, last 3 months against a year earlier, %", values: o.yoy3.slice(from).map((v) => (v == null ? null : 100 * v)), digits: 0 },
      (i) => `${o.months[from + i]}: NT$${fmt(o.total_bn_twd[from + i], 0)}bn · ${Object.entries(o.by_company).map(([n, v]) => `${n} ${fmt(v[from + i], 0)}`).join(" · ")} · 3 months ${pct(o.yoy3[from + i], 0)}`);
  }
  return sec;
}

// Vendor financing: how much of Nvidia's revenue it funds itself through stakes in its customers,
// plus what it has promised or guaranteed. From SEC data; the commitments line is hand-entered.
function cpVendor(d) {
  const v = d.vendor, q = v.quarters, last = q[q.length - 1];
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "Who pays? Nvidia funding its own customers"));
  sec.append(el("p", { class: "help" }, `New money: cash Nvidia put into stakes in other companies (its customers, mostly: OpenAI, Anthropic, xAI, CoreWeave and other labs and neoclouds; also Intel and Nokia), from the cash flow statement where tagged, else the change in holdings less the quarter's investment gains. Before 2026 stakes in listed companies are not tagged and are left out. Exposure: stakes held, equity promised but not yet paid in, and the guarantees' maximum. ${v.promised.note} (${v.promised.source}.) Lucent, at the 1999–2000 peak, had about a fifth of a year's revenue out as customer financing, and wrote most of it off. Receivable days: receivables over quarterly revenue, times 91; rising days mean customers pay later.`));
  const ttm = v.ttm_new_share;
  const lines = el("div", { class: "v-lines" });
  if (ttm != null) lines.append(nowLine(ttm > 0.1 ? "bad" : ttm > 0.05 ? "care" : "good", `${hlPct(ttm)} self-funded`, `Last 12 months: Nvidia put ${bn(v.ttm_new_bn, 0)} into stakes, ${hlPct(ttm)} of its ${bn(v.ttm_rev_bn, 0)} revenue. Read it as: roughly ${fmt(100 * ttm, 0)}¢ of every dollar it sold came back from its own pocket.`));
  lines.append(el("p", {}, `Exposure: ${bn(v.exposure_bn, 0)} (stakes ${bn(last.stakes_bn, 0)}, promised ${bn(v.promised.equity_bn, 0)}, guarantees ${bn(v.guarantees_bn, 0)}), ${hlPct(v.exposure_bn / v.ttm_rev_bn)} of a year's revenue, against about ${hlPct(v.lucent_share)} at Lucent's peak. On top: ${bn(v.promised.cloud_bn, 0)} of cloud capacity it rents back from customers.`));
  const ago = q[q.length - 5];
  if (last.dso != null && ago?.dso != null) lines.append(el("p", {}, `Receivable days ${last.dso} in ${last.label} (${ago.dso} a year earlier).`));
  sec.append(lines);

  const t = el("table", { class: "ps-table" });
  t.append(el("thead"), el("tbody"));
  const hr = el("tr");
  ["Nvidia", "Revenue", "New money into stakes", "share of revenue", "Stakes held", "Guarantees (max)", "Receivable days"].forEach((h, k) => hr.append(el("th", { class: k ? "num" : "" }, h)));
  t.tHead.append(hr);
  for (const r of q.slice(-8)) {
    const tr = el("tr", { class: r.listed_known ? "" : "cp-uncertain" });
    tr.append(el("td", {}, r.label), ...[bn(r.rev_bn, 1), r.new_bn == null ? "n/a" : bn(r.new_bn, 1), hlPct(r.new_share),
      r.stakes_bn == null ? "n/a" : bn(r.stakes_bn, 1), r.guarantees_bn == null ? "—" : bn(r.guarantees_bn, 1), r.dso ?? "n/a"].map((x) => el("td", { class: "num" }, x)));
    t.tBodies[0].append(tr);
  }
  const sc = el("div", { class: "ps-scroll" });
  sc.append(t);
  sec.append(sc);
  const s = { dates: q.map((r) => r.end) };
  psChart(sec, s, { title: "New money into stakes, % of Nvidia's quarterly revenue", values: q.map((r) => (r.new_share == null ? null : 100 * r.new_share)), digits: 0 },
    (i) => `${q[i].label}: ${q[i].new_bn == null ? "n/a" : bn(q[i].new_bn, 1)} of ${bn(q[i].rev_bn, 1)} (${hlPct(q[i].new_share)})`);
  return sec;
}

function cpDisclosed(d) {
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "What the companies themselves said"));
  sec.append(el("p", { class: "help" }, "Figures stated by the companies (earnings calls, events, filings) or reported from their documents, collected with sources; added to as new ones appear. Hover a value for the quote. Italic rows rest on a secondary source or an approximate date. Run-rates are the latest month times twelve, so they run ahead of booked revenue. Hover a source link for the quote."));
  const D = d.disclosed;
  if (D.commitments?.length) {
    sec.append(el("h4", {}, D.commitments_title ?? "Anthropic's compute commitments"));
    const t = el("table", { class: "ps-table" });
    t.append(el("thead"), el("tbody"));
    const hr = el("tr");
    ["With", "Amount", "What", "Source"].forEach((h, i) => hr.append(el("th", { class: i === 1 ? "num" : "" }, h)));
    t.tHead.append(hr);
    for (const c of D.commitments) {
      const tr = el("tr");
      const src = el("td");
      src.append(el("a", { href: c.url, target: "_blank", rel: "noopener" }, c.source));
      tr.append(el("td", {}, c.counterparty), el("td", { class: "num" }, bn(c.amount_bn)), el("td", {}, c.what), src);
      t.tBodies[0].append(tr);
    }
    const sc = el("div", { class: "ps-scroll" });
    sc.append(t);
    sec.append(sc);
  }
  const groups = new Map();
  for (const p of D.points ?? []) {
    if (!groups.has(p.series)) groups.set(p.series, []);
    groups.get(p.series).push(p);
  }
  const figure = (p) => `${fmt(p.value, p.value < 10 ? 2 : p.value < 100 ? 1 : 0)} ${p.unit}`;
  const source = (p) => el("a", { href: p.url, target: "_blank", rel: "noopener", title: [p.quote, p.note].filter(Boolean).join(" · ") }, p.where || "source");
  // Series long enough to chart get the chart and their latest figure; the rest share one table.
  const rest = table(["Series", "Date", "Figure", "Said by", "Source"], { numFrom: 2 });
  for (const [series, pts] of groups) {
    pts.sort((a, b) => a.date.localeCompare(b.date));
    const name = D.series_names?.[series] ?? series;
    if (pts.length >= 3 && new Set(pts.map((p) => p.unit)).size === 1) {
      const s = { dates: pts.map((p) => p.date) };
      psChart(sec, s, { title: `${name}, ${pts[0].unit}`, values: pts.map((p) => p.value), digits: 0 }, (i) => `${pts[i].date}: ${figure(pts[i])} (${pts[i].who})`);
      const last = pts[pts.length - 1];
      const line = el("p", { class: "help keep" }, `Latest: ${figure(last)} on ${last.date}, ${last.who ?? ""} (`);
      line.append(source(last), ").");
      sec.append(line);
    } else {
      for (const p of pts) {
        const tr = el("tr", { class: p.note ? "cp-uncertain" : "" });
        const src = el("td");
        src.append(source(p));
        tr.append(el("td", {}, name), el("td", { class: "num" }, p.date), el("td", { class: "num", title: [p.quote, p.note].filter(Boolean).join(" · ") }, figure(p)), el("td", { class: "num" }, p.who ?? ""), src);
        rest.tBodies[0].append(tr);
      }
    }
  }
  if (rest.tBodies[0].children.length) {
    sec.append(el("h4", {}, "Other figures they stated"));
    sec.append(scroll(rest));
  }
  return sec;
}

// One chart for everything: each line divided by its own latest value, on a log scale, so the
// slope is the growth rate whatever the unit (tokens, dollars, users, an index).
const CP_LINE_COLOR = {
  openrouter: "--cp-c1", google_tokens: "--cp-c2", google_api: "--cp-c3", bytedance: "--cp-c4",
  anthropic_rr: "--cp-c5", openai_rr: "--cp-c6", gemini_users: "--cp-c7", chatgpt_users: "--cp-c7",
  capex: "--cp-c8", backlog: "--cp-c9", dram: "--cp-c10",
};
const CP_ALL_RANGES = [
  { label: "1 year", days: 365 },
  { label: "2 years", days: 730 },
  { label: "Since 2019", days: null },
];
const cpAll = { range: 730, off: new Set() };

// Value at a day by log-linear interpolation between the points around it; null outside the series.
function cpAt(line, t) {
  const ts = line.ts;
  if (t < ts[0] || t > ts[ts.length - 1]) return null;
  let i = ts.findIndex((x) => x >= t);
  if (ts[i] === t) return line.values[i];
  const a = i - 1, f = (t - ts[a]) / (ts[i] - ts[a]);
  return Math.exp(Math.log(line.values[a]) * (1 - f) + Math.log(line.values[i]) * f);
}

function cpYearGrowth(line) {
  const last = line.ts[line.ts.length - 1];
  const then = cpAt(line, last - 365);
  if (then) return { x: line.values[line.values.length - 1] / then, approx: false };
  const span = last - line.ts[0];
  if (span < 90) return null;
  return { x: (line.values[line.values.length - 1] / line.values[0]) ** (365 / span), approx: true };
}

function cpCombined(d) {
  const sec = el("section", { class: "hz-sec" });
  sec.append(el("h3", {}, "Everything in one chart"));
  sec.append(el("p", { class: "help" }, "Each line is divided by its own latest value and drawn on a log scale, so every line ends at 1 and a steeper line is faster growth, whatever its unit. A line that rose 10× ends one gridline above where it started. Dots are the dates a company stated a figure; between them the line is drawn straight. Click a name to hide or show it. The number after each name is its growth over the last year (~ where the series is younger than a year, scaled to a year)."));
  const ranges = el("div", { class: "ranges" });
  for (const r of CP_ALL_RANGES) {
    const b = el("button", { class: "chip", "aria-pressed": String(cpAll.range === r.days) }, r.label);
    b.addEventListener("click", () => { cpAll.range = r.days; render(DD); });
    ranges.append(b);
  }
  sec.append(ranges);

  const lines = d.combined.map((l) => ({ ...l, ts: l.dates.map(dayNum) }));
  const end = Math.max(...lines.map((l) => l.ts[l.ts.length - 1]));
  const start = cpAll.range ? end - cpAll.range : Math.min(...lines.map((l) => l.ts[0]));
  const shown = lines.filter((l) => !cpAll.off.has(l.key));
  // Log of value ÷ latest, over the visible window.
  let lo = 0;
  for (const l of shown) {
    const last = l.values[l.values.length - 1];
    l.ys = l.values.map((v) => Math.log10(v / last));
    l.ts.forEach((t, i) => { if (t >= start) lo = Math.min(lo, l.ys[i]); });
    const edge = cpAt(l, start);
    if (edge) lo = Math.min(lo, Math.log10(edge / last));
  }
  lo = Math.floor(lo) === lo ? lo - 0.25 : Math.floor(lo * 2) / 2;
  const hi = 0.15;
  const W = 900, H = 420, L = 64, R = 14, T = 12, B = 28;
  const xOf = (t) => L + ((t - start) / (end - start)) * (W - L - R);
  const yOf = (v) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);
  const wrap = el("div", { class: "chart cp-big" });
  const readout = el("div", { class: "help ps-readout" });
  wrap.append(readout);
  const root = svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "AI demand measures, each relative to its latest value, log scale" });
  wrap.append(root);
  const grid = svg("g", { class: "grid" });
  for (let k = Math.ceil(lo); k <= 0; k++) {
    grid.append(svg("line", { x1: L, x2: W - R, y1: yOf(k), y2: yOf(k) }));
    const lab = svg("text", { x: L - 6, y: yOf(k) + 4, "text-anchor": "end", class: "tick" });
    lab.textContent = k === 0 ? "today" : `÷${10 ** -k >= 1000 ? `${10 ** -k / 1000}k` : 10 ** -k}`;
    grid.append(lab);
  }
  for (const f of [0, 0.25, 0.5, 0.75, 1]) {
    const t = start + f * (end - start);
    const lab = svg("text", { x: xOf(t), y: H - 8, "text-anchor": f === 0 ? "start" : f === 1 ? "end" : "middle", class: "tick" });
    lab.textContent = new Date(t * DAY).toISOString().slice(0, 7);
    grid.append(lab);
  }
  root.append(grid);
  const clip = svg("clipPath", { id: "cp-clip" });
  clip.append(svg("rect", { x: L, y: T, width: W - L - R, height: H - T - B }));
  root.append(clip);
  const plot = svg("g", { "clip-path": "url(#cp-clip)" });
  root.append(plot);
  for (const l of shown) {
    const color = `var(${CP_LINE_COLOR[l.key] ?? "--line"})`;
    let path = "";
    l.ts.forEach((t, i) => { path += `${i ? "L" : "M"}${xOf(t).toFixed(1)},${yOf(l.ys[i]).toFixed(1)}`; });
    plot.append(svg("path", { d: path, fill: "none", stroke: color, "stroke-width": l.values.length > 40 ? 1.6 : 2, "stroke-linejoin": "round" }));
    if (l.values.length <= 40) l.ts.forEach((t, i) => plot.append(svg("circle", { cx: xOf(t), cy: yOf(l.ys[i]), r: 3.2, fill: color })));
  }
  const cross = svg("line", { class: "cross", y1: T, y2: H - B, visibility: "hidden" });
  root.append(cross);
  const hit = svg("rect", { class: "hit", x: L, y: T, width: W - L - R, height: H - T - B });
  root.append(hit);
  const say = (t) => {
    if (t == null) {
      readout.textContent = "Hover the chart to read every line on one date.";
      return;
    }
    const parts = shown.map((l) => [l, cpAt(l, t)]).filter(([, v]) => v != null)
      .map(([l, v]) => `${l.label} ${fmt((100 * v) / l.values[l.values.length - 1], v / l.values[l.values.length - 1] < 0.1 ? 1 : 0)}%`);
    readout.textContent = `${new Date(t * DAY).toISOString().slice(0, 10)}, as % of today: ${parts.join(" · ") || "no data"}`;
  };
  say(null);
  hit.addEventListener("pointermove", (e) => {
    const r = root.getBoundingClientRect();
    const x = ((e.clientX - r.left) / r.width) * W;
    const t = Math.round(start + ((x - L) / (W - L - R)) * (end - start));
    cross.setAttribute("x1", xOf(t));
    cross.setAttribute("x2", xOf(t));
    cross.setAttribute("visibility", "visible");
    say(t);
  });
  hit.addEventListener("pointerleave", () => { cross.setAttribute("visibility", "hidden"); say(null); });
  sec.append(wrap);

  const legend = el("div", { class: "cp-legend" });
  const groups = { tokens: "Tokens", revenue: "Lab revenue", users: "Users", spend: "Capex and backlog", memory: "Memory prices" };
  for (const [g, name] of Object.entries(groups)) {
    const ls = lines.filter((l) => l.group === g);
    if (!ls.length) continue;
    const col = el("div", { class: "cp-lgroup" });
    col.append(el("div", { class: "cp-lhead" }, name));
    for (const l of ls) {
      const gr = cpYearGrowth(l);
      const item = el("button", { class: "cp-litem", "aria-pressed": String(!cpAll.off.has(l.key)) });
      const sw = el("span", { class: "cp-swatch" });
      sw.style.background = `var(${CP_LINE_COLOR[l.key] ?? "--line"})`;
      item.append(sw, el("span", {}, l.label), el("span", { class: "cp-growth" }, gr ? `${gr.approx ? "~" : ""}${fmt(gr.x, gr.x < 10 ? 1 : 0)}×` : ""));
      item.title = `Latest ${l.dates[l.dates.length - 1]}: ${fmt(l.values[l.values.length - 1], 1)} ${l.unit}`;
      item.addEventListener("click", () => {
        if (cpAll.off.has(l.key)) cpAll.off.delete(l.key); else cpAll.off.add(l.key);
        render(DD);
      });
      col.append(item);
    }
    legend.append(col);
  }
  sec.append(legend);
  return sec;
}

export function signal(Dx) {
  const c = Dx.compute, s = c.sec;
  const qi = s.capex_total_bn.findLastIndex((v) => v != null);
  const yoy = growth(s.capex_total_bn[qi], s.capex_total_bn[qi - 4]);
  const nv = c.buyers?.nvidia?.at(-1);
  const g = c.returns?.cloud?.googl_cloud, a = c.returns?.cloud?.amzn_aws;
  const mg = (x) => x && hlPct(x.margin[cpLast(x.margin)]);
  const vf = c.vendor?.ttm_new_share;
  const over = Object.entries(c.returns?.companies ?? {}).filter(([, v]) => v.capex_ocf[cpLast(v.capex_ocf)] > 1).map(([t]) => CP_CO[t]);
  return { area: "AI build-out", level: yoy > 0.3 ? "good" : yoy < 0 ? "bad" : "care", state: yoy > 0.3 ? "Still accelerating" : yoy < 0 ? "Shrinking" : "Slowing",
    short: `Big-five capex ${pct(yoy, 0)} on a year${over.length ? `; ${over.join(" and ")} now borrow to build` : ""}${vf != null ? `; Nvidia self-funds ${hlPct(vf)} of its sales` : ""}.`,
    means: `${yoy > 0.3 ? "Spending is still accelerating, broadening and earning money: demand for your AI hardware and memory names holds." : "Spending growth is slowing: watch your AI hardware names' guidance."}${over.length ? ` The risk to watch: ${over.join(" and ")} now spend more than they earn in cash, so the build-out depends on debt markets staying open.` : ""}${vf != null && vf > 0.1 ? ` Nvidia funded ${hlPct(vf)} of its own sales through stakes in customers: part of the demand is its own money, so a stumbling lab hits Nvidia twice.` : ""}`,
    reading: `Big-five capex ${bn(s.capex_total_bn[qi])} in ${s.quarters[qi]}${nv ? `; ${hlPct(nv.acie_share)} of Nvidia's data-centre sales outside the hyperscalers` : ""}${g && a ? `; cloud margins Google ${mg(g)}, AWS ${mg(a)}` : ""}.`,
    lines: cpSummary(c) };
}

export function render(Dx) {
  DD = Dx;
  const d = Dx.compute;
  const box = pageBox();
  box.replaceChildren(topCard(signal(Dx), SOURCES));
  if (d.returns) box.append(cpReturns(d));
  if (d.buyers) box.append(cpBuyers(d));
  if (d.vendor) box.append(cpVendor(d));
  box.append(cpCapex(d), cpTokens(d));
  if (d.combined) box.append(cpCombined(d));
  box.append(cpDisclosed(d));
}
