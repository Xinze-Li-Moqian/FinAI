---
aliases:
- nominal and real interest rates
- nominal interest rate
- real interest rate
- inflation-adjusted interest rate
tags:
  - node/concept
  - cluster/rates-and-bonds
reviewed_on: 2026-09-20
---

# Nominal and Real Interest Rates

A **nominal rate** describes the monetary payment; a **real rate** describes the inflation-adjusted purchasing-power result. [ECB: Nominal and real interest rates](https://www.ecb.europa.eu/ecb-and-you/explainers/tell-me/html/nominal_and_real_interest_rates.en.html)

For a realized one-period return with nominal rate $i$ and inflation $\pi$ over the same period:

$$r=\frac{1+i}{1+\pi}-1\approx i-\pi.$$

For an expectation-based comparison, use expected inflation over that horizon: $r^e\approx i-\pi^e$. This is an approximation, not an identity about uncertain future outcomes.

**Worked example, calculated here:** a 5% nominal return with 3% realized inflation gives $1.05/1.03-1=1.94\%$ real, approximately 2%. Subtracting last year's inflation from a long-term bond yield does not by itself establish its future real return.

## Source-reading example

In [[Transcripts/20220822_Can the Fed Fight Inflation with Negative Real Rates_B9KoZrouVW4|Can the Fed Fight Inflation with Negative Real Rates?]], the speaker argues that tighter borrowing conditions can matter even when a quoted rate is below recent inflation. His later deflation scenario is a forecast, not part of this definition. The transcript date comes from an unverified instructor filename.

## Relationships

- **adjusts_measure → [[Concepts/Economics/Monetary Economics/Interest and Interest Rates|Interest and Interest Rates]]** — A real rate expresses an interest rate in purchasing-power terms. Distinguish a realized rate from an expectation-based estimate. [ECB: Nominal and real interest rates](https://www.ecb.europa.eu/ecb-and-you/explainers/tell-me/html/nominal_and_real_interest_rates.en.html) ^rates-rel-03

- **adjusts_for → [[Concepts/Economics/Macroeconomics/Inflation|Inflation]]** — Subtracting inflation gives the usual approximate real rate. Match periods; the exact realized gross-return ratio is shown below. [ECB: Nominal and real interest rates](https://www.ecb.europa.eu/ecb-and-you/explainers/tell-me/html/nominal_and_real_interest_rates.en.html) ^rates-rel-04
