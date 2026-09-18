"""Create a reviewable, overlapping title-based thematic index; no API needed."""
import csv
import json
import re
from pathlib import Path

root = Path(__file__).parent
rows = list(csv.DictReader((root / 'youtube_channel_videos.csv').open()))
themes = json.loads((root / 'themes.json').read_text())
lines = ['# Title-based theme map', '',
         'Prepared for APS1053 Generative AI Assignment, Part 1 (2026-09-18).', '',
         f'This preliminary taxonomy uses the **{len(rows):,} public video titles** in `youtube_channel_videos.csv`. It does not assert that a title is true, or that its argument has been checked. The source is one financial-commentary channel, not an independently verified financial dataset.', '',
         'The themes and subtopics are an editorial synthesis. Counts and examples use the explicit keyword rules in `themes.json` to make the first-pass index reproducible. Matches overlap; broad words such as “market” create false positives. Unmatched titles need review. These are navigation aids, not validated semantic labels.', '',
         'For Part 2, read the actual transcript before extracting claims, preserve source attribution, distinguish predictions from observations, and keep the date on every claim. Opposing claims over time should remain visible rather than being silently reconciled.', '']
matched = set()
assignments = []
for theme in themes:
    hits = [r for r in rows if re.search(theme['pattern'], r['video_title'], re.I)]
    matched.update(r['video_id'] for r in hits)
    assignments.extend({'video_id': r['video_id'], 'theme': theme['theme'], 'video_title': r['video_title']} for r in hits)
    lines.extend([f"## {theme['theme']}", '', theme['subtopics'], '', f'Keyword matches: **{len(hits)}** (overlapping, provisional). Example titles:', ''])
    # Spread examples across channel order rather than only the newest videos.
    positions = sorted({0, len(hits)//3, 2*len(hits)//3}) if hits else []
    for i in positions:
        r = hits[i]
        title = r['video_title'].replace('[', '\\[').replace(']', '\\]')
        lines.append(f"- [{title}](https://www.youtube.com/watch?v={r['video_id']})")
    lines.append('')
lines.extend(['## Coverage and next step', '', f'{len(matched):,}/{len(rows):,} titles match at least one rule; {len(rows)-len(matched):,} need manual review or additional themes.', '',
              'This completes a first title-based theme list. It is not the final Claim → Theme → Argument → Evidence & EvolutionOverTime compendium. That requires transcript-level synthesis and evaluation in Part 2.', ''])
(root / 'THEMES.md').write_text('\n'.join(lines))
with (root / 'title_theme_matches.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['video_id', 'theme', 'video_title'], lineterminator='\n')
    writer.writeheader(); writer.writerows(assignments)
print(f'{len(themes)} themes; {len(matched)}/{len(rows)} titles matched')
