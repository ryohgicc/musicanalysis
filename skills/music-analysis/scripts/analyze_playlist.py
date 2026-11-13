#!/usr/bin/env python3
"""Read-only playlist statistics and conservative recommendation overlap checks."""
import argparse
import collections
import csv
import json
import re
import unicodedata
from pathlib import Path


def pick(row, *keys, default=''):
    return next((row[k] for k in keys if row.get(k) is not None and row[k] != ''), default)


def text_key(value):
    text = unicodedata.normalize('NFKC', str(value)).casefold()
    return ''.join(c for c in text if c.isalnum())


def artist_key(value):
    value = re.sub(r'\s+[（(][^()（）]*[)）]\s*$', '', str(value))
    key = text_key(value)
    return {'fujiikaze': '藤井風', '藤井风': '藤井風', '藤井風': '藤井風'}.get(key, key)


VERSION = re.compile(r'\b(?:live|remix|version|ver\.?|acoustic|demo|reimagined|explicit|clean)\b|'
                     r'from the first take|现场|演唱会|吉他版|再録|再录|再編|再编', re.I)


def title_base(title):
    title = unicodedata.normalize('NFKC', str(title))
    def strip_annotation(match):
        inside = match.group(1)
        translation = bool(re.search(r'[ぁ-ヿ]', title[:match.start()]) and
                           re.fullmatch(r'[\u3400-\u9fff\s·、，。！？～~]+', inside))
        return '' if VERSION.search(inside) or translation else match.group(0)
    title = re.sub(r'\(([^()]*)\)', strip_annotation, title)
    title = re.sub(r'\s+-\s+(?:From THE FIRST TAKE|Live|Acoustic|Remix)\b.*$', '', title, flags=re.I)
    return text_key(title)


def credits(row):
    raw = pick(row, 'artists', 'singer', 'artist', '歌手', 'Artist', default=[])
    if isinstance(raw, list):
        return [str(x.get('name', '') if isinstance(x, dict) else x).strip()
                for x in raw if (x.get('name') if isinstance(x, dict) else x)]
    raw = str(raw).replace('リリィ、さよなら。', 'リリィ\x00さよなら。')
    return [x.replace('\x00', '、').strip() for x in re.split(r'、|;', raw) if x.strip()]


def load_tracks(path):
    if path.suffix.lower() == '.csv':
        with path.open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
    else:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        if isinstance(data, dict):
            data = data.get('data', data)
            data = data.get('result', data)
            if 'cdlist' in data:
                data = data['cdlist'][0]
            rows = data.get('tracks', data.get('songlist'))
        else:
            rows = data
    if not isinstance(rows, list) or not rows:
        raise ValueError('Expected a nonempty list in tracks, songlist, or an array.')
    result = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f'Track {index} must be an object.')
        title = str(pick(row, 'title', 'songname', 'name', '歌名', '歌曲', 'Title')).strip()
        artists = credits(row)
        if not title or not artists:
            raise ValueError(f'Track {index} needs a title and artist; no rows were silently skipped.')
        result.append({'index': index, 'title': title, 'artists': artists,
                       'album': str(pick(row, 'album', 'albumname', '专辑', 'Album')),
                       'songId': str(pick(row, 'songId', 'songid')),
                       'songMid': str(pick(row, 'songMid', 'songmid', 'id'))})
    return result


def analyze(tracks, candidates=None):
    counts, families, display, title_groups, albums = (collections.Counter(), {}, {}, {}, collections.Counter())
    for t in tracks:
        aks = tuple(sorted(set(artist_key(a) for a in t['artists'])))
        base = title_base(t['title'])
        for a in t['artists']:
            display.setdefault(artist_key(a), a)
        counts.update(aks)
        families.setdefault((aks, base), []).append(t)
        title_groups.setdefault(base, []).append(t)
        if t['album']:
            albums[(aks, t['album'])] += 1
    adjusted = collections.Counter()
    for aks, _ in families:
        adjusted.update(aks)
    rank = lambda counter: [{'artist': display[k], 'count': n} for k, n in counter.most_common()]
    summary = {
        'trackCount': len(tracks), 'artistCount': len(counts),
        'artistParticipation': rank(counts), 'heuristicFamilyParticipation': rank(adjusted),
        'heuristicFamilyCount': len(families),
        'versionCandidates': [group for group in families.values() if len(group) > 1],
        'sameTitleAcrossCredits': [group for group in title_groups.values()
                                  if len({tuple(sorted(artist_key(a) for a in t['artists'])) for t in group}) > 1],
        'topAlbumCounts': [{'artists': [display[a] for a in aks], 'album': album, 'count': n}
                           for (aks, album), n in albums.most_common(25)],
        'limitations': ['Artist counts include collaborations and are not additive.',
                       'Version groups are heuristic, not verified composition identity.',
                       'Translations, aliases and covers require manual review.',
                       'No play counts, listening chronology or audio features are inferred.'],
        'tracks': tracks,
    }
    if candidates is not None:
        summary['candidateChecks'] = []
        for c in candidates:
            wanted = set(map(artist_key, credits(c)))
            exact_ids = [t for t in tracks if
                         (c.get('songMid') and c['songMid'] == t['songMid']) or
                         (c.get('songId') and str(c['songId']) == t['songId'])]
            title_hits = title_groups.get(title_base(c['title']), [])
            same_artist = [t for t in title_hits if wanted.intersection(map(artist_key, t['artists']))]
            status = 'already_present_id' if exact_ids else 'already_present_title_artist' if same_artist else 'review_same_title' if title_hits else 'not_detected'
            summary['candidateChecks'].append({**c, 'status': status,
                'artistAlreadyPresent': bool(wanted.intersection(counts)),
                'matches': exact_ids or same_artist or title_hits})
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--candidates', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() == args.input.resolve() or (args.candidates and args.output.resolve() == args.candidates.resolve()):
        parser.error('Output must not overwrite input or candidate data.')
    candidates = json.loads(args.candidates.read_text()) if args.candidates else None
    summary = analyze(load_tracks(args.input), candidates)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: summary[k] for k in ('trackCount', 'artistCount', 'heuristicFamilyCount')}, ensure_ascii=False))
    if candidates is not None:
        print(json.dumps([{'title': c['title'], 'status': c['status']} for c in summary['candidateChecks']], ensure_ascii=False))


if __name__ == '__main__':
    main()
