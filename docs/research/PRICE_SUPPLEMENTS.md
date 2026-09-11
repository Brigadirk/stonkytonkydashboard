# Reviewed public daily-close supplements

Checked 10 September 2026. Four originally sourced observations resolve or independently check explicit holes in the base Yahoo daily feed. The final Yahoo refresh also supplied the two Korean September 10 closes, matching Naver exactly; those base-feed records retain their Yahoo provenance. The ASML and BESI September 7 rows are inserted from the exchange source. Each source is retained by hash, and the chart export now includes price-source URLs and hashes separately from forecast provenance. These are observed closes, not interpolated prices.

| Listing | Date | Native daily close | Original source |
|---|---|---:|---|
| SK hynix, KRX 000660 | 2026-09-10 | KRW 1,853,000 | [Naver dated daily response](https://api.finance.naver.com/siseJson.naver?symbol=000660&requestType=1&startTime=20260910&endTime=20260910&timeframe=day), matched to its KRX-provided daily HTML table |
| Samsung Electronics, KRX 005930 | 2026-09-10 | KRW 269,000 | [Naver dated daily response](https://api.finance.naver.com/siseJson.naver?symbol=005930&requestType=1&startTime=20260910&endTime=20260910&timeframe=day), matched to its KRX-provided daily HTML table |
| ASML, Euronext Amsterdam XAMS | 2026-09-07 | EUR 1,500.40 | [Original exchange historical daily table](https://live.euronext.com/fr/product/equities/NL0010273215-XAMS) |
| BESI, Euronext Amsterdam XAMS | 2026-09-07 | EUR 202.50 | [Original exchange historical daily table](https://live.euronext.com/fr/product/equities/NL0012866412-XAMS) |

Both Korean observations were retrieved after the completed regular session. Their observation date equals the current dataset cutoff, so no later split normalization is required. Naver's historical adjustment convention remains undocumented. The older September 19, 2025 closes were also recovered and preserved, but are not admitted into the valuation price series. [Korean source checks and issuer share-capital evidence](KOREAN_PRICE_GAP_CHECK.md).

The ASML and BESI daily tables explicitly identifies the Amsterdam listing and its closing-price column. The adjacent September 4, 8, 9 and 10 closes match the retained base feed within floating-point representation. There is no intervening split in the retained action history between September 7 and this cutoff. The original page's public JavaScript renders an encrypted transport response; the exchange DOM was captured after rendering, with the original HTTP responses retained separately. No access gate was bypassed and no proxy service was used.

Policy: `data/market/price_supplements.json`. Rebuild: `scripts/apply_price_supplements.py`, also invoked inside the archived refresh workflow. The parser verifies original source hashes and exact dated table values, applies only subsequent known stock splits, skips future observations, and rejects disagreement with an existing base-feed value. It does not overwrite an observed price silently. A future price refresh still needs the same documented corporate-action conventions as the rest of the dataset.

Reproduce the public exchange captures with `node data/discovery/asml_price_gap_check/collect_rendered.mjs asml` or the same command ending in `besi`. Captures use content-addressed filenames; a new capture is a new artifact. Recheck Naver evidence with `python3 data/discovery/korean_price_gap_check/verify_closes.py`. The latter revalidates retained rows and does not modify the central price file.

These repairs do not amount to a complete independent exchange-calendar audit. The two older Korean provider holes remain explicit, and exchange-session completeness is still a backtest prerequisite.
