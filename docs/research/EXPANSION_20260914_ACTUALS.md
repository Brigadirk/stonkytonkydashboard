# Reported annual and quarterly EPS for the selected companies

This note records the September 2026 collection. Original downloads remain in the separate research archive; the reviewed values are included in `data/reviewed/expansion_20260914/`.

Collected on 14 September 2026, Amsterdam time. The cutoff is **11 September 2026**. The period-end window begins on 10 September 2020.

This folder retains issuer SEC facts and filings. `annual_latest.json` is the display input: 13 companies and 69 annual diluted EPS records. All records have a filing date, accession, source URL, local file, SHA-256 hash and location. No earnings-release date is inferred from a filing date.

## Latest annual results

| Company | Period end | Diluted EPS | Unit | Filing date | Source |
|---|---|---:|---|---|---|
| AMD | 2025-12-27 | 2.65 | USD/shares | 2026-02-04 | [SEC issuer record](https://data.sec.gov/api/xbrl/companyfacts/CIK0000002488.json) |
| CBRS | 2025-12-31 | 1.38 | USD/shares | 2026-05-14 | [SEC issuer record](https://www.sec.gov/Archives/edgar/data/2021728/000162828026035214/cerebras-424b4.htm) |
| MRVL | 2026-01-31 | 3.07 | USD/shares | 2026-03-11 | [SEC issuer record](https://data.sec.gov/api/xbrl/companyfacts/CIK0001835632.json) |
| TSM | 2025-12-31 | 10.43 | USD/ADS | 2026-04-16 | [SEC issuer record](https://www.sec.gov/Archives/edgar/data/1046179/000162828026025362/tsm-20251231.htm) |
| ANET | 2025-12-31 | 2.75 | USD/shares | 2026-02-17 | [SEC issuer record](https://data.sec.gov/api/xbrl/companyfacts/CIK0001596532.json) |
| VRT | 2025-12-31 | 3.41 | USD/shares | 2026-02-13 | [SEC issuer record](https://data.sec.gov/api/xbrl/companyfacts/CIK0001674101.json) |
| NBIS | 2025-12-31 | 0.33 | USD/shares | 2026-04-30 | [SEC issuer record](https://data.sec.gov/api/xbrl/companyfacts/CIK0001513845.json) |
| ORCL | 2026-05-31 | 5.83 | USD/shares | 2026-06-22 | [SEC issuer record](https://data.sec.gov/api/xbrl/companyfacts/CIK0001341439.json) |
| MSFT | 2026-06-30 | 17.95 | USD/shares | 2026-07-29 | [SEC issuer record](https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json) |
| AMZN | 2025-12-31 | 7.17 | USD/shares | 2026-02-06 | [SEC issuer record](https://data.sec.gov/api/xbrl/companyfacts/CIK0001018724.json) |
| META | 2025-12-31 | 23.49 | USD/shares | 2026-01-29 | [SEC issuer record](https://data.sec.gov/api/xbrl/companyfacts/CIK0001326801.json) |
| SPCX | 2025-12-31 | -1.69 | USD/shares | 2026-06-12 | [SEC issuer record](https://www.sec.gov/Archives/edgar/data/1181412/000162828026042639/spaceexplorationtechnologi.htm) |
| PLTR | 2025-12-31 | 0.63 | USD/shares | 2026-02-17 | [SEC issuer record](https://data.sec.gov/api/xbrl/companyfacts/CIK0001321655.json) |

These are reported annual earnings. They are not adjusted earnings forecasts. The annual list is for a separate results table; it does not create a valuation target or a forecast comparison.

## Basis and limits

- **TSMC:** The display uses directly reported USD per ADS from each annual Form 20-F. Each ADS represents five ordinary shares. The issuer translates these IFRS results at the stated year-end exchange rate for reader convenience. This differs from Taiwan IFRS earnings and from quarterly USD/ADS conversions. The 2025 IFRS amounts are TWD 65.47 per ordinary share and USD 10.43 per ADS. [2025 Form 20-F](https://www.sec.gov/Archives/edgar/data/1046179/000162828026025362/tsm-20251231.htm).
- **Cerebras:** Annual results predate its May 2026 IPO. The 2025 GAAP diluted EPS is USD 1.38. The separate USD 0.42 pro forma result is excluded. Share classes, preferred-share participation and the IPO capital structure limit comparison with later periods. [Final prospectus](https://www.sec.gov/Archives/edgar/data/2021728/000162828026035214/cerebras-424b4.htm).
- **SpaceX:** Annual results predate its June 2026 IPO. The final prospectus includes xAI and X under common-control accounting and reflects the five-for-one split effective 4 May 2026. The 2024 diluted EPS rounds to USD 0.00. [Final prospectus](https://www.sec.gov/Archives/edgar/data/1181412/000162828026042639/spaceexplorationtechnologi.htm).
- **Nebius:** The display shows 2024 and 2025 only. Earlier Yandex results remain in the raw files. Total 2025 diluted EPS of USD 0.33 includes USD 0.04 from continuing operations and USD 0.29 from discontinued operations. [2025 Form 20-F](https://www.sec.gov/Archives/edgar/data/1513845/000110465926052948/nbis-20251231x20f.htm).
- **Arista:** The latest 2020 and 2021 API facts use an earlier share basis. Later comparative periods reflect the four-for-one split effective 3 December 2024. These two older values require a split adjustment before direct comparison with current per-share figures. They remain as filed in this table. [2025 Form 10-K, Note 1](https://www.sec.gov/Archives/edgar/data/1596532/000159653226000013/anet-20251231.htm).
- **Fiscal periods:** Annual results use exact period-end dates. Oracle ends in May, Microsoft in June, and Marvell in late January or early February. The filing fiscal year on a comparative XBRL fact is not used as the earnings year. The SEC source records in each row retain the exact context.

## Files and checks

- `manifest.json`: 13 SEC companyfacts files and 13 submissions files. Issuer names and tickers were checked against the requested identities.
- `filing_downloads.json`: 11 complete SEC filings with original bytes and SHA-256 hashes. This fills annual API gaps for Cerebras, SpaceX and TSMC.
- `eps_all_vintages.json` and `.csv`: 1,380 basic and diluted EPS facts, including 312 diluted quarter filing-vintage facts. Repeated contexts from different filings remain separate.
- `annual_latest_vintage.json`: Latest standard-API annual diluted EPS context per company, period and unit. This is a raw extraction; it includes old Nebius/Yandex records and TSMC ordinary-share units.
- `quarterly_latest_vintage.json`: Latest standard-API quarter facts. Fourth quarters absent from SEC facts are not computed as annual less nine months, because separate EPS denominators can make that subtraction invalid.
- `annual_latest.json`: 69 display records. It selects USD/ADS for TSMC, adds annual prospectus facts, and omits legacy Yandex years from the display.
- `collect.py` and `build_annual.py`: Collection and display-file construction.
- `validation.json`: All 37 raw downloads passed hash checks. All 13 SEC ticker identities match. No same-context, same-filing conflicting diluted EPS values were found.

## Remaining gaps

The SEC standard API did not supply annual Cerebras or SpaceX facts, or TSMC 2025 annual facts. The retained full filings fill these annual gaps. It did not supply quarter facts for TSMC or Nebius. Their quarterly issuer releases were not collected in this bounded task. SEC facts also omit some fiscal fourth quarters. No absent period is assigned zero.

The oldest available Cerebras annual period is 2022 and the oldest SpaceX annual period is 2023 in the retained registration statements. These fiscal histories do not imply public share-price history before either IPO. No broker estimates, forecast comparisons or valuation targets were created here.
