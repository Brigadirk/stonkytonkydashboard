# BESI access options

Verified against public primary pages on 10 September 2026. Retained artifacts and UTC capture times are in `data/discovery/besi_access/`. This pass did not alter round8 observations or any app output.

## Smallest IEX subscription for the identified articles

**IEX Premium, one-month option, is advertised at €17.95 per month.** The public subscription selector and the following order page both show this price. Premium promises access to online Premium content and daily stock analyses. That supports choosing Premium for the identified Hildo Laman articles. It does **not** establish that the unseen articles contain the precise consecutive annual EPS tables we need. [Premium order choices](https://premium.iex.nl/marktplaats/abonnement.aspx?type=digitaal), [one-month order page](https://premium.iex.nl/marktplaats/order.aspx?id=421).

| Tier | One-month option | One-year option, monthly displayed rate | Two-year option, monthly displayed rate | Relevant entitlement |
|---|---:|---:|---:|---|
| Premium | €17.95 | €15.95 | €14.95 | Online Premium articles |
| Premium Plus | €20.95 | €17.95 | €15.95 | Online articles plus digital IEX Expert magazine |

The cheaper starting prices on the marketing page correspond to longer terms. Premium Plus is only needed for the additional digital magazine entitlement, not for the ordinary online Premium analyses. No evidence found that an IEX Pro product is required for these articles. [Plan comparison](https://premium.iex.nl/), [Plus order choices](https://premium.iex.nl/marktplaats/abonnement.aspx?type=plus).

These are recurring subscription offers, not verified one-off purchases. The marketing page says discounted terms continue until the discount period ends and subsequently move to the then-current regular rate; it describes a one-month cancellation notice. The help center contains older terminology and more detailed renewal instructions. Check the final terms at purchase rather than assuming the entire cost will be one monthly payment. No checkout details were entered and no purchase or account action occurred. [Current plan FAQ](https://premium.iex.nl/), [help center](https://www.iex.nl/content/helpcentrum.aspx).

## Exact articles to inspect once entitled

| Original article | Verified original date | Public content | What remains unverified |
|---|---|---|---|
| [Langdurige groei voor Besi betekent hogere waardering](https://www.iex.nl/Premium/Adviezen/854137/Langdurige-groei-voor-Besi-betekent-hogere-waardering.aspx) | 19 February 2026, 13:00 printed local time | Hildo Laman article excerpt; zero HTML tables | Full model, adjustment/dilution, actual revision dates |
| [Koersdoelverhoging voor Besi](https://www.iex.nl/Premium/Adviezen/868324/Koersdoelverhoging-voor-Besi.aspx) | 19 June 2026, 11:45 printed local time | Hildo Laman article excerpt and explicit subscription gate | Whether a revised FY2026/27/28 EPS table is present |
| [Orders Besi overtuigen, resultaten net niet](https://www.iex.nl/Premium/Adviezen/871925/Orders-Besi-overtuigen-resultaten-net-niet.aspx) | 23 July 2026, 13:00 printed local time | Hildo Laman article excerpt and explicit subscription gate | Whether annual EPS assumptions changed and which definition applies |

The correct February URL was recovered from the publisher's [20 February IEX podcast description distributed by Apple](https://podcasts.apple.com/pk/podcast/dit-belastingplan-ontmoedigt-mensen-om-te-beleggen/id1535360244?i=1000750673579). It is distinct from the already collected StockWatch/Saxo February 19 LSEG consensus table. A Grok claim that a February IEX table was public was not confirmed. Exact searches for `IEX04_2026_compressed`, `IEX05_2026` and q4cdn variants yielded no verified original PDF. No guessed magazine file was treated as evidence.

The access test should retain the full original article and any table image, then verify the forecast owner, EPS adjustments, denominator, fiscal years, currency, and whether the article actually revises the model. Article access alone cannot resolve the presently unknown IEX EPS definition. General online-article entitlement also does not establish a complete five-year archive of every numerical model.

Subsequent result: the public original February 27 magazine was recovered and its Hildo table integrated in [BESI round9](BESI_ROUND9.md). This improves an earlier vintage; it does not expose the gated June or July articles above.

## Other issuer-listed research providers

[BESI's research coverage directory](https://www.besi.com/investor-relations/research-coverage/) lists 23 independent providers and analyst names. The entries are plain text, with no report downloads or links to dated EPS models. A current coverage-directory name must not be applied retrospectively to an older report by a different writer.

Selected primary distribution routes were checked, rather than treating the issuer directory as a report archive:

| Route | Original public evidence | Outcome |
|---|---|---|
| [New Street BESI coverage](https://www.newstreetresearch.com/company/besi/) | Lists Pierre Ferragu and Ben Harwood on July 24, 2026 research, and Pierre Ferragu on June 19 | Both linked original report URLs return a login page. No annual EPS model is public. The index also lists older 2022–25 events, which are not forecasts |
| [New Street July 24 original report](https://www.newstreetresearch.com/research/besi-2q26-broad-based-order-strength-sets-up-continued-momentum-buy/) | Correct report endpoint exists | Authentication gate, not an anti-bot error. No email/login request sent |
| [New Street June 19 original report](https://www.newstreetresearch.com/research/besi-capital-markets-daystrong-outlook-increasingly-reflected-in-the-stock/) | Correct report endpoint exists | Same authentication gate |
| [UBS original disclosures](https://researchdmz.ibb.ubs.com/openaccess/compliance/131994_1_new.html) | Dated BESI ratings and targets from 2023 through June 2026 | No annual EPS forecasts; target history cannot substitute for earnings estimates |
| [KBC/Bolero February 19, 2026](https://www.bolero.be/nl/analyse-en-inzicht/blog/hoger-koersdoel-voor-besi-bij-kbc-securities) | Names Thibault Leneeuw and explicitly refers to diluted EPS growth | No numeric consecutive annual EPS table. Reported versus adjusted numerator remains unspecified |
| [KBC/Bolero June 12, 2025](https://www.bolero.be/nl/analyse-en-inzicht/blog/besi-verhoogt-financiele-vooruitzichten-met-aangepaste-tijdlijn) | Names the analyst and discusses FY2027 valuation assumptions | Price targets and multiples only; EPS was not calculated from them |
| [KBC/Bolero recent public blog](https://www.bolero.be/nl/blog/latest?page=3) | BESI discussion after Hot Chips 2026 names Quinten Nijs and says existing forecasts are retained | No annual EPS values. The mutable blog capture is not a new model revision |
| Berenberg/Arete/Van Lanschot Kempen indexed primary-domain searches | Current coverage names are confirmed by the issuer | No newly verified public full BESI annual model found in this bounded pass; this is not proof that none exists |

An additional [AlphaValue May 20, 2026 report landing page](https://www.alphavalue.com/Research/ViewItem/30e8287f-5f54-f111-b78e-00155d6aa002?NewsStyle=Publish) was indexed with a report description and 49-page count, but both direct retrieval and browser opening reached a failed browser-verification page. This is a retrieval limitation for the landing page. The index description does not establish that the complete report would be free once rendered. No annual figures were extracted.

## Additional public historical lead

Add Value Fund is a separate buy-side original source, not one of the named providers in the issuer directory. Its [January 2024 report](https://addvaluefund.nl/uploads/media/maandberichten/Add-Value-Fund-maandbericht-januari-2024_2024-02-02-165401_lowh.pdf), physical page 9, explicitly states BESI EPS assumptions of approximately €3.50 for FY2024 and €7 for FY2026. The [June 2023 report](https://addvaluefund.nl/uploads/media/maandberichten/Add-Value-Fund-maandbericht-juni-2023_2023-07-13-135435_ylio.pdf), physical pages 7–8, states approximately €2.25 for FY2023 and €6 for FY2025, plus a €7 scenario labelled 2026/27.

Both original PDFs are retained. These are discovery candidates, not integrated observations. Their dates require publication review beyond report-month headings, individual author attribution is not established, EPS basis is unresolved, and the explicitly stated annual periods do not give consecutive FY1/FY2 pairs. The ambiguous 2026/27 scenario must not become two forecasts. No fresh public dated annual model suitable for immediate integration was found in this handoff pass.

## Access categories and handoff

1. **Publisher subscription:** IEX Premium is the smallest evidenced article-access option, €17.95 monthly for the shortest advertised term. It could expose specific missing BESI originals. This is a narrow and relatively inexpensive inspection route, with table contents still unverified.
2. **Public-page retrieval:** MarketScreener's retained round8 403 and the AlphaValue verification failure are access failures. Chartmill's JavaScript shell is an unverified rendering candidate. ScrapingBee could be tested for such pages, but it is not evidence of entitlement to IEX or other paid reports.
3. **Historical forecast-detail feed:** None of the IEX plans examined promises a structured, contributor-level, timestamped annual-estimates database across the project's ten companies. That requirement is separate from reading selected articles and is being evaluated in the broader provider workstream.

All raw sources here were fetched without payment, credentials, provider contact or external messages. `source_inventory.csv` records 20 retained artifacts and verified hashes. Existing round8 and earlier collections remain frozen.
