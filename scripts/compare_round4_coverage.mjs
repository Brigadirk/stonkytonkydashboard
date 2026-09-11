// Replay both retained bundles with identical settings. Counts are unique price
// dates across separate series, never a stitched consensus or one trading model.
import { readFileSync, writeFileSync } from 'node:fs';
import { calculate, bandValue } from '../web/src/engine.ts';

const root = new URL('../', import.meta.url);
const read = path => JSON.parse(readFileSync(new URL(path, root), 'utf8'));
const before = read('data/market/round4_baseline_dashboard.json');
const after = read('web/public/data/dashboard.json');
function coverage(data) {
  return data.companies.map(company => {
    const valid = new Set(), bands = new Set();
    const series = company.series.map(series => {
      const points = calculate(company, series, { asOf: data.cutoff, window: 365, maxAge: 180, strict: false });
      for (const point of points) {
        if (point.multiple !== null) valid.add(point.date);
        if (bandValue(point, 0, 'price') !== null) bands.add(point.date);
      }
      const last = points.at(-1);
      return { id: series.id, label: series.label, valid_pe_days: points.filter(p => p.multiple !== null).length, band_days: points.filter(p => bandValue(p, 0, 'price') !== null).length, latest_pe: last?.multiple ?? null, latest_median: last?.median ?? null };
    });
    return { id: company.id, price_days: company.prices.length, eligible_eps_observations: company.series.reduce((n,s) => n+s.snapshots.reduce((n,s) => n+s.estimates.length,0),0), model_snapshots: company.series.reduce((n,s) => n+s.snapshots.length,0), unique_valid_pe_days: valid.size, unique_band_days: bands.size, first_valid_pe_date: [...valid].sort()[0] ?? null, last_valid_pe_date: [...valid].sort().at(-1) ?? null, series };
  });
}
const oldCoverage = coverage(before), newCoverage = coverage(after);
const result = { as_of: after.cutoff, window_days: 365, max_age_days: 180, interpretation: 'Unique usable dates across separate analyst/basis/consensus series. These are archive coverage counts, not a pooled or continuous series.', companies: newCoverage.map(after => ({ id: after.id, before: oldCoverage.find(c => c.id === after.id), after })) };
writeFileSync(new URL('data/market/round4_coverage_comparison.json', root), JSON.stringify(result, null, 2)+'\n');
console.log(result.companies.map(c => ({ company: c.id, eps_before: c.before.eligible_eps_observations, eps_after: c.after.eligible_eps_observations, band_dates_before: c.before.unique_band_days, band_dates_after: c.after.unique_band_days, latest_series_with_bands: c.after.series.filter(s => s.latest_pe !== null && s.latest_median !== null).length })));
