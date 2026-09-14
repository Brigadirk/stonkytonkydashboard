# GPU rental prices

Open **GPU prices** in the Forward dashboard, in either Simple or Advanced view.
The direct view uses `?view=gpu`. The dataset is separate from equity prices,
earnings forecasts, and portfolio records.

## Use the view

- The five cards show each GPU's price on the selected Friday and its change
  from the prior Friday. Select a card to include or remove its chart series.
- **Price history** shows daily prices in USD per GPU-hour. **Weekly change**
  shows Friday-to-Friday percentage changes as grouped bars.
- **Older GPUs only** selects A100 SXM4 and H100 SXM. **All GPUs** restores all
  five types. The range control selects four weeks or the full saved history.
- Select a week from the menu or the weekly table to change the price cards.
  The table always compares all five types. Its colors mean price increases
  and decreases; they are not investment ratings.
- **Export weekly CSV** includes exact baseline/end dates, prices, unrounded
  percentage changes, and source URLs for all five types and all displayed weeks.
- **Data & method** provides source links, collection time, coverage dates,
  calculation rules, and a download of the saved JSON dataset.
- **GPU details** on each card opens a model profile. A short hover hint shows
  the architecture and introduction year. The full panel also works with touch
  and keyboard controls; Escape or the close button returns to the chart.

## GPU model profiles

Profiles record the model's **introduction year**, not the manufacture date of
an individual rented GPU. H200 is explicitly marked as announced in 2023 with
systems scheduled for 2024. Model context comes from these NVIDIA sources,
checked on 14 September 2026:

| Ornn type | Architecture | Introduction | Manufacturer source |
|---|---|---|---|
| A100 SXM4 | Ampere | May 2020 | [A100 launch](https://nvidianews.nvidia.com/news/nvidias-new-ampere-data-center-gpu-in-full-production) |
| H100 SXM | Hopper | March 2022 | [Hopper and H100 launch](https://nvidianews.nvidia.com/news/nvidia-announces-hopper-architecture-the-next-generation-of-accelerated-computing) |
| H200 | Hopper | November 2023 | [H200 launch and planned availability](https://nvidianews.nvidia.com/news/nvidia-supercharges-hopper-the-worlds-leading-ai-computing-platform) |
| B200 | Blackwell | March 2024 | [Blackwell launch](https://nvidianews.nvidia.com/news/nvidia-blackwell-platform-arrives-to-power-a-new-era-of-computing) |
| RTX 5090 | Blackwell | January 2025 | [GeForce RTX 50 launch](https://nvidianews.nvidia.com/news/nvidia-blackwell-geforce-rtx-50-series-opens-new-world-of-ai-computer-graphics) |

The reviewed sources do not give a fixed physical lifetime or a hardware
retirement date for these models. The panels therefore mark hardware end of
life as **unknown**, and do not assign an expected useful life in years.
Workload, power cost, maintenance, and support are operating considerations,
not a manufacturer forecast of useful life.

NVIDIA's [CUDA architecture support matrix](https://docs.nvidia.com/datacenter/tesla/drivers/cuda-toolkit-driver-and-architecture-matrix.html)
lists ongoing CUDA toolkit and driver support for Ampere, Hopper, and Blackwell
at the review date. A software driver branch's end date must not be presented as
a GPU hardware retirement date. The model profiles are manually maintained in
`web/src/gpuProfiles.ts`; the Ornn price refresh does not update these facts.

## Source and access

Ornn's index measures prices paid for active, on-demand GPU rentals across its
global contributor network, in USD per GPU-hour. Its daily series aggregates
hourly values. It is not a provider's list price. See the
[index definition](https://data.ornn.com/docs/price-index) and
[methodology](https://data.ornn.com/methodology).

The public API needs no account or API key. As verified on **14 September 2026**,
it supplies three months of daily history for these five models:

| GPU | Public daily history JSON |
|---|---|
| A100 SXM4 | [A100 SXM4 history](https://api.ornnai.com/api/gpu/A100%20SXM4/index-history) |
| H100 SXM | [H100 SXM history](https://api.ornnai.com/api/gpu/H100%20SXM/index-history) |
| H200 | [H200 history](https://api.ornnai.com/api/gpu/H200/index-history) |
| B200 | [B200 history](https://api.ornnai.com/api/gpu/B200/index-history) |
| RTX 5090 | [RTX 5090 history](https://api.ornnai.com/api/gpu/RTX%205090/index-history) |

Other entry points:

- [Ornn charts](https://data.ornn.com/markets)
- [Latest daily prices for all public types](https://api.ornnai.com/api/daily-index/all)
- [Public history API documentation](https://data.ornn.com/docs/api-reference/historical-prices/get-a-public-daily-series)
- [API documentation index](https://data.ornn.com/docs)

GPU names are case-sensitive. Encode spaces as `%20` in URL paths. For example:

```sh
curl --fail --show-error --silent \
  'https://api.ornnai.com/api/gpu/H100%20SXM/index-history' \
  --output /tmp/ornn-h100-history.json
```

The response has `success`, `gpu_type`, `access`, and a `data` array. Each row
has an ISO timestamp in `timestamp` and a numeric rental price in `index_value`.
The current access label is `public-3mo`. Use the history endpoint for weekly
comparisons; the latest-prices endpoint alone has no historical baseline.

## Refresh the dashboard dataset

Requires **Node.js 22.18+**. No extra library or API key is needed. Run this from
the repository root:

```sh
npm run data:gpu --prefix web
```

Then reload the GPU tab. The dev server serves the changed JSON immediately.
If serving a production build, rebuild and publish the updated `web/dist`
directory with the usual app procedure:

```sh
npm run build --prefix web
```

The script is `scripts/collect_gpu_prices.mjs`, relative to this app. It fetches
the five public series, with a 20-second timeout per request. It checks model
identity, explicit time zones, unique daily dates, and finite positive prices.
It writes the dataset only after all five series pass. A failed refresh exits
with a nonzero status and preserves the previous dashboard dataset.

Opening the dashboard does **not** contact Ornn. It reads the saved public JSON.
The browser therefore does not depend on Ornn allowing cross-origin requests.
This collector is a separate manual refresh. It has no scheduled refresh job.

Files produced inside this app:

| File | Purpose |
|---|---|
| `web/public/data/gpu-prices.json` | Current normalized dataset loaded by the browser |
| `data/collection/ornn/<run-id>/<GPU>.json` | Exact response bytes for each public history request |
| `data/collection/ornn/<run-id>/manifest.json` | Dataset copy with source URL, retrieval time, access label and SHA-256 for each response |
| `data/collection/ornn/<run-id>/error.txt` | Failure details, if the refresh fails |

The public snapshot contains only Ornn observations and provenance. It has no
portfolio positions, provider credentials, equity forecasts, or model outputs.
Each successful refresh replaces its trailing window. Old raw responses remain
in the collection archive; the dashboard does not yet merge them into a longer
series or claim access to Ornn's full paid history.

The first collection saved **460 daily observations**, 92 per type, from
**14 June through 13 September 2026**. The latest complete weekly comparison
ends **11 September 2026**. The exact collection time is in the JSON manifest.

## Dates, calculations, and gaps

Daily timestamps are retained unchanged and also mapped to calendar dates in
**Europe/Amsterdam**, to match the weekly report's date convention. This is a
local display convention, not a claim about Ornn's own daily boundary.
Observations on the current Amsterdam day, or after collection time, are
excluded because the current daily average can still change.

```text
weekly change (%) = (price on Friday / price on prior Friday - 1) × 100
```

Friday is complete from Saturday 00:00 in Amsterdam. The table keeps up to
13 complete Friday endpoints, within the available comparison history.
It uses exact dates seven calendar days apart. If either date is missing,
the change is blank (`—`); an older price is not substituted. These are endpoint
changes, not changes between weekly averages. Values are rounded only for display.

Daily chart gaps stay gaps. The chart includes weekends, because GPU rental
prices have daily observations. A notice identifies series whose latest daily
observation is more than three calendar days old. Missing Friday comparisons
have a separate notice. The current date controls which week is selected, so
a stale snapshot cannot silently present an old week as current.

Rental prices can change with both supply and demand. They do not measure
utilization or prove continued demand for older hardware.

## Checks

```sh
npm test --prefix web -- tests/gpuPrices.test.ts
npm run build --prefix web
npm run test:browser --prefix web -- tests/gpuPrices.browser.ts --workers=2
```

The checks cover exact weekly dates, missing baselines, incomplete days, time
zones, invalid responses, saved response hashes, chart filters, CSV export,
mobile width, source links, stale data, and recovery to stock views after a GPU
data error.

The first Ornn response set is also bundled under `web/tests/fixtures/ornn/`
so a fresh checkout can verify every saved observation against its source hash.
After a refresh, local checks use the new collection archive. When committing a
new GPU snapshot, include its matching five responses and manifest as fixtures.
