# Refreshing the dashboard

Run these commands from the project folder. The preview remains at http://127.0.0.1:5178; reload the page after a successful refresh.

The GitHub checkout includes a ready-to-run dashboard snapshot. `scripts/run_dashboard.sh` serves that snapshot without rebuilding research data. The refresh commands below require the separate retained source archive, reviewed collection outputs and market-data inputs. They cannot reconstruct missing broker PDFs from the bundled snapshot alone. Git excludes raw downloads and local archives; source hashes and evidence checks remain enforced when those inputs are available.

Rebuild from reviewed, retained data without network requests:

```sh
python3 scripts/refresh_dashboard.py
```

Refresh public prices and check the last seven days for new public Morningstar PDFs:

```sh
python3 scripts/refresh_dashboard.py --prices --discover-days 7
```

`--prices` uses today's UTC cutoff by default. `--as-of YYYY-MM-DD` sets an explicit cutoff. Changing the cutoff requires a price refresh, because prices and EPS must share the same split units. Offline rebuilds retain the existing cutoff. `--replay-prices` reparses the latest retained price downloads, useful for retrying after a later build failure without downloading the same prices again. Discovery accepts 0–31 days and is optional.

The command indexes retained sources, merges reviewed forecasts, rebuilds annual EPS models and forecast/result comparisons, calculates the monthly gap map, backtest readiness and exact field/date handoff, then builds the browser app. It does not start a scheduler or buy access.

## Preserving vintages

Each run creates `data/refresh/<UTC timestamp>/` with:

- `before/` and `after/`: generated datasets and the built browser app.
- `inputs/`: original collection CSV/JSON metadata, the archive database, basis evidence rules and calculation/build source files.
- `run.json`: cutoff, input hashes, commands, outcome, latest price dates and discovery counts.
- `commands.log`: complete build and collection output.

Original report and price downloads remain in their existing retained source directories. Their hashes and paths travel with the observations and source catalog. A reprint does not become a newer model merely because its publication date is later.

A failed build, incomplete price refresh, lost historical price sessions or changed collection input triggers restoration of the prior generated files. Production assets are built in the run directory and published after validation. Concurrent refresh commands are rejected. An operating-system kill or power loss can prevent automatic restoration; the `before/` archive remains available for recovery. Raw downloads and request logs are retained even after a failed run.

## New reports need review

Discovery checks Firstrade's public Morningstar distributor IDs for Broadcom, Alphabet, NVIDIA, Micron, Sandisk, ASML and Apple. It does not cover the Korean broker archives or BESI. BESI prices refresh with the full universe, while its dated IEX, LSEG and Morningstar forecasts require the documented collection routes and review. Failed requests and missing dates are recorded, and a PDF is retained only when its content passes the PDF header check. A source URL that changes content produces a separate hash-addressed artifact.

New files go to `data/inbox/morningstar/`. They are excluded from the forecast merger. Discovery alone cannot update EPS in the chart.

To import a report, review its printed date, numerical model date, named analyst, actual/forecast columns, fiscal years, currency, EPS definition and split basis. Add reviewed rows and source metadata to a collection folder using the established `observations.csv` and `manifest.csv` formats, then refresh. Preserve source pages, hashes and raw labels. Explicit evidence is required to connect different EPS labels.

The run summary separates new PDFs awaiting review from the number of reviewed forecasts in the app. A successful price refresh is not a claim that the earnings archive is current or complete.

## Reviewed evidence policies

The input archive now includes `data/market/observation_exclusions.json` and `data/market/availability_evidence.json` when present. The first records source-hash-scoped extraction exclusions without modifying original collections. The second binds an original PDF, identical archive replay and the retained CDX timestamp/content digest. `scripts/availability.py` validates the evidence before the panel can expose verified availability bounds. A mismatched file, index timestamp, URL or digest fails the rebuild.

Ordinary charts preserve explicitly labelled report-date reconstruction. Strict charts use a model only after its verified availability bound, conservatively the next UTC day after an exact archived capture. An archive proves the contents were available by its capture; it does not establish the first publication instant. Reprints retain the numerical model's age.

`data/market/ensemble_compatibility.json` scopes reviewed earnings equivalence to source hashes, model dates, authors, fiscal targets and exact values. New unreviewed snapshots cannot inherit that approval. Named coauthor teams remain one estimator; a firm contributes at most one model per date.

`data/market/model_date_evidence.json` records complete EPS vectors repeated in later originals. Both source hashes and both complete vectors must match before the earlier model date is applied. The raw collection stays unchanged, while merged observations preserve the original date and review evidence. Partial target overlap cannot backdate a larger newer model.

The refresh also produces `data/market/delivery_report.json` and `data/market/missing_data_dates.csv`. These report exact retained-session gaps, current model ages, compatibility groups and missing evaluation prerequisites. They are covered by the same rollback/archive workflow. Run `node scripts/build_delivery_report.mjs` to regenerate only this diagnostic from the existing bundle.

The refresh still waits for source inputs to be stable. Collectors should finish or freeze their reviewed CSV/JSON files before this command runs. No Grok response, inbox report or quarantined source enters usable EPS without original-source review.

Reviewed daily-close supplements are configured in `data/market/price_supplements.json`. Original source hashes and exact dated values are checked by `scripts/apply_price_supplements.py` before price validation. Its four current entries verify or repair two Korean September 10 closes and the Amsterdam ASML/BESI September 7 closes. Existing base-feed observations are never overwritten when they disagree. The two older Korean bars stay unfilled pending their share-adjustment convention. See [price supplement evidence](research/PRICE_SUPPLEMENTS.md).
