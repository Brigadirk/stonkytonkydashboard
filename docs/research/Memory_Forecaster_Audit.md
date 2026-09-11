# Memory stock forecaster source audit

Research cutoff: 2026-09-10. Scope: SK Hynix, Samsung Electronics, Micron Technology (interpreting “Micon”), and Sandisk. This is a source-availability audit, not an analyst accuracy ranking. Report dates below are printed publication dates; exact original dissemination times and whether files were subsequently replaced have not been established.

## Finding

Start with the Korean companies for the first public-data forecast audit. Mirae Asset, KB Securities, Hana Securities and Daishin publish dated research containing numerical forecasts. Several reports also preserve a contemporaneous consensus comparison. This is enough to begin assembling and testing a small forecast dataset without buying a feed. It does not yet establish a complete archive or anyone’s forecasting skill.

For Micron and Sandisk, named analyst coverage is readily verifiable. Public material retrieved here is substantially less complete for each analyst’s numerical earnings history. Company guidance and commentary are useful separate inputs; neither should be relabeled as an individual analyst estimate.

## Instruments and comparable earnings

| Company | Working instrument | Currency | Treatment |
|---|---|---|---|
| SK Hynix | KRX 000660, shown as 000660 KS in broker reports | KRW | Use ordinary-share prices and KRW-per-share forecasts together. |
| Samsung Electronics | KRX 005930, ordinary shares, shown as 005930 KS | KRW | Keep separate from preferred shares and GDRs; the September Mirae report discusses both common and preferred shares in its valuation. |
| Micron Technology | Nasdaq MU | USD | August fiscal year; distinguish company GAAP and non-GAAP diluted EPS. |
| Sandisk | Nasdaq SNDK | USD | June fiscal year; use the post-2025 separation entity. |

The Korean instrument identities and currencies are printed in the [Mirae Hynix report](https://securities.miraeasset.com/bbs/download/2147118.pdf?attachmentId=2147118) and [Samsung report](https://securities.miraeasset.com/bbs/download/2147119.pdf?attachmentId=2147119). US tickers and fiscal months are independently listed in [Wedbush’s coverage document](https://media.wedbush.com/CoverageList.pdf). Micron’s [June 2026 presentation](https://investors.micron.com/static-files/2354ecda-77a0-4ddd-8462-a631eb491356) reconciles its earnings definitions.

## Candidate forecasters: SK Hynix

| Candidate | Primary evidence | Numerical history/access found | Audit status |
|---|---|---|---|
| Young-gun Kim, Mirae Asset | [September 7, 2026 report](https://securities.miraeasset.com/bbs/download/2147118.pdf?attachmentId=2147118); [October 29, 2025 report](https://securities.miraeasset.com/bbs/download/2137954.pdf?attachmentId=2139502) | Public English PDFs with annual EPS/revenue, quarterly operating models, revisions and valuation charts. Earlier report includes coauthor Jaeho Kim. | Strong retrieval candidate; at least two distinct forecast vintages located. Accuracy unmeasured. |
| Jeff Kim, KB Securities | [May 29, 2026 report](https://rdata.kbsec.com/pdf_data/20260528173943487E.pdf); [April 2026 report](https://rdata.kbsec.com/pdf_data/20260413190727533E.pdf) | Public English PDFs; May report includes Changmin Lee as coauthor, annual EPS, quarterly revenue/OP and FnGuide consensus comparison. | Strong retrieval candidate. Preserve broker/team attribution rather than counting coauthors as independent forecasts. |
| Rok-ho Kim, Hana Securities | [February 24, 2026 semiconductor report](https://www.hanaw.com/download/research/FileServer/WEB/industry/industry/2026/02/23/Semi_260224.pdf); [October 30, 2025 report](https://www.hanaw.com/main/research/research/download.cmd?attachFileSeq=1&bbsCd=2206&bbsId=&bbsSeq=1284695&dbType=) | Public Korean PDFs with EPS/revenue tables and separate consensus tables; Kim Young-gyu identified as research associate. | Strong retrieval candidate; Korean parsing required. |
| Hyung-keun Ryu, Daishin Securities | [September 8, 2026 sector report](https://money2.daishin.com/PDF/Out/intranet_data/product/researchcenter/report/2026/09/59055_260908_semicon_industry.pdf); [broker research index](https://money2.daishin.co.kr/E5/ResearchCenter/Work/Research_BasicList.aspx?pr_code=4) | Latest public Korean report gives explicit quarterly OP forecasts and revisions. Index also identifies his July 7 Hynix preview. | Useful fourth independent source; full EPS archive not collected. |

Hana’s analyst identity is additionally corroborated by an [SK Hynix interview dated May 13, 2026](https://news.skhynix.com/en/2026-analyst-interview-02/). Issuer interviews establish coverage, not accuracy.

## Candidate forecasters: Samsung Electronics

| Candidate | Primary evidence | Numerical history/access found | Audit status |
|---|---|---|---|
| Young-gun Kim, Mirae Asset | [September 7, 2026 report](https://securities.miraeasset.com/bbs/download/2147119.pdf?attachmentId=2147119); [May 7, 2026 report](https://securities.miraeasset.com/bbs/download/2144364.pdf?attachmentId=2144364) | Public English PDFs with annual EPS/revenue, segment models and revisions. | Strong retrieval candidate; fresh and older vintages available. |
| Jeff Kim, KB Securities | [June 10, 2026 report](https://rdata.kbsec.com/pdf_data/20260609193955660E.pdf); [January 15, 2026 report](https://rdata.kbsec.com/pdf_data/20260114182402580E.pdf) | Public English earnings models; June report coauthored with Changmin Lee. | Strong retrieval candidate; June sample is a historical observation, not a September estimate. |
| Rok-ho Kim, Hana Securities | [May 4, 2026 report](https://file.hanaw.com/download/research/FileServer/WEB/industry/enterprise/2026/04/30/SEC_260504.pdf); [February 24, 2026 report](https://www.hanaw.com/download/research/FileServer/WEB/industry/industry/2026/02/23/Semi_260224.pdf) | Public Korean forecast and consensus tables for both earnings and revenue. | Strong retrieval candidate; accounting/share definitions still need field-level validation. |
| Hyung-keun Ryu, Daishin Securities | [September 8, 2026 report](https://money2.daishin.com/PDF/Out/intranet_data/product/researchcenter/report/2026/09/59055_260908_semicon_industry.pdf) and [broker index](https://money2.daishin.co.kr/E5/ResearchCenter/Work/Research_BasicList.aspx?pr_code=4) | Explicit Q3 OP forecast; index identifies his Samsung earnings review dated July 7. | Fourth independent source; EPS archive not collected. |

## Numerical observations actually retrieved

Values below are dated forecast samples. They are not a harmonized live consensus. Revenue is KRW **billions**, EPS is KRW **per share**; annual fiscal periods end in December. An `EPS` label alone does not prove adjusted or diluted EPS.

| Issuer | Forecaster | Publication date | Target FY | Revenue, KRW bn | EPS, KRW/share | Printed basis / source |
|---|---|---|---|---:|---:|---|
| SK Hynix | Young-gun Kim / Mirae | 2026-09-07 | 2026 | 330,065 | 393,968 | Consolidated K-IFRS; parent-attributable NP; [p. 1](https://securities.miraeasset.com/bbs/download/2147118.pdf?attachmentId=2147118) |
| SK Hynix | Young-gun Kim / Mirae | 2026-09-07 | 2027 | 486,647 | 529,561 | Same basis and source |
| Samsung Electronics | Young-gun Kim / Mirae | 2026-09-07 | 2026 | 713,635 | 43,637 | Consolidated K-IFRS; parent-attributable NP; [p. 1](https://securities.miraeasset.com/bbs/download/2147119.pdf?attachmentId=2147119) |
| Samsung Electronics | Young-gun Kim / Mirae | 2026-09-07 | 2027 | 953,514 | 63,846 | Same basis and source |
| SK Hynix | Jeff Kim / KB, with Changmin Lee | 2026-05-29 | 2026 | 357,084 | 349,089 | IFRS-C in financial statements; [p. 1, basis p. 5](https://rdata.kbsec.com/pdf_data/20260528173943487E.pdf) |
| SK Hynix | Jeff Kim / KB, with Changmin Lee | 2026-05-29 | 2027 | 557,039 | 541,965 | Same basis and source |
| Samsung Electronics | Jeff Kim / KB, with Changmin Lee | 2026-06-10 | 2026 | 741,801 | 45,182 | EPS and parent-attributable NP labels; detailed EPS adjustments not established; [p. 1](https://rdata.kbsec.com/pdf_data/20260609193955660E.pdf) |
| Samsung Electronics | Jeff Kim / KB, with Changmin Lee | 2026-06-10 | 2027 | 922,447 | 65,970 | Same basis and source |

Daishin’s September 8 report, p. 1, forecasts **Q3 2026 OP** of KRW105.5tn for Samsung and KRW74.7tn for Hynix, reduced from KRW110tn and KRW77tn. These are operating-profit forecasts, not EPS. [Original report](https://money2.daishin.com/PDF/Out/intranet_data/product/researchcenter/report/2026/09/59055_260908_semicon_industry.pdf)

Do not average the September and May/June rows as if they were contemporaneous. Do not divide an ADR price by ordinary-share EPS. Do not assume reported K-IFRS EPS equals the normalized earnings denominator intended for the dashboard.

### Temporary source files for independent checking

Downloaded with `curl`, parsed using `pypdf`; these temporary paths are for verification and are not durable project dependencies:

- `/tmp/memory-audit-hynix.pdf`: Mirae September 7, p. 1 bottom annual table; `Revenue (Wbn)` and `EPS (W)`. Fiscal columns 2024, 2025, 2026F, 2027F, 2028F.
- `/tmp/memory-audit-samsung.pdf`: Mirae September 7, p. 1 bottom annual table; identical units and fiscal columns. First page also rendered to `/tmp/memory-audit-samsung.png` for a layout check.
- `/tmp/memory-audit-kb-samsung.pdf`: KB June 10, p. 1 “Earnings Forecast & Valuation.”
- `/tmp/memory-audit-daishin.pdf`: Daishin September 8, p. 1 quarterly OP revisions.
- `/tmp/memory-audit-micron.pdf`: Samsung Securities June 25 Micron review, discussed below.

Mirae’s public [research index](https://securities.miraeasset.com/bbs/board/message/list.do?categoryId=481) lists both September 7 publications under Young-gun Kim. Some PDF requests timed out through the web parser but succeeded through a direct public download.

## Candidate forecasters: Micron

| Candidate | Coverage evidence owned by issuer/research firm | Accessible record and gap |
|---|---|---|
| Matthew Bryson, Wedbush | [Official analyst profile and coverage list](https://www.wedbush.com/analysts/matthew-bryson/); [June 2019 initiation](https://www.wedbush.com/wedbush-securities-equity-research-welcomes-analyst-matthew-bryson-as-he-initiates-coverage-on-stocks-in-the-tech-space-amd-intc-mu-nvda-stx-and-wdc/) | Long coverage history and public appearances verified. Complete dated EPS models not retrieved; institutional research access terms/cost unknown. |
| Vijay Rakesh, Mizuho | [Official equity research profiles](https://www.mizuhogroup.com/binaries/content/assets/pdf/americas/who-we-are/equity-research/equity-research-profiles-5.23.23-v2.pdf) | Firm document identifies MU coverage. The filename has an older date: current assignment should be reconfirmed before automated attribution. No current primary-source numerical EPS model retrieved. |
| C. J. Muse, Cantor | [Cantor’s winter 2025 coverage document](https://www.cantor.com/wp-content/uploads/2025/02/Software-and-SaaS-Sector-Update-Winter-2025_vFINALv2.pdf) | Semiconductor coverage includes Micron under Muse/Matthew Prisco. Historical coverage evidence, not a current earnings forecast; current assignment and model entitlement need checking. |
| William Kerwin, Morningstar | [Author page with June 25, 2026 MU research](https://www.morningstar.com/people/william-kerwin); [dated report archive](https://www.morningstar.com/company-reports?listing=0P000003MC) | Public dated notes, including 2025 and 2026 history. Full numerical earnings model/history not retrieved. Useful candidate with an explicit cyclical thesis; being contrarian does not establish accuracy. |

Supplementary accessible material: Samsung Securities’ **Jong-wook Lee** authored a [June 25, 2026 Micron review](https://www.samsungpop.com/common.do?cmd=down&contentType=application%2Fpdf&fileName=3010%2F2026062508013418K_02_02.pdf&inlineYn=Y&saveKey=research.pdf). It contains company results, guidance and Bloomberg consensus, not a clearly separated set of Lee’s own EPS predictions. Use it for source discovery, not analyst ranking.

There is a concrete data-quality issue in that review: some tables labeled non-GAAP reproduce values matching Micron’s GAAP results, and its Q4 EPS guidance range differs from the issuer’s table. Quarantine its EPS observations until reconciled. The issuer’s presentation explicitly shows **Q4 FY2026 revenue $50.0bn ± $1.0bn; GAAP diluted EPS $30.73 ± $1.00; non-GAAP diluted EPS $31.00 ± $1.00**, published **June 24, 2026**. This is **management guidance**, not a broker forecast. [Micron presentation, p. 43](https://investors.micron.com/static-files/2354ecda-77a0-4ddd-8462-a631eb491356)

## Candidate forecasters: Sandisk

Sandisk’s [official analyst coverage page](https://investor.sandisk.com/stock-information/analyst-coverage) lists all five candidates below. It is an undated coverage page retrieved during this audit, so historical coverage dates must come from dated reports.

| Candidate | Supporting first-party evidence | Accessible record and gap |
|---|---|---|
| Matthew Bryson, Wedbush | [Official analyst profile](https://www.wedbush.com/analysts/matthew-bryson/) | Coverage verified; standalone SNDK earnings-model archive not retrieved. |
| Vijay Rakesh, Mizuho | Sandisk issuer coverage page | Coverage verified; dated EPS forecasts not retrieved. |
| C. J. Muse, Cantor | Sandisk issuer coverage page | Coverage verified; dated EPS forecasts not retrieved. |
| William Kerwin, Morningstar | [August 19, 2026 note](https://www.morningstar.com/stocks/sandisk-we-retain-skepticism-longer-term-targets) | Public dated analysis and stated cycle expectations; annual EPS model not exposed in the retrieved article. |
| Ishan Majumdar, Baptista Research | Sandisk issuer coverage page; [firm report storefront](https://baptistaresearch.com/buy-our-reports/) | Candidate independent provider. No Sandisk numerical model, complete forecast archive, or applicable price verified in this audit. |

Latest company guidance located: published **August 5, 2026**, for **Q1 FY2027**, revenue **$10.30–10.80bn**, non-GAAP diluted EPS **$44.00–46.00**. Again, this is a management-guidance row; it cannot fill the missing individual analyst forecast cells. [Sandisk Q4 FY2026 results](https://investor.sandisk.com/node/8136/pdf)

### Sandisk history break

The current company began regular Nasdaq trading on **February 24, 2025**, after separating from Western Digital. [Issuer announcement](https://investor.sandisk.com/news-releases/news-release-details/sandisk-celebrates-nasdaq-listing-after-completing-separation)

Consequently, a continuous two- or three-year historical forward-multiple band for this standalone equity does not exist as of this audit date. Pre-separation flash-business financials can inform operating history, but should not be spliced to Western Digital’s share price or treated as the same capital structure. The [2025 annual report](https://www.sec.gov/Archives/edgar/data/2023554/000202355425000034/sndk-20250627.htm) documents the separation and basis of presentation. Earlier historical use of the `SNDK` ticker requires an entity check before any import.

## Consensus baseline and subscriptions

| Source | What this audit verified | What remains missing |
|---|---|---|
| Consensus printed inside Korean broker reports | KB May 29 has FnGuide comparisons for annual revenue, OP and parent-attributable NP, plus a Q2 preview consensus. Hana reports have separate EPS/revenue consensus tables. Mirae September reports print FY2026 OP consensus beside their own OP. | Exact source timestamp, contributor set, accounting comparability and a complete vintage series. Store as `report_embedded_consensus`, not as an unqualified live feed. |
| Current FnGuide pages | Older URLs redirected to a new service or returned missing-page responses. | Current endpoint, entitlement and automated historical access not verified. |
| US consensus pages | Direct Zacks detailed-estimates pages for MU and SNDK returned HTTP 403 in this tool environment. | No current numerical consensus value certified from those pages here; this does not establish whether a user’s browser/subscription can access them. |
| Broker PDFs and public notes | Selected research readable without payment or login. | Public readability does not establish export, bulk-download, storage or redistribution rights. No institutional feed access terms or exact applicable price verified. |
| Full individual-forecast feed | Not procured or contacted. | Sample needed with analyst IDs, publication/availability timestamps, forecast fiscal periods, basis, revisions, comparable actuals, and historical coverage of Korean ordinary shares and the new Sandisk entity. |

The initial source audit required no new market-data subscription. Do not buy a charting/news subscription on the assumption that it includes historical individual-analyst forecasts or a backend API. Any purchase should follow a specific missing-data test.

## Next bounded work

1. Assemble all retrievable forecast vintages for one Korean stock from Mirae, KB, Hana and Daishin over a fixed period; record missing reports rather than selecting only successful calls.
2. Preserve report publication date, retrieval time, exact target period, units, accounting labels, analyst/team, source URL and page. Retain file hashes if archiving is permitted. A current download’s printed date alone is not proof of unaltered historical availability.
3. Reconcile forecasts to issuer-reported results on the same basis and to a contemporaneous consensus. Compare forecasts at fixed horizons; don’t score a two-day preview against someone else’s six-month forecast.
4. Only then rank observed earnings accuracy, with sample counts and insufficient-evidence labels. Price targets and recommendation returns are a different task.
5. For MU/SNDK, identify which candidate models are accessible through existing research subscriptions before requesting or purchasing a feed. Start collecting prospective snapshots while historical gaps are being assessed.

No forecast accuracy has been scored, no “best analyst” has been established, no purchase or provider contact occurred, and no trading action was taken.
