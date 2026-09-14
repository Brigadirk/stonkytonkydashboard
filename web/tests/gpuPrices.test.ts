import { describe, expect, it } from 'vitest';
import { readFileSync, readdirSync, existsSync, mkdtempSync, mkdirSync, cpSync, writeFileSync, rmSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
import { amsterdamDate, completedFriday, dailyGrid, gpuUrl, normalizeHistory, parseGpuDataset, weekEnds, weeklyChange, weeklyCsv } from '../src/gpuPrices';

const payload = (rows: [string, unknown][]) => ({ success: true, gpu_type: 'A100 SXM4', data: rows.map(([timestamp, index_value]) => ({ timestamp, index_value })) });
const normalize = (rows: [string, unknown][], asOf = '2026-09-14T10:00:00Z') => normalizeHistory(payload(rows), 'A100 SXM4', asOf);
const saved = JSON.parse(readFileSync(new URL('../public/data/gpu-prices.json', import.meta.url), 'utf8'));

describe('GPU rental observations and weekly comparisons', () => {
  it('uses exact prior-Friday prices, without substituting a nearby date', () => {
    const rows = normalize([['2026-09-04T20:00:00Z', 2], ['2026-09-10T20:00:00Z', 2.4], ['2026-09-11T20:00:00Z', 2.2]]);
    expect(weeklyChange(rows, '2026-09-11').change).toBeCloseTo(10);
    expect(weeklyChange(rows.filter(row => row.date !== '2026-09-04'), '2026-09-11')).toMatchObject({ price: 2.2, baseline: null, change: null });
    expect(weeklyChange(rows.filter(row => row.date !== '2026-09-11'), '2026-09-11')).toMatchObject({ price: null, baseline: 2, change: null });
  });
  it('excludes an unfinished Friday and handles weekend, year and DST boundaries', () => {
    expect(completedFriday('2026-09-11')).toBe('2026-09-04');
    expect(completedFriday('2026-09-12')).toBe('2026-09-11');
    expect(completedFriday('2026-09-14')).toBe('2026-09-11');
    expect(completedFriday('2027-01-01')).toBe('2026-12-25');
    expect(completedFriday('2026-03-30')).toBe('2026-03-27');
    expect(amsterdamDate('2026-09-11T22:30:00Z')).toBe('2026-09-12');
    expect(amsterdamDate('2026-12-11T22:30:00Z')).toBe('2026-12-11');
  });
  it('sorts daily prices and excludes the current Amsterdam day and future data', () => {
    const rows = normalize([['2026-09-13T20:00:00Z', 1.1], ['2026-09-14T00:00:00Z', 1.2], ['2026-09-12T20:00:00Z', 1], ['2026-09-15T20:00:00Z', 2]]);
    expect(rows.map(row => row.date)).toEqual(['2026-09-12', '2026-09-13']);
    expect(normalize([['2026-09-12T20:00:00Z', 1], ['2026-09-12T22:30:00Z', 2]], '2026-09-13T10:00:00Z')).toHaveLength(1);
  });
  it('rejects malformed identity, dates, duplicate days and nonpositive prices', () => {
    expect(() => normalizeHistory({ ...payload([['2026-09-11T20:00:00Z', 1]]), gpu_type: 'H200' }, 'A100 SXM4', '2026-09-14T10:00:00Z')).toThrow();
    for (const price of [0, -1, true, '1', Infinity, NaN]) expect(() => normalize([['2026-09-11T20:00:00Z', price]])).toThrow();
    expect(() => normalize([['2026-09-11T20:00:00', 1]])).toThrow();
    expect(() => normalize([['2026-09-11T20:00:00Z', 1], ['2026-09-11T21:00:00Z', 1.2]])).toThrow(/Duplicate/);
  });
  it('leaves missing days as chart gaps, including weekend dates', () => {
    const rows = normalize([['2026-09-11T20:00:00Z', 1], ['2026-09-13T20:00:00Z', 1.2]]);
    expect(dailyGrid(rows, '2026-09-11', '2026-09-13')).toEqual({ dates: ['2026-09-11', '2026-09-12', '2026-09-13'], prices: [1, null, 1.2] });
  });
  it('rejects missing series, wrong units and invalid saved provenance', () => {
    expect(() => parseGpuDataset({ ...saved, unit: 'USD' })).toThrow();
    expect(() => parseGpuDataset({ ...saved, series: saved.series.slice(1) })).toThrow();
    expect(() => parseGpuDataset({ ...saved, series: [{ ...saved.series[0], source_url: 'https://example.com' }, ...saved.series.slice(1)] })).toThrow();
  });
  it('exports raw precision and blank missing changes, with no fabricated weekly observations', () => {
    const data = parseGpuDataset(saved);
    // Keep the calculation fixture stable when the live trailing window moves.
    data.series = data.series.map(series => ({ ...series, observations: normalize([
      ['2026-09-04T20:00:00Z', 1.06], ['2026-09-11T20:00:00Z', .99],
    ]) }));
    const weeks = weekEnds(data, '2026-09-14');
    expect(weeks.at(-1)).toBe('2026-09-11');
    expect(weeks.every(date => new Date(date).getUTCDay() === 5)).toBe(true);
    const csv = weeklyCsv(data, ['2026-09-11', '2020-01-03']);
    const first = csv.split('\n')[1].split(',');
    expect(first.slice(0, 5)).toEqual(['2026-09-04', '2026-09-11', 'A100 SXM4', '1.06', '0.99']);
    expect(Number(first[5])).toBeCloseTo(-6.6037735849, 9);
    expect(csv).toContain(`2019-12-27,2020-01-03,A100 SXM4,,,,${gpuUrl('A100 SXM4')}`);
  });
  it('matches every saved daily value to an archived response with an exact SHA-256', () => {
    const data = parseGpuDataset(saved);
    const archives = [new URL('../../data/collection/ornn/', import.meta.url), new URL('./fixtures/ornn/', import.meta.url)];
    const directories = archives.flatMap(archive=>existsSync(archive)?readdirSync(archive).sort().reverse().map(name=>new URL(`${name}/`,archive)):[]);
    const run = directories.find(directory => {
      try { return JSON.parse(readFileSync(new URL('manifest.json', directory), 'utf8')).collected_at === data.collected_at; } catch { return false; }
    });
    expect(run).toBeTruthy();
    for (const series of data.series) {
      const raw = readFileSync(new URL(`${series.gpu.replaceAll(' ', '-')}.json`, run!));
      expect(createHash('sha256').update(raw).digest('hex')).toBe(series.sha256);
      expect(normalizeHistory(JSON.parse(raw.toString()), series.gpu, series.retrieved_at)).toEqual(series.observations);
    }
  });
  it('keeps the previous snapshot when one API request fails', () => {
    const directory = mkdtempSync(join(tmpdir(), 'forward-gpu-collector-'));
    try {
      mkdirSync(join(directory, 'scripts'), { recursive: true });
      mkdirSync(join(directory, 'web/src'), { recursive: true });
      mkdirSync(join(directory, 'web/public/data'), { recursive: true });
      writeFileSync(join(directory, 'package.json'), '{"type":"module"}');
      cpSync(new URL('../../scripts/collect_gpu_prices.mjs', import.meta.url), join(directory, 'scripts/collect_gpu_prices.mjs'));
      cpSync(new URL('../src/gpuPrices.ts', import.meta.url), join(directory, 'web/src/gpuPrices.ts'));
      const target = join(directory, 'web/public/data/gpu-prices.json');
      writeFileSync(target, 'previous snapshot');
      const script = `globalThis.fetch = async url => {
        const gpu = decodeURIComponent(new URL(url).pathname.split('/')[3]);
        if (gpu === 'H200') return new Response('Unavailable', { status: 503 });
        return new Response(JSON.stringify({ success: true, gpu_type: gpu, access: 'public-3mo', data: [{ timestamp: '2020-01-01T20:00:00Z', index_value: 1 }] }));
      }; await import(${JSON.stringify(pathToFileURL(join(directory, 'scripts/collect_gpu_prices.mjs')).href)});`;
      const result = spawnSync(process.execPath, ['--input-type=module', '-e', script], { encoding: 'utf8', timeout: 10_000 });
      expect(result.status).toBe(1);
      expect(result.stderr).toContain('H200: Ornn returned HTTP 503');
      expect(readFileSync(target, 'utf8')).toBe('previous snapshot');
    } finally { rmSync(directory, { recursive: true, force: true }); }
  });
});
