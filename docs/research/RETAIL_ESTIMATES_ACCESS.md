# Retail access to historical analyst EPS estimates

Checked 10 September 2026. Scope: TIKR, Koyfin and Fiscal.ai, using public first-party documentation. No account creation, purchase or provider contact. This note concerns an input dataset for this app, including analyst accuracy evaluation; an on-screen consensus chart is a smaller requirement.

None of these three services is documented to deliver the complete requirement: five years of individually attributed EPS revisions, original historical availability timestamps, comparable actuals and permitted numerical export across our ten companies. TIKR explicitly excludes contributor attribution; Koyfin explicitly prohibits equity-estimates downloads; Fiscal.ai's reviewed API catalogue does not document the required estimates endpoints. These findings do not establish that an institutional subscription is mandatory, or that any institutional package automatically qualifies. The evidence and remaining uncertainties follow.

## Plans and demonstrated access

Prices below are public advertised USD amounts, not checkout quotations. Tax treatment was not established.

| Provider | Cheapest relevant advertised route | Named EPS revision history | Numerical access relevant to this app | Assessment |
| --- | --- | --- | --- | --- |
| TIKR | Plus $24.95 monthly or $17.95/month with annual billing; Pro $54.95 monthly or $37.95/month annually | Explicitly unavailable by analyst or bank | Plus permits table copying and Pro provides Excel download, subject to dataset restrictions; historical estimates export is not established | Useful consensus research; cannot supply named forecaster rankings |
| Koyfin | Plus displayed at $39/month; Premium $79/month. The retrieved comparison includes an annual toggle, but its billing state was not verified | Consensus statistics documented; five-year contributor-level revision archive not demonstrated | Equity financials, estimates and valuation downloads explicitly restricted in both tables and charts | Does not qualify as this app's estimates feed |
| Fiscal.ai | Current retail price and relevant export entitlement unverified because live pricing retrieval failed | Contributor identities, five-year revisions and original availability fields not documented in the reviewed API catalogue | API exists, but no documented analyst-estimates/revisions endpoint or retail-plan entitlement to such an endpoint was found | Unresolved, not a demonstrated cheaper replacement |

TIKR prices come from its live [pricing page](https://www.tikr.com/pricing); annual figures were read from that same page's public `__NUXT_DATA__` plan configuration (`monthlyPrice` and `annualPrice`), whose monthly values match the rendered cards. Annual totals calculated from those rates are $215.40 for Plus and $455.40 for Pro. Koyfin's figures are those displayed by its [plan comparison](https://www.koyfin.com/pricing/plans-comparison/). No checkout was opened.

## TIKR: consensus rather than individual forecasts

TIKR's Estimates help, updated 22 June 2026, explicitly states that estimates cannot be viewed by analyst name or bank. It documents consensus averages, contributor counts, normalized and GAAP EPS, and consensus revision trends. Pro and Ultimate add revision trends, breakdowns and beats/misses. The advertised four years for Pro and five years for Ultimate describe **forward forecast horizons**, not historical revision depth. The page does not specify a five-year revision lookback, immutable publication timestamps or superseded individual forecasts. Its adjustment discussion also means that historical GAAP financials must not automatically become the actuals for normalized EPS forecasts. [TIKR Estimates documentation](https://support.tikr.com/hc/en-us/articles/39071375390235-How-do-I-use-TIKR-s-Estimates-feature)

The export help, updated 8 July 2025, permits Plus table copying and reserves direct downloads for Pro. It also says some data partners prohibit export altogether, and identifies the Morningstar dataset as offering better export capabilities. Therefore a generic Excel feature does **not** demonstrate that Capital IQ consensus revision tables can be exported. The relevant dataset, table, historical timestamps and export rights would still need verification even for a consensus-only implementation. [TIKR export documentation](https://support.tikr.com/hc/en-us/articles/38745516537115-How-can-I-export-and-download-data-to-Excel)

Paid plans advertise global data. That statement is not a security-by-security historical EPS coverage audit. Paying for a higher TIKR tier would not resolve the explicit absence of named contributors. [TIKR pricing and coverage](https://www.tikr.com/pricing)

## Koyfin: useful displayed data, explicit download restriction

Koyfin documents consensus mean, median, high, low and contributor count, with annual/quarterly periods, fiscal/calendar choices, period-ending dates and reported dates. Reporting currency is the default; optional currency conversion must be tracked if used. Most figures are adjusted, with unadjusted fields labelled GAAP. This supports comparisons within the provider's definitions, but does not establish compatibility with every broker's EPS numerator or dilution convention. The documented reported date is not evidence of an individual forecast's original publication timestamp. [Actuals and Consensus](https://www.koyfin.com/help/actuals-consensus/)

Its March 2026 release adds historical pre-results estimates, actuals and surprises to tables. An estimate immediately before earnings is useful for surprise analysis; it does not establish access to all forecasts issued 90 or 180 days earlier. The paid-plan allowance of 10 actual and 10 estimate years likewise describes displayed fiscal periods, not ten years of individually attributed revisions. [March 2026 release](https://www.koyfin.com/help/release-notes/v3-81-historical-estimates-actuals-surprises/), [plan comparison](https://www.koyfin.com/pricing/plans-comparison/)

The decisive restriction is explicit: equity financials, estimates and valuation data cannot be downloaded from either tables or charts because of vendor restrictions. Generic plan download features apply to other categories and do not override this. [Download FAQ, updated 1 July 2025](https://www.koyfin.com/help/faq/can-i-download-data/)

For a separate manual workflow, Koyfin documents multiplying an NTM consensus EPS series by a chosen multiple to plot a valuation line. That is relevant to inspecting forward-earnings valuation visually, but does not provide this app with its required exported observations or analyst accuracy data. [Chart multiplier release](https://www.koyfin.com/help/release-notes/v-3-39-july-10th-update/)

## Fiscal.ai: do not confuse adjusted actuals with forecast revisions

Fiscal.ai's first-party product announcement describes consensus EPS and other estimates. That does not establish named contributions. [Fiscal.ai product newsletter](https://newsletter.fiscal.ai/p/makes-100bagger)

The current API catalogue documents financials, adjusted metrics, prices, filings, ownership, events and other endpoints. No endpoint for individual analyst EPS forecasts or their revision history appeared in the reviewed catalogue. Its five-plus-year adjusted-metrics history concerns financial observations, not a demonstrated five-year forecast archive. Geographic coverage columns include the US, Canada, US ADRs, UK and EU; the page does not establish coverage of the Korean ordinary listings required here. API access is presented separately, and a retail subscription's entitlement to the required hypothetical endpoint is unknown. These are documentation limits, not a claim that Fiscal.ai has no additional internal or custom products. [API introduction, endpoint catalogue and coverage](https://docs.fiscal.ai/docs/introduction)

The adjusted-metrics reference identifies adjusted EPS among metrics intended for comparison with estimates. It does not, on its own, provide the forecast side, contributor identities, original revision timestamps, dilution conventions or a complete reconciliation to each broker's model. [Adjusted metrics reference](https://docs.fiscal.ai/docs/reference/adjusted)

Live [pricing-page](https://fiscal.ai/pricing/) retrieval returned a Vercel security checkpoint/HTTP 429 through direct requests and a 403 through the browsing tool. Search results contained older pricing and export claims, which were not treated as verified current entitlements. This is a retrieval limitation for the pricing page; overcoming it would not by itself prove the missing forecast data exists.

## Dataset acceptance criteria for the next access decision

The required universe is Broadcom, Alphabet, Nvidia, SK Hynix, Samsung Electronics, Micron, new standalone Sandisk, ASML, Apple and BESI. Confirm the actual listing and currency for each; a US ADR or broad claim of global coverage is insufficient for the Korean and Dutch ordinary-share series. Sandisk's new standalone history starts in 2025; an older acquired entity must not be used to manufacture five years.

A qualifying sample export should contain, or link unambiguously to, security and fiscal-period identifiers; contributor firm and stable analyst identity where named ranking is intended; EPS value, currency, adjustment and dilution basis; original publication/availability time and superseded revisions; split treatment; and matching actuals with release/restatement metadata. The access entitlement must permit retaining and processing those numerical observations in this app. A field labelled `date` without its meaning is insufficient.

That same sample test should apply to an institutional detail feed. The retail review removes three unproven shortcuts; it does not justify purchasing the more expensive alternative before its fields, exact ten-company coverage and historical export entitlement are demonstrated.
