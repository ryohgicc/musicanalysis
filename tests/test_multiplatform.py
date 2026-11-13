"""Cross-platform resolver contracts with fictional tracks; no upstream fixtures."""
import contextlib
import copy
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import urllib.parse
import urllib.request

from test_workflow import complete_fixture
from test_visual_pipeline import PNG
from workflow import fetch_playlist, normalize, main, request_json, snapshot_hash, save_json
from platforms import PLATFORMS, playlist_target, media_url
from covers import ArtworkRedirect, collect_covers, download

LINKS = {
    'qqmusic': 'https://y.qq.com/n/ryqq/playlist/12345',
    'netease': 'https://music.163.com/#/playlist?id=12345',
    'kugou': 'https://m.kugou.com/songlist/gcid_fake12345/',
    'kuwo': 'https://www.kuwo.cn/playlist_detail/12345',
    'qishui': 'https://music.douyin.com/qishui/share/playlist?playlist_id=12345',
    'migu': 'https://music.migu.cn/v5/#/playlist/12345',
}
ART = {
    'qqmusic': 'https://y.gtimg.cn/fictional.png',
    'netease': 'https://p3.music.126.net/fictional.png',
    'kugou': 'http://imge.kugou.com/fictional.png',
    'kuwo': 'https://img1.kuwo.cn/fictional.png',
    'qishui': 'https://p3-luna.douyinpic.com/fictional.png',
    'migu': 'https://d.musicapp.migu.cn/fictional.png',
}


def canonical(platform, identity='12345'):
    return dict(success=True, data=dict(kind='playlist', platform=platform, result=dict(
        platform=platform, id=identity, name='Fictional playlist', sourceUrl=LINKS[platform], trackCount=1,
        tracks=[dict(index=1, title='Fictional song', artist='Artist A, Artist B', album='Synthetic album',
                     id='ABC123' if platform == 'qqmusic' else '67890', durationMs=123000, coverUrl=ART[platform])]
    )))


class MultiplatformTest(unittest.TestCase):
    def test_resolver_receives_correct_platform_and_input(self):
        for platform, link in LINKS.items():
            with self.subTest(platform=platform):
                with patch('workflow.request_json', return_value=canonical(platform)) as request:
                    playlist, _ = fetch_playlist('分享歌单「测试」：' + link, provider='playlistout')
                parsed = urllib.parse.urlparse(request.call_args.args[0])
                params = urllib.parse.parse_qs(parsed.query)
                self.assertEqual(parsed.hostname, 'playlistout-api.lengxiqwq.com')
                self.assertEqual(params['platform'], [platform])
                self.assertEqual(params['type'], ['playlist'])
                self.assertEqual(params['q'], [link])
                self.assertEqual(playlist['platform'], platform)
                self.assertEqual(playlist['tracks'][0]['artists'], ['Artist A', 'Artist B'])
                self.assertEqual(playlist['tracks'][0]['durationSeconds'], 123)
                self.assertEqual(playlist['tracks'][0]['coverUrl'], ART[platform])
                if platform == 'qqmusic':
                    self.assertEqual(playlist['tracks'][0]['songMid'], 'ABC123')
                else:
                    self.assertEqual(playlist['tracks'][0]['songMid'], '')
                    self.assertEqual(playlist['tracks'][0]['songId'], '67890')
                    self.assertNotIn('qq.com', playlist['tracks'][0]['sourceUrl'])
                self.assertEqual(normalize(playlist), playlist)

    def test_auto_routing_keeps_qq_direct_and_does_not_fallback(self):
        raw = dict(cdlist=[dict(disstid='12345', songnum=1, songlist=[dict(songname='Synthetic', singer=[dict(name='A')])])])
        with patch('workflow.request_json', return_value=raw) as request:
            playlist, _ = fetch_playlist('12345')
        self.assertEqual(playlist['platform'], 'qqmusic')
        self.assertEqual(urllib.parse.urlparse(request.call_args.args[0]).hostname, 'c.y.qq.com')
        with patch('workflow.request_json', side_effect=ValueError('unavailable')) as request:
            with self.assertRaisesRegex(ValueError, 'unavailable'):
                fetch_playlist(LINKS['qqmusic'])
            self.assertEqual(request.call_count, 1)
        with patch('workflow.request_json', return_value=canonical('netease')) as request:
            fetch_playlist('12345', platform='netease')
            self.assertIn('platform=netease', request.call_args.args[0])

    def test_shortlinks_share_text_and_concept_edition(self):
        for platform, link in [
            ('qqmusic', 'https://c6.y.qq.com/base/fcgi-bin/u?__=opaque'),
            ('netease', 'https://163cn.tv/fictional'),
            ('kugou', 'https://t.kugou.com/fictional'),
            ('kugou', 'https://m.kugou.com/share/?global_specialid=collection_3_12345_2_0'),
            ('kuwo', 'https://m.kuwo.cn/h5app/playlist/12345'),
            ('qishui', 'https://qishui.douyin.com/s/fictional/'),
            ('migu', 'https://c.migu.cn/fictional'),
        ]:
            with self.subTest(link=link), patch('workflow.request_json', return_value=canonical(platform)) as request:
                fetch_playlist('分享：' + link + '，快来听')
                params = urllib.parse.parse_qs(urllib.parse.urlparse(request.call_args.args[0]).query)
                self.assertEqual(params['q'], [link])
                self.assertEqual(params['platform'], [platform])

    def test_invalid_input_and_response_identity_fail(self):
        for link in ['https://qq.com.evil.test/?id=12345', 'https://localhost/?id=12345',
                     'https://user:password@music.163.com/playlist?id=12345', 'https://open.spotify.com/playlist/test']:
            with self.subTest(link=link), patch('workflow.request_json') as request:
                with self.assertRaises(ValueError):
                    fetch_playlist(link)
                request.assert_not_called()
        with self.assertRaisesRegex(ValueError, 'differs'):
            playlist_target(LINKS['netease'], 'qqmusic')
        with self.assertRaisesRegex(ValueError, 'only accepts QQ'):
            fetch_playlist(LINKS['netease'], provider='qq')
        for raw in [canonical('qqmusic'), canonical('netease', identity='999')]:
            with patch('workflow.request_json', return_value=raw), self.assertRaisesRegex(ValueError, 'differs'):
                fetch_playlist(LINKS['netease'])
        raw = canonical('netease'); raw['data']['kind'] = 'user_playlists'
        with self.assertRaisesRegex(ValueError, 'single playlist'):
            normalize(raw)

    def test_partial_retrieval_rejected_even_when_counts_match(self):
        base = canonical('kugou')
        variants = []
        for location in ['root', 'data', 'result']:
            data = copy.deepcopy(base)
            target = data if location == 'root' else data['data'] if location == 'data' else data['data']['result']
            target['retrieval'] = dict(mode='preview', reason='auth_required')
            variants.append(data)
        for field, value in [('isPartial', True), ('loadedTrackCount', 10), ('trackCount', 99)]:
            data = copy.deepcopy(base); data['data']['result'][field] = value; variants.append(data)
        data = copy.deepcopy(base); data['meta'] = dict(parseInfo=dict(mode='preview')); variants.append(data)
        for data in variants:
            with self.subTest(data=data), self.assertRaisesRegex(ValueError, '[Ii]ncomplete'):
                normalize(data)

    def test_cli_incomplete_does_not_write_a_snapshot(self):
        raw = canonical('kugou'); raw['data']['result']['isPartial'] = True
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / 'snapshot'
            args = ['workflow.py', 'fetch', LINKS['kugou'], '--out', str(out)]
            with patch('sys.argv', args), patch('workflow.request_json', return_value=raw), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main()
            self.assertFalse(out.exists())

    def test_http_error_explains_platform_disambiguation(self):
        error = urllib.error.HTTPError('https://example.org', 409, 'Conflict', {}, io.BytesIO(
            json.dumps(dict(success=False, error=dict(code='AMBIGUOUS_INPUT'))).encode()))
        with patch('urllib.request.urlopen', side_effect=error), self.assertRaisesRegex(ValueError, '--platform'):
            request_json('https://example.org')

    def test_csv_import_keeps_external_link_duration_cover_and_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.csv'; out = Path(folder) / 'normalized'
            with source.open('w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=['index', 'title', 'artist', 'album', 'duration', 'url', 'coverUrl', 'songId'])
                writer.writeheader(); writer.writerow(dict(index=1, title='Fictional', artist='A', album='Synthetic', duration=90,
                    url='https://music.163.com/#/song?id=67890', coverUrl=ART['netease'], songId='67890'))
            with patch('sys.argv', ['workflow.py', 'normalize', str(source), '--out', str(out)]):
                main()
            result = json.loads((out / 'playlist.json').read_text())
            self.assertEqual(result['platform'], 'netease')
            self.assertEqual(result['tracks'][0]['durationSeconds'], 90)
            self.assertEqual(result['tracks'][0]['songId'], '67890')
            self.assertEqual(result['tracks'][0]['coverUrl'], ART['netease'])
            second = copy.deepcopy(result); second['platform'] = 'migu'
            self.assertNotEqual(snapshot_hash(result), snapshot_hash(second))

    def test_artwork_downloads_from_all_platforms_and_loads_offline(self):
        playlist, report = complete_fixture()
        for track in playlist['tracks']:
            track['songMid'] = ''
            track['coverUrl'] = ART[PLATFORMS[(track['index'] - 1) % len(PLATFORMS)]]
        with tempfile.TemporaryDirectory() as folder:
            with patch('covers.open_source', side_effect=lambda *a, **k: io.BytesIO(PNG)) as network:
                images, failures = collect_covers(playlist, report, folder)
                self.assertFalse(failures)
                self.assertEqual(len(images), 27)
                self.assertEqual(network.call_count, len(PLATFORMS))
                self.assertTrue(all(call.args[0].full_url.startswith('https://') for call in network.call_args_list))
            with patch('covers.open_source', side_effect=AssertionError('offline accessed network')):
                cached, failures = collect_covers(playlist, report, folder, offline=True)
                self.assertEqual(cached, images)
                self.assertFalse(failures)
        for value in ['https://music.126.net.evil.test/a.png', 'http://127.0.0.1/a.png', 'file:///etc/passwd', 'https://x:y@p3.music.126.net/a.png']:
            with self.subTest(value=value), patch('covers.open_source') as network:
                with self.assertRaises(ValueError):
                    download(value)
                network.assert_not_called()
        redirect = ArtworkRedirect()
        with self.assertRaises(ValueError):
            redirect.redirect_request(urllib.request.Request(ART['netease']), None, 302, 'Found', {}, 'http://127.0.0.1/a.png')
        self.assertEqual(media_url(ART['kugou']), ART['kugou'].replace('http:', 'https:'))


if __name__ == '__main__':
    unittest.main()
