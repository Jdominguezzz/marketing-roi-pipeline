# Data contracts

What each source table promises: grain, keys, ranges and known quality issues.
Every promise here becomes a dbt test in `transform/`, and every issue is fixed in exactly one staging model.

Data: Olist public datasets on Kaggle (CC BY-NC-SA 4.0). Raw files are not committed to this repo.

---

## marketing_qualified_leads
- **Source:** Kaggle, Marketing Funnel by Olist, `olist_marketing_qualified_leads_dataset.csv`
- **Grain:** one row per marketing-qualified lead (a seller who filled in a form on a landing page)
- **Primary key:** mql_id (8,000 rows = 8,000 distinct → unique ✔)
- **Foreign keys:** referenced BY closed_deals.mql_id (842 deals, 0 orphans). landing_page_id → no landing-page table available (495 distinct pages)
- **Rows:** 8,000 · **Date range:** 2017-06-14 to 2018-05-31 (column: first_contact_date, already a DATE)
- **Key columns null %:** origin 0.75% (60 rows); all other columns 0%
- **Data-quality issues:**
  1. Two kinds of missing channel: 60 NULL + 1,099 literal "unknown" = 1,159 leads (14.5%) with no channel → unify as `unknown` in staging and report it as its own row, never drop it (dropping it would inflate every channel's share).
  2. Vague channels: "other" (150) and "other_publicities" (65) aren't actionable → keep them, but group them as "other" in `dim_channel` and say so.
  3. Partial edge month: June 2017 has only 4 leads (data starts on 14 Jun) → exclude it from month-over-month charts or flag it as partial.
  4. Volume break: leads jump from 200 (Dec 2017) to 1,141 (Jan 2018), 5.7×. That's a business change (a bigger acquisition push), not a data error → note it in findings and calibrate the spend simulator to follow it, otherwise CPL will look 5× better in 2018 for no reason.

## closed_deals
- **Source:** Kaggle, Marketing Funnel by Olist, `olist_closed_deals_dataset.csv`
- **Grain:** one row per won deal (a lead that signed up as a seller)
- **Primary key:** mql_id (842 rows = 842 distinct → unique ✔). seller_id is also unique (842 distinct), so 1 lead = 1 deal = 1 seller
- **Foreign keys:** mql_id → marketing_qualified_leads.mql_id (0 orphans) · seller_id → order_items.seller_id (380 of 842 found = **45.1% match**, see below) · sdr_id (36) and sr_id (22) are sales reps, no table available
- **Rows:** 842 · **Date range:** 2017-12-05 to 2018-11-14 (column: won_date, TIMESTAMP)
- **Key columns null %:** mql_id, seller_id, won_date 0% · lead_behaviour_profile 21% · has_company, has_gtin, average_stock, declared_product_catalog_size ~92% (optional form fields, sparse)
- **Data-quality issues:**
  1. declared_monthly_revenue is 0 in 797 rows (94.7%), with outliers up to 50,000,000 that push the mean to 73k → it means "not filled in", not "no revenue". Never use it as a revenue measure; revenue comes from order_items.
  2. 1 deal has won_date 2 days before its lead's first_contact_date (impossible) → flag with a singular dbt test, keep the row, set days_to_close to NULL.
  3. **Right-censoring:** won_date runs to Nov 2018, but order data effectively ends on 31 Aug 2018 (see orders). 50 deals won after 1 Sep 2018 have no orders at all, and recent cohorts had little time to sell → never compare "revenue to date" across cohorts; compare cohorts over the same window (see design decisions).
  4. Sparse profile columns (~92% null) → keep them in staging, but don't use them as segmentation features without saying how sparse they are.
- **Median days from first contact to won:** 14 (max 427)

## order_items
- **Source:** Kaggle, Brazilian E-Commerce Public Dataset by Olist, `olist_order_items_dataset.csv`
- **Grain:** one row per item within an order
- **Primary key:** (order_id, order_item_id), composite (112,650 rows = 112,650 distinct pairs ✔). order_id alone is NOT a key: 98,666 orders, up to 21 items in one order
- **Foreign keys:** order_id → orders (0 orphans) · seller_id → sellers (0 orphans) · product_id → products (not used in this project)
- **Rows:** 112,650 · **Date range:** shipping_limit_date 2016-09-19 to 2020-04-09 (dates come from orders; see issue 3)
- **Key columns null %:** 0% on all columns
- **Data-quality issues:**
  1. Grain trap: joining orders to order_items multiplies order-level columns (e.g. payment totals) by the number of items → aggregate items to order level *before* joining anything order-grain.
  2. 1,278 orders contain items from more than one seller → seller revenue must be summed from items (price), never taken from order or payment totals.
  3. shipping_limit_date goes to 2020-04-09, after the dataset ends → it's a deadline, not an event date; use orders.order_purchase_timestamp for time.
  4. freight_value is 0 in 383 rows (free shipping, plausible) · price ranges 0.85 to 6,735 BRL, no zeros → revenue measure = price (GMV excludes freight).
- **Totals:** price BRL 13.59M · freight BRL 2.25M · sellers from closed_deals account for BRL 0.68M of price

## orders
- **Source:** Kaggle, Brazilian E-Commerce Public Dataset by Olist, `olist_orders_dataset.csv`
- **Grain:** one row per order
- **Primary key:** order_id (99,441 rows = 99,441 distinct ✔)
- **Foreign keys:** customer_id → customers (0 orphans) · referenced BY order_items (775 orders have no items) and order_payments (1 order has no payment)
- **Rows:** 99,441 · **Date range:** order_purchase_timestamp 2016-09-04 to 2018-10-17
- **Key columns null %:** order_approved_at 160 rows · order_delivered_carrier_date 1,783 · order_delivered_customer_date 2,965 (expected for orders not yet delivered)
- **Data-quality issues:**
  1. **The real end of the data is 31 Aug 2018.** Sep 2018 has 16 orders and Oct 2018 has 4, against ~6,500 a month before → treat 2018-08-31 as the observation end date (a dbt var), and exclude Sep and Oct 2018 from any monthly chart.
  2. Sparse start too: Sep 2016 has 4 orders, Nov 2016 has none, Dec 2016 has 1 → the time series is only usable from Jan 2017.
  3. Status: 96,478 delivered, 625 canceled, 609 unavailable, plus 1,729 in progress → revenue counts only status `delivered` (state the rule; it's a business definition, not a technical one).
  4. 166 orders have the carrier pickup before the purchase timestamp, and 8 "delivered" orders have no delivery date → flag with tests; they don't affect revenue.

## order_payments
- **Source:** Kaggle, Brazilian E-Commerce Public Dataset by Olist, `olist_order_payments_dataset.csv`
- **Grain:** one row per payment within an order (vouchers and split payments create several rows)
- **Primary key:** (order_id, payment_sequential), composite (103,886 rows = 103,886 distinct pairs ✔). order_id alone is NOT a key: 2,961 orders have more than one payment
- **Foreign keys:** order_id → orders (0 orphans)
- **Rows:** 103,886 · **Date range:** no date column (use the order's date)
- **Key columns null %:** 0%
- **Data-quality issues:**
  1. payment_type includes `not_defined` (3 rows) and 9 payments of value 0 → keep them, exclude from payment-mix analysis.
  2. payment_installments = 0 in 2 rows (impossible; minimum is 1) → flag with a test.
  3. Sum of payments ≠ sum of item price + freight by more than BRL 1 in 249 orders (interest on instalments, vouchers) → payments are NOT used for seller revenue; only order_items.price is.
- **Why it's in scope at all:** it's the cross-check for revenue (payments total BRL 16.01M vs items price + freight BRL 15.84M); the reconciliation becomes a dbt test with a tolerance.

## customers
- **Source:** Kaggle, Brazilian E-Commerce Public Dataset by Olist, `olist_customers_dataset.csv`
- **Grain:** one row per customer **per order** (not per person)
- **Primary key:** customer_id (99,441 = one per order ✔). The real person is customer_unique_id: 96,096 distinct, and 2,997 people ordered more than once
- **Foreign keys:** referenced BY orders.customer_id (0 orphans)
- **Rows:** 99,441 · **Date range:** none (dimension)
- **Key columns null %:** 0%
- **Data-quality issues:**
  1. Misleading key: customer_id looks like a customer key but is generated per order → any "unique customers" or repeat-rate metric must use customer_unique_id.
  2. Zip prefix has leading zeros in 23,995 rows → cast to VARCHAR (same issue as sellers).
  3. City names need the same normalisation as sellers. Not needed for the ROI question, kept for completeness.

## sellers
- **Source:** Kaggle, Brazilian E-Commerce Public Dataset by Olist, `olist_sellers_dataset.csv`
- **Grain:** one row per seller
- **Primary key:** seller_id (3,095 rows = 3,095 distinct → unique ✔)
- **Foreign keys:** referenced BY order_items.seller_id (0 orphans) and closed_deals.seller_id (see match rate)
- **Rows:** 3,095 · **Date range:** none (dimension table, no event date)
- **Key columns null %:** 0% on all 4 columns
- **Data-quality issues:**
  1. Zip code prefix has leading zeros in 1,027 rows (e.g. "01023"). Read as a number it becomes 1023 and geography joins break → cast to VARCHAR in staging.
  2. City names are dirty ("sao paulo", "são paulo", "sao paulo / sao paulo", "sao paulop", "04482255") → normalise in staging (lowercase, strip accents, drop "/ state" suffix); never use city as a join key.
  3. Every seller here has at least one order item: this is "sellers who sold", not "all sellers". Funnel-acquired sellers who never sold are absent → affects the match rate; state it in the README.

---

## Match rate: closed_deals → order_items
- Distinct sellers in closed_deals: **842**
- Of those, found in order_items: **380 (45.1%)**
- None of the 380 sold anything before their won_date ✔ (the acquisition date is consistent)
- **What it means for CAC and LTV:** CAC must divide spend by *all* 842 won deals. A seller who never sells still cost money to acquire. Dividing by the 380 who sold would make acquisition look 2.2× cheaper than it is. LTV per seller must also average over all deals in a cohort (non-sellers count as 0), otherwise it's survivorship bias.

## Design decisions these contracts force
1. **Observation end date = 2018-08-31**, stored as a dbt var, not hard-coded.
2. **LTV window:** a cohort is only measured over months it fully observed.
   - **3-month LTV (primary):** deals won Dec 2017 to May 2018 → 665 deals, 345 matched sellers.
   - **6-month LTV (secondary):** deals won Dec 2017 to Feb 2018 only → 189 deals, 103 matched sellers. Too small to rank 10 channels reliably; report it with that caveat.
   - Deals won Jun 2018 onward: shown for funnel volume and CAC only, never for LTV.
3. **Revenue = sum of order_items.price for orders with status `delivered`**, attributed to the item's seller. Freight and payments are excluded and used only for reconciliation tests.
4. **Channel = leads.origin**, with NULL and "unknown" unified as `unknown`, kept as its own row.
5. **Composite keys** (order_items, order_payments) get a surrogate key in staging (`dbt_utils.generate_surrogate_key`) so every model has a single-column key to test.
