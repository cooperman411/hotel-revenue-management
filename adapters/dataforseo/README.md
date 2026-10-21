# DataForSEO adapter (superseded)

This folder is kept for history only. The DataForSEO placeholder has been
superseded by the source-agnostic market-data adapter.

See `../market-data/README.md` for the current market-data boundary:

- any source (rate shopper, Nuitee LiteAPI, manual CSV) that can produce the
  `market_rates` schema contract is accepted;
- DataForSEO is no longer named as a price source. It remains an
  experimental option for event and demand signals only, not for rate data.

Do not build new work against this folder.
