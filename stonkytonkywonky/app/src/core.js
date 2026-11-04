// Shared helpers: DOM builders, number formats, and the router hook every tab uses.

export const SVG = "http://www.w3.org/2000/svg";
export const DAY = 864e5;

export const $ = (sel) => document.querySelector(sel);

export function el(tag, attrs = {}, text) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (text !== undefined) node.textContent = text;
  return node;
}
export function svg(tag, attrs = {}) {
  const node = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
}

export const fmt = (v, d = 1) => (v == null || !Number.isFinite(v) ? "n/a" : v.toFixed(d));
export const pct = (v, d = 1) => (v == null ? "n/a" : `${v >= 0 ? "+" : ""}${(v * 100).toFixed(d)}%`);
export const money = (v, ccy) => (v == null || !Number.isFinite(v) ? "n/a" : `${v >= 1000 ? v.toFixed(0) : v.toFixed(2)} ${ccy || ""}`.trim());
export const dayNum = (iso) => Math.round(Date.parse(iso) / DAY);
export const isoOf = (n) => new Date(n * DAY).toISOString().slice(0, 10);
export const hlPct = (v) => (v == null ? "n/a" : `${Math.round(v * 100)}%`);
export const hzSigned = (v, d = 0) => `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(d)}`;
export const sgn = (v, d = 1) => (v == null ? "n/a" : hzSigned(v, d));
export const ok = (pass) => (pass ? "✓" : "✗");

export function ordinal(n) {
  const tail = n % 100 >= 11 && n % 100 <= 13 ? "th" : ["th", "st", "nd", "rd"][n % 10] || "th";
  return `${n}${tail}`;
}
export const psOrd = (p) => (p == null ? "n/a" : ordinal(Math.round(p)));
export const lower1 = (s) => (s ? s.charAt(0).toLowerCase() + s.slice(1) : s);

export const lsGet = (k) => { try { return localStorage.getItem(k); } catch { return null; } };
export const lsSet = (k, v) => { try { localStorage.setItem(k, v); } catch { /* private window */ } };

// The open page and the router; main.js sets go() so tabs can link to each other without importing it.
export const app = { page: "valuation", go: () => {} };
export const pageBox = () => $("#pagebody");
