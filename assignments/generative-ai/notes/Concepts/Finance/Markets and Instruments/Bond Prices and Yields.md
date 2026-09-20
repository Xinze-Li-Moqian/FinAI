---
aliases:
- bond prices and yields
- bond price
- bond yield
tags:
  - node/concept
  - cluster/rates-and-bonds
reviewed_on: 2026-09-20
---

# Bond Prices and Yields

A bond price is what a buyer pays; a yield relates that price to its promised cash flows. For a plain fixed-rate bond with unchanged cash flows, price and required yield move in opposite directions. The coupon rate on that bond remains fixed. [SEC Investor Bulletin: Interest rates and fixed-rate bond prices](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-86)

For annual payments and an annual effective yield $y$:

$$P=\sum_{t=1}^{T}\frac{CF_t}{(1+y)^t}.$$

**Worked example, calculated here:** a one-year bond paying $1,050 at maturity is worth $1,000 at a 5% yield and about $990.57 at 6%. This comparison holds the cash flow and remaining maturity constant. Default, embedded options and changing expected cash flows require additional analysis.

## Source-reading example

[[Transcripts/20220211_Staggering Inflation Sends Bond Market Tumbling_CEXa_YaJzus|Staggering Inflation Sends Bond Market Tumbling]] reports selling after an inflation surprise. This illustrates the speaker's interpretation of an event; the transcript alone does not independently verify the data or establish its cause. Its filename date is unverified.

## Relationships

- **uses_discount_rate → [[Concepts/Economics/Monetary Economics/Interest and Interest Rates|Interest and Interest Rates]]** — Bond valuation discounts future cash flows using a required yield. A single yield-to-maturity is a summary; a full valuation may use maturity-specific discount rates. [SEC Investor Bulletin: Interest rates and fixed-rate bond prices](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-86) ^rates-rel-13

- **has_sensitivity_measure → [[Concepts/Finance/Investing and Portfolios/Bond Duration|Bond Duration]]** — Duration summarizes local price sensitivity to a yield change. Specify the duration measure and cash-flow assumptions. [FINRA: Duration and interest-rate risk](https://syndication.finra.org/content/duration-what-interest-rate-hike-could-do-your-bond-portfolio) ^rates-rel-14
