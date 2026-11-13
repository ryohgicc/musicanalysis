#!/usr/bin/env python3
"""Public playlist metadata → normalized export → grounded analysis → offline report."""
import argparse
import base64
import csv
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
import re
import ssl
import sys
import urllib.parse
import urllib.request

from analyze_playlist import analyze, credits, pick
from covers import collect_covers, hero_indices, tls_context

HERE = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def safe_output(path, *inputs):
    if Path(path).resolve() in {Path(p).resolve() for p in inputs if p}:
        raise ValueError('Output must not overwrite an input file.')


def request_json(url):
    # Respect host trust stores / SSL_CERT_FILE; never disable TLS verification.
    req = urllib.request.Request(url, headers={'User-Agent': 'MusicAnalysis/1.0', 'Referer': 'https://y.qq.com/'})
    with urllib.request.urlopen(req, timeout=30, context=tls_context()) as response:
        data = response.read(32 * 1024 * 1024 + 1)
    if len(data) > 32 * 1024 * 1024:
        raise ValueError('Metadata response exceeds 32 MiB.')
    return json.loads(data.decode('utf-8-sig'))


def playlist_id(value):
    value = value.strip()
    if re.fullmatch(r'\d{1,20}', value):
        return value
    match = re.search(r'https?://[^\s<>]+', value)
    if not match:
        raise ValueError('Provide a QQ playlist ID, link, or share text containing a link.')
    url = urllib.parse.urlparse(html.unescape(match.group()).rstrip('。，；)）'))
    if url.scheme != 'https' or not (url.hostname == 'qq.com' or (url.hostname or '').endswith('.qq.com')):
        raise ValueError('Only HTTPS QQ links are accepted. Resolve other short links in your browser first.')
    query = urllib.parse.parse_qs(url.query)
    for key in ('id', 'disstid', 'tid'):
        if key in query and re.fullmatch(r'\d{1,20}', query[key][0]):
            return query[key][0]
    match = re.search(r'/playlist/(\d{1,20})(?:/|$)', url.path)
    if match:
        return match.group(1)
    raise ValueError('Link has no playlist ID. Open the shared card in a browser and copy its final URL.')


def unwrap(data):
    if isinstance(data, list):
        if not data:
            raise ValueError('Expected a nonempty track array.')
        return {}, data
    if not isinstance(data, dict):
        raise ValueError('Playlist input must be an object or track array.')
    if data.get('success') is False or data.get('code', 0) not in (0, '0', None):
        raise ValueError('Upstream returned an error; export public metadata or use a local file.')
    data = data.get('data', data)
    if not isinstance(data, dict):
        raise ValueError('Invalid data envelope.')
    data = data.get('result', data)
    if 'cdlist' in data:
        if len(data['cdlist']) != 1:
            raise ValueError('Expected exactly one playlist; export multiple playlists separately.')
        data = data['cdlist'][0]
    rows = data.get('tracks', data.get('songlist'))
    if not isinstance(rows, list) or not rows:
        raise ValueError('Expected a nonempty tracks or songlist array.')
    return data, rows


def normalize(data, expected=None):
    meta, rows = unwrap(data)
    declared = [int(meta[k]) for k in ('trackCount', 'songnum', 'total_song_num') if meta.get(k) is not None]
    if expected is not None:
        declared.append(int(expected))
    if any(n != len(rows) for n in declared):
        raise ValueError(f'Incomplete or inconsistent export: received {len(rows)} tracks, declared {declared}. Do not analyze a preview; export the complete playlist.')
    tracks = []
    for i, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f'Track {i} must be an object.')
        title = str(pick(row, 'title', 'songname', 'name', '歌名', '歌曲', 'Title')).strip()
        artists = credits(row)
        if not title or not artists:
            raise ValueError(f'Track {i} needs title and artists; no entries were skipped.')
        if 'index' in row and int(row['index']) != i:
            raise ValueError('Noncontiguous indices: preserve original order; normalize a complete export.')
        album = pick(row, 'album', 'albumname', '专辑', 'Album')
        album_mid = str(pick(row, 'albumMid', 'albummid'))
        if isinstance(album, dict):
            album_mid = str(album.get('mid', ''))
            album = album.get('title', album.get('name', ''))
        mid = str(pick(row, 'songMid', 'songmid', 'mid'))
        # Playlist Out uses id as QQ song MID, but other platforms use different identifiers.
        if not mid and meta.get('platform') == 'qqmusic':
            mid = str(row.get('id', ''))
        if mid and not re.fullmatch(r'[A-Za-z0-9]+', mid):
            raise ValueError(f'Invalid QQ song MID at track {i}.')
        source = str(row.get('sourceUrl', ''))
        if not source and mid:
            source = 'https://y.qq.com/n/ryqq/songDetail/' + mid
        seconds = pick(row, 'durationSeconds', 'interval', default=0)
        if not seconds and row.get('durationMs') is not None:
            seconds = float(row['durationMs']) / 1000
        cover = str(row.get('coverUrl', row.get('songCover', '')))
        if not cover and re.fullmatch(r'[A-Za-z0-9_]+', album_mid):
            cover = f'https://y.gtimg.cn/music/photo_new/T002R300x300M000{album_mid}.jpg'
        tracks.append(dict(index=i, title=title, artists=artists, artist='、'.join(artists),
                           album=str(album), albumMid=album_mid, durationSeconds=round(float(seconds or 0)),
                           songId=str(pick(row, 'songId', 'songid')), songMid=mid,
                           sourceUrl=source, coverUrl=cover))
    pid = str(pick(meta, 'id', 'disstid'))
    date = dt.datetime.now(dt.timezone.utc).isoformat()
    return dict(schemaVersion=1, name=str(pick(meta, 'name', 'dissname', default='我的歌单')),
                id=pid, sourceUrl=str(meta.get('sourceUrl', '')),
                exportedAt=meta.get('exportedAt', meta.get('exportedDate', date)),
                trackCount=len(tracks), tracks=tracks)


def snapshot_hash(playlist):
    # Exact ordered evidence snapshot. Cover cache changes do not alter identity.
    evidence = [{k: t.get(k) for k in ('index', 'title', 'artists', 'album', 'songId', 'songMid')}
                for t in playlist['tracks']]
    return hashlib.sha256(json.dumps(evidence, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def url_ok(value):
    url = urllib.parse.urlparse(value)
    return url.scheme in ('http', 'https') and bool(url.hostname) and not url.username and not url.password


def validate_analysis(playlist, report):
    n = playlist['trackCount']
    if report.get('playlistHash') != snapshot_hash(playlist):
        raise ValueError('Analysis references a different ordered playlist snapshot. Reconcile the analysis before rendering.')
    if report.get('status') != 'ready':
        raise ValueError('Analysis is still a draft. Complete grounded findings and mark status ready.')
    for key in ('title', 'summary'):
        if not isinstance(report.get(key), str) or not report[key].strip():
            raise ValueError(f'Analysis needs {key}.')
    order = report.get('order')
    if order not in ('first-oldest', 'last-oldest', 'unknown'):
        raise ValueError('order must be first-oldest, last-oldest, or unknown.')
    chapters = report.get('stages', [])
    if order == 'unknown' and chapters:
        raise ValueError('Unknown collection order: omit chronological chapters and analyze static preferences.')
    if chapters:
        covered = []
        for stage in chapters:
            lo, hi = stage['range']
            if not (1 <= lo <= hi <= n):
                raise ValueError('Invalid chapter range.')
            covered.extend(range(lo, hi + 1) if order == 'first-oldest' else range(hi, lo - 1, -1))
            for key in ('title', 'body', 'insight'):
                if not stage.get(key):
                    raise ValueError(f'Chapter needs {key}.')
            if not stage.get('anchorIds'):
                raise ValueError('Every chapter needs collection evidence.')
        expected = list(range(1, n + 1)) if order == 'first-oldest' else list(range(n, 0, -1))
        if covered != expected:
            raise ValueError('Chapters must cover every track exactly once in confirmed chronological order.')
    insights = report.get('insights', [])
    if not insights:
        raise ValueError('Analysis needs at least one evidence-backed insight.')
    def anchors(ids):
        if not ids or any(type(i) is not int or not 1 <= i <= n for i in ids):
            raise ValueError('Evidence indices must refer to this playlist.')
    for stage in chapters:
        anchors(stage['anchorIds'])
        if any(not stage['range'][0] <= i <= stage['range'][1] for i in stage['anchorIds']):
            raise ValueError('Chapter anchor is outside its chapter range.')
        if stage.get('coverIndex') is not None:
            anchors([stage['coverIndex']])
    for insight in insights:
        if not insight.get('title') or not insight.get('body'):
            raise ValueError('Insight needs title and body.')
        anchors([e['index'] for e in insight.get('evidence', [])])
        if any(not e.get('note') for e in insight['evidence']):
            raise ValueError('Explain each evidence track.')
        recommendation_ids = insight.get('recommendationIds', [])
        if not isinstance(recommendation_ids, list) or any(
                type(i) is not int or not 0 <= i < len(report.get('recommendations', []))
                for i in recommendation_ids):
            raise ValueError('Insight recommendationIds must refer to report recommendations (zero-based).')
    if report.get('heroAnchorIds'):
        anchors(report['heroAnchorIds'])
    stats = analyze(playlist['tracks'])
    seen_recs = set()
    for rec in report.get('recommendations', []):
        for key in ('title', 'artist', 'tier', 'reason', 'difference', 'source'):
            if not rec.get(key):
                raise ValueError(f'Recommendation needs {key}.')
        if rec['tier'] not in ('大概率合口味', '相邻风格', '探索') or not url_ok(rec['source']):
            raise ValueError('Recommendation requires a known tier and a verified HTTP(S) source.')
        anchors(rec.get('anchorIds'))
        rec_key = (rec['artist'].casefold(), rec['title'].casefold())
        if rec_key in seen_recs:
            raise ValueError('Duplicate recommendation in report.')
        seen_recs.add(rec_key)
        check = analyze(playlist['tracks'], [rec])['candidateChecks'][0]
        if check['status'] != 'not_detected':
            raise ValueError(f'Recommendation overlap requires review: {rec["title"]}: {check["status"]}')
    return stats


def export_files(playlist, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    save_json(out / 'playlist.json', playlist)
    (out / 'playlist.txt').write_text('\n'.join(f'{t["title"]} - {t["artist"]}' for t in playlist['tracks']) + '\n', encoding='utf-8')
    with (out / 'playlist.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['index', 'title', 'artist', 'album', 'durationSeconds', 'songMid', 'sourceUrl'])
        for t in playlist['tracks']:
            values = [t[k] for k in ('index', 'title', 'artist', 'album', 'durationSeconds', 'songMid', 'sourceUrl')]
            # Spreadsheet-safe CSV; original JSON preserves exact titles.
            w.writerow(["'" + x if isinstance(x, str) and x.startswith(('=', '+', '-', '@', '\t', '\r')) else x for x in values])


def render(playlist, report, covers=None):
    stats = validate_analysis(playlist, report)
    embedded = {}
    for index, value in (covers or {}).items():
        if not str(index).isdigit() or not 1 <= int(index) <= playlist['trackCount']:
            raise ValueError('Cover key must be a valid track index.')
        if not re.fullmatch(r'data:image/(?:jpeg|png|webp);base64,[A-Za-z0-9+/=\s]+', value):
            raise ValueError('Covers must be base64 JPEG, PNG or WebP data URLs.')
        embedded[str(index)] = value
    bundle = dict(playlist=playlist, report=report, stats=stats, covers=embedded, heroIndices=hero_indices(playlist, report), templateVersion='0.2.1')
    payload = json.dumps(bundle, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    template = (HERE.parent / 'assets/report.html').read_text(encoding='utf-8')
    return template.replace('__DOCUMENT_TITLE__', html.escape(report['title'])).replace('/*__REPORT_DATA__*/', payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    f = sub.add_parser('fetch', help='Fetch public QQ metadata; never downloads audio.')
    f.add_argument('link'); f.add_argument('--out', type=Path, required=True)
    f.add_argument('--provider', choices=['qq', 'playlistout'], default='qq')
    f.add_argument('--expect-count', type=int)
    n = sub.add_parser('normalize', help='Import QQ/Playlist Out JSON, normalized JSON, track arrays, or CSV.')
    n.add_argument('input', type=Path); n.add_argument('--out', type=Path, required=True); n.add_argument('--expect-count', type=int)
    st = sub.add_parser('stats'); st.add_argument('input', type=Path); st.add_argument('--output', type=Path, required=True)
    init = sub.add_parser('init-analysis'); init.add_argument('input', type=Path); init.add_argument('--output', type=Path, required=True)
    for command in ('validate', 'render'):
        p = sub.add_parser(command); p.add_argument('playlist', type=Path); p.add_argument('analysis', type=Path)
        if command == 'render':
            p.add_argument('--output', type=Path, required=True); p.add_argument('--covers', type=Path)
            p.add_argument('--offline', action='store_true', help='Use only supplied / cached artwork; no network.')
            p.add_argument('--require-covers', action='store_true', help='Fail if a chapter/hero representative image is unavailable.')
            p.add_argument('--cover-cache', type=Path, help='Artwork cache (default: beside output).')
    args = parser.parse_args()
    try:
        if args.command == 'fetch':
            pid = playlist_id(args.link)
            if args.provider == 'qq':
                url = 'https://c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg?' + urllib.parse.urlencode(dict(type=1, json=1, utf8=1, onlysong=0, disstid=pid, format='json'))
            else:
                url = 'https://playlistout-api.lengxiqwq.com/api/v1/resolve?' + urllib.parse.urlencode({'q': f'https://y.qq.com/n/ryqq/playlist/{pid}'})
            raw = request_json(url)
            playlist = normalize(raw, args.expect_count)
            if playlist['id'] != pid:
                raise ValueError('Returned playlist ID differs from requested ID.')
            playlist['sourceUrl'] = f'https://y.qq.com/n/ryqq/playlist/{pid}'
            args.out.mkdir(parents=True, exist_ok=True)
            save_json(args.out / 'source.json', raw)
            export_files(playlist, args.out)
            print(f'Exported {playlist["trackCount"]} tracks; snapshot {snapshot_hash(playlist)[:12]}')
        elif args.command == 'normalize':
            if args.input.suffix.lower() == '.csv':
                with args.input.open(encoding='utf-8-sig', newline='') as file:
                    data = list(csv.DictReader(file))
            else:
                data = read_json(args.input)
            for name in ('playlist.json', 'playlist.txt', 'playlist.csv'):
                safe_output(args.out / name, args.input)
            export_files(normalize(data, args.expect_count), args.out)
        elif args.command in ('stats', 'init-analysis'):
            safe_output(args.output, args.input)
            playlist = normalize(read_json(args.input))
            if args.command == 'stats':
                save_json(args.output, analyze(playlist['tracks']))
            else:
                if args.output.exists():
                    raise ValueError('Analysis draft already exists; edit it rather than overwriting it.')
                save_json(args.output, dict(schemaVersion=1, status='draft', playlistHash=snapshot_hash(playlist),
                    title='我的听歌地图', summary='', order='unknown', stages=[], insights=[], recommendations=[]))
        else:
            playlist = normalize(read_json(args.playlist)); report = read_json(args.analysis)
            if args.command == 'validate':
                validate_analysis(playlist, report); print('Analysis evidence and chronology are valid.')
            else:
                safe_output(args.output, args.playlist, args.analysis, args.covers)
                supplied = read_json(args.covers) if args.covers else None
                # Validate before network access. User metadata cannot trigger rendering of an invalid report.
                render(playlist, report, supplied)
                covers, failures = collect_covers(playlist, report,
                    args.cover_cache or args.output.parent / '.music-analysis-covers', supplied, args.offline)
                required = {s.get('coverIndex') or s['anchorIds'][0] for s in report.get('stages', [])}
                required.update(hero_indices(playlist, report))
                missing = sorted(i for i in required if str(i) not in covers)
                if args.require_covers and missing:
                    raise ValueError(f'Representative artwork unavailable at indices {missing}. Check metadata/network or supply --covers.')
                page = render(playlist, report, covers)
                print(f'Artwork: {len(covers)} embedded, {len(failures)} unavailable.', file=sys.stderr)
                if failures:
                    print('Artwork fallback: ' + '; '.join(f"#{f['index']} {f['reason']}" for f in failures[:5]), file=sys.stderr)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(page, encoding='utf-8'); print(f'Wrote {args.output}')
    except (ValueError, KeyError, TypeError, OSError) as e:
        parser.exit(1, f'Error: {e}\n')


if __name__ == '__main__':
    main()
