"""Resume a bounded, serial public-transcript download; stop on blocking."""
import argparse
import json
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
    dest = root / 'data/new_transcripts'
    dest.mkdir(parents=True, exist_ok=True)
    log = root / 'manifests/download_log.json'
    log.parent.mkdir(parents=True, exist_ok=True)
    state = json.loads(log.read_text()) if log.exists() else {}
    api = YouTubeTranscriptApi(http_client=TimeoutSession())
    count = 0
    for e in candidates:
        vid = e['id']
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
                filename = f'{date}_{vid}.txt'
                (dest / filename).write_text(text)
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
