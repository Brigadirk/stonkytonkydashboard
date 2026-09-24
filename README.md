# AI valuation dashboard

See also [StonkyTonkyWonky](stonkytonkywonky/README.md): a separate cheap-to-self screen for 164 stocks on consensus estimates, recorded nightly.

Forward earnings valuation screener for ten stocks. Requires Node.js 22.18 or newer and npm.

```sh
git clone https://github.com/Brigadirk/stonkytonkydashboard.git
cd stonkytonkydashboard
./scripts/run_dashboard.sh
```

Open http://127.0.0.1:5178. The launcher installs the frontend dependencies, builds the app and serves the included September 10, 2026 research snapshot. It does not download or refresh market data. For development, run `npm run dev --prefix web` after installing dependencies.

The repository contains the application, tests, collection scripts, research notes and derived dashboard dataset. The 1.8 GB local research archive, original broker PDFs, raw downloads and historical build copies are excluded. Source URLs, hashes and evidence paths remain in the snapshot; local evidence paths require that separate archive. The collection and refresh documentation describes the original workflow and its additional inputs.

Run the frontend and dataset checks with `npm test --prefix web`. Python collection tests use `python3 -m unittest discover -s tests`; install `requirements.txt` in a virtual environment first. Browser checks use `npm exec --prefix web -- playwright install chromium`, then `npm run test:browser --prefix web` after a production build.

The app opens in a simple stock view: the last closing price, a dated one-year target with percentage change, and one chart. Choose 90 days, 180 days or one year for the entry comparison: today's price versus its usual valuation and the historical entry bands. Future targets always use a separate 365-day valuation reference, so changing the entry window leaves them unchanged. The median and all ±1, ±1.5 and ±2σ targets appear together, each with its price and percentage change. Click any target to highlight its projected band and marker and update the large target; the other levels stay visible. The main price chart is 640 pixels tall and fits the vertical axis to the displayed prices, bands and targets instead of forcing a zero baseline. Move horizontally anywhere in the plot to see a vertical guide, an exact calendar-date label, that date's closing price and its forward P/E using the estimate eligible then. Historical dates without a recorded closing price are removed from the horizontal axis, including weekends, local holidays and missing price sessions. The historical cursor moves through recorded closes only. A day with a close but missing earnings remains visible and shows "Forward P/E unavailable". Future projection dates remain on the chart. Future dates show the selected projected valuation and its forward P/E, with the anniversary labelled as the one-year target. On touch screens, tap the chart to show the date and value. Chart history selects 6 months, 1, 2, 3 or 5 years independently of entry and target calculations. The same selection applies in All stocks and Advanced and survives reload. All stocks gives the same comparison across the ten names. The larger text and controls are preserved.

Advanced opens the research workspace: individual or combined estimators, historical dates, custom windows, every ±1/±1.5/±2 band, sources, data coverage, accuracy evidence and exports. The simple view uses the same calculation and selected model: forecasts for the earnings year after the target date, valued at historical forward-P/E levels.

The ten-stock dataset contains 13,928 daily closes, 1,173 eligible annual EPS observations in 350 model snapshots and 74 separate earnings series. The memory collection fills missing Micron and Sandisk revisions and extends the older SK hynix and Samsung histories. All ten default models support current bands and one-year targets at the September 10 cutoff. NVIDIA's reviewed reported-diluted group combines Morningstar and Bernstein: 56 of its 251 one-year reference sessions have both firms, beginning June 18. Historical availability remains a dated-report reconstruction. Other unresolved definitions stay separate. The larger interface sizing is preserved.

[Latest memory collection and remaining gaps](docs/research/MEMORY_COVERAGE_ROUND12.md) · [All-stock access handoff](docs/research/ESTIMATOR_ROUND11.md) · [One-year projections and future price tracking](docs/PROJECTIONS.md) · [Usage and calculations](docs/DASHBOARD.md) · [Initial ensemble delivery](docs/research/ENSEMBLE_COLLECTION_DELIVERY.md) · [Missing fields and dates](data/market/missing_data_dates.csv)

All stocks shows current prices and one-year targets. Model dates, ages and reference coverage are under Advanced. The future chart area extends all valuation bands to the dated one-year targets. Each day uses the latest frozen annual forecasts to calculate earnings for the twelve months after that day, multiplied by the fixed 365-day historical P/E levels. Missing forecast intervals leave gaps. The actual-price line stops at the origin. No live feed is connected. Projection exports preserve inputs for later tracking against observed prices. The ensemble audit shows contributors, exclusions, age ranges, disagreement and membership changes. Published consensus and coauthor reprints do not receive extra analyst votes. Mean/median aggregation happens before historical P/E and band calculation. No estimates are invented or carried across unsupported dates.

The archive retains 396 original broker PDFs and 2,420 extracted observations, plus source-page images, articles and issuer documents. Forty-eight initial issuer EPS outcomes support eight illustrative fixed-horizon comparison pairs across five company-years. Sample sizes, horizons and definitions are visible; no analyst ranking is justified. The Korean revenue pilot contains 22 forecast/result pairs. The [backtest protocol](docs/BACKTEST_PROTOCOL.md) remains data-limited and no strategy returns are presented.

Refresh reviewed data offline with `python3 scripts/refresh_dashboard.py`, or include public prices with `--prices`. Every refresh validates source hashes, archives inputs and previous/resulting datasets, and restores generated files on failure. [Refresh instructions](docs/REFRESH.md). No paid feed is connected and no purchase was made.

## Research universe

| Company | Research listing | Price and EPS currency |
|---|---|---|
| Broadcom | NASDAQ: AVGO | USD |
| Alphabet, Google | NASDAQ: GOOGL, Class A | USD |
| NVIDIA | NASDAQ: NVDA | USD |
| SK hynix | KRX: 000660, common shares | KRW |
| Samsung Electronics | KRX: 005930, common shares | KRW |
| Micron Technology | NASDAQ: MU | USD |
| Sandisk | NASDAQ: SNDK | USD |
| ASML | Euronext Amsterdam: ASML | EUR |
| Apple | NASDAQ: AAPL | USD |
| BE Semiconductor Industries | Euronext Amsterdam: BESI | EUR |

These are research conventions, not a record of holdings. Alphabet's GOOG listing can be added separately. A US-listed ASML price requires a currency-compatible EPS series. "Micon" has been interpreted as Micron and "Samsung" as Samsung Electronics.

Listing references: [Alphabet filing](https://www.abc.xyz/assets/51/e1/bf43f01041f6a8882a29d7e89cae/goog-10-q-q1-2025.pdf), [Samsung listing information](https://www.samsung.com/global/ir/stock-information/listing-Info/), [ASML shares and trading currencies](https://www.asml.com/en/en/investors/shares). The company audits below provide the other issuer and broker references.

## Documents and data

- [Build plan](docs/BUILD_PLAN.md)
- [Five-year analyst shortlist and current findings](docs/research/FIVE_YEAR_SHORTLIST.md)
- [Five-year analyst evaluation rules](docs/ANALYST_EVALUATION.md)
- [Five-year U.S. and ASML analyst evidence](docs/research/FIVE_YEAR_US_ASML_ANALYSTS.md)
- [Five-year memory analyst evidence](docs/research/FIVE_YEAR_MEMORY_ANALYSTS.md)
- [Historical data sample specification](docs/DATA_SAMPLE_REQUEST.md)
- [Eight-stock source map](docs/research/SOURCE_MAP.md)
- [Broadcom, Alphabet, NVIDIA and ASML audit](docs/research/US_ASML_Forecaster_Audit.md)
- [SK hynix, Samsung, Micron and Sandisk audit](docs/research/Memory_Forecaster_Audit.md)
- [Data access and subscription findings](docs/research/DATA_ACCESS.md)
- [Machine-readable watchlist](data/universe.csv)
- [Analyst candidate register](data/analyst_candidates.csv), 35 company–analyst pairs covering 23 people; accuracy ranks remain unassigned
- [Checked forecast samples](data/forecast_samples.csv), 16 observations from four reports dated in 2021 and 2026
- [Source document manifest and checksums](data/source_manifest.csv)

## Initial source audit

For each company, identify candidate earnings forecasters, establish which dated numerical forecasts can be retrieved, record the latest accessible forecast samples, and state the gaps and any known access cost. Coverage is evidence of relevance; forecast accuracy requires a separate historical evaluation.

Preserve publication date, target fiscal period, accounting basis, currency, source and author for each estimate. Store broker forecasts, consensus estimates, management guidance and model scenarios as different observations. A price target is not an earnings forecast. An older report demonstrates historical access, not that its figures are current.

The sample CSV contains FY2026 and FY2027 EPS and revenue from Young-gun Kim's 7 September 2026 reports on SK hynix and Samsung Electronics, plus FY2021 and FY2022 forecasts from his and Sunwoo Kim's 27 October 2021 SK hynix reports. The original PDFs are retained in `data/source_reports`. Their stated report dates are recorded, but the exact original availability timestamps are unknown and left blank. EPS share bases remain unspecified or unreconciled as recorded per row. These samples have been checked against the report tables; they are not a continuous five-year dataset or an evaluated forecast history.

The existing Positioning Lab at `/Users/dirk/Documents/TheLab/Documents/Trading/PositioningLab` may supply reusable components. This project is separate; no code has been moved from Positioning Lab.
