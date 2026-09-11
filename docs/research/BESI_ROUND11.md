# BESI round 11: fresh publisher estimates, named-model refresh still blocked

Reviewed 10 September 2026. This pass retained 23 public source artifacts and extracted three exact annual EPS observations from Dividendinfo.nl. It added **zero named-analyst models, zero compatible ensemble contributors and zero estimates eligible for the current price bands**. The selected Hildo Laman model remains dated 23 April 2026. All new files are under `data/collection/besi_round11/`; earlier collections and shared app/merger policies were not changed.

## Verified new numerical capture

The [original Dividendinfo BESI page](https://www.dividendinfo.nl/besi) expressly describes its own EPS assumption and refers readers to its annual forecast table. These are publisher forecasts, not identified individual-analyst forecasts or labelled consensus.

| Period | EPS, EUR/share | Source label |
|---|---:|---|
| FY2026 | 3.85 | TAX |
| FY2027 | 5.00 | TAX |
| FY2028 | 5.80 | TAX |

Capture: **2026-09-10T20:43:19.791644+00:00**. SHA-256: `6fcb6415a80ec3059713c9bfdd0e3a3e7f158fdefded56186028e2bf00f93436`. The retained HTML table and its rendered evidence were checked. The source's July 23 news paragraph is not sufficient to establish when every number in its mutable forecast table was last revised. `model_date` and original publication timestamps remain blank; `report_date` is explicitly the first-observed date. No earlier availability is claimed.

Neither the page nor the retained [FAQ](https://www.dividendinfo.nl/meer/faq-veel-gestelde-vragen), [contact page](https://www.dividendinfo.nl/meer/contact) or [disclaimer](https://www.dividendinfo.nl/meer/disclaimer) establishes a named forecast author, EPS adjustments or basic/diluted denominator. The observations use `publisher_forecast_unattributed` and a separate unresolved Dividendinfo basis. Existing panel eligibility excludes that source type; no invented analyst name or compatibility alias is supplied. Even a supported first-observed capture would become daily-eligible no earlier than September 11 and supplies no earlier valuation reference history.

## New routes reviewed and excluded

| Original/discovery route | Verified result | Why it does not refresh the chart |
|---|---|---|
| [Add Value Fund Q2 report](https://addvaluefund.nl/uploads/media/maandberichten/Add-Value-Fund-tweede-kwartaalbericht-2026_2026-07-20-090341_uqmm.pdf), signed July 17, physical pages 6–7 | Own FY2030 EPS assumption is **at least €10**, revised from at least €8.50 | A lower bound for 2030; no FY2027/28 pair. Not converted into a point forecast or interpolated years. |
| [Add Value Fund July report](https://addvaluefund.nl/uploads/media/maandberichten/Maandbericht-juli-2026_2026-08-20-080809_flgk.pdf), signed August 19, physical page 8 | Promises fuller BESI discussion in the next monthly report | Later issue not linked in the retained [public report archive](https://addvaluefund.nl/nieuws/maandberichten). April/May reports were also checked without finding consecutive BESI EPS. |
| [KBC August 26 commentary](https://www.kbc.com/nl/economics/the-front-row/artikels/beursnieuws-26augustus20261.html) | Original hybrid-bonding discussion and maintained recommendation | No annual EPS figures; target/multiple arithmetic was not used to infer them. |
| [Muffett September 2 note](https://www.muffettinvestments.com/stock-research-reports/besi-stock-analysis) | Full apparent FY2026–29 table, but footer calls all projections consensus | Rejected as an independent analyst source. Historical figures and the implied share denominator also conflict with issuer evidence; the table was not repaired. |
| [Naina Garg BESI dashboard](https://nainagarg.com/besi-dashboard/) | Author's illustrative FY2027 scenarios explicitly separated from quoted consensus | No FY2028 own-model EPS; snapshot label does not verify the revision history of this mutable page. Scenarios and consensus not stitched together. |
| [Macrostream Barclays summary](https://www.macrostream.ai/articles/6a62f1f43341cc34a352453b) | Secondary lead mentions a July model with annual EPS through 2028 | Its [only linked image](https://doctext.wisburg.com/32e5c2deef7b80817737b236c3b4fd2c_0_29_f.jpg), retained and visually inspected, is only a price chart. Original EPS table, byline, date and basis remain unverified; no observations extracted. |

For the Muffett rejection, its FY2025 historical row shows approximately €675m revenue, €189m net income and €4.80 EPS. The already retained [issuer FY2025 report](https://www.besi.com/fileadmin/data/Investor_Relations/_Semi__Annual_Reports/Annual_Report_2025.pdf) instead records €591.3m, €131.6m and €1.66. This is a source-consistency check, not a judgment based on whether a forecast is optimistic. Its claimed August release timing also differs from the [issuer's July 23 Q2/H1 publication](https://www.besi.com/investor-relations/press-releases/details/be-semiconductor-industries-nv-announces-q2-26-and-h1-26-results/).

## Remaining access checkpoint

The missing refresh is a **dated post-April-23 named BESI model**, ideally FY2026, FY2027 and FY2028 EPS in EUR on a documented share/accounting basis. FY2027/28 are needed to cover roughly September 2027–September 2028 for the one-year target. Original author, numerical revision date and earlier vintages are also needed for historical comparisons. Unknown IEX EPS definitions still prevent automatic cross-firm compatibility.

The original IEX [June 19 analysis](https://www.iex.nl/Premium/Adviezen/868324/Koersdoelverhoging-voor-Besi.aspx) and [July 23 analysis](https://www.iex.nl/Premium/Adviezen/871925/Orders-Besi-overtuigen-resultaten-net-niet.aspx) again returned explicit subscription excerpts. The [magazine index](https://www.iex.nl/Premium/Magazines.aspx) reaches August 28 but its full-issue access is gated. Searches for public newer publisher/issuer-distributed magazines found no verified replacement. Parsing the [Saxo article sitemap](https://www.home.saxo/nl-nl/article-sitemap-nl-nl-1.xml) found no newer full Hildo model; matching locations are retained in `evidence/saxo_besi_urls.json`.

This is a **content subscription gap**, not evidence that ScrapingBee can reveal the missing IEX tables. The earlier same-day [access review](BESI_ACCESS_OPTIONS.md) verified the shortest IEX Premium article-access option at €17.95/month. That unlocks the identified articles, but their unseen annual table contents remain unconfirmed. A newly checked [Lezerij distributor page](https://www.lezerij.nl/magazine/iex) advertises IEX magazine access at €12.50/month; it does not demonstrate that the required specific BESI models are in the included issues. No purchase is justified as a guaranteed numerical-data unlock from these excerpts alone.

Public follow-up candidates are the next Add Value Fund monthly report and an explicitly linked full Barclays original. Neither currently needs a paid renderer; neither currently supplies a verified replacement model. No credentials, paid access, provider contact or external messages were used.

## Reproduction and checks

`python3 data/collection/besi_round11/collect.py` verifies all retained source hashes, asserts the original table cells/attribution and rebuilds this collection's `manifest.csv`, `observations.csv`, extraction evidence and validation file. `node data/collection/besi_round11/render_evidence.mjs` renders the exact retained table fragment for review. The Add Value Fund pages 6 and 8 and the linked Barclays price graph were visually reviewed.

`python3 data/collection/besi_round11/fetch.py --refresh` repeats the retained URL recipe into a **new timestamped retrieval directory**. It never replaces existing originals or promotes new captures without review. `download_log.json` preserves response statuses, capture times, URLs and hashes; `reviews.json` records source decisions; `search_log.json` preserves discovery output. `file_hashes.json` freezes all collection files and this note. No shared refresh command was run.
