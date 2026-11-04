#!/usr/bin/env node
// Nightly: record today's readings (src/state.js, the same code the app uses) in public/data/changes.json,
// so the Signals tab can say what flipped since the previous data day. Keeps the last 60 data days.
import { readFileSync, writeFileSync, existsSync, copyFileSync, renameSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { snapshot, diff } from "../src/state.js";

const APP = join(dirname(fileURLToPath(import.meta.url)), "..");
const DATA = join(APP, "public", "data");
const read = (n) => { try { return JSON.parse(readFileSync(join(DATA, `${n}.json`), "utf8")); } catch { return null; } };

const D = Object.fromEntries(["ranking", "highlow", "dipjudge", "fear", "breadth", "positioning", "industry", "discounts"].map((n) => [n, read(n)]));
const snap = snapshot(D);
if (!snap.date) { console.error("snapshot: no data date; nothing written"); process.exit(1); }
const file = join(DATA, "changes.json");
const C = existsSync(file) ? JSON.parse(readFileSync(file, "utf8")) : { snapshots: [] };
const snaps = C.snapshots.filter((s) => s.date !== snap.date);
snaps.push(snap);
snaps.sort((a, b) => a.date.localeCompare(b.date));
const out = { generated: new Date().toISOString(), snapshots: snaps.slice(-60) };
writeFileSync(`${file}.tmp`, JSON.stringify(out));
renameSync(`${file}.tmp`, file);
if (existsSync(join(APP, "dist", "data"))) copyFileSync(file, join(APP, "dist", "data", "changes.json"));
const prev = out.snapshots.at(-2);
if (prev) {
  const d = diff(prev, snap);
  console.log(`${snap.date} against ${prev.date}: ${d.flips.length} flips, ${d.added.length} new cheap, ${d.dropped.length} dropped`);
  for (const f of d.flips) console.log(`  ${f.label}: ${f.from} -> ${f.to}`);
} else console.log(`${snap.date}: first snapshot, ${Object.keys(snap.items).length} readings, ${snap.cheap.length} cheap`);
