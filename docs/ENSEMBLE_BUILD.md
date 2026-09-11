# Estimator views and public-data completion

Completed 10 September 2026 at the documented data-access checkpoint. See [delivery, validation and limits](research/ENSEMBLE_COLLECTION_DELIVERY.md) and [exact missing fields/dates](ACCESS_CHECKPOINT.md).

## Implementation contract

- Single estimator, independent overlays, and a median or equal-weighted mean ensemble.
- Select all compatible named estimators or a subset. Published consensus can be viewed independently but never counts as another analyst.
- At most one vote per named analyst and research firm at each date. Use the latest eligible model; an author handover or joint author list cannot manufacture independent votes for the same research house. Exclusions explain this conservative independence policy.
- Reported diluted EPS is compatible within the same issuer/currency and fiscal calendar. Adjusted definitions remain firm-specific. Unresolved definitions remain separate unless scoped primary evidence establishes compatibility.
- At each date select the latest available numerical model for each analyst. A later reprint cannot replace a newer numerical model or renew model age. Missing fiscal years, stale models and unverified availability in strict mode remain explicit exclusions.
- Normalize each member's full next-twelve-month estimate to the price share basis before aggregation. Never assemble an analyst's model from different snapshots. Preserve zero/negative estimates in aggregation; suppress P/E only if the resulting ensemble EPS is non-positive or unstable.
- Compute historical price/combined-EPS first, then trailing median and sample standard deviation. No averaging of finished valuation bands. Current date excluded, minimum 20 usable prior sessions.
- Show members, weights, source documents, age range, disagreement, entry/exit dates and reference coverage. Disagreement is distinct from historical multiple standard deviation.
- Keep 16px base sizing, 44px controls, price-axis main chart, all ten companies and saved/shareable views.

## Completed work sequence

1. Build and test estimator calculation and selection, overlays, ensemble audit and exports.
2. Add model date/age and explicit reference-window coverage to the overview.
3. Collect BESI and Korean fresh/history sources plus remaining seven companies and issuer outcomes in isolated round8 collections.
4. Integrate validated sources, refresh reproducibly, evaluate exact-basis forecast outcomes and revisit backtest prerequisites.
5. Inspect desktop/mobile views and record concrete access gaps. Continue public collection while a productive route remains; do not infer that ScrapingBee unlocks subscription-only data.

Research notes: `research/BESI_ROUND8.md`, `research/KOREA_ROUND8.md`, `research/US_EUROPE_ROUND8.md`.

All five implementation/collection/verification steps above are completed within the verified public-data boundary. The remaining earnings definitions, archive access and evaluation prerequisites are itemized in the handoff; they are not silently treated as satisfied.
