"""Resume a bounded, serial public-transcript download; stop on blocking."""
import argparse
import json
import re
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

import yt_dlp
import requests
from youtube_transcript_api import YouTubeTranscriptApi


class TimeoutSession(requests.Session):
    def request(self, *args, **kwargs):
        kwargs.setdefault('timeout', (10, 25))
        return super().request(*args, **kwargs)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, default=Path(__file__).resolve().parent.parent)
    p.add_argument('--limit', type=int, default=4)
    p.add_argument('--delay', type=float, default=25)
    args = p.parse_args()
    root = args.workspace
    entries = json.loads((root / 'data/channel.json').read_text())['entries']
    boundary = next(i for i, e in enumerate(entries) if e['id'] == '6Voa_CRRc2M')
    candidates = entries[:boundary]
    dest = root.parent / 'notes/Transcripts'
    dest.mkdir(parents=True, exist_ok=True)
    log = root / 'manifests/download_log.json'
    log.parent.mkdir(parents=True, exist_ok=True)
    state = json.loads(log.read_text()) if log.exists() else {}
    api = YouTubeTranscriptApi(http_client=TimeoutSession())
    existing_ids = {p.stem[-11:] for p in dest.glob('*.md')}
    count = 0
    for e in candidates:
        vid = e['id']
        if vid in existing_ids:
            continue
        if state.get(vid, {}).get('status') in ('downloaded', 'unavailable', 'outside_window'):
            continue
        if count >= args.limit:
            break
        time.sleep(args.delay)
        count += 1
        stamp = datetime.now(timezone.utc).isoformat()
        try:
            opts = dict(quiet=True, skip_download=True, socket_timeout=20,
                        retries=0, extractor_retries=0, no_warnings=True)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(e['url'], download=False)
            date = info.get('upload_date') or ''
            if not ('20260514' < date <= '20260918'):
                state[vid] = dict(status='outside_window', upload_date=date, checked_at=stamp)
            else:
                transcript = api.fetch(vid, languages=['en'])
                text = '\n'.join(s.text.strip() for s in transcript if s.text.strip()) + '\n'
                if not text.strip():
                    raise ValueError('Empty transcript')
                safe = re.sub(r'[\\/*?:"<>|\[\]#^\x00-\x1f]', '_', info['title']).strip(' .')
                safe = safe.encode('utf-8')[:170].decode('utf-8', errors='ignore')
                filename = f'{date}_{safe}_{vid}.md'
                target = dest / filename
                props = dict(title=info['title'], video_id=vid,
                             recorded_date=f'{date[:4]}-{date[4:6]}-{date[6:]}',
                             date_source='YouTube video metadata via yt-dlp',
                             source_url=f'https://www.youtube.com/watch?v={vid}',
                             source_path=str(target.relative_to(root.parent / 'notes')),
                             original_source_sha256=hashlib.sha256(text.encode()).hexdigest(),
                             reading_format='Subtitle lines joined into paragraphs; original words and punctuation preserved.')
                words = text.split()
                body = '\n\n'.join(' '.join(words[i:i+110]) for i in range(0, len(words), 110)) + '\n'
                markdown = '---\n' + ''.join(k + ': ' + json.dumps(v, ensure_ascii=False) + '\n' for k,v in props.items()) + '---\n\n# ' + info['title'] + '\n\n' + body
                with target.open('x', encoding='utf-8') as handle:
                    handle.write(markdown)
                existing_ids.add(vid)
                state[vid] = dict(status='downloaded', upload_date=date, video_title=info['title'],
                                  filename=filename, language=transcript.language,
                                  is_generated=transcript.is_generated, downloaded_at=stamp)
        except Exception as exc:
            name = type(exc).__name__
            unavailable = name in ('TranscriptsDisabled', 'NoTranscriptFound', 'VideoUnavailable')
            state[vid] = dict(status='unavailable' if unavailable else 'failed',
                              error_type=name, message=str(exc), checked_at=stamp)
            log.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
            print(vid, name, flush=True)
            if not unavailable:
                print('Stopped. Inspect the error before resuming; no automatic retry or proxy rotation.', flush=True)
                return
        log.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
        print(vid, state[vid]['status'], state[vid].get('upload_date', ''), flush=True)
    print('Candidates:', len(candidates), 'recorded:', len(state), flush=True)


if __name__ == '__main__':
    main()
