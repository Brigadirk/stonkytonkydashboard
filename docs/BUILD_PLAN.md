Implementation update, 10 September 2026: the ten-stock local app, estimator overlays, compatible median/mean ensembles, source collection and exact access handoff are delivered. See [completion evidence](research/ENSEMBLE_COLLECTION_DELIVERY.md). See [dashboard usage](DASHBOARD.md) and the [historical earnings access checkpoint](ACCESS_CHECKPOINT.md). The original roadmap below includes later research and trading-rule work beyond this implementation.

AI valuation dashboard: build plan

Drafted 10 September 2026 for Dirk and Edwin. This is a proposed implementation sequence. Data subscriptions, budget and provider entitlements are unconfirmed.

The product should let us compare a stock's price with contemporaneous forward earnings, identify where its valuation sits in its own history, evaluate analyst forecasts, and inspect evidence that the business or its valuation has changed. Each stage should produce something usable or resolve a specific uncertainty.

Start with a private dashboard updated after the US close. Use the eight pilot companies selected by Dirk on 10 September 2026: Broadcom, Alphabet, NVIDIA, SK hynix, Samsung Electronics, Micron, Sandisk and ASML. Proposed research listings are AVGO, GOOGL, NVDA, KRX 000660, KRX 005930, MU, SNDK and Euronext Amsterdam ASML. Keep Korean prices and EPS in KRW, ASML prices and EPS in EUR, and the US listings in USD; record any deliberate currency conversion. These are test cases with different business characteristics, not a recommended portfolio. Expand to 20–30 names after the pilot is reliable. Manual investment decisions remain the first version's operating model; broker execution is a later, separate project.

1. Agree on the first screen and calculation rules.

   The first stock page answers: What are we paying for expected earnings? How does that compare with the past? Are forecasts changing? What could make this comparison misleading?

   Use price divided by next-twelve-month adjusted diluted EPS as the initial valuation measure, subject to confirming the provider's exact definition. Preserve the fiscal period, accounting basis, currency, share basis and forecast horizon. A sum of four forecast fiscal quarters must be labelled as such if it differs from the provider's NTM calculation. Negative, near-zero or missing earnings produce an explanation and an unavailable P/E, not an extreme bargain ranking.

   Show the requested trailing windows: 90 days, 180 days, one year, two years and three years. Treat these as calendar windows containing trading-day observations. Show the number and coverage of usable observations. Use percentiles and median bands as the main summaries; retain minimum and maximum as context. Label these as historical valuation ranges, not fair-value ranges.

   Finish when the team can inspect one proposed stock-page layout and agree on the definitions. A mock-up may use explicitly synthetic values while provider discussions continue.

2. Prove that the necessary data is accessible.

   Evaluate existing subscriptions first. Then compare an institutional estimates feed with a lower-cost consensus option. Obtain sample records before selecting a provider. The sample should include all eight pilots and multiple historical dates, including observations around an earnings release, an estimate revision, a stock split and a fiscal-year rollover.

   | Requirement | Evidence needed from the sample or provider |
   |---|---|
   | Historical consensus | Forecast snapshots demonstrably available on the historical observation date, not today's revised history |
   | Individual forecasts | Stable analyst or broker identity, target period, estimate value, publication/availability time, revision history and methodology |
   | Comparable actuals | Earnings on the same accounting basis as forecasts, with announcement times and revision records |
   | Prices and corporate actions | Documented price adjustment convention, splits, dividends and stable security identifiers |
   | History | Daily coverage sufficient to populate a three-year window and leave a later evaluation period; longer history where available |
   | Operating costs and access | Historical package price, recurring cost, application access, storage rights and permitted users |

   FactSet documents historical consensus snapshots that exclude information entered after the snapshot cutoff. Its public overview describes consensus, which must not be mistaken for proof that a particular subscription includes individual analyst histories. Confirm the actual package and coverage. [FactSet methodology](https://insight.factset.com/resources/at-a-glance-factset-estimates-point-in-time-consensus)

   LSEG documents estimates weighted by analyst accuracy and recency, plus analyst-ranking analytics. This is a candidate data source and a benchmark for a custom weighting method. Confirm whether historical analyst-level inputs, historical rankings and comparable actuals are included. [LSEG estimate analytics](https://www.lseg.com/en/data-catalogue/company-data/ibes-estimates/estimate-analytics)

   The fallback is explicit: if only historical consensus is affordable, build the consensus dashboard and postpone custom analyst weighting. If only current estimates are available, begin saving daily snapshots and build the live research view; historical forward-multiple bands and historical strategy validation remain unavailable until proper history is acquired or accumulated. Never reconstruct old forecasts using today's values.

   Finish with a provider comparison, a costed recommendation and an eight-stock data-quality report. Any paid subscription remains a separate purchase decision. No provider has been selected or contacted as part of drafting this plan.

3. Build the data foundation in the new project, reusing suitable existing components.

   The project now lives at /Users/dirk/Documents/Code/ai-valuation-dashboard, as requested by Dirk. The existing Positioning Lab in TheLab contains Python, DuckDB, Streamlit, Plotly, a watchlist, an IBKR collector and source-freshness displays. Its components are candidates for reuse in this separate project after checking coupling and data conventions. Application architecture and any code extraction remain undecided. This research stage has not changed either application.

   Reuse infrastructure after checking its suitability. The current IBKR collector requests `ADJUSTED_LAST`, which includes dividend adjustments. It should not be inserted directly into a historical P/E calculation against differently adjusted EPS. Store a documented valuation-price series with a compatible share basis, and keep return calculations separate. A price adjusted for splits still needs EPS on the same split basis. [IBKR historical-data conventions](https://www.interactivebrokers.com/campus/?p=152355)

   Preserve original downloaded records and append revisions. Deduplicate identical re-runs without erasing a previously available forecast. Store separately when the provider made a record available, when its underlying document was published, and when our system retrieved it. A historical backfill retrieved today can be used at an earlier cutoff only if the provider supports that historical availability claim.

   The minimum records are security identity and corporate actions; prices; consensus snapshots; individual estimates when licensed; comparable actuals; filed financials; universe membership; dated research notes; and calculation/run versions. Tie every displayed value to its inputs and observation date. Missing, stale and invalid values remain visible.

   Finish when the eight pilots refresh reproducibly, a past observation can be replayed, and a later correction cannot silently rewrite an earlier decision record. Use a single scheduled writer for the local database and a repeatable backup/recovery procedure.

4. Deliver the eight-stock valuation pilot.

   Build one stock page with a share-price chart, historical forward P/E, the five window summaries, forecast history, 30/90-day estimate revisions, analyst count and forecast dispersion where available. Include a scenario grid combining user-selected EPS and multiples; these are scenarios, not predicted probabilities.

   Calculate historical observations using only information available at their respective cutoff. Compute each historical percentile against the trailing observations preceding that date. Keep consensus and any later analyst-weighted history separate. Comparing a selected analyst's higher current EPS forecast with an old consensus-based multiple range does not establish like-for-like cheapness.

   Compare estimate revisions for the same target period. A change in rolling NTM EPS can arise because the forecast horizon advances; do not label that mechanical change as an analyst upgrade. Show the method when the UI uses a constant-horizon alternative.

   Required checks cover a split, a dividend, a fiscal rollover, an after-close earnings release, a later forecast correction, a missing quarter, non-positive EPS and a switch of accounting basis. Reconcile sampled calculations with the provider's reference values and record any explained differences.

   Finish when Dirk can reproduce the numbers for an ordinary day and the exceptional cases without relying on a screenshot from somebody else's chart. This is the first usable deliverable.

5. Expand to a daily screening workflow.

   Extend the universe to 20–30 explicitly selected stocks. Version additions and removals with their dates and rationale. Add a sortable overview with valuation percentiles, revisions, estimate dispersion, expected growth, next earnings date and data freshness. Do not average overlapping lookback windows into an apparent count of independent confirmations.

   Add transparent financial filters for net debt, interest coverage, profitability, free cash flow, share-count dilution and stock-based compensation. Use reported periods and publication dates correctly. Agree on thresholds by business type; do not pretend a single debt or cash-flow threshold is appropriate for every business. Show exclusions and their reasons. Incomplete data is not a passing quality assessment.

   SEC APIs can supply filing histories and reported financial facts. These do not replace analyst estimates or automatically provide earnings on a broker's adjusted basis. [SEC data documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)

   Finish with a saved watchlist, a daily refresh, visible failed/stale feeds, and a short list of changed valuations worth investigating. Measure time saved against the current manual workflow. Notifications can initially stay inside the application.

6. Test simple valuation rules before adding elaborate forecasts.

   Start with consensus so we can measure the incremental value of later additions. First examine subsequent returns and drawdowns by historical valuation percentile. Then define a small number of portfolio rules before evaluating them on later data. Any illustrative percentile threshold remains a research parameter until evaluated.

   Specify the main lookback, entry and exit thresholds, rebalance frequency, sizing, cash treatment, maximum positions and rules for missing observations. Use after-close information no earlier than the next eligible trading session. Include dividends, corporate actions, transaction costs, turnover and slippage assumptions. Record every rule version and experiment.

   Compare with buying and holding the same basket, a simple periodically rebalanced basket, and an appropriate market/sector benchmark. Report returns, maximum drawdown, time invested, concentration, turnover and how results vary by company and market period. Evaluate costs and parameter sensitivity rather than searching a large grid for the best historical result.

   Separate rule development from later evaluation in time. Allow earlier data to warm up a trailing window, but keep evaluation-period outcomes out of parameter selection and analyst rankings. Account for overlapping forward-return horizons when measuring uncertainty.

   A backtest of today's eight or thirty names answers a question about that selected basket. A claim about a general AI-stock strategy requires a historically defined universe with exits, failures and delistings handled. If that history is unavailable, state the narrower scope and begin a prospective record.

   Finish with a reproducible evaluation and a decision to retain, modify or discard each tested rule. A working dashboard can still be valuable if the timing strategy fails.

7. Add analyst selection and measure its contribution.

   Dirk's 10 September 2026 follow-up expands the analyst investigation to roughly five years, with outcomes announced from September 2021 through September 2026 and earlier forecast warmup where needed. This source investigation starts now, before the application is built. The five-year analyst evaluation is separate from the requested 90-day through three-year valuation chart windows. See [evaluation rules](ANALYST_EVALUATION.md) and [the historical sample specification](DATA_SAMPLE_REQUEST.md). Sandisk has a shorter standalone record.

   This stage depends on obtaining the individual forecast data in step 2. Score earnings accuracy at comparable horizons such as 90, 180 and 365 days before the earnings announcement. At each historical ranking date, use only completed outcomes that had been announced by that date. Identify stale estimates and changes of analyst or broker. Do not treat multiple revisions from one analyst for the same period as independent successes.

   Compare analysts against the consensus forecast available on the same date. Start with transparent, bounded weights and a consensus fallback when the track record is small. Set the minimum evidence threshold before evaluation. Use an error measure that remains meaningful near zero earnings; show bias, error and sample size rather than a single unexplained ranking.

   Test forecast accuracy on later observations first. Then rebuild the corresponding analyst-weighted historical valuation series and test whether it improves the investment rules over consensus. Compare provider-supplied weighting with a custom method where both histories are accessible.

   Finish when weights can be reproduced for any historical cutoff and we know whether analyst selection contributes useful information. If it does not, keep consensus as the default.

8. Add research assistance and changes in the business.

   Use AI to summarise dated filings and transcripts, flag guidance changes, and gather evidence for hypotheses about margins, capital intensity, cyclicality or governance. Every substantive claim links to a source passage and date. Numerical calculations use structured inputs and explicit code.

   Provide a small thesis journal: the proposed change, supporting evidence, objections, what would challenge it, its review date and the user's chosen valuation scenarios. Keep both the original and revised thesis. AI suggestions do not silently modify an earnings forecast, exclusion rule or trading threshold.

   Evaluate summaries for unsupported claims and missed material changes on a fixed sample. Historical AI commentary can contain knowledge learned after the historical date even when shown older documents. Keep it outside the historical trading rules unless that leakage problem has been addressed; prospective testing is the initial path for AI-assisted judgment.

   Finish with useful cited research briefs whose numerical inputs and user decisions remain auditable. Financial-quality calculations from step 5 do not depend on an AI opinion.

9. Add portfolio context and test sector timing separately.

   Show the proportion of covered stocks near the upper or lower end of their own valuation history, with equal-weighted and portfolio-weighted views. Display coverage, estimate revisions, subsector composition and concentration alongside that breadth measure.

   Treat “many AI stocks look expensive, therefore reduce exposure” as its own rule. Define the replacement allocation, sizing and re-entry condition before testing. Evaluate it against staying invested and simpler allocation rules. Looking expensive relative to history does not by itself identify the best alternative investment.

   Reuse Positioning Lab's market context where relevant, without equating expensive valuations with crowded ownership. Finish with a descriptive portfolio view and a separately documented result for any rotation experiment.

10. Run the workflow prospectively and expand only where useful.

   Start an immutable daily observation and paper-decision record as soon as the pilot works. Log the information available, proposed action, rationale, actual user decision and later outcome. Run it through earnings events and data failures. An initial six-to-twelve-week observation period can establish operational reliability and usefulness; it cannot by itself establish a durable trading advantage.

   Measure data failure rate, stale observations, reproducibility, time saved and whether research briefs improve the decisions being recorded. Expand to more securities only when ingestion and review are reliable. Decide on remote access for Edwin when it is needed; sharing must fit the chosen feed's permitted users. Public distribution and automatic order placement require separate designs.

Suggested engineering sequence and effort

| Milestone | Indicative effort after suitable access is available | Tangible result |
|---|---|---|
| Definition and sample audit | 2–4 working days, plus any provider wait | Agreed calculations and a data-source decision |
| Storage and eight-stock pilot | About 1–2 engineering weeks | Reproducible stock pages |
| Broader screening and quality checks | About 1 week | A useful daily watchlist |
| Initial historical evaluation | About 1–2 weeks | Results for a small set of fixed rules |
| Analyst weighting | About 1–2 additional weeks if data supports it | Measured forecast and strategy comparison |
| Research assistance and portfolio context | About 1–2 additional weeks | Cited briefs and an exposure overview |

These are planning estimates for one engineer familiar with the existing stack, with prompt product feedback. They are not delivery commitments. The basic dashboard and first evaluation can plausibly fit roughly four to eight engineering weeks; detailed analyst work and later features can extend that. Provider procurement and prospective observation have separate elapsed times.

The first work package is deliberately concrete:

- Inventory available data subscriptions and establish a spending ceiling.
- Confirm the eight pilot listings and the earnings definition.
- Obtain and inspect provider samples against the step-2 requirements.
- Record which parts of Positioning Lab can be reused and which data conventions need extension.
- Produce one proposed stock page and a short data audit before scaling implementation.

Open decisions: available subscriptions, acceptable recurring and historical-data cost, whether the first shared version must work on separate computers, and preferred review/holding horizons for the initial trading-rule experiment. The default assumptions above let planning continue while these are resolved.

## Universe additions

Apple and BE Semiconductor Industries were subsequently added at Dirk’s request on 10 September 2026. The live universe is maintained in `data/universe.csv`. BESI uses Amsterdam ordinary shares and EUR prices/EPS with a December31 fiscal year.
