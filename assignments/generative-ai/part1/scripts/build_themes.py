"""Build a title-based theme map and an explicit review queue; no API needed."""
import csv
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
rows = list(csv.DictReader((root / 'data/youtube_channel_videos.csv').open()))
themes = json.loads((root / 'analysis/themes.json').read_text())
corpus = {r['video_id'] for r in csv.DictReader((root / 'manifests/transcript_manifest.csv').open())}
title_ids = {r['video_id'] for r in rows}
if len(title_ids) != len(rows):
    raise ValueError('Duplicate video IDs in the title index')
if not corpus <= title_ids:
    raise ValueError('Corpus contains videos missing from the title index')
lines = ['# Title-based theme map', '',
         'Prepared for APS1053 Generative AI Assignment, Part 1. Taxonomy reviewed on 2026-09-19; channel-title snapshot retrieved on 2026-09-18.', '',
         f'This preliminary taxonomy uses the **{len(rows):,} public video titles** in [the channel index](../data/youtube_channel_videos.csv). It does not assert that a title is true, or that its argument has been checked. The source is one financial-commentary channel, not an independently verified financial dataset.', '',
         'The 16 themes and their subtopics were refined through an AI-assisted review of the earlier unmatched titles and selected ambiguous matches. Counts and examples below are deterministic keyword suggestions, not a claim that every title has been individually classified. Matches overlap. Titles without a clear rule match remain in the review queue rather than receiving a guessed label.', '',
         '[Review notes](THEME_REVIEW.md) · [Title review queue](title_review_queue.csv) · [Match evidence](title_theme_matches.csv)', '',
         'For Part 2, read the actual transcript before extracting claims, preserve source attribution, distinguish predictions from observations, and keep the date on every claim. Opposing claims over time should remain visible rather than being silently reconciled.', '']
matched = set()
assignments = []
for theme in themes:
    hits = [r for r in rows if re.search(theme['pattern'], r['video_title'], re.I)]
    matched.update(r['video_id'] for r in hits)
    assignments.extend({'video_id': r['video_id'], 'theme': theme['theme'], 'video_title': r['video_title'],
                        'matched_terms': '; '.join(dict.fromkeys(m.group(0) for m in re.finditer(theme['pattern'], r['video_title'], re.I))),
                        'transcript_available': str(r['video_id'] in corpus).lower(),
                        'label_basis': 'keyword suggestion; not transcript-verified'} for r in hits)
    lines.extend([f"## {theme['theme']}", '', theme['subtopics'], '',
                  f"Scope: {theme['boundary']}", '',
                  f'Keyword matches: **{len(hits)}** across the title index; **{sum(r["video_id"] in corpus for r in hits)}** have a prepared transcript. Counts overlap. Example titles:', ''])
    # Spread examples across channel order rather than only the newest videos.
    positions = sorted({0, len(hits)//3, 2*len(hits)//3}) if hits else []
    for i in positions:
        r = hits[i]
        title = r['video_title'].replace('[', '\\[').replace(']', '\\]')
        lines.append(f"- [{title}](https://www.youtube.com/watch?v={r['video_id']})")
    lines.append('')
unmatched = [r for r in rows if r['video_id'] not in matched]
lines.extend(['## Coverage and next step', '',
              f'{len(matched):,}/{len(rows):,} channel titles match at least one rule; {len(unmatched):,} remain in `title_review_queue.csv`.', '',
              f'For the **{len(corpus):,} prepared transcripts**, {len(corpus & matched):,} have a title-based suggestion and {len(corpus - matched):,} need contextual review. A title in the channel index does not imply that its transcript is available.', '',
              'This is a detailed title-based theme list for Step 5, not the final Claim → Theme → Argument → Evidence & EvolutionOverTime compendium. Matched and unmatched titles alike need transcript-level evidence before making claims in Part 2. No source files are excluded or deleted by this classification.', ''])
(root / 'analysis/THEMES.md').write_text('\n'.join(lines))
with (root / 'analysis/title_theme_matches.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['video_id', 'theme', 'video_title', 'matched_terms', 'transcript_available', 'label_basis'], lineterminator='\n')
    writer.writeheader(); writer.writerows(assignments)
with (root / 'analysis/title_review_queue.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['video_id', 'video_title', 'url', 'transcript_available', 'review_reason'], lineterminator='\n')
    writer.writeheader()
    writer.writerows(dict(video_id=r['video_id'], video_title=r['video_title'],
                          url=f'https://www.youtube.com/watch?v={r["video_id"]}',
                          transcript_available=str(r['video_id'] in corpus).lower(),
                          review_reason='No rule match; inspect context before assigning a financial theme or marking as non-financial') for r in unmatched)
print(f'{len(themes)} themes; {len(matched)}/{len(rows)} titles matched')
print(f'{len(corpus & matched)}/{len(corpus)} prepared transcripts have title suggestions; {len(unmatched)} titles queued for review')
