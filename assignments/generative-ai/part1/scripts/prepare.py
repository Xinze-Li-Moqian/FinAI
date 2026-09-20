"""Build a provenance-preserving APS1053 Part 1 workspace (stdlib only)."""
import argparse
import csv
import hashlib
import json
import re
import shutil
from collections import Counter
from pathlib import Path


def write_csv(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as out:
        writer = csv.DictWriter(out, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--metadata', type=Path)
    parser.add_argument('--materialize', action='store_true')
    args = parser.parse_args()
    root, out = args.repo.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / 'data').mkdir(exist_ok=True)
    (out / 'manifests').mkdir(exist_ok=True)
    source = root / 'materials/03_Generative_AI_Assignment/Youtube_AI_students/transcripts_ids_upto_20260514'
    entries = []
    if args.metadata:
        entries = json.loads(args.metadata.read_text()).get('entries', [])
    metadata = {e['id']: e for e in entries if e and e.get('id')}
    records, seen, hashes, dates = [], set(), Counter(), Counter()
    generated = out / 'generated/transcripts'
    if args.materialize:
        generated.mkdir(parents=True, exist_ok=True)
        # This directory contains reproducible copies only; fail on foreign files.
        for old in generated.iterdir():
            if not old.is_file() or not re.fullmatch(r'\d{8}_.+\.txt', old.name):
                raise ValueError(f'Unexpected generated entry; inspect manually: {old}')
    download_log = out / 'manifests/download_log.json'
    downloads = json.loads(download_log.read_text()) if download_log.exists() else {}
    sources = sorted(source.glob('*.txt')) + sorted((out / 'data/new_transcripts').glob('*.txt'))
    for file in sources:
        match = re.fullmatch(r'(\d{8})_([\w-]{11})\.txt', file.name)
        if not match:
            raise ValueError(f'Unexpected filename: {file.name}')
        date, video_id = match.groups()
        if video_id in seen:
            raise ValueError(f'Duplicate video ID: {video_id}')
        seen.add(video_id)
        raw = file.read_bytes()
        text = raw.decode('utf-8-sig')
        sha = hashlib.sha256(raw).hexdigest()
        hashes[sha] += 1
        dates[date[:4]] += 1
        title = downloads.get(video_id, {}).get('video_title') or metadata.get(video_id, {}).get('title') or ''
        safe = re.sub(r'[\\/*?:"<>|\x00-\x1f]', '_', title).strip(' .')[:110]
        filename = f'{date}_{safe}_{video_id}.txt' if safe else file.name
        if args.materialize:
            target = generated / filename
            if target.exists() and target.read_bytes() != raw:
                raise ValueError(f'Refusing overwrite: {target}')
            shutil.copyfile(file, target)
            assert hashlib.sha256(target.read_bytes()).hexdigest() == sha
        original = file.parent == source
        try:
            source_path = str(file.relative_to(root))
        except ValueError:
            source_path = str(file.resolve())
        records.append(dict(video_id=video_id, upload_date=date,
                            date_source='instructor-provided filename; not independently verified' if original else 'YouTube video metadata via yt-dlp',
                            video_title=title, url=f'https://www.youtube.com/watch?v={video_id}',
                            source_path=source_path, output_filename=filename,
                            bytes=len(raw), words=len(text.split()), sha256=sha))
    write_csv(out / 'manifests/transcript_manifest.csv', records, list(records[0]))
    if args.materialize:
        wanted = {r['output_filename'] for r in records}
        for old in generated.iterdir():
            if old.name not in wanted:
                old.unlink()
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
