# Monetary-policy reading pilot

[Part 1 progress](../../README.md#current-progress) · [Theme map](../THEMES.md) · [Structured claims](claims.json)

Prepared 2026-09-20. This is a three-transcript learning exercise using the existing corpus. It supports reading and source attribution; it is not the formal Part 2 submission or an evaluation of financial truth. No paid API calls or new downloads were made.

## Learning objective

Separate what a speaker reports, how the speaker interprets it, and what the speaker predicts. A passage supports attribution to the speaker; it does not independently establish that the financial claim is true.

## Sources and theme review

All three transcripts were read. Their existing primary theme, **Central banking and monetary transmission**, is supported by their discussion of reserves, QT/QE, and balance-sheet policy. Secondary topics include sovereign debt and funding markets. No keyword rule or corpus-wide theme assignment was changed.

| ID | Source date | Video | Local text |
|---|---|---|---|
| S1 | 2025-10-16 | [The Fed Just Announced When QT Will End](https://www.youtube.com/watch?v=SDzVzd6JVdg) | [Transcript](<../../../notes/Transcripts/20251016_The Fed Just Announced When QT Will End_SDzVzd6JVdg.md>) |
| S2 | 2025-12-10 | [The Real Reason the Fed Just Ended QT](https://www.youtube.com/watch?v=58vA8WGCYEE) | [Transcript](<../../../notes/Transcripts/20251210_The Real Reason the Fed Just Ended QT_58vA8WGCYEE.md>) |
| S3 | 2026-07-09 | [The Fed is About to Do QE Without Calling it QE](https://www.youtube.com/watch?v=IQ--1laVPFE) | [Transcript](<../../../notes/Transcripts/20260709_The Fed is About to Do QE Without Calling it QE_IQ--1laVPFE.md>) |

Dates for S1 and S2 are inherited from instructor filenames and are not independently verified. S3 uses downloaded YouTube metadata. None is a verified recording date. Current Markdown SHA-256 values, exact excerpts and paragraph block references are in `claims.json`.

## Claims, arguments, and evidence

Every claim below is attributed to the Heresy Financial speaker. Evidence links refer to verified paragraphs in the canonical transcripts. The JSON retains the excerpts and their block IDs; the statements here are paraphrases.

### C01 · reported policy outlook

The speaker reports Powell saying balance-sheet runoff may stop in coming months when reserves are somewhat above the level judged ample.

- **Argument:** The quoted reserve condition is presented as the reason to approach the end of QT, rather than a fixed calendar deadline.
- **Evidence:** [SDzVzd6JVdg · p-1](<../../../notes/Transcripts/20251016_The Fed Just Announced When QT Will End_SDzVzd6JVdg.md#^p-1>).
- **Time/condition:** Coming months relative to the October 2025 transcript; no exact end date in this passage.
- **Limit:** This is a quotation relayed through the speaker and an imperfect transcript, not a directly checked Fed statement.
- **Later verification:** Locate the original speech, its date, and the exact wording of the reserve condition.

### C02 · speaker interpretation

The speaker interprets near-zero reverse-repo usage together with renewed regular-repo usage as evidence that QT has drained excess liquidity.

- **Argument:** He treats the first facility as an overflow indicator and the second as an indicator of institutions seeking cash.
- **Evidence:** [SDzVzd6JVdg · p-29](<../../../notes/Transcripts/20251016_The Fed Just Announced When QT Will End_SDzVzd6JVdg.md#^p-29>), [SDzVzd6JVdg · p-30](<../../../notes/Transcripts/20251016_The Fed Just Announced When QT Will End_SDzVzd6JVdg.md#^p-30>), [SDzVzd6JVdg · p-31](<../../../notes/Transcripts/20251016_The Fed Just Announced When QT Will End_SDzVzd6JVdg.md#^p-31>).
- **Time/condition:** Contemporaneous chart interpretation in the October 2025 transcript.
- **Limit:** The referenced charts are not included in the text. Loss of excess liquidity is not itself evidence of an imminent crisis.
- **Later verification:** Check the chart dates, the separate facility definitions, and whether their usage supports this inference.

### C03 · speaker forecast

The speaker expects renewed QE to provide demand for government borrowing over the long term.

- **Argument:** He dismisses stablecoins and changes to interest on reserves as sufficient alternatives and anticipates monetary expansion.
- **Evidence:** [SDzVzd6JVdg · p-39](<../../../notes/Transcripts/20251016_The Fed Just Announced When QT Will End_SDzVzd6JVdg.md#^p-39>), [SDzVzd6JVdg · p-40](<../../../notes/Transcripts/20251016_The Fed Just Announced When QT Will End_SDzVzd6JVdg.md#^p-40>), [SDzVzd6JVdg · p-41](<../../../notes/Transcripts/20251016_The Fed Just Announced When QT Will End_SDzVzd6JVdg.md#^p-41>).
- **Time/condition:** Long-term outlook; the excerpt gives no falsifiable date for QE restarting.
- **Limit:** This is the speaker's financing thesis, not an announced purchase program or a measured financing requirement.
- **Later verification:** Define what counts as QE, a time horizon, and the financing assumptions before evaluating the forecast.

### C04 · reported policy event

The speaker says QT ended on December 1, 2025.

- **Argument:** He subsequently describes rolling over Treasury principal and reinvesting agency principal into Treasury bills.
- **Evidence:** [58vA8WGCYEE · p-7](<../../../notes/Transcripts/20251210_The Real Reason the Fed Just Ended QT_58vA8WGCYEE.md#^p-7>), [58vA8WGCYEE · p-12](<../../../notes/Transcripts/20251210_The Real Reason the Fed Just Ended QT_58vA8WGCYEE.md#^p-12>), [58vA8WGCYEE · p-13](<../../../notes/Transcripts/20251210_The Real Reason the Fed Just Ended QT_58vA8WGCYEE.md#^p-13>).
- **Time/condition:** Claimed policy effective date: 2025-12-01; source filename date: 2025-12-10.
- **Limit:** The claimed event date and the source date are distinct. No original implementation note has been independently checked here.
- **Later verification:** Check the relevant FOMC implementation note and its effective date.

### C05 · speaker interpretation

The speaker argues that the removal of excess liquidity does not by itself imply an approaching liquidity shortage or crisis.

- **Argument:** He goes on to argue that the Fed facility supplies needed overnight liquidity, which he treats as protection against an acute shortage.
- **Evidence:** [58vA8WGCYEE · p-9](<../../../notes/Transcripts/20251210_The Real Reason the Fed Just Ended QT_58vA8WGCYEE.md#^p-9>), [58vA8WGCYEE · p-10](<../../../notes/Transcripts/20251210_The Real Reason the Fed Just Ended QT_58vA8WGCYEE.md#^p-10>), [58vA8WGCYEE · p-11](<../../../notes/Transcripts/20251210_The Real Reason the Fed Just Ended QT_58vA8WGCYEE.md#^p-11>), [58vA8WGCYEE · p-12](<../../../notes/Transcripts/20251210_The Real Reason the Fed Just Ended QT_58vA8WGCYEE.md#^p-12>).
- **Time/condition:** Near-term risk assessment in the December 2025 transcript.
- **Limit:** His further claim about unlimited accessible liquidity is broad and unverified; this review does not adopt it as fact.
- **Later verification:** Check facility eligibility, collateral requirements, pricing, limits, and whether access actually prevents the claimed failure mode.

### C06 · speaker interpretation

The speaker describes reallocating mortgage-related principal into Treasury bills as easing for Treasuries even if the total balance sheet stays steady.

- **Argument:** He separates the composition of assets from the total balance-sheet level and argues that the change makes government borrowing easier.
- **Evidence:** [58vA8WGCYEE · p-18](<../../../notes/Transcripts/20251210_The Real Reason the Fed Just Ended QT_58vA8WGCYEE.md#^p-18>), [58vA8WGCYEE · p-19](<../../../notes/Transcripts/20251210_The Real Reason the Fed Just Ended QT_58vA8WGCYEE.md#^p-19>), [58vA8WGCYEE · p-20](<../../../notes/Transcripts/20251210_The Real Reason the Fed Just Ended QT_58vA8WGCYEE.md#^p-20>), [58vA8WGCYEE · p-21](<../../../notes/Transcripts/20251210_The Real Reason the Fed Just Ended QT_58vA8WGCYEE.md#^p-21>).
- **Time/condition:** Interpretation of the policy configuration described as effective from 2025-12-01.
- **Limit:** The phrase QE for Treasuries is the speaker's characterization. The transcript alone does not establish the scale or causal effects.
- **Later verification:** Check reinvestment rules and distinguish aggregate reserve creation from a shift in the composition of purchases.

### C07 · reported observation

The speaker reports that the Fed holds about 11.5% of national debt at the time discussed.

- **Argument:** He compares the reported share with earlier periods and uses the comparison to motivate his prediction of further purchases.
- **Evidence:** [IQ--1laVPFE · p-13](<../../../notes/Transcripts/20260709_The Fed is About to Do QE Without Calling it QE_IQ--1laVPFE.md#^p-13>), [IQ--1laVPFE · p-14](<../../../notes/Transcripts/20260709_The Fed is About to Do QE Without Calling it QE_IQ--1laVPFE.md#^p-14>), [IQ--1laVPFE · p-15](<../../../notes/Transcripts/20260709_The Fed is About to Do QE Without Calling it QE_IQ--1laVPFE.md#^p-15>).
- **Time/condition:** Contemporaneous observation in the source dated 2026-07-09; the underlying chart date is unspecified.
- **Limit:** The transcript does not provide the data series, exact numerator, or denominator. A percentage is not an absolute holdings level.
- **Later verification:** Obtain the underlying series and define whether the denominator is gross debt, marketable Treasuries, or another measure.

### C08 · speaker forecast

The speaker considers continued growth in the Fed's total balance sheet very likely over the coming quarters.

- **Argument:** His proposed mechanism is maintaining a consistent share of outstanding Treasury ownership while the debt stock grows.
- **Evidence:** [IQ--1laVPFE · p-27](<../../../notes/Transcripts/20260709_The Fed is About to Do QE Without Calling it QE_IQ--1laVPFE.md#^p-27>), [IQ--1laVPFE · p-28](<../../../notes/Transcripts/20260709_The Fed is About to Do QE Without Calling it QE_IQ--1laVPFE.md#^p-28>).
- **Time/condition:** Coming quarters relative to the July 2026 source; no exact forecast cutoff is given.
- **Limit:** The proposed share target is the speaker's scenario, not a confirmed Fed target in this review.
- **Later verification:** Define the evaluation window and compare announced policy and subsequent balance-sheet data with the forecast.

### C09 · speaker forecast

The speaker says it is very possible that much of the purchasing continues at the short end of the Treasury market.

- **Argument:** He suggests purchases could move the maturity mix of Fed holdings toward the mix of Treasuries outstanding.
- **Evidence:** [IQ--1laVPFE · p-27](<../../../notes/Transcripts/20260709_The Fed is About to Do QE Without Calling it QE_IQ--1laVPFE.md#^p-27>), [IQ--1laVPFE · p-28](<../../../notes/Transcripts/20260709_The Fed is About to Do QE Without Calling it QE_IQ--1laVPFE.md#^p-28>).
- **Time/condition:** Same coming-quarters discussion as C08, with weaker probability language.
- **Limit:** A maturity-composition forecast is separate from the aggregate-growth forecast; one can occur without the other.
- **Later verification:** Check maturity-bucket holdings and purchases separately from total balance-sheet growth.

### C10 · conditional speaker forecast

If the Fed sells long-dated Treasuries to change its balance sheet, the speaker expects accompanying bank deregulation to help banks absorb them.

- **Argument:** He says outright long-term sales are unlikely and argues that otherwise buyer demand and upward pressure on yields would be problems.
- **Evidence:** [IQ--1laVPFE · p-28](<../../../notes/Transcripts/20260709_The Fed is About to Do QE Without Calling it QE_IQ--1laVPFE.md#^p-28>), [IQ--1laVPFE · p-29](<../../../notes/Transcripts/20260709_The Fed is About to Do QE Without Calling it QE_IQ--1laVPFE.md#^p-29>).
- **Time/condition:** Conditional future scenario; the speaker does not say the long-term sales will occur.
- **Limit:** The condition must remain attached. Bank deregulation and bank purchases are distinct events that have not been verified here.
- **Later verification:** Check whether the antecedent occurs, then evaluate any rule change, bank demand, and timing separately.

## Evolution over time

| Stage | Speaker narrative | How to record the relationship |
|---|---|---|
| October 2025 | A conditional near-term end to QT, plus a longer-term expectation of renewed QE | Preserve the reserve condition and the open-ended forecast horizon |
| December 2025 | QT is reported ended; the speaker emphasizes reserve backstops and the balance-sheet composition | Record a later report and a qualification of the liquidity-risk interpretation, not independent proof |
| July 2026 | The speaker reports a Treasury-ownership share and forecasts further growth and possible short-end purchases | Separate total size, ownership share, and maturity composition; preserve conditional deregulation language |

Do not automatically call these statements a contradiction: a possible future change, a later reported policy event, and a further forecast refer to different dates. Likewise, a steady total balance sheet with a changing composition differs from a later forecast of aggregate growth. A contradiction needs incompatible propositions about the same quantity, scope, and time.

## Quality checks and remaining work

- Three source hashes match the corpus manifest; all evidence line ranges exist and their saved excerpts match the source text exactly. All claim IDs and cross-claim references are valid.
- Ten selected claims are classified by speaker role and uncertainty; this is an editorial extraction, not a completeness or semantic-accuracy score.
- Promotional material is outside the selected claims. No transcript text was deleted or corrected. Transcription artifacts and missing visual charts remain limitations.
- The 185-title keyword-review queue is unchanged. This pilot reviews three already-matched transcripts and does not resolve the 119 available unmatched transcripts.
- No external factual checks, forecast outcome tests, causal evaluation, or formal Part 2 metrics have been performed.

The next reading exercise should include an available transcript with an ambiguous title. Before larger-scale generation, agree on the formal Part 2 schema and evaluation criteria, and preserve this distinction between source support and independent verification.
