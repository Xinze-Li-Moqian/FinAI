# Title theme review

Reviewed on 2026-09-19 for Step 5 of the instructor’s Part 1 instructions: derive a detailed theme list from the `video_title` column. The result is in [THEMES.md](THEMES.md), separate from the transcript-level knowledge base required later.

## Inputs and method

The channel snapshot contains 1,468 titles; the prepared corpus contains 980 transcripts. A listed title does not imply that its transcript has been downloaded.

The AI-assisted editorial review examined all 317 titles left unmatched by the earlier rules and selected ambiguous matches. The revised taxonomy has 16 themes with detailed subtopics and scope boundaries in [themes.json](themes.json). This was not a complete individual semantic review of every title.

`build_themes.py` applies explicit, overlapping rules to produce reproducible navigation aids. [title_theme_matches.csv](title_theme_matches.csv) records the matching words and transcript availability. Matches are keyword suggestions, not transcript-verified judgments.

## Added themes

| Theme | Topics | Example |
|---|---|---|
| Personal finance, retirement and financial resilience | Saving, budgeting, household debt, auto loans, pensions, Roth accounts, insurance, and family financial decisions | [How to Use a Roth — Even if you Make Too Much](https://www.youtube.com/watch?v=HlvXNjkQE-s) |
| Monetary history and the nature of money | Fiat and sound money, creation and destruction, backing, legal tender, counterfeiting, and monetary systems | [What Is Money](https://www.youtube.com/watch?v=kFuxyqFMJr0) |
| Economic reasoning, value and economic education | Subjective value, production, profit, seen and unseen effects, economic fallacies, and educational resources | [The Broken Window Fallacy](https://www.youtube.com/watch?v=U6Wpf2xZb7M) |

## Rule corrections

| Earlier issue | Revision |
|---|---|
| `bank` also matched `bankrupt` | Require bank/banking terms or other credit-system signals |
| `reserve` matched Federal Reserve, bank reserves, and oil reserves as international currency topics | Use specific currency and payment terms, including reserve currency |
| `hous` matched White House and all household references | Separate property markets from household finance; exclude White House as a standalone property signal |
| `market` treated bond, housing, and labor markets as portfolio topics | Require investment, asset, trading, or valuation signals; queue vague market titles for context |
| Any `prices` implied inflation | Use inflation, purchasing-power, or more specific price-level terms |
| `wealth` or `rich` implied political economy | Require institutional or distributional context; personal finance has its own theme |
| Missing vocabulary left explicit topics unmatched | Add stagflation, FOMC, YCC, Roth, pensions, fiat money, and broken-window reasoning |

Ten targeted checks covered corrected false positives and newly recognized terms. These checks validate specific rule behaviors, not classification accuracy across the dataset.

## Coverage and remaining review

- Channel titles with at least one suggestion: **1,283 / 1,468**.
- Titles without a rule match: **185**, in [title_review_queue.csv](title_review_queue.csv).
- Prepared transcripts with a title-based suggestion: **861 / 980**.
- Prepared transcripts requiring contextual review: **119 / 980**.
- Relative to the earlier rules, 187 titles gained a suggestion and 55 moved to the review queue after broad matches were removed.

Theme counts overlap and must not be added to estimate the number of videos. Higher coverage alone does not demonstrate higher accuracy.

Some titles are too vague to assign confidently, such as “The Next Big Crisis — and when it begins.” Others may be channel announcements or personal content, including office tours and equipment tutorials. No records are excluded automatically. Read the available transcript or other source context before assigning a financial theme or marking an item as non-financial. Matched titles also need evidence review before Part 2 claim extraction.

The detailed title-based theme list is prepared. Remaining work includes contextual label review where needed, outstanding downloads when access recovers, and knowledge-base synthesis and evaluation under the formal Part 2 instructions. No paid API calls were used for this review.
