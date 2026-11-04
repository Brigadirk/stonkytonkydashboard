// Every tab's JSON, fetched once per visit, with the time each file was last written (Last-Modified)
// so a tab can say when a nightly script failed and left yesterday's numbers in place.

export const FILES = ["ranking", "highlow", "dipjudge", "fear", "breadth", "markets", "positioning", "korea_margin",
  "horizon", "compute", "industry", "discounts", "changes"];
// Readable names for the freshness line.
export const FILE_NAMES = {
  ranking: "valuations", highlow: "highs and lows", dipjudge: "dip verdict", fear: "fear and rates", breadth: "breadth",
  markets: "prices", positioning: "positioning", korea_margin: "Korean margin", horizon: "calendar", compute: "AI data",
  industry: "memory, GPUs, shipping", discounts: "discounts", changes: "changes",
};

const meta = {};
let all = null;

async function fetchOne(name) {
  try {
    const r = await fetch(`data/${name}.json`, { cache: "no-store" });
    if (!r.ok) return null;
    const lm = r.headers.get("last-modified");
    const j = await r.json();
    // The script's own timestamp when it writes one; a rebuild of the app restamps the files.
    meta[name] = { modified: j?.generated ? new Date(j.generated) : lm ? new Date(lm) : null };
    return j;
  } catch {
    return null;
  }
}

export function allData() {
  all ??= Promise.all(FILES.map(fetchOne)).then((got) => Object.fromEntries(FILES.map((n, i) => [n, got[i]])));
  return all;
}

// The nightly job runs Monday to Friday at 23:30 Prague time. A file is stale when it was last written
// before the latest run that should have finished (three hours' grace).
function lastRun(now = new Date()) {
  const wall = new Date(now.toLocaleString("en-US", { timeZone: "Europe/Prague" }));
  const shift = wall - now;
  const cut = new Date(wall.getTime() - 3 * 3600e3);
  for (let i = 0; i < 8; i++) {
    const c = new Date(cut);
    c.setDate(cut.getDate() - i);
    c.setHours(23, 30, 0, 0);
    if (c.getDay() >= 1 && c.getDay() <= 5 && c <= cut) return new Date(c.getTime() - shift);
  }
  return null;
}

export function freshness(name) {
  const m = meta[name]?.modified;
  if (!m) return { name, label: FILE_NAMES[name] ?? name, when: null, stale: !(name in meta) };
  const run = lastRun();
  return { name, label: FILE_NAMES[name] ?? name, when: m, stale: run != null && m < run };
}

export const whenText = (d) => (d ? d.toLocaleString("en-GB", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "never");
