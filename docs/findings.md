# Findings

## Headline
Paid social looks 26% cheaper than paid search per lead (€11.5 vs €15.6), but it converts at less than half the rate (5.6% vs 12.3%). So each won seller costs 63% more (€207 vs €127) and earns half as much in its first 3 months (€5.77 vs €11.92 of Olist revenue). On 3-month LTV:CAC, paid search is 3.4× better. Ranking channels by cost per lead points budget the wrong way.

## What drives it
CAC = CPL ÷ conversion rate. A cheap lead that rarely converts is an expensive customer. The goal is to see the actual value of a lead, not its price tag.

## Other findings
1. **The best-converting channel is "unknown".** Leads with no tracked channel convert at 16.7% (193 deals from 1,157 leads), the highest of all. The most valuable leads can't be attributed, so every channel's numbers undercount the channel those leads really came from. Fixing tracking comes before moving budget.
2. **No channel pays back within 3 months.** 3-month LTV:CAC is below 0.1 for every paid channel. At a 10% commission (`take_rate`, an assumption), payback takes years: seller acquisition is a long-term investment. The 3-month metric is for ranking channels against each other, not for proving profit.

## So what (3 actions)
| Action | Owner | Expected impact |
|---|---|---|
| Shift part of the paid-social budget to paid search, as a test with a holdout | Marketing (paid media) | Lower CAC on the shifted budget: each seller costs €127 instead of €207 |
| Fix lead attribution: UTM tags on every form, CRM source mandatory for sales-sourced leads | Marketing ops + Sales | 1,157 leads (14.5%) move from "unknown" into real channels, so budget decisions use complete data |
| Report CAC and 3-month LTV:CAC by channel monthly, alongside CPL | Marketing analytics | Budget decisions based on customer value, not lead price |

## Caveats
- **Spend is simulated** (ADR-003). CPL is an assumption; conversion and revenue are real Olist data. The reversal comes from the real part.
- **Small samples:** email (13 LTV-eligible deals), display (6) and other publicity (3) are too small to rank reliably.
- **3-month window:** only deals won by 31 May 2018 had 3 full months before the data ends (31 Aug 2018). See the data contracts on right-censoring.
- **Take rate of 10%** is an assumption; LTV scales directly with it, but the channel ranking does not change.
