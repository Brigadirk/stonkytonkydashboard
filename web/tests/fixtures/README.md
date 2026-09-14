# Portable source fixtures

`imported-forecast-baseline.json` is derived from the original upstream commit
`587e791e61dac0fb8dccf7ee7d5fc6403dd4fd42`, file
`web/public/data/dashboard.json`. Each company has the SHA-256 of its original
forecast series, serialized with `JSON.stringify`, and its retained price dates.
This checks forecast preservation without adding another complete dashboard.

`ornn/` holds the five exact public API responses and normalized manifest for
the included GPU snapshot. The GPU test checks each response hash and every
normalized daily value. It uses a later local archive when a manual refresh
changes the saved dataset. New committed GPU snapshots need matching fixtures.

Large broker PDF and issuer archives remain separate under the repository's
existing archive policy. The importer validates their hashes when those inputs
are available. Calculation and failure tests use isolated synthetic inputs.
