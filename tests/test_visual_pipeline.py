"""The normal render command must produce the illustrated report without a manual cover file."""
import base64
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from test_workflow import fixture, complete_fixture
from workflow import main, save_json, validate_analysis, render
from covers import collect_covers, collect_recommendation_covers, selected_indices, data_url

# Original synthetic 1px PNG. Network bytes are deterministic; no music cover is committed.
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jM9kAAAAASUVORK5CYII=')

class VisualPipelineTest(unittest.TestCase):
    def test_default_render_embeds_available_covers(self):
        playlist,report=complete_fixture()
        for track in playlist['tracks']:
            track['coverUrl']='https://y.gtimg.cn/music/photo_new/test-cover.png'
        for rec in report['recommendations']:
            rec['artwork']=dict(kind='album', label='Synthetic release', source='https://music.apple.com/album/synthetic', imageUrl='https://is1-ssl.mzstatic.com/synthetic.png')
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);save_json(folder/'playlist.json',playlist);save_json(folder/'analysis.json',report)
            args=['workflow.py','render',str(folder/'playlist.json'),str(folder/'analysis.json'),'--output',str(folder/'report.html'),'--require-covers']
            with patch('sys.argv',args),patch('covers.open_source',side_effect=lambda *a,**k:io.BytesIO(PNG)),contextlib.redirect_stdout(io.StringIO()):
                main()
            page=(folder/'report.html').read_text()
            payload=page.split('<script type="application/json" id="report-data">')[1].split('</script>')[0]
            data=json.loads(payload)
            self.assertTrue(data['covers'],'Default render dropped all album images; it requires an undocumented manual --covers step.')
            for index in (1,3,5,6):self.assertIn(str(index),data['covers'])
            self.assertTrue(all(x.startswith('data:image/png;base64,') for x in data['covers'].values()))
            self.assertEqual(len(data['recommendationCovers']), 12)
            with patch('sys.argv',args+['--offline']),patch('covers.open_source',side_effect=AssertionError('Offline CLI accessed network')),contextlib.redirect_stdout(io.StringIO()):
                main()
            self.assertEqual((folder/'report.html').read_text(),page)

    def test_default_cli_rejects_incomplete_content_before_network(self):
        playlist,report=fixture()
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);save_json(folder/'playlist.json',playlist);save_json(folder/'analysis.json',report)
            args=['workflow.py','render',str(folder/'playlist.json'),str(folder/'analysis.json'),'--output',str(folder/'report.html')]
            with patch('sys.argv',args),patch('workflow.collect_covers') as fetch,contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                main()
            fetch.assert_not_called()
            self.assertFalse((folder/'report.html').exists())

    def test_mid_lookup_and_offline_cache(self):
        playlist,report=fixture()
        def source(url):
            if 'songmid=' in url:
                from urllib.parse import parse_qs, urlparse
                mid=parse_qs(urlparse(url).query)['songmid'][0]
                return json.dumps({'data':[{'mid':mid,'album':{'mid':'album'+mid}}]}).encode()
            return PNG
        with tempfile.TemporaryDirectory() as tmp:
            with patch('covers.download',side_effect=source) as download:
                covers,failures=collect_covers(playlist,report,tmp)
                self.assertFalse(failures)
                self.assertEqual(len(covers),len(selected_indices(playlist,report)))
                self.assertEqual(download.call_count,len(covers)*2)
            with patch('covers.download',side_effect=AssertionError('Offline render accessed network')):
                cached,failures=collect_covers(playlist,report,tmp,offline=True)
                self.assertEqual(cached,covers)
                self.assertFalse(failures)
                playlist['tracks'][0]['songMid']='changedMid'
                changed,failures=collect_covers(playlist,report,tmp,offline=True)
                self.assertNotIn('1',changed)
                self.assertTrue(any(f['index']==1 for f in failures))

    def test_rejects_wrong_track_and_non_image_responses(self):
        playlist,report=fixture()
        with tempfile.TemporaryDirectory() as tmp:
            wrong=json.dumps({'data':[{'mid':'anotherTrack','album':{'mid':'album'}}]}).encode()
            with patch('covers.download',return_value=wrong):
                covers,failures=collect_covers(playlist,report,tmp)
                self.assertFalse(covers)
                self.assertTrue(all('another track' in f['reason'] for f in failures))
            for track in playlist['tracks']:
                track['coverUrl']='https://y.gtimg.cn/not-an-image'
            with patch('covers.download',return_value=b'<html>Unavailable</html>'):
                covers,failures=collect_covers(playlist,report,tmp)
                self.assertFalse(covers)
                self.assertTrue(all('not JPEG, PNG or WebP' in f['reason'] for f in failures))

    def test_require_covers_fails_without_writing_partial_report(self):
        playlist,report=fixture()
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);save_json(folder/'playlist.json',playlist);save_json(folder/'analysis.json',report)
            args=['workflow.py','render',str(folder/'playlist.json'),str(folder/'analysis.json'),'--output',str(folder/'report.html'),'--offline','--require-covers','--preview']
            with patch('sys.argv',args),contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code,1)
            self.assertFalse((folder/'report.html').exists())

    def test_verified_recommendation_and_artist_images_cache_offline(self):
        playlist, report = complete_fixture()
        report['trackArtwork'] = {'2': dict(kind='artist', label='Artist portrait',
            source='https://y.qq.com/n/ryqq/singerDetail/artist', imageUrl='https://y.gtimg.cn/portrait.jpg')}
        for rec in report['recommendations']:
            rec['artwork'] = dict(kind='album', label='Verified live release',
                source='https://music.apple.com/album/verified', imageUrl='https://is1-ssl.mzstatic.com/image/verified.jpg')
        validate_analysis(playlist, report)
        with tempfile.TemporaryDirectory() as tmp:
            with patch('covers.download', return_value=PNG) as fetch:
                recs, failures = collect_recommendation_covers(report, tmp)
                self.assertFalse(failures)
                self.assertEqual(len(recs), 12)
                self.assertEqual(fetch.call_count, 1)
                images, _ = collect_covers(playlist, report, tmp)
                self.assertEqual(images['2'], data_url(PNG))
                self.assertTrue(any(c.args[0] == 'https://y.gtimg.cn/portrait.jpg' for c in fetch.call_args_list))
            with patch('covers.download', side_effect=AssertionError('Offline network')):
                cached, failures = collect_recommendation_covers(report, tmp, offline=True)
                self.assertEqual(cached, recs)
                self.assertFalse(failures)
                report['recommendations'][0]['artwork']['imageUrl'] = 'https://is1-ssl.mzstatic.com/new-version.jpg'
                changed, failures = collect_recommendation_covers(report, tmp, offline=True)
                self.assertNotIn('0', changed)
                self.assertEqual(failures[0]['recommendation'], 0)

    def test_invalid_artwork_rejected_before_network(self):
        playlist, report = complete_fixture()
        rec = report['recommendations'][0]
        for art in [dict(kind='artist', label='Wrong version', source='https://example.org', imageUrl='https://y.gtimg.cn/cover.jpg'),
                    dict(kind='album', label='Release', source='javascript:alert(1)', imageUrl='https://y.gtimg.cn/cover.jpg'),
                    dict(kind='album', label='Release', source='https://example.org', imageUrl='https://evil.test/cover.jpg')]:
            rec['artwork'] = art
            with self.assertRaises(ValueError):
                render(playlist, report)
        rec.pop('artwork')
        with self.assertRaisesRegex(ValueError, 'verified artwork metadata'):
            render(playlist, report, recommendation_covers={'0': data_url(PNG)})

    def test_require_covers_checks_evidence_and_recommendations(self):
        playlist, report = complete_fixture()
        for track in playlist['tracks']:
            track['coverUrl'] = 'https://y.gtimg.cn/cover.jpg'
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            save_json(folder/'playlist.json', playlist)
            save_json(folder/'analysis.json', report)
            args = ['workflow.py', 'render', str(folder/'playlist.json'), str(folder/'analysis.json'),
                    '--output', str(folder/'report.html'), '--require-covers']
            with patch('sys.argv', args), patch('covers.download', return_value=PNG), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main()
            self.assertFalse((folder/'report.html').exists())
            for rec in report['recommendations']:
                rec['artwork'] = dict(kind='album', label='Release', source='https://music.apple.com/album/test', imageUrl='https://is1-ssl.mzstatic.com/cover.jpg')
            save_json(folder/'analysis.json', report)
            images = {str(i): data_url(PNG) for i in selected_indices(playlist, report) if i != 27}
            with patch('sys.argv', args), patch('workflow.collect_covers', return_value=(images, [{'index': 27, 'reason': 'missing'}])), patch('covers.download', return_value=PNG), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main()
            self.assertFalse((folder/'report.html').exists())

if __name__=='__main__':unittest.main()
