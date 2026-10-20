# ADR-003: Simulated ad spend, calibrated to real lead volume

- **Status:** Accepted · 2026-10-20
- **Context:** CAC needs marketing spend per channel. Olist publishes leads, deals and orders, but not spend. Without spend the project can show funnel conversion and revenue, but not CAC or LTV:CAC, which is the business question.
- **Options considered:**
  1. **Drop CAC** and report conversion and revenue only: honest, but it doesn't answer the question.
  2. **One flat assumed CAC per channel:** simple, but there's no daily data to engineer, test or reconcile.
  3. **A seeded daily simulator calibrated to real lead volume (chosen).**
- **Decision:** Generate daily spend per paid channel from `config/spend_simulation.yml`:
  - base daily spend = observed leads/day (Jun–Dec 2017) × an assumed target CPL per channel;
  - a ramp on 2018-01-01 that follows the real ~4–5× lead jump, set slightly higher to model diminishing returns;
  - weekday factors and ±15% Gaussian noise, with a fixed seed (42) so every run is identical;
  - organic channels (organic_search, direct_traffic, referral) get no media spend;
  - three injected delivery problems, so staging has something real to catch: a duplicated day (2017-11-24), a file 6 days late (2018-02-10), and a renamed field `cost` (2018-03-15).
  - Files land like a real ad-platform export: one JSON per spend day, delivered the next day under `ingest_date=`.
- **Consequences:**
  - ➕ CAC and LTV:CAC can be computed and tested end to end, with realistic incremental-load problems.
  - ➕ All assumptions sit in one YAML file that anyone can challenge or change.
  - ➖ **CPL is an input, not a finding.** Channel CPLs reflect the assumed targets. Real findings come from what happens *after* the lead: conversion to deal, the 45% match rate, and revenue per acquired seller. The README must say this on its first screen.
  - ➖ Swapping in a real source (Meta or Google Ads API) changes only the extractor; staging onwards stays the same.
