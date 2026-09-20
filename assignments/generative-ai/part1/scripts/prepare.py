"""Build a provenance-preserving APS1053 Part 1 workspace (stdlib only)."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


def write_csv(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as out:
        writer = csv.DictWriter(out, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)



def read_transcript(path):
    """Read our JSON-quoted YAML properties and subtitle body, excluding Markdown metadata."""
    raw = path.read_text(encoding='utf-8-sig')
    if not raw.startswith('---\n'):
        raise ValueError(f'Missing transcript frontmatter: {path}')
    _, front, body = raw.split('---\n', 2)
    properties = {}
    for line in front.splitlines():
        if line.strip():
            key, value = line.split(':', 1)
            properties[key] = json.loads(value.strip())
    body = re.sub(r'^\s*# [^\n]+\n+', '', body, count=1)
    body = re.sub(r'(?m) \^[a-zA-Z0-9-]+$', '', body)
    body = re.sub(r'(?<!!)\[\[([^\]\n]+)\]\]', lambda m: m[1].split('|', 1)[1] if '|' in m[1] else m[1].split('#', 1)[0], body)
    body = body.replace('\\$', '$')
    return properties, body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--metadata', type=Path)
    parser.add_argument('--materialize', action='store_true', help='Legacy compatibility flag; no transcript copies are created.')
    args = parser.parse_args()
    root, out = args.repo.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / 'data').mkdir(exist_ok=True)
    (out / 'manifests').mkdir(exist_ok=True)
    source = root / 'assignments/generative-ai/notes/Transcripts'
    entries = []
    if args.metadata:
        entries = json.loads(args.metadata.read_text()).get('entries', [])
    metadata = {e['id']: e for e in entries if e and e.get('id')}
    records, seen, hashes, dates = [], set(), Counter(), Counter()
    download_log = out / 'manifests/download_log.json'
    downloads = json.loads(download_log.read_text()) if download_log.exists() else {}
    sources = sorted(source.glob('*.md'))
    if not sources:
        raise ValueError(f'No canonical transcripts in {source}')
    for file in sources:
        properties, text = read_transcript(file)
        video_id = properties['video_id']
        date = properties['recorded_date'].replace('-', '')
        if video_id in seen:
            raise ValueError(f'Duplicate video ID: {video_id}')
        seen.add(video_id)
        raw = file.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        hashes[hashlib.sha256(re.sub(r'\s', '', text).encode()).hexdigest()] += 1
        dates[date[:4]] += 1
        records.append(dict(video_id=video_id, upload_date=date,
                            date_source=properties['date_source'],
                            video_title=properties['title'], url=properties['source_url'],
                            source_path=str(file.relative_to(root)), output_filename=file.name,
                            bytes=len(raw), words=len(text.split()), sha256=sha))
    write_csv(out / 'manifests/transcript_manifest.csv', records, list(records[0]))
    indexed = {r['video_id']: r for r in records}
    write_csv(out / 'data/youtube_channel_videos.csv',
              [dict(video_id=e['id'], upload_date=indexed.get(e['id'], {}).get('upload_date', e.get('upload_date') or ''),
                    video_title=e.get('title') or '', date_source=indexed.get(e['id'], {}).get('date_source', 'not retrieved')) for e in metadata.values()],
              ['video_id', 'upload_date', 'video_title', 'date_source'])
    ordered_ids = list(metadata)
    boundary = ordered_ids.index('6Voa_CRRc2M') if '6Voa_CRRc2M' in metadata else 0
    candidates = ordered_ids[:boundary]
    pending = [v for v in candidates if downloads.get(v, {}).get('status') not in ('downloaded', 'outside_window')]
    status = dict(transcripts=len(records), total_bytes=sum(r['bytes'] for r in records),
                  total_words=sum(r['words'] for r in records),
                  date_min=min(r['upload_date'] for r in records), date_max=max(r['upload_date'] for r in records),
                  counts_by_year=dict(sorted(dates.items())), empty_files=sum(not r['words'] for r in records),
                  duplicate_content_groups=sum(n > 1 for n in hashes.values()),
                  channel_metadata_records=len(metadata), matched_titles=sum(bool(r['video_title']) for r in records),
                  updated_transcripts_downloaded=sum(s.get('status') == 'downloaded' for s in downloads.values()),
                  update_candidates=len(candidates), unresolved_update_candidates=len(pending),
                  date_provenance='Original dates come from instructor filenames; update dates come from YouTube metadata. See each manifest row.',
                  snapshot_data_preparation_complete=bool(metadata) and not pending and all(r['video_title'] for r in records))
    (out / 'manifests/inventory.json').write_text(json.dumps(status, indent=2) + '\n')
    print(json.dumps(status, indent=2))


if __name__ == '__main__':
    main()
