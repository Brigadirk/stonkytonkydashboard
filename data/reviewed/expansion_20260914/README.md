# Reviewed September 2026 expansion inputs

These are the reviewed, extracted values used to add the 13 companies to the
stock snapshot. They retain source URLs, original file paths, hashes, report
and model dates, accounting bases, and exact source locations.

- `hardware.json`: AMD, Marvell, Arista, Vertiv, Nebius, and SpaceX forecasts.
- `platforms.json`: Microsoft, Amazon, Meta, Oracle, Palantir, and TSMC forecasts.
- `actuals.json`: reported annual diluted EPS for all 13 additions.
- `cerebras_gap.json`: later current-page observations excluded from the cutoff.

Original downloads and the preserved import base remain in the separate
research archive. Relative `source_file` paths refer to that archive under the
repository root. These files are inputs to the checked incremental importer,
not substitutes for its source-hash verification.

See [collection methods and limits](../../../docs/research/EXPANSION_20260914.md).
The SEC collection helper needs `SEC_USER_AGENT` set to the operator's
application name and contact email.
