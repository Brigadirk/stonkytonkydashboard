# Sourcing plan

Started September 10, 2026. Objective: obtain enough dated, attributable revenue and EPS forecasts to evaluate analysts for the eight-stock universe over September 2021 through September 2026. Sandisk has a shorter standalone history. Source collection is followed by accounting reconciliation and a limited comparison before a broader ranking.

The [second-pass results](research/ROUND2_PROGRESS.md) record execution of this plan: 2023 U.S. originals and missing Korean broker-years were added, Grok was used for web discovery, and a 13-pair revenue pilot was completed. Native X search is not connected in the installed CLI. Complete institutional histories and consensus remain open.

## Starting position

The first pass retained 66 relevant broker PDFs, 356 extracted forecast/consensus observations and issuer results. The [first-pass report](research/COLLECTION_STATUS.md) records that baseline. The main weakness is the missing 2021–2023 U.S. analyst history. The Korean collection has better year coverage but incomplete broker sequences. More pages alone will not fill those gaps.

## Ordered work

| Priority | Work | Concrete output | Completion test |
|---|---|---|---|
| 1 | Find original 2021–2023 U.S. forecasts | Dated company models for AVGO, Alphabet, Nvidia, Micron or ASML, plus a query/source log | At least one previously empty company-year gains an attributable numerical forecast; unsuccessful searches remain explicit |
| 1 | Fill missing Korean broker-years | KB 2024; Hana 2021/2023 with author changes; Hyundai late 2021/2026; accessible Mirae gaps | New originals and extracted tables, preserving author and firm at publication |
| 2 | Use Grok for discovery | Exact report URLs, archive endpoints and any attributable X post links with dates | A lead is independently checked before entering the forecast dataset; model assertions alone do not qualify |
| 2 | Extract saved but unused models | Relevant company tables from dated sector reports, with physical page references | No historical-actual columns mislabelled as forecasts; unresolved publication dates stay explicit |
| 3 | Assemble comparable actuals | Original issuer revenue outcomes first, then accounting/share-basis-matched EPS | Each outcome has a target period, value, unit, release date and source; preliminary and restated results remain distinguishable |
| 3 | Run a small comparison | Matched long-lead revenue forecasts against issuer outcomes, with report age and missing consensus stated | Reproducible arithmetic and traceable pairs; no five-year winner inferred from a small sample |
| 4 | Obtain missing historical consensus and institutional detail | A verified sample using the [data request](DATA_SAMPLE_REQUEST.md) | Same-company/period analyst estimates and consensus, author/broker identity, original availability and comparable actuals |
| 5 | Evaluate and then connect to valuation | Per-company accuracy, bias, coverage, recent performance and held-out results | Enough comparable outcomes under the [evaluation rules](ANALYST_EVALUATION.md); only then analyst weights and forward-valuation ranges |

The first next milestone is a concrete improvement in early U.S. coverage, missing Korean broker-years and a traceable issuer-outcome sample. Collection proceeds alongside normalization so problems are discovered before downloading a much larger archive.

## Discovery routes

Search the publisher or broker archive first, then issuer-hosted material and identifiable research distributors. Public Morningstar reports and dated broker summaries are useful alternatives when the original institutional shortlist is unavailable. Keep those alternative authors explicit.

Use X to locate original publications, dated model screenshots or links. Preserve the post URL, handle, posting date, attachment and underlying report URL where obtainable. An original analyst's dated post is different evidence from a third party reposting a screenshot. Neither a repost nor Grok's description establishes a complete historical record.

For this round, use the existing Grok installation for one bounded discovery job, with public search/fetch only, no local-file access and no additional agents. Record the prompt, result, actually available tools and any reported usage. Native X search must be confirmed by the tool trace; ordinary web results from x.com must not be described as native X retrieval. Existing sign-in is used if it works. No new account, subscription or provider contact is part of this step.

The Grok API separately documents `x_search`, including date filters and image understanding. This does not prove the installed CLI exposes it. [xAI X Search documentation](https://docs.x.ai/developers/tools/x-search)

## Admission and tracking

Every accepted observation needs company, author or explicit unknown attribution, firm, metric, target period, original value/units, report date, model date if present, source URL, retained file hash and physical page. Independently verified original availability stays separate from a printed date.

Preserve failed retrievals, repeated models, unknown dates and conflicting values. Do not fill missing history using current consensus or later retrospective tables. Acquisition scope, splits, treasury shares and GAAP/adjusted EPS must be reconciled where they affect a comparison.

New research rounds live in separate collection directories. The combined catalog and forecast export must discover them without overwriting earlier manifests. Duplicate source contents and repeated forecast versions are counted separately from new evidence.

## Access escalation

Use ordinary public downloads first. Test a scraping service only against a specific public endpoint whose content is useful and currently blocked. Additional compute cannot supply a licensed analyst archive.

When a gap persists across the original publisher, a known distributor and dated public references, record it as an access gap and use the prepared supplier specification. Requesting or buying data is separate from public discovery. No request will be sent to a provider without authorization to contact them.
