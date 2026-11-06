# Market-Data Adapter

The market-data adapter is the boundary between external market signals and
the toolkit's deterministic rate engine. It is source-agnostic: any source
that can produce the `market_rates` schema contract is accepted, and sources
are interchangeable without changing the engine.

## The contract

Normalize observations into `shared/schemas/market_rates.json`:

- `observed_at` - when the data was collected (date-time);
- `stay_date` - the future stay date the rate applies to (date);
- `room_type` - the property's own room type (standard, deluxe, suite);
- `property_rate` - the property's own rate for that date and room type,
  when known; 0 is allowed and is treated as a data gap, not as a real rate;
- `comp_median_rate` - the median observed competitor rate for that date
  and room type; must be greater than 0 to be used;
- `comp_count` - how many competitor hotels contributed to the median.

The engine uses `comp_median_rate` as a position signal only. It applies at
most a 10 percent adjustment toward or away from the comp median, and it
treats a missing market file as an explicit data gap (confidence drops, the
rate is not faked as zero). See `scripts/calculate_rates.py` and
`shared/methodology/rate-optimization.md`.

## Recommended sources

1. **Subscribed rate shoppers (primary recommended path).** Use the
   hotel's existing rate shopping subscription. These tools are built
   specifically for comp-set pricing. They normalize competitor rates
   by stay date and room category, which is exactly what this schema wants.
   Export their comp-set report, map it to the schema (CSV column order is
   documented below), and feed it to `calculate_rates.py --market-rates`.
   Named tools, verified Nov 5, 2026:
   - Lighthouse Rate Insight, formerly OTA Insight.
   - RateGain Navigator, RateGain's rate intelligence platform for
     competitor rate tracking, rate parity monitoring, and demand
     forecasting.
   - Amadeus Hotelligence360.
   Any other subscribed rate shopping tool that can export a comp-set
   report by stay date and room category fits here. The point is the
   subscription, not the brand name.

2. **Veetal Connect API (recommended live retail API path, spec only, not implemented yet).**
   Veetal Connect API supplies live Booking.com, Expedia, Hotels.com, Google
   Hotels, and Airbnb rates as structured JSON, with like-for-like comparison
   by board and cancellation terms. It uses authorized data partnerships; it
   is not a scraping service. This is the live retail path when a hotel
   wants real OTA retail prices. It replaces the removed Nuitee path, which
   is not to be used for any reason.

   Status, Nov 5, 2026: no Veetal account has been created, no live call has
   been run, and `scripts/fetch_market_rates.py` does not have a Veetal mode
   yet. Do not present Veetal as implemented until the playground call below
   has been run and the adapter code exists.

   ### Credit model, verified Nov 6, 2026

   Credit is per API request, not per room/night and not per room type.
   One request is one hotel plus one stay: property, check-in, check-out,
   occupancy.

   - Accommodation parity API: 1.1765 credits per request. One call returns
     one rate per OTA for that stay, as listed on Google Hotels.
   - Expedia rates API: 1.1765 credits per request. One call returns all
     room types for that hotel and stay, with room size, bed configuration,
     board, meal plan, cancellation policies, special offers, and
     availability. Do not multiply by room type.
   - Flight rates API (real-time): 1 credit per request. Not used by this
     toolkit.

   A 3-night stay is still one request for that check-in and check-out pair,
   not three. The multiplier to watch is channels, not rooms: parity plus
   Expedia plus Booking.com for the same hotel and date is 3 requests, or
   3.5295 credits.

   Plans, annual billing as shown on the pricing page: Seed 39 euros per
   month for 10,000 credits, Grow 190 euros for 50,000, Bloom 490 euros for
   150,000. Month-to-month, without the annual discount: Seed 49 euros,
   Grow 239 euros, Bloom 690 euros. Extra credits on Seed and Grow: 5 euros
   per 1,000. Enterprise: up to 2.40 euros per 1,000 credits. Free signup:
   1,000 credits, no credit card.

   In requests at 1.1765 credits each: free is about 850 requests, Seed is
   about 8,499, Grow is about 42,497, Bloom is about 127,493.

   Worked examples, parity only, checked daily:

   - 1 hotel, next 30 arrival dates: 900 requests per month, about
     1,059 credits. Fits Seed.
   - 5-hotel comp set, 30 dates: 4,500 requests, about 5,294 credits.
     Fits Seed.
   - Same 5 hotels and dates, parity plus Expedia detail for each:
     9,000 requests, about 10,588 credits. Just over Seed.
   - 5 hotels, 90 dates, parity only: 13,500 requests, about 15,883
     credits. Needs Grow.

   ### Cache and cost control

   Real-time responses can be cached 0 to 24 hours per API, set in the
   Veetal dashboard. Within the window, a repeated request returns the
   cached payload at no extra cost. Set 6 to 24 hours for listings, 1 to 3
   hours for a hotel detail view, and use `no_cache=true` only for a
   check-price-before-booking call. Account endpoints are free, and the
   city catalog search is 0 credits. Check balance with the customer-info
   endpoint at no cost and alert on burn rate.

   ### Feed versus real-time

   Use Feed for the recurring and configured comp set, and real-time for
   the one-off and arbitrary hotel. Feed prices are bulk import prices, not
   per-request prices. For example, Events API is 4,000 credits per Tier 1
   location for 12 months ahead, and Booking Location Search is 3,592
   credits per search for 365 days ahead. Do not use a Feed call for the
   playground test.

   ### Proposed adapter shape, to be confirmed by the playground call

   Proposed, not yet built:

   ```text
   export VEETAL_API_KEY=<key from dashboard.veetal.app, Developers > Authentication>

   python3 scripts/fetch_market_rates.py --source veetal \
     --hotel-slugs <slug,slug> \
     --as-of 2026-09-01 \
     --days 14 \
     --room-map work/comp-room-map.json \
     --output inputs/market_rates.csv
   ```

   Rules for the implementation, when it is built:

   - The API key comes only from the `VEETAL_API_KEY` environment variable.
     It is never accepted as a CLI argument, never logged, and never written
     to any output file. This matches the toolkit's existing environment-only
     rule for API keys.
   - Register each hotel once through the Veetal Account API and use its
     slug. Every Feed and Real Time endpoint then accepts
     `reference_type=accommodation` plus that slug. For a known comp set,
     this is the right pattern.
   - Use the parity endpoint for the headline comp position, and the Expedia
     endpoint for room-level detail. Normalize both into the same
     `market_rates` rows, with board and cancellation recorded in the
     work notes so the rate engine does not rank a flexible breakfast rate
     against a non-refundable room-only rate.
   - Keep the existing `--room-map` rule: map supplier room labels to the
     property's room types. Unmapped offers are skipped and counted, never
     guessed.
   - Keep `property_rate` as 0, a data gap, until a live Veetal response
     proves a property rate is returned for the hotel itself. Do not invent
     a property rate from a comp median.
   - The API is now v3, base `https://api.veetal.app/v3`, with snake_case
     field names. Veetal blog examples use v2 paths. Verify the v3 parity
     and Expedia paths in the playground before writing the adapter. Do not
     hardcode a v3 path from this document alone.

   ### Playground test, one hotel, one date

   Run this before writing the adapter:

   1. Create the free Veetal Connect API account. It is 1,000 free credits,
      no credit card, one-header API key, dashboard at
      `dashboard.veetal.app`.
   2. Register one hotel and one comp hotel, and record their slugs.
   3. Call the parity endpoint for one stay date. Record the exact credit
      deduction from the dashboard or customer-info endpoint.
   4. Call the Expedia endpoint for the same hotel and stay date. Confirm
      that all room types arrive in that one call, and record the exact
      credit deduction.
   5. Check the returned fields against the `market_rates` schema:
      `observed_at,stay_date,room_type,property_rate,comp_median_rate,comp_count`.
      Note any field that does not map cleanly, and do not force it.
   6. Do not call a Feed API in this test.

**Nuitee LiteAPI (removed, do not use).**
   Nuitee is out as a market-data source. Kerry killed it Oct 21, 2026
   because this use case violates Nuitee's terms of service. That decision
   supersedes the earlier state where Nuitee LiteAPI was the implemented
   path in `scripts/fetch_market_rates.py`.
   The Nuitee code is still in the repo today, and it still needs to be
   stripped from the repo and from the adapter docs. Until that cleanup is
   done, do not present Nuitee as a sandbox, proxy, demo, or fallback path,
   and do not run a live Nuitee pull.
## No CSV option for comp set

There is no CSV option for comp-set rates and availability.

A hotel's PMS, CRS, or channel manager can export its own rates and
availability. It cannot export its competitors' rates and availability.
No one is going to hand-type comp rates for 90 to 180 days, and a
hand-entered snapshot would be rates only in any case: the `market_rates`
schema has no availability field at all, only
`observed_at,stay_date,room_type,property_rate,comp_median_rate,comp_count`.

Comp data comes only from path 1 or path 2 above: a subscribed rate
shopping tool, or Veetal. If the hotel has neither, the honest answer is
that there is no comp signal for this run. The engine then runs without
market data, lowers confidence, and says the market signal is missing,
rather than pretending a hand-typed file is a comp set.

Note for cleanup: `scripts/fetch_market_rates.py` still has a `--from-csv`
mode. That mode is not a comp source. It is test fixture handling only,
and it should not be documented as a user path. Removing or restricting
it to test fixtures is a separate code cleanup step, still to do.
Comp availability, if it is ever needed, is a separate gap: it is not in
this schema, and it would need a separate feed, for example Veetal's
Booking availability endpoint, not this file.

## Evidence rules (apply to every source)

- Record source, `observed_at` freshness, and `comp_count` coverage on every
  row. A single-hotel "median" is a weak signal; say so in the data-gap
  report rather than hiding it.
- Record collection errors (timeouts, partial dates, unmapped rooms) and
  omit failed dates instead of filling them with guesses. Partial success
  must be explicit.
- Never treat scraped, wholesale, or incomplete data as ground truth. The
  engine already bounds market influence and lowers confidence when data is
  thin; the adapter's job is to give it honest inputs.
- Never include guest or employee PII. Market data is property-level and
  public by nature; keep it that way.
- For Veetal, record the endpoint used (parity or Expedia), the cache
  setting, and whether `no_cache=true` was used, so a later reader can tell
  a fresh live price from a cached repeat.

## Output format

The adapter writes `market_rates.csv` with exactly this header:

```text
observed_at,stay_date,room_type,property_rate,comp_median_rate,comp_count
```

Example row:

```text
2026-09-01T09:00:00Z,2026-09-05,standard,0,228.50,4
```

Feed it to the rate engine with:

```text
python3 scripts/calculate_rates.py \
  --property inputs/property.json \
  --history work/history.json \
  --inventory inputs/inventory.csv \
  --reservations inputs/reservations.csv \
  --market-rates inputs/market_rates.csv \
  --as-of 2026-09-01 \
  --days 180 \
  --output outputs/rate-recommendations.csv
```

## Sources

- Veetal pricing: https://connect-api.veetal.app/pricing, rechecked Nov 6, 2026
- Veetal hotel price comparison guide: https://connect-api.veetal.app/blog/build-hotel-price-comparison-tool
- Veetal API docs: https://developers.veetal.app/
