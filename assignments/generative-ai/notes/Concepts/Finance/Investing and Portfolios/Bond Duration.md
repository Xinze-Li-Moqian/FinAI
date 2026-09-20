---
aliases:
- bond duration
- modified duration
- Macaulay duration
tags:
  - node/concept
  - cluster/rates-and-bonds
reviewed_on: 2026-09-20
---

# Bond Duration

Duration describes a bond's exposure to yield changes. **Macaulay duration** summarizes the timing of discounted cash flows; **modified duration** measures local price sensitivity. **Effective duration** can account for cash flows changing with rates. [FINRA: Duration and interest-rate risk](https://syndication.finra.org/content/duration-what-interest-rate-hike-could-do-your-bond-portfolio)

For modified duration $D_{mod}$:

$$\frac{\Delta P}{P}\approx-D_{mod}\,\Delta y.$$

Here $\Delta y$ is a decimal yield change. **Worked example, calculated here:** duration 6 and a yield rise of 0.005 (50 basis points) imply approximately a 3% price decline.

This is a first-order approximation. Large moves, changing cash flows and nonparallel yield-curve shifts need more detail. Low duration does not remove default, liquidity or inflation risk. [FINRA: Duration and interest-rate risk](https://syndication.finra.org/content/duration-what-interest-rate-hike-could-do-your-bond-portfolio)

## Relationships

- **measures_sensitivity_of → [[Concepts/Finance/Markets and Instruments/Bond Prices and Yields|Bond Prices and Yields]]** — Higher modified duration implies a larger first-order percentage price response to the same yield change. Small yield change, unchanged cash flows; a single duration does not capture every yield-curve movement. [FINRA: Duration and interest-rate risk](https://syndication.finra.org/content/duration-what-interest-rate-hike-could-do-your-bond-portfolio) ^rates-rel-15
