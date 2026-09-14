import { useEffect, useMemo, useRef, useState } from 'react';
import * as Plotly from 'plotly.js-basic-dist-min';
import type { Data, Layout } from 'plotly.js';
import { GPU_COLORS, GPU_TYPES, ORNN_DOCS, amsterdamDate, dailyGrid, daysApart, parseGpuDataset, shiftDay, weekEnds, weeklyChange, weeklyCsv } from './gpuPrices';
import type { GpuDataset, GpuType } from './gpuPrices';
import GpuDetails from './GpuDetails';
import { GPU_PROFILES } from './gpuProfiles';
import './gpuPrices.css';

const shortDate = (date: string) => new Date(`${date}T12:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
const longDate = (date: string) => new Date(`${date}T12:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
const percent = (value: number | null) => value === null ? '—' : `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
const direction = (value: number | null) => value === null ? 'missing' : value > 0 ? 'up' : value < 0 ? 'down' : 'flat';
const money = (value: number | null) => value === null ? '—' : `$${value.toFixed(3)}`;

function GpuChart({ data, selected, mode, range, weeks }: {
  data: GpuDataset; selected: GpuType[]; mode: 'price' | 'weekly'; range: number; weeks: string[];
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    let cancelled = false;
    const latest = data.series.map(series => series.observations.at(-1)!.date).sort().at(-1)!;
    const earliest = data.series.map(series => series.observations[0].date).sort()[0];
    const start = range ? shiftDay(latest, -(range - 1)) : earliest;
    const visibleWeeks = range && weeks.length ? weeks.filter(end => end >= shiftDay(weeks.at(-1)!, -(range - 1))) : weeks;
    const traces: Data[] = data.series.filter(series => selected.includes(series.gpu)).map(series => {
      const grid = dailyGrid(series.observations, start, latest);
      return mode === 'price' ? {
        type: 'scatter', mode: 'lines', name: series.gpu, x: grid.dates, y: grid.prices,
        line: { color: GPU_COLORS[series.gpu], width: 2.7 }, connectgaps: false,
        hovertemplate: '%{x|%d %b %Y}<br>$%{y:.3f} / GPU-hour<extra>%{fullData.name}</extra>',
      } : {
        type: 'bar', name: series.gpu, x: visibleWeeks, y: visibleWeeks.map(end => weeklyChange(series.observations, end).change),
        marker: { color: GPU_COLORS[series.gpu] },
        hovertemplate: 'Week ending %{x|%d %b %Y}<br>%{y:+.1f}% vs prior Friday<extra>%{fullData.name}</extra>',
      };
    });
    const layout: Partial<Layout> = {
      autosize: true, height: 350, margin: { l: 62, r: 18, t: 18, b: 45 },
      paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
      font: { family: 'DM Sans, sans-serif', color: '#6a7d70', size: 12 },
      xaxis: { type: 'date', tickformat: '%d %b', nticks: 7, showgrid: false, zeroline: false, fixedrange: true },
      yaxis: { tickprefix: mode === 'price' ? '$' : '', ticksuffix: mode === 'weekly' ? '%' : '',
        gridcolor: '#e7ece3', zerolinecolor: '#bccbbf', rangemode: mode === 'price' ? 'tozero' : 'normal', fixedrange: true },
      barmode: 'group', bargap: .26, showlegend: false, hovermode: mode === 'price' ? 'x unified' : 'closest',
      hoverlabel: { bgcolor: '#fffefa', bordercolor: '#d3dfd4', font: { color: '#233d36', size: 13 } },
    };
    setError(false);
    const drawn = Plotly.react(element, traces, layout, { displayModeBar: false, responsive: true });
    const observer = new ResizeObserver(() => { if (!cancelled && element.isConnected) void drawn.then(() => { if (!cancelled) Plotly.Plots.resize(element); }).catch(() => {}); });
    observer.observe(element);
    void drawn.catch(() => { if (!cancelled) setError(true); });
    return () => { cancelled = true; observer.disconnect(); };
  }, [data, selected, mode, range, weeks]);
  useEffect(() => { const element = ref.current; return () => { if (element) Plotly.purge(element); }; }, []);
  return <>{error && <p role="alert" className="gpu-notice">The chart could not be drawn. The weekly table below has the values.</p>}<div ref={ref} className="gpu-plot" data-testid="gpu-chart" role="img" aria-label={mode === 'price' ? 'Daily GPU rental prices in US dollars per GPU-hour' : 'Weekly GPU rental price changes in percent'} /></>;
}

export default function GpuPrices() {
  const [data, setData] = useState<GpuDataset | null>(null), [error, setError] = useState('');
  const [selected, setSelected] = useState<GpuType[]>([...GPU_TYPES]);
  const [profile, setProfile] = useState<GpuType | null>(null);
  const [mode, setMode] = useState<'price' | 'weekly'>('price'), [range, setRange] = useState(0), [week, setWeek] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    fetch('/data/gpu-prices.json', { signal: controller.signal, cache: 'no-store' })
      .then(response => { if (!response.ok) throw new Error(`GPU data returned HTTP ${response.status}`); return response.json(); })
      .then(value => setData(parseGpuDataset(value)))
      .catch(cause => { if (!controller.signal.aborted) setError(String(cause)); });
    return () => controller.abort();
  }, []);
  const weeks = useMemo(() => data ? weekEnds(data) : [], [data]);
  if (error) return <section className="card gpu-error" role="alert"><h2>GPU prices are unavailable</h2><p>The saved GPU dataset could not be opened. The stock views are still available.</p><p>{error}</p><a href="https://data.ornn.com/markets" target="_blank" rel="noreferrer">View prices at Ornn ↗</a><button onClick={() => location.reload()}>Try again</button></section>;
  if (!data) return <section className="card gpu-error" role="status">Loading GPU rental prices…</section>;
  const activeWeek = weeks.includes(week) ? week : weeks.at(-1) || '';
  const latestDates = data.series.map(series => series.observations.at(-1)!.date).sort();
  const today = amsterdamDate(new Date());
  const stale = data.series.filter(series => daysApart(today, series.observations.at(-1)!.date) > 3);
  const missing = activeWeek ? data.series.filter(series => weeklyChange(series.observations, activeWeek).change === null) : data.series;
  const toggle = (gpu: GpuType) => setSelected(current => current.includes(gpu) ? current.filter(value => value !== gpu) : [...current, gpu]);
  const exportCsv = () => {
    const url = URL.createObjectURL(new Blob([weeklyCsv(data, weeks)], { type: 'text/csv' }));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = `ornn-gpu-weekly-${activeWeek || 'history'}.csv`; anchor.click(); URL.revokeObjectURL(url);
  };
  return <div className="gpu-workspace">
    <div className="gpu-intro"><p>Follow the cost of compute.<br/><span>Daily rental prices and weekly moves, with older GPUs first.</span></p><a className="gpu-source-badge" href="https://data.ornn.com/markets" target="_blank" rel="noreferrer"><span className="gpu-status-dot"/> ORNN INDEX <span>↗</span></a></div>
    {stale.length > 0 && <p className="gpu-notice" role="status">Saved data is more than three days old for {stale.map(series => series.gpu).join(', ')}. See the collection dates under Data & method.</p>}
    {missing.length > 0 && <p className="gpu-notice" role="status">{activeWeek ? `A Friday comparison is missing for ${missing.map(series => series.gpu).join(', ')}. Missing changes are shown as —.` : 'There is not yet enough history for a complete Friday-to-Friday comparison.'}</p>}
    <div className="gpu-week-control"><div><span className="gpu-kicker">THE WEEK IN COMPUTE</span><h2>{activeWeek ? `${shortDate(shiftDay(activeWeek, -7))} — ${longDate(activeWeek)}` : 'Weekly comparison unavailable'}</h2></div><label>Week ending<select aria-label="GPU week ending" value={activeWeek} onChange={event => setWeek(event.target.value)} disabled={!weeks.length}>{[...weeks].reverse().map(end => <option key={end} value={end}>{longDate(end)}</option>)}</select></label></div>
    <div className="gpu-card-hint"><span>Friday prices · USD per GPU-hour</span><span>Select cards to compare in the chart</span></div>
    <div className="gpu-cards">{data.series.map((series, index) => {
      const result = activeWeek ? weeklyChange(series.observations, activeWeek) : null;
      return <div key={series.gpu} className="gpu-card-tile" style={{ '--gpu-color': GPU_COLORS[series.gpu] } as React.CSSProperties}><button className={`gpu-price-card ${selected.includes(series.gpu) ? 'is-selected' : ''}`} aria-label={`Compare ${series.gpu}`} aria-pressed={selected.includes(series.gpu)} onClick={() => toggle(series.gpu)}>
        <span className="gpu-card-name"><i/>{series.gpu}<span className="gpu-check" aria-hidden="true">{selected.includes(series.gpu) ? '✓' : '+'}</span></span>
        <strong>{money(result?.price ?? null)}</strong>
        <span className={`gpu-change ${direction(result?.change ?? null)}`}>{percent(result?.change ?? null)} <small>vs prior Friday</small></span>
        <span className="gpu-card-tag">{index < 2 ? 'OLDER GPU WATCH' : 'ORNN DAILY INDEX'}</span>
      </button><button className="gpu-info-button" aria-label={`About ${series.gpu}`} aria-haspopup="dialog" title={`${GPU_PROFILES[series.gpu].architecture} · introduced ${GPU_PROFILES[series.gpu].introduced.slice(0, 4)} · Open model details`} onClick={() => setProfile(series.gpu)}>GPU details <span aria-hidden="true">↗</span></button></div>;
    })}</div>
    <section className="card gpu-chart-card">
      <div className="gpu-chart-heading"><div><span className="gpu-kicker">RENTAL MARKET</span><h2>{mode === 'price' ? 'Rental prices over time' : 'Weekly price changes'}</h2><p>{mode === 'price' ? 'Daily observations · USD per GPU-hour' : 'Friday-to-Friday change · percent'}</p></div><div className="gpu-segmented" aria-label="GPU chart view">{(['price', 'weekly'] as const).map(value => <button key={value} aria-pressed={mode === value} className={mode === value ? 'selected' : ''} onClick={() => setMode(value)}>{value === 'price' ? 'Price history' : 'Weekly change'}</button>)}</div></div>
      <div className="gpu-chart-controls"><div className="gpu-presets"><button onClick={() => setSelected([...GPU_TYPES])}>All GPUs</button><button onClick={() => setSelected(['A100 SXM4', 'H100 SXM'])}>Older GPUs only</button></div><div className="gpu-range" aria-label="GPU chart range">{[[28, '4 weeks'], [0, 'All history']].map(([value, label]) => <button key={value} aria-pressed={range === value} className={range === value ? 'selected' : ''} onClick={() => setRange(Number(value))}>{label}</button>)}</div></div>
      <div className="gpu-legend">{GPU_TYPES.filter(gpu => selected.includes(gpu)).map(gpu => <span key={gpu}><i style={{ background: GPU_COLORS[gpu] }}/>{gpu}</span>)}</div>
      {selected.length ? <GpuChart data={data} selected={selected} mode={mode} range={range} weeks={weeks}/> : <div className="gpu-empty-chart">Select a GPU card above to show its history.</div>}
      <div className="gpu-chart-note"><span>Daily data through {latestDates[0] === latestDates.at(-1) ? longDate(latestDates[0]) : `${shortDate(latestDates[0])}–${longDate(latestDates.at(-1)!)}`} · saved {longDate(amsterdamDate(data.collected_at))}</span><a href="#gpu-data-method">Data & method ↓</a></div>
    </section>
    <section className="card gpu-weekly-card"><div className="gpu-table-heading"><div><span className="gpu-kicker">WEEK BY WEEK</span><h2>Which GPU prices are moving?</h2><p>Change from the prior Friday. Select a week to see its prices above.</p></div><button className="gpu-export" onClick={exportCsv}>Export weekly CSV ↓</button></div>
      <div className="gpu-table-scroll" tabIndex={0} role="region" aria-label="Weekly GPU price changes"><table className="gpu-weekly-table"><caption>Friday-to-Friday changes (%) · — means an exact comparison date is missing</caption><thead><tr><th scope="col">Week ending</th>{GPU_TYPES.map(gpu => <th scope="col" key={gpu}><i style={{ background: GPU_COLORS[gpu] }}/>{gpu}</th>)}</tr></thead><tbody>{[...weeks].reverse().map(end => <tr key={end} className={end === activeWeek ? 'gpu-active-week' : ''}><th scope="row"><button onClick={() => setWeek(end)} aria-pressed={end === activeWeek} aria-label={`View week ending ${longDate(end)}`}>{shortDate(end)}<span>{end.slice(0, 4)}</span></button></th>{data.series.map(series => {
        const result = weeklyChange(series.observations, end);
        return <td key={series.gpu}><span className={`gpu-heat ${direction(result.change)}`} style={{ '--gpu-intensity': result.change === null ? 0 : Math.min(.06 + Math.abs(result.change) / 150, .25) } as React.CSSProperties} title={`${series.gpu}: ${money(result.baseline)} on ${result.start} → ${money(result.price)} on ${end}`}>{percent(result.change)}</span></td>;
      })}</tr>)}</tbody></table></div>
    </section>
    <details className="card gpu-method" id="gpu-data-method"><summary>Data & method <span>Ornn · public daily index</span></summary><div className="gpu-method-grid"><div><h3>What the index measures</h3><p>Ornn measures prices paid for active, on-demand GPU rentals. Values are in US dollars per GPU-hour and cover its global index.</p><p>A100 and H100 are listed first to help track older GPUs. Rental prices reflect both supply and demand; prices alone do not measure utilization or prove continued demand.</p><div className="gpu-source-links"><a href="https://data.ornn.com/methodology" target="_blank" rel="noreferrer">Ornn methodology ↗</a><a href={ORNN_DOCS} target="_blank" rel="noreferrer">API documentation ↗</a></div></div><div><h3>How the comparison works</h3><p>Weekly change = (Friday price ÷ prior Friday price − 1) × 100. We use exact dates, without interpolation. Daily timestamps are grouped in Europe/Amsterdam. The current day and an unfinished Friday are excluded.</p><p>The free API supplies three months of daily history. This view uses a saved dataset, collected {new Date(data.collected_at).toLocaleString('en-GB', { timeZone: 'Europe/Amsterdam' })} (Amsterdam). It does not refresh from Ornn when you open the page.</p><div className="gpu-source-links"><a href="/data/gpu-prices.json" download>Download saved data ↓</a><a href="https://api.ornnai.com/api/daily-index/all" target="_blank" rel="noreferrer">Latest prices API ↗</a></div></div></div><div className="gpu-provenance">{data.series.map(series => <div key={series.gpu}><a href={series.source_url} target="_blank" rel="noreferrer">{series.gpu} history ↗</a><span>{series.observations.length} days · {shortDate(series.observations[0].date)}–{longDate(series.observations.at(-1)!.date)}</span></div>)}</div></details>
    {profile && <GpuDetails gpu={profile} onClose={() => setProfile(null)}/>}
  </div>;
}
