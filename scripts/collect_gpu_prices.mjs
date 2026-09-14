#!/usr/bin/env node
// Node 22.18+; no API key or third-party runtime dependencies.
import { mkdir, writeFile, rename, rm } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { createHash, randomUUID } from 'node:crypto';
import { GPU_TYPES, gpuUrl, normalizeHistory, parseGpuDataset } from '../web/src/gpuPrices.ts';

const app = new URL('../', import.meta.url);
const target = new URL('web/public/data/gpu-prices.json', app);
const started = new Date().toISOString();
const runId = `${started.replace(/[:.]/g, '-')}-${randomUUID().slice(0, 8)}`;
const archive = new URL(`data/collection/ornn/${runId}/`, app);
await mkdir(archive, { recursive: true });
try {
  const results = await Promise.allSettled(GPU_TYPES.map(async gpu => {
    const source_url = gpuUrl(gpu);
    const response = await fetch(source_url, {
      headers: { Accept: 'application/json', 'User-Agent': 'Forward GPU price collector' },
      signal: AbortSignal.timeout(20_000),
    });
    if (!response.ok) throw new Error(`${gpu}: Ornn returned HTTP ${response.status}`);
    const raw = Buffer.from(await response.arrayBuffer());
    const retrieved_at = new Date().toISOString();
    // Retain the exact response bytes, including if later validation rejects it.
    await writeFile(new URL(`${gpu.replaceAll(' ', '-')}.json`, archive), raw);
    const payload = JSON.parse(raw.toString('utf8'));
    return { gpu, source_url, retrieved_at, sha256: createHash('sha256').update(raw).digest('hex'),
      access: typeof payload.access === 'string' ? payload.access : 'not-specified',
      observations: normalizeHistory(payload, gpu, retrieved_at) };
  }));
  const failed = results.filter(result => result.status === 'rejected');
  if (failed.length) throw new Error(failed.map(result => result.reason.message).join('; '));
  const dataset = parseGpuDataset({ schema_version: 1, provider: 'Ornn', unit: 'USD per GPU-hour',
    timezone: 'Europe/Amsterdam', collected_at: new Date().toISOString(), series: results.map(result => result.value) });
  await writeFile(new URL('manifest.json', archive), JSON.stringify(dataset, null, 2) + '\n');
  const temporary = new URL(`web/public/data/.gpu-prices-${runId}.tmp`, app);
  try {
    await writeFile(temporary, JSON.stringify(dataset, null, 2) + '\n');
    await rename(temporary, target);
  } finally { await rm(temporary, { force: true }); }
  console.log(`Saved ${dataset.series.length} GPU series to ${fileURLToPath(target)}`);
  for (const series of dataset.series) console.log(`${series.gpu}: ${series.observations.length} daily prices, through ${series.observations.at(-1).date}`);
  console.log(`Raw responses and provenance: ${fileURLToPath(archive)}`);
} catch (error) {
  await writeFile(new URL('error.txt', archive), `${error.message}\n`);
  console.error(`GPU refresh failed. The previous dashboard dataset is unchanged. ${error.message}`);
  process.exitCode = 1;
}
