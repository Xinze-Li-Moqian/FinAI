"""Link equivalent concept terms in the canonical Obsidian transcripts.

Default is dry-run. Use --apply after inspecting the preview; --limit 1 checks
only the first dated transcript. Aliases live exclusively in concept-page YAML.
"""
import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import yaml

WIKI = re.compile(r'(?<!!)\[\[([^\]\n]+)\]\]')
WITHHELD = {
    'Fed': 'May be the ordinary verb; only Federal Reserve and specific Fed phrases are matched.',
    'interest': 'May mean attention or a stake; match interest rate or specific interest types.',
    'options': 'Only matched with an explicit trading, contract or premium context; ordinary choices are skipped.',
    'saving': 'May mean rescue or saving time; require personal or household saving.',
    'production': 'May mean video production; require economic production or production of goods.',
    'leverage': 'May mean influence; require financial or investment leverage.',
    'capital': 'Ambiguous and not an equivalent name for a specific concept.',
    'real': 'Only appears inside specific real-wage or real-interest-rate phrases.',
    'federal': 'Too broad to identify the Federal Reserve.',
    'AI': 'Broad technology abbreviation; require an explicit economy phrase.',
    'gold': 'The monetary-gold concept requires an explicit monetary phrase.',
    'stock': 'Singular stock is ambiguous; use equities, stocks or specific equity phrases.',
    'Treasury': 'May mean the department; use Treasury securities or Treasuries.',
    'repo': 'May mean a software repository; use repurchase agreement or repo market.',
}
# Restrict inflections to known count nouns; never stem arbitrary financial words.
NOUNS = dict(x.split(':') for x in (
    'account:accounts agreement:agreements asset:assets authority:authorities bank:banks '
    'balance:balances benchmark:benchmarks bill:bills bond:bonds bottleneck:bottlenecks '
    'bubble:bubbles budget:budgets ceiling:ceilings chain:chains coin:coins collapse:collapses '
    'contract:contracts cost:costs currency:currencies cycle:cycles deficit:deficits '
    'deposit:deposits drawdown:drawdowns duty:duties effect:effects eviction:evictions '
    'expectation:expectations expenditure:expenditures facility:facilities failure:failures '
    'foreclosure:foreclosures fund:funds incentive:incentives index:indexes indicator:indicators '
    'line:lines limit:limits loan:loans market:markets mechanism:mechanisms mortgage:mortgages '
    'network:networks note:notes option:options pension:pensions plan:plans policy:policies '
    'price:prices profit:profits rate:rates recession:recessions reserve:reserves '
    'return:returns risk:risks run:runs sale:sales sanction:sanctions security:securities '
    'share:shares sheet:sheets shock:shocks signal:signals squeeze:squeezes stablecoin:stablecoins '
    'statistic:statistics system:systems tariff:tariffs tax:taxes transition:transitions '
    'wage:wages ETF:ETFs banknote:banknotes value:values'
).split())
INFLECTION = {a.casefold(): b.casefold() for a, b in NOUNS.items()}
INFLECTION.update({b.casefold(): a.casefold() for a, b in NOUNS.items()})


def display_text(text):
    """Render wikilink labels and literal currency escapes without changing displayed text."""
    return WIKI.sub(lambda m: m[1].split('|', 1)[1] if '|' in m[1] else m[1].split('#', 1)[0], text).replace('\\$', '$')


def normalize(alias):
    return re.sub(r'[\s\-‐‑‒–—]+', ' ', alias.strip().casefold()).replace('’', "'")


def variants(alias):
    result = {normalize(alias)}
    head, sep, last = normalize(alias).rpartition(' ')
    if last in INFLECTION:
        result.add(head + sep + INFLECTION[last])
    return result


def alias_pattern(alias):
    # Flexible horizontal spacing and hyphenation, never cross paragraphs.
    parts = alias.split(' ')
    return r'[ \t\-‐‑‒–—]+'.join(re.escape(x).replace("'", "['’]") for x in parts)


def frontmatter(text):
    match = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
    return (yaml.safe_load(match[1]) or {}, match.end()) if match else ({}, 0)


def load_aliases(vault):
    aliases = {}; themes = []
    for file in sorted(vault.rglob('*.md')):
        relative = file.relative_to(vault)
        if relative.parts[0] == 'Transcripts' or any(part.startswith('.') for part in relative.parts):
            continue
        meta, _ = frontmatter(file.read_text(encoding='utf-8'))
        tags = meta.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
        if 'node/theme' in tags:
            themes.append(file)
            continue
        if relative.parts[0] != 'Concepts' and 'node/concept' not in tags:
            continue
        values = meta.get('aliases', [])
        if not isinstance(values, list) or not values or not all(isinstance(x, str) and x.strip() for x in values):
            raise ValueError(f'Missing or malformed aliases: {file}')
        target = file.relative_to(vault).with_suffix('').as_posix()
        if any(x in target for x in '|[]#'):
            raise ValueError(f'Unsafe wikilink target: {target}')
        aliases[target] = values
    if not aliases:
        raise ValueError('No concept aliases found')
    return aliases, themes


def protected_spans(text):
    spans = []
    _, end = frontmatter(text)
    if end:
        spans.append((0, end))
    # Fenced blocks, including an unterminated final fence.
    fence = None; start = 0; offset = 0
    for line in text.splitlines(keepends=True):
        m = re.match(r' {0,3}(`{3,}|~{3,})(.*)', line)
        if fence:
            if m and m[1][0] == fence[0] and len(m[1]) >= len(fence) and not m[2].strip():
                spans.append((start, offset + len(line))); fence = None
        elif m:
            start = offset; fence = m[1]
        offset += len(line)
    if fence:
        spans.append((start, len(text)))
    for pattern in [r'(?m)^ {0,3}#{1,6}[ \t].*$', r'(?m)^(?: {4}|\t).*$',
                    r'(?m)^ {0,3}\[[^\]\n]+\]:.*$',
                    r'(?m) \^[a-zA-Z0-9-]+[ \t]*$',
                    r'(?i)\b(?:https?://|www\.)[^\s<>]+',
                    r'<[^>\n]+>', r'(?m)^ {0,3}[-*_]{3,}[ \t]*$']:
        spans.extend(m.span() for m in re.finditer(pattern, text))
    i = 0
    while i < len(text):
        if text[i] == '\\':
            i += 2; continue
        if text[i] == '`':
            j = i
            while j < len(text) and text[j] == '`': j += 1
            close = re.search(r'(?<!`)'+re.escape(text[i:j])+r'(?!`)', text[j:])
            if close:
                end = j + close.end(); spans.append((i, end)); i = end; continue
            i = j; continue
        if text.startswith('[[', i):
            j = text.find(']]', i + 2)
            if j != -1:
                spans.append((i, j + 2)); i = j + 2; continue
        if text[i] == '[':
            # Balanced labels and destinations protect nested Markdown links.
            j = balanced_end(text, i, '[', ']')
            if j is not None:
                if j < len(text) and text[j] in '([':
                    close = ')' if text[j] == '(' else ']'
                    end = balanced_end(text, j, text[j], close)
                    if end is not None: j = end
                spans.append((i, j)); i = j; continue
        i += 1
    merged = []
    for a, b in sorted(spans):
        if merged and a <= merged[-1][1]: merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else: merged.append((a, b))
    return merged


def balanced_end(text, start, opening, closing):
    level = 0; i = start
    while i < len(text):
        if text[i] == '\\': i += 2; continue
        if text[i] == opening: level += 1
        elif text[i] == closing:
            level -= 1
            if level == 0: return i + 1
        i += 1
    return None


def ambiguous_context(alias, text, start, end):
    left, right = text[max(0, start-45):start].casefold(), text[end:end+45].casefold()
    if alias in ('option', 'options', 'automation', 'profitable', 'budgeting'):
        # Inspect visible text within the same paragraph, never target-path words.
        a = text.rfind('\n\n', 0, start)
        b = text.find('\n\n', end)
        before = display_text(text[a+2 if a >= 0 else 0:start])[-140:].casefold()
        after = display_text(text[end:b if b >= 0 else len(text)])[:140].casefold()
        if alias == 'profitable':
            return not re.search(r'\b(?:money|revenue|costs?|margins?|earnings?|business|prices?)\b', before + ' ' + after)
        if alias == 'budgeting':
            context = before + ' ' + after
            return (not re.search(r'\b(?:my|your|our|household|personal|wife|husband|family|groceries)\b', context)
                    or bool(re.search(r'\b(?:government|federal|corporate|company|department)\b', context)))
        if alias in ('option', 'options'):
            return not (re.search(r'\b(?:trade|trading|spx|stock|equity|index|call|put)\s+$', before)
                        or re.match(r'\s+(?:trading|contracts?|premiums?|expiration)\b', after))
        return not re.search(r'\b(?:jobs?|employment|workers?|labor|labour|workforce|wages?)\b', before + ' ' + after)
    if alias in ('bond', 'bonds'):
        return bool(re.search(r'(?:chemical|covalent|ionic|hydrogen|family|emotional|social|bail|marriage)\s+$', left) or re.match(r'\s+(?:with|between|of friendship)\b', right))
    if alias in ('mortgage', 'mortgages'):
        return bool(re.match(r'[\s‐‑–—-]+backed\b', right))
    if alias == 'silver':
        return bool(re.match(r'[\s‐‑–—-]+(?:lining|bullet|screen)\b', right))
    if alias == 'stocks':
        return bool(re.search(r'(?:food|fish|oil|inventory|breeding)\s+$', left))
    if alias == 'gold standard':
        return bool(re.match(r'\s+(?:for|of)\b', right))
    return False


class Linker:
    def __init__(self, aliases):
        self.aliases = aliases
        self.owners = defaultdict(set)
        for target, names in aliases.items():
            for name in names:
                for alias in variants(name): self.owners[alias].add(target)
        self.conflicts = {k: sorted(v) for k,v in self.owners.items() if len(v) > 1}
        self.pattern = re.compile(r'(?<![\w])(?:' + '|'.join(alias_pattern(a) for a in sorted(self.owners, key=lambda a: (-len(a), a))) + r')(?:[’\']s)?(?![\w])', re.I)

    def transform(self, text):
        counts = Counter(); skipped = Counter(); examples = []
        def substitute(m):
            alias = normalize(m[0]); alias = re.sub(r"'s$", '', alias) if alias not in self.owners else alias
            owners = self.owners[alias]
            if len(owners) != 1:
                skipped['conflict: '+alias] += 1; return m[0]
            if ambiguous_context(alias, text, segment_start + m.start(), segment_start + m.end()):
                skipped['context: '+alias] += 1; return m[0]
            target = next(iter(owners)); counts[target] += 1
            link = '[['+target+'|'+m[0]+']]'
            if len(examples) < 8: examples.append(link)
            return link
        pieces = []; cursor = 0
        for a,b in protected_spans(text) + [(len(text),len(text))]:
            segment_start = cursor
            pieces.append(self.pattern.sub(substitute,text[cursor:a])); pieces.append(text[a:b]); cursor=b
        result = ''.join(pieces)
        if display_text(result) != display_text(text):
            raise AssertionError('Displayed text changed')
        return result, counts, skipped, examples


def sha(raw): return hashlib.sha256(raw).hexdigest()


def write_changed(path, text):
    if path.read_text(encoding='utf-8') != text:
        path.write_text(text, encoding='utf-8'); return 1
    return 0


def refresh_manifests(vault):
    """Refresh live file hashes; original-source and visible-body hashes remain valid."""
    part = vault.parent / 'part1'; repo = vault.parents[2]; manifest = part/'manifests/transcript_manifest.csv'
    if not manifest.exists(): return 0
    from prepare import read_transcript
    rows = list(csv.DictReader(manifest.open(encoding='utf-8',newline=''))); current = {}; changed = 0
    for row in rows:
        file = repo/row['source_path']; raw=file.read_bytes(); props,body=read_transcript(file)
        row.update(bytes=str(len(raw)),words=str(len(body.split())),sha256=sha(raw))
        current[row['video_id']] = (file, raw, body)
    stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows);changed+=write_changed(manifest,stream.getvalue())
    def update_json(path, callback):
        nonlocal changed
        if path.exists():
            d=json.loads(path.read_text());callback(d);changed+=write_changed(path,json.dumps(d,indent=2,ensure_ascii=False)+'\n')
    def export(d):
        d['manifest_sha256']=sha(manifest.read_bytes())
        for e in d['entries']:
            file,raw,body=current[e['video_id']]
            digest=sha(re.sub(r'\s','',body).encode())
            if digest != e.get('current_body_nonwhitespace_sha256', e['body_nonwhitespace_sha256']): raise AssertionError(f'Original body differs: {file}')
            text=raw.decode('utf-8');meta,end=frontmatter(text)
            heading=re.match(r'\s*# [^\n]+\n+',text[end:])
            e.update(source_sha256=sha(raw),markdown_sha256=sha(raw),source_bytes=len(raw),
                     frontmatter_fields=list(meta),header_bytes=len(text[:end+(heading.end() if heading else 0)].encode('utf-8')))
        d['concept_links']='Native wikilinks preserve original display text. Body hashes exclude wikilink syntax, YAML, H1 and paragraph block IDs.'
    update_json(part/'manifests/obsidian_transcript_export.json',export)
    def inventory(d):
        d['total_bytes']=sum(len(x[1]) for x in current.values());d['total_words']=sum(len(x[2].split()) for x in current.values())
    update_json(part/'manifests/inventory.json',inventory)
    def claims(d):
        for s in d['sources']:s['sha256']=sha(current[s['video_id']][1])
        for claim in d['claims']:
            text=current[claim['video_id']][2]
            for e in claim['evidence']:
                if re.sub(r'\s','',e['excerpt']) not in re.sub(r'\s','',text):raise AssertionError('Evidence no longer found')
                raw=current[claim['video_id']][1].decode()
                for block in e['source_blocks']:
                    if ' ^'+block+'\n' not in raw:raise AssertionError('Missing evidence block')
    update_json(part/'analysis/monetary-policy-pilot/claims.json',claims)
    def materials(d):
        for item in d['files']:
            file=(repo/'materials'/item.get('published','')).resolve()
            if file.is_file() and (file.parent == vault/'Transcripts' or file.name=='deepseek_speech_processing_program1_notree_revised2.py'):
                raw=file.read_bytes();item.update(sha256=sha(raw),bytes=len(raw))
    update_json(repo/'materials/MANIFEST.json',materials)
    return changed


def run(vault, apply=False, limit=None, video_ids=None):
    aliases,themes=load_aliases(vault);linker=Linker(aliases)
    files=sorted((vault/'Transcripts').glob('*.md'),key=lambda p:(p.name[:8],p.name))
    if video_ids:
        requested=set(video_ids)
        files=[f for f in files if frontmatter(f.read_text(encoding='utf-8'))[0].get('video_id') in requested]
        found={frontmatter(f.read_text(encoding='utf-8'))[0].get('video_id') for f in files}
        if found != requested: raise ValueError(f'Unknown video IDs: {sorted(requested-found)}')
    if limit is not None:files=files[:limit]
    counts=Counter();total=Counter();skipped=Counter();edits=[];matched_files=0;first=None
    for file in files:
        original=file.read_text(encoding='utf-8');new,hits,misses,examples=linker.transform(original)
        # An independent second pass must not introduce another link.
        if linker.transform(new)[0] != new: raise AssertionError(f'Not idempotent: {file}')
        counts.update(hits);skipped.update(misses)
        existing=Counter(m[1].split('|',1)[0] for m in WIKI.finditer(new) if m[1].split('|',1)[0] in aliases)
        total.update(existing);matched_files+=bool(existing)
        if new != original:edits.append((file,original,new))
        if first is None:first={'file':str(file),'examples':examples}
    summary=dict(mode='apply' if apply else 'dry-run',scanned_transcripts=len(files),matched_transcripts=matched_files,
                 changed_transcripts=len(edits),new_links=sum(counts.values()),total_concept_links=sum(total.values()),
                 concept_count=len(aliases),theme_pages_excluded=len(themes),covered_concepts=len(total),
                 unmatched_concepts=sorted(set(aliases)-set(total)),conflicts=linker.conflicts,
                 ambiguous_matches_skipped=dict(skipped),withheld_ambiguous_aliases=WITHHELD,
                 links_by_concept=dict(sorted(total.items())),first_transcript=first,
                 display_text_preserved=True,idempotence_verified=True,
                 scope='selected-transcripts' if video_ids else 'all-transcripts',selected_video_ids=sorted(video_ids or []))
    if apply:
        # Verify all preconditions before writing any transcript.
        for file,original,new in edits:
            if file.read_text(encoding='utf-8')!=original: raise RuntimeError(f'Concurrent edit: {file}')
        for target in aliases:
            if not (vault/(target+'.md')).is_file():raise RuntimeError(f'Missing target: {target}')
        for file,original,new in edits:write_changed(file,new)
        summary['manifest_files_refreshed']=refresh_manifests(vault) if edits else 0
        # Preserve the last actual run's record on no-op verification runs.
        if edits:
            report=vault.parent/'part1/manifests/concept_linking.json'
            previous=json.loads(report.read_text()) if report.exists() else {}
            if video_ids: previous['last_targeted_run']=summary
            else: previous.update(summary)
            report.write_text(json.dumps(previous,indent=2,ensure_ascii=False)+'\n')
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault',type=Path,default=Path(__file__).resolve().parents[2]/'notes')
    mode=parser.add_mutually_exclusive_group();mode.add_argument('--apply',action='store_true');mode.add_argument('--dry-run',action='store_true')
    parser.add_argument('--limit',type=int)
    parser.add_argument('--video-id',action='append',help='Restrict writes to this reviewed video ID; repeat as needed')
    args=parser.parse_args()
    if args.limit is not None and args.limit<1:parser.error('--limit must be positive')
    summary=run(args.vault.resolve(),args.apply,args.limit,args.video_id)
    print(json.dumps(summary,indent=2,ensure_ascii=False))


if __name__=='__main__':main()
