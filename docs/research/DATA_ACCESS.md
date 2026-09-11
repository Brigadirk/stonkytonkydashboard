# Data access and subscriptions

Research date: 10 September 2026. No subscription has been purchased or provider contacted. Prices below are published offers, not a quote for this project's use.

## Decision for the first stage

Use public issuer materials and dated broker reports to start the eight-company forecast audit. These can establish a small collection of attributable forecasts. They do not establish complete coverage of every analyst or a daily historical forecast series. The company audits record exactly which material was retrieved.

Before paying for a feed, demonstrate a specific missing input: historical individual forecasts, a comparable historical consensus, documented actuals, or automated retrieval with suitable usage rights. A live-price subscription does not supply those inputs.

## Paid options checked

| Source | Verified capability | Published cost | Fit for this project |
|---|---|---|---|
| Koyfin Plus | Stock research with consensus estimates and financial history; estimates supplied by Capital IQ | USD 39/month billed annually, equivalent to USD 468/year, per July 2026 guide | Optional manual reference tool. Its FAQ says no data API and restricts downloads of estimates, financials and valuation data. It is not a verified backend for our application. |
| FactSet Estimates | Historical consensus, individual analyst/broker estimates, actuals and guidance; institutional delivery | No public project-specific price verified | Strong candidate if the public audit shows that complete analyst histories are needed. Confirm all eight securities, individual analyst identity, timestamps and the exact package. |
| LSEG I/B/E/S and estimate analytics | Earnings-estimate data and SmartEstimates weighted using analyst accuracy and recency | No public project-specific price verified | Candidate feed and external benchmark for our analyst weighting. Product description alone does not establish our access to a full historical panel. |
| SemiAnalysis institutional models | Industry forecasts and supply-chain models, with separate memory and accelerator offerings | Sales quote; no public price verified | Potential research input for forecast assumptions. These are not a substitute for a complete panel of individual EPS forecasts. Newsletter membership excludes institutional models. |

Koyfin sources: [pricing guide, updated 27 July 2026](https://www.koyfin.com/pricing-llm-info/), [data coverage and consensus source](https://www.koyfin.com/help/data-overview/), [API restriction](https://www.koyfin.com/help/faq/can-i-get-the-data-via-api/), [download restrictions, updated July 2025](https://www.koyfin.com/help/faq/can-i-download-data/).

FactSet sources: [estimates categories and historical coverage](https://insight.factset.com/resources/factset-consensus-estimates-datafeed), [OnDemand reference manual with broker/analyst identifiers and estimate entry dates](https://go.factset.com/hubfs/Website/Website_Downloads/Statistical%20Package%20Integration/factset%20ondemand%20web%20services%20reference%20manual_2.0.pdf), [official SDK and API access](https://github.com/factset/enterprise-sdk). The manual documents a delivery route, not an entitlement or a confirmed current contract. Broker-level data must not silently be presented as a stable individual analyst record.

LSEG source: [I/B/E/S estimate analytics](https://www.lseg.com/en/data-catalogue/company-data/ibes-estimates/estimate-analytics).

SemiAnalysis sources: [models and research](https://semianalysis.com/models-research/), [Memory Model](https://semianalysis.com/memory-model/). The memory product lists Samsung, SK hynix and Micron for DRAM, and those vendors plus Kioxia-Sandisk for NAND. It advertises quarterly Excel delivery, an archive and separate institutional licensing. We have not inspected the paid workbook, verified company EPS output or established whether every old forecast version is retained.

## Independent researchers

Doug O'Laughlin's Fabricated Knowledge is a candidate source of semiconductor research. A dated NVIDIA article from 26 May 2022 discusses segment forecasts and says numbers are attached. The article is marked paid, and this audit did not retrieve the attached model or a complete forecast archive. Treat it as a research lead, not an evaluated forecaster. His own retrospective list of successful articles is not an accuracy study. [About the publication](https://www.fabricatedknowledge.com/about), [dated NVIDIA article](https://www.fabricatedknowledge.com/p/nvidias-crypto-issues-ciscos-supply).

SemiAnalysis is a candidate for assessing accelerator demand, memory pricing and supplier margins. These business forecasts can help explain disagreement between company earnings forecasts. Model coverage and marketing claims do not establish a measured EPS forecasting advantage.

## Acceptance criteria for any paid sample

- Coverage of AVGO, GOOGL, NVDA, KRX 000660, KRX 005930, MU, SNDK and Amsterdam ASML.
- An estimate's author or broker, numerical value, fiscal target, currency, accounting definition, share basis and original publication/availability timestamps.
- Multiple historical versions of the same target period, plus comparable actuals and the consensus available at the same cutoff.
- Clear handling of stock splits, annual rollovers, accounting changes and Sandisk's 2025 separation.
- Rights and mechanisms for automated retrieval, local storage and the intended users. A downloadable SDK is not a data license.
- A sample reconciliation that shows later estimate revisions have not been inserted into an earlier observation.

## How the first collection should be scored later

Capture full report sequences rather than selecting successful calls. Choose a common forecast horizon, then compare each analyst's error with the consensus error for the same company and target period. Keep earnings definitions consistent. Record errors, directional bias and the number of independent outcomes; mark an insufficient record explicitly. Price-target returns and analyst popularity are different questions.

For now, the source map ranks the practicality of collecting evidence. It does not rank investment performance or forecast skill.
