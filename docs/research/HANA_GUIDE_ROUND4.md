# Hana U.S. guide extraction, round 4

The original [2026 guide](https://www.hanaw.com/download/research/FileServer/WEB/global/industry/2026/01/09/2026guide.pdf) has a printed cover date of **12 January 2026**. The January 9 path is a discovery hint, not publication evidence. The same retained PDF also supplies Sandisk observations in the ASML/Sandisk collection; it counts once in the source catalog.

Physical pages 53, 57 and 71 explicitly identify the following table forecasts as Bloomberg market consensus. They are not attributed to an individual Hana analyst. Only columns explicitly marked as estimates were extracted.

| Company | Fiscal years | EPS, USD per share | Revenue, USD million |
|---|---|---|---|
| NVIDIA | 2026 / 2027 | 4.68 / 7.71 | 213,293 / 327,047 |
| Broadcom | 2026 / 2027 | 9.86 / 13.86 | 95,260 / 130,431 |
| Micron | 2026 / 2027 | 30.33 / 38.45 | 71,016 / 88,320 |

EPS adjustment and dilution are not specified. These models use a separate accounting-basis label from Hana tables that explicitly print adjusted Bloomberg EPS. Twelve observations, including six EPS observations, are usable under those limitations. Original historical availability remains unverified.

Four additional Alphabet observations from physical page 145 are quarantined: the page mixes Alphabet financials with an Amazon company-data panel and questionable fiscal labels. These values are retained for review and do not enter the charts.

The hash and literal EPS/revenue table values are checked by [extract.py](../../data/collection/hana_guide_round4/extract.py). Raw records, pages and source links are retained in that directory. Annual fiscal periods in the browser use the issuer calendars, not rounded month-end template labels.
