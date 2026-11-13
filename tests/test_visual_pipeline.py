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
from test_workflow import fixture
from workflow import main, save_json
from covers import collect_covers, selected_indices

# Original synthetic 1px PNG. Network bytes are deterministic; no music cover is committed.
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jM9kAAAAASUVORK5CYII=')

class VisualPipelineTest(unittest.TestCase):
    def test_default_render_embeds_available_covers(self):
        playlist,report=fixture()
        for track in playlist['tracks']:
            track['coverUrl']='https://y.gtimg.cn/music/photo_new/test-cover.png'
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);save_json(folder/'playlist.json',playlist);save_json(folder/'analysis.json',report)
            with patch('sys.argv',['workflow.py','render',str(folder/'playlist.json'),str(folder/'analysis.json'),'--output',str(folder/'report.html')]),patch('urllib.request.urlopen',side_effect=lambda *a,**k:io.BytesIO(PNG)),contextlib.redirect_stdout(io.StringIO()):
                main()
            page=(folder/'report.html').read_text()
            payload=page.split('<script type="application/json" id="report-data">')[1].split('</script>')[0]
            data=json.loads(payload)
            self.assertTrue(data['covers'],'Default render dropped all album images; it requires an undocumented manual --covers step.')
            for index in (1,3,5,6):self.assertIn(str(index),data['covers'])
            self.assertTrue(all(x.startswith('data:image/png;base64,') for x in data['covers'].values()))

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
            args=['workflow.py','render',str(folder/'playlist.json'),str(folder/'analysis.json'),'--output',str(folder/'report.html'),'--offline','--require-covers']
            with patch('sys.argv',args),contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code,1)
            self.assertFalse((folder/'report.html').exists())

if __name__=='__main__':unittest.main()
