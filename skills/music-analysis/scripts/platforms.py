"""Platform routing and source links; metadata retrieval belongs to Playlist Out."""
import html
import re
import urllib.parse

PLATFORMS = ('qqmusic', 'netease', 'kugou', 'kuwo', 'qishui', 'migu')
LINK_HOSTS = {
    'qqmusic': ('qq.com',),
    'netease': ('music.163.com', '163cn.tv'),
    'kugou': ('kugou.com',),
    'kuwo': ('kuwo.cn',),
    'qishui': ('douyin.com', 'qishui.com'),
    'migu': ('migu.cn',),
}
ARTWORK_HOSTS = ('qq.com', 'gtimg.cn', 'music.126.net', 'music.163.com',
                 'kgimg.com', 'kugou.com', 'kuwo.cn', 'byteimg.com',
                 'douyinpic.com', 'douyincdn.com', 'pstatp.com', 'migu.cn')


def host_matches(host, roots):
    return any(host == root or host.endswith('.' + root) for root in roots)


def platform_from_url(value):
    host = urllib.parse.urlparse(value).hostname or ''
    return next((p for p, roots in LINK_HOSTS.items() if host_matches(host, roots)), '')


def media_url(value):
    """Upgrade legacy artwork URLs only on known source CDN hosts."""
    parsed = urllib.parse.urlparse(value)
    if (parsed.scheme not in ('http', 'https') or parsed.username or parsed.password
            or parsed.port not in (None, 80, 443)
            or not host_matches(parsed.hostname or '', ARTWORK_HOSTS)):
        raise ValueError('Artwork must use a supported music platform HTTPS/CDN source.')
    return parsed._replace(scheme='https', netloc=parsed.hostname).geturl()


def song_url(platform, identity):
    if not identity or not re.fullmatch(r'[A-Za-z0-9_-]+', identity):
        return ''
    if platform == 'qqmusic':
        return 'https://y.qq.com/n/ryqq/songDetail/' + identity
    if platform == 'netease' and identity.isdigit():
        return 'https://music.163.com/#/song?id=' + identity
    if platform == 'kugou' and re.fullmatch(r'[A-Fa-f0-9]{32}', identity):
        return 'https://www.kugou.com/song/#hash=' + identity
    if platform == 'kuwo' and identity.isdigit():
        return 'https://www.kuwo.cn/play_detail/' + identity
    if platform == 'migu':
        return 'https://music.migu.cn/v5/#/song/' + identity
    # Qishui IDs can denote tracks or original sounds. Use only supplied links.
    return ''


def playlist_url(platform, identity):
    if not re.fullmatch(r'\d{1,20}', identity):
        return ''
    prefix = {
        'qqmusic': 'https://y.qq.com/n/ryqq/playlist/',
        'netease': 'https://music.163.com/#/playlist?id=',
        'kuwo': 'https://www.kuwo.cn/playlist_detail/',
        'migu': 'https://music.migu.cn/v5/#/playlist/',
        'qishui': 'https://music.douyin.com/qishui/share/playlist?playlist_id=',
    }.get(platform)
    return prefix + identity if prefix else ''


def playlist_target(value, platform='auto'):
    """Return platform, resolver input and any verifiable playlist ID.

    Legacy bare numeric IDs keep their QQ meaning. Other IDs need --platform.
    Shortlinks are resolved by the upstream, never fetched as arbitrary URLs here.
    """
    value = value.strip()
    if not value or len(value) > 2048:
        raise ValueError('Provide a playlist link/share text or ID (at most 2048 characters).')
    if platform not in ('auto', *PLATFORMS):
        raise ValueError('Unsupported platform.')
    match = re.search(r'https?://[^\s<>「」【】，。；！）]+', value, re.I)
    if not match:
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', value):
            raise ValueError('Provide a supported playlist link or an ID with --platform.')
        if platform == 'auto':
            if not re.fullmatch(r'\d{1,20}', value):
                raise ValueError('Non-numeric IDs require --platform.')
            platform = 'qqmusic'
        return platform, playlist_url(platform, value) or value, value
    parsed = urllib.parse.urlparse(html.unescape(match.group()).rstrip('。，；,;!！)）]'))
    detected = platform_from_url(parsed.geturl())
    if (not detected or parsed.username or parsed.password or parsed.port not in (None, 80, 443)):
        raise ValueError('Unsupported playlist host. Use QQ, NetEase, Kugou, Kuwo, Qishui or Migu.')
    if platform != 'auto' and platform != detected:
        raise ValueError('Link platform differs from --platform.')
    # Strip tracking on long playlist links. Keep opaque shortlink parameters intact.
    combined = parsed.path + ('?' + parsed.query if parsed.query else '')
    if parsed.fragment:
        combined += parsed.fragment
    identity = ''
    patterns = {
        'qqmusic': (r'/playlist/(\d{1,20})(?:/|$|[?&#])', r'[?&](?:id|disstid|tid)=(\d{1,20})(?:&|$|#)'),
        'netease': (r'/playlist/(\d{1,20})(?:/|$|[?&#])', r'/playlist\?id=(\d{1,20})(?:&|$)'),
        'kuwo': (r'/playlist_detail/(\d{1,20})(?:/|$|[?&#])',),
        'migu': (r'/playlist/(\d{1,20})(?:/|$|[?&#])',),
        'qishui': (r'[?&]playlist_id=(\d{1,20})(?:&|$)',),
    }
    for pattern in patterns.get(detected, ()):
        found = re.search(pattern, combined)
        if found:
            identity = found.group(1)
            break
    query = playlist_url(detected, identity) if identity else ''
    return detected, query or parsed._replace(scheme='https').geturl(), identity
