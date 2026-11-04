import { el, svg, dayNum } from "./core.js";

export function lineChart(box, s, { title, values, digits, band, extra }) {
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

// A chart with a one-line readout under its title that follows the pointer.
export function psChart(box, s, opts, readout) {
  const ch = lineChart(box, s, opts);
  const line = el("div", { class: "help ps-readout" }, readout(s.dates.length - 1));
  ch.wrap.querySelector("h4").after(line);
  ch.onMove((i) => {
    ch.cross(i);
    line.textContent = readout(i ?? s.dates.length - 1);
  });
  return ch;
}

// Charts over the same dates: move one crosshair, move all, and every readout follows.
export function linkCharts(charts, readout, last) {
  for (const ch of charts) ch.onMove((i) => charts.forEach((c) => {
    c.cross(i);
    c.wrap.querySelector(".ps-readout").textContent = readout(i ?? last);
  }));
}
