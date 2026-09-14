// Public Ornn observations only. No equity or portfolio data enters this dataset.
export const GPU_TYPES = ['A100 SXM4', 'H100 SXM', 'H200', 'B200', 'RTX 5090'] as const;
export type GpuType = typeof GPU_TYPES[number];
export const GPU_COLORS: Record<GpuType, string> = {
  'A100 SXM4': '#267c72', 'H100 SXM': '#b66138', H200: '#8063ac', B200: '#337ea1', 'RTX 5090': '#9b842e',
};
export const ORNN_DOCS = 'https://data.ornn.com/docs/api-reference/historical-prices/get-a-public-daily-series';
export const gpuUrl = (gpu: GpuType) => `https://api.ornnai.com/api/gpu/${encodeURIComponent(gpu)}/index-history`;
export interface GpuObservation { date: string; price: number; timestamp: string }
export interface GpuSeries {
  gpu: GpuType; source_url: string; retrieved_at: string; sha256: string;
  access: string; observations: GpuObservation[];
}
export interface GpuDataset {
  schema_version: 1; provider: 'Ornn'; unit: 'USD per GPU-hour';
  timezone: 'Europe/Amsterdam'; collected_at: string; series: GpuSeries[];
}
export interface GpuWeek { end: string; start: string; price: number | null; baseline: number | null; change: number | null }
const DAY = 86_400_000;
export const shiftDay = (date: string, days: number) => new Date(Date.parse(`${date}T12:00:00Z`) + days * DAY).toISOString().slice(0, 10);
export function amsterdamDate(value: Date | string): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Amsterdam', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(value));
}
export const daysApart = (later: string, earlier: string) => Math.round((Date.parse(later) - Date.parse(earlier)) / DAY);
export function completedFriday(today: string): string {
  // A Friday is complete from Saturday 00:00 Amsterdam, including across DST.
  const weekday = new Date(`${today}T12:00:00Z`).getUTCDay();
  return shiftDay(today, -((weekday + 1) % 7 + 1));
}
function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Invalid Ornn data structure');
  return value as Record<string, unknown>;
}
function validTimestamp(value: unknown): value is string {
  return typeof value === 'string' && /T.*(?:Z|[+-]\d{2}:\d{2})$/.test(value) && Number.isFinite(Date.parse(value));
}
export function normalizeHistory(payload: unknown, gpu: GpuType, collectedAt: string): GpuObservation[] {
  const data = record(payload);
  if (data.success !== true || data.gpu_type !== gpu || !Array.isArray(data.data)) throw new Error(`Invalid Ornn response for ${gpu}`);
  if (!validTimestamp(collectedAt)) throw new Error('Invalid collection timestamp');
  const today = amsterdamDate(collectedAt), seen = new Set<string>();
  const rows: GpuObservation[] = [];
  for (const raw of data.data) {
    const row = record(raw), timestamp = row.timestamp, price = row.index_value;
    if (!validTimestamp(timestamp) || typeof price !== 'number' || !Number.isFinite(price) || price <= 0) throw new Error(`Invalid Ornn observation for ${gpu}`);
    const date = amsterdamDate(timestamp);
    // Today's daily average can still change. Keep only completed calendar days.
    if (Date.parse(timestamp) > Date.parse(collectedAt) || date >= today) continue;
    if (seen.has(date)) throw new Error(`Duplicate Ornn date for ${gpu}: ${date}`);
    seen.add(date);
    rows.push({ date, price, timestamp });
  }
  if (!rows.length) throw new Error(`No completed daily observations for ${gpu}`);
  return rows.sort((a, b) => a.date.localeCompare(b.date));
}
export function parseGpuDataset(value: unknown): GpuDataset {
  const data = record(value);
  if (data.schema_version !== 1 || data.provider !== 'Ornn' || data.unit !== 'USD per GPU-hour' || data.timezone !== 'Europe/Amsterdam' || !validTimestamp(data.collected_at) || !Array.isArray(data.series)) throw new Error('Unsupported GPU dataset');
  if (data.series.length !== GPU_TYPES.length) throw new Error('GPU dataset must contain all five public series');
  const series = GPU_TYPES.map(gpu => {
    const matches = (data.series as unknown[]).map(record).filter(item => item.gpu === gpu);
    if (matches.length !== 1) throw new Error(`Missing or duplicate series: ${gpu}`);
    const item = matches[0];
    if (item.source_url !== gpuUrl(gpu) || !validTimestamp(item.retrieved_at) || Date.parse(item.retrieved_at) > Date.parse(data.collected_at as string) || typeof item.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(item.sha256) || typeof item.access !== 'string' || !Array.isArray(item.observations)) throw new Error(`Invalid provenance for ${gpu}`);
    const observations = normalizeHistory({ success: true, gpu_type: gpu, data: item.observations.map(raw => {
      const row = record(raw);
      if (!validTimestamp(row.timestamp) || row.date !== amsterdamDate(row.timestamp)) throw new Error(`Invalid observation date for ${gpu}`);
      return { timestamp: row.timestamp, index_value: row.price };
    }) }, gpu, data.collected_at as string);
    if (observations.length !== item.observations.length) throw new Error(`Incomplete daily values in saved ${gpu} series`);
    return { gpu, source_url: item.source_url, retrieved_at: item.retrieved_at, sha256: item.sha256, access: item.access, observations };
  });
  return { schema_version: 1, provider: 'Ornn', unit: 'USD per GPU-hour', timezone: 'Europe/Amsterdam', collected_at: data.collected_at, series };
}
export function weeklyChange(rows: GpuObservation[], end: string): GpuWeek {
  const start = shiftDay(end, -7);
  const price = rows.find(row => row.date === end)?.price ?? null;
  const baseline = rows.find(row => row.date === start)?.price ?? null;
  return { end, start, price, baseline, change: price !== null && baseline !== null ? (price / baseline - 1) * 100 : null };
}
export function weekEnds(data: GpuDataset, today = amsterdamDate(new Date())): string[] {
  const first = data.series.map(series => series.observations[0].date).sort()[0];
  const end = completedFriday(today);
  return Array.from({ length: 13 }, (_, i) => shiftDay(end, -7 * (12 - i))).filter(date => date >= shiftDay(first, 7));
}
export function dailyGrid(rows: GpuObservation[], start: string, end: string): { dates: string[]; prices: (number | null)[] } {
  const byDate = new Map(rows.map(row => [row.date, row.price]));
  const dates = Array.from({ length: Math.max(0, daysApart(end, start) + 1) }, (_, i) => shiftDay(start, i));
  return { dates, prices: dates.map(date => byDate.get(date) ?? null) };
}
export function weeklyCsv(data: GpuDataset, weeks: string[]): string {
  return ['week_start,week_end,gpu,baseline_usd_per_gpu_hour,price_usd_per_gpu_hour,change_pct,source_url', ...weeks.flatMap(end => data.series.map(series => {
    const week = weeklyChange(series.observations, end);
    return [week.start, end, series.gpu, week.baseline ?? '', week.price ?? '', week.change ?? '', series.source_url].join(',');
  }))].join('\n');
}
