"""Fetch bounded music-platform artwork and cache it for offline reports."""
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import ssl
import urllib.parse
import urllib.request
from platforms import media_url

MAX_BYTES = 2 * 1024 * 1024


def tls_context():
    context = ssl.create_default_context()
    # Python.org macOS builds may omit the macOS CA bundle from default paths.
    system_bundle = Path('/etc/ssl/cert.pem')
    if system_bundle.is_file():
        context.load_verify_locations(cafile=str(system_bundle))
    return context


def qq_host(url):
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or ''
    return parsed.scheme == 'https' and not parsed.username and not parsed.password and (
        host in ('qq.com', 'gtimg.cn') or host.endswith(('.qq.com', '.gtimg.cn')))


class ArtworkRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, code, msg, headers, media_url(newurl))


def open_source(request):
    opener = urllib.request.build_opener(ArtworkRedirect(), urllib.request.HTTPSHandler(context=tls_context()))
    return opener.open(request, timeout=8)


def download(url):
    url = media_url(url)
    headers = {'User-Agent': 'MusicAnalysis/0.4'}
    if qq_host(url):
        headers['Referer'] = 'https://y.qq.com/'
    request = urllib.request.Request(url, headers=headers)
    with open_source(request) as response:
        if hasattr(response, 'geturl'):
            media_url(response.geturl())
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('Artwork exceeds 2 MiB.')
    return data


def data_url(data):
    if data.startswith(b'\xff\xd8\xff'):
        mime = 'jpeg'
    elif data.startswith(b'\x89PNG\r\n\x1a\n'):
        mime = 'png'
    elif data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        mime = 'webp'
    else:
        raise ValueError('Artwork response is not JPEG, PNG or WebP.')
    return f'data:image/{mime};base64,' + base64.b64encode(data).decode('ascii')


def hero_indices(playlist, report):
    candidates = list(report.get('heroAnchorIds', []))
    stages = report.get('stages', [])
    if stages:
        candidates.extend(s.get('coverIndex') or s['anchorIds'][0] for s in stages)
    candidates.extend(e['index'] for i in report.get('insights', []) for e in i.get('evidence', []))
    candidates.extend(t['index'] for t in playlist['tracks'])
    return list(dict.fromkeys(candidates))[:4]


def selected_indices(playlist, report):
    indices = [s.get('coverIndex') or s['anchorIds'][0] for s in report.get('stages', [])]
    indices.extend(hero_indices(playlist, report))
    indices.extend(i for s in report.get('stages', []) for i in s['anchorIds'])
    indices.extend(e['index'] for s in report.get('insights', []) for e in s['evidence'])
    indices.extend(i for r in report.get('recommendations', []) for i in r['anchorIds'])
    return list(dict.fromkeys(indices))[:96]


def collect_covers(playlist, report, cache_dir, supplied=None, offline=False):
    """Return embedded images plus failures. Cache is URL/MID keyed, never index keyed."""
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    by_id = {t['index']: t for t in playlist['tracks']}
    supplied = supplied or {}
    indices = [i for i in selected_indices(playlist, report) if str(i) not in supplied]
    # Album URLs often repeat; group identical sources into one download.
    groups = {}
    for i in indices:
        t = by_id[i]
        identity = t.get('coverUrl') or ('mid:' + t['songMid'] if t.get('songMid') else '')
        if identity:
            groups.setdefault(identity, []).append(i)
    def fetch(item):
        identity, ids = item
        path = cache / (hashlib.sha256(identity.encode()).hexdigest() + '.image')
        try:
            if path.exists():
                try:
                    return ids, data_url(path.read_bytes()), None
                except ValueError:
                    pass
            if offline:
                return ids, None, 'not cached (offline)'
            url = identity
            if identity.startswith('mid:'):
                mid = identity[4:]
                if not re.fullmatch(r'[A-Za-z0-9]+', mid):
                    raise ValueError('Invalid QQ song MID.')
                raw = download('https://c.y.qq.com/v8/fcg-bin/fcg_play_single_song.fcg?' + urllib.parse.urlencode(
                    dict(songmid=mid, tpl='yqq_song_detail', format='json')))
                detail = json.loads(raw)['data'][0]
                # Verify the response belongs to the requested track before borrowing artwork.
                if str(detail.get('mid', detail.get('songmid', ''))) != mid:
                    raise ValueError('QQ song detail returned another track.')
                album = detail.get('album', {})
                album_mid = album.get('pmid') or album.get('mid', '')
                if not re.fullmatch(r'[A-Za-z0-9_]+', str(album_mid)):
                    raise ValueError('Song detail contains no album MID.')
                url = f'https://y.gtimg.cn/music/photo_new/T002R300x300M000{album_mid}.jpg'
            raw = download(url)
            result = data_url(raw)
            path.write_bytes(raw)
            return ids, result, None
        except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
            return ids, None, type(error).__name__ + ': ' + str(error)[:140]
    result = dict(supplied)
    failures = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for ids, value, error in pool.map(fetch, groups.items()):
            if value:
                result.update((str(i), value) for i in ids)
            else:
                failures.extend({'index': i, 'reason': error} for i in ids)
    failures.extend({'index': i, 'reason': 'No artwork URL or QQ song MID in metadata.'}
                    for i in indices if not by_id[i].get('coverUrl') and not by_id[i].get('songMid'))
    return result, failures
