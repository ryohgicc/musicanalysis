import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/music-analysis/scripts'))
from workflow import normalize, playlist_id, snapshot_hash, validate_analysis, render, export_files
from analyze_playlist import analyze, credits

def fixture():
    p = normalize({'name': '虚构收藏', 'id': '12345', 'trackCount': 6, 'tracks': [
        {'title': 'Alpha (Live)', 'artists': ['A'], 'album': 'Live', 'songMid': 'mid1'},
        {'title': 'Alpha', 'artists': ['A'], 'album': 'Studio', 'songMid': 'mid2'},
        {'title': 'Duet', 'artists': ['A', 'B'], 'album': 'Duets', 'songMid': 'mid3'},
        {'title': 'Flow', 'artists': ['C'], 'album': 'One', 'songMid': 'mid4'},
        {'title': 'Bridge', 'artists': ['リリィ、さよなら。'], 'album': 'Two', 'songMid': 'mid5'},
        {'title': 'Origin', 'artists': ['B'], 'album': 'Three', 'songMid': 'mid6'}]})
    r = dict(status='ready', playlistHash=snapshot_hash(p), title='虚构数据示例', summary='演示流程，不是音乐偏好结论。', order='last-oldest',
        stages=[dict(range=[4,6], tag='起点', title='较早收藏', body='虚构阶段说明', insight='示例', anchorIds=[6,5]),
                dict(range=[1,3], tag='延伸', title='较新收藏', body='虚构阶段说明', insight='示例', anchorIds=[3,1])],
        insights=[dict(title='示例线索', summary='这里是示例，不是听感推断。', body='真实报告应解释具体作品。', evidence=[dict(index=6,note='示例证据'),dict(index=1,note='示例证据')])], recommendations=[])
    return p,r

class WorkflowTest(unittest.TestCase):
    def test_share_links(self):
        for v in ['12345','https://y.qq.com/n/ryqq/playlist/12345','分享：https://i2.y.qq.com/n3/share?id=12345&hosteuin=abc','https://y.qq.com/share?disstid=12345']:
            self.assertEqual(playlist_id(v),'12345')
        for v in ['https://evil.test/?id=12345','https://qq.com.evil.test/?id=12345','http://y.qq.com/?id=12345','https://c6.y.qq.com/shortlink']:
            with self.assertRaises(ValueError): playlist_id(v)
    def test_versions_credits_order(self):
        p,_=fixture(); stats=analyze(p['tracks']); counts={a['artist']:a['count'] for a in stats['artistParticipation']}
        self.assertEqual(counts['A'],3); self.assertEqual(stats['heuristicFamilyCount'],5)
        self.assertEqual(credits({'artist':'リリィ、さよなら。'}),['リリィ、さよなら。'])
        self.assertEqual([t['index'] for t in p['tracks']],list(range(1,7)))
    def test_upstream_completeness(self):
        raw={'cdlist':[{'disstid':'12','songnum':1,'songlist':[{'songname':'X','singer':[{'name':'A'}],'songmid':'abc','interval':120}]}]}
        self.assertEqual(normalize(raw)['tracks'][0]['durationSeconds'],120)
        raw['cdlist'][0]['songnum']=50
        with self.assertRaises(ValueError): normalize(raw)
        with self.assertRaises(ValueError): normalize({'success':False})
        canonical={'success':True,'data':{'result':{'platform':'qqmusic','id':'12','trackCount':1,'tracks':[{'title':'X','artist':'A','id':'mid12','durationMs':123000}]}}}
        self.assertEqual(normalize(canonical)['tracks'][0]['songMid'],'mid12')
        with self.assertRaises(ValueError): normalize(canonical,expected=3)
    def test_snapshot_and_ranges(self):
        p,r=fixture();validate_analysis(p,r);p['tracks'].reverse()
        with self.assertRaisesRegex(ValueError,'different ordered'):validate_analysis(p,r)
        p,r=fixture();r['stages'][1]['range']=[1,4]
        with self.assertRaises(ValueError):validate_analysis(p,r)
        p,r=fixture();r['stages'][0]['anchorIds']=[1]
        with self.assertRaisesRegex(ValueError,'outside'):validate_analysis(p,r)
        p,r=fixture();r['order']='unknown'
        with self.assertRaises(ValueError):validate_analysis(p,r)
        r['stages']=[];validate_analysis(p,r)
        r['order']='first-oldest';r['stages']=[dict(range=[1,6],title='all',body='all',insight='all',anchorIds=[1,6])];validate_analysis(p,r)
    def test_recommendation_overlap(self):
        p,r=fixture();rec=dict(title='Alpha (Remix)',artist='A',tier='探索',anchorIds=[6],reason='test',difference='test',source='https://example.org/work');r['recommendations']=[rec]
        with self.assertRaisesRegex(ValueError,'overlap'):validate_analysis(p,r)
        rec['title']='Duet';rec['artist']='New artist'
        with self.assertRaisesRegex(ValueError,'review_same_title'):validate_analysis(p,r)
        rec['title']='Uncollected';validate_analysis(p,r);rec['source']='javascript:alert(1)'
        with self.assertRaises(ValueError):validate_analysis(p,r)
    def test_insight_recommendation_references(self):
        p,r=fixture();r['insights'][0]['recommendationIds']=[0]
        with self.assertRaisesRegex(ValueError,'recommendationIds'):validate_analysis(p,r)
        r['recommendations']=[dict(title='Uncollected',artist='New artist',tier='探索',anchorIds=[3],reason='test',difference='test',source='https://example.org/work')]
        validate_analysis(p,r)
        r['insights'][0]['recommendationIds']=[True]
        with self.assertRaisesRegex(ValueError,'recommendationIds'):validate_analysis(p,r)

    def test_exports_and_untrusted_metadata(self):
        p,r=fixture();p['tracks'][0]['title']='=SUM(1,2)'
        with tempfile.TemporaryDirectory() as d:
            export_files(p,d);self.assertEqual(json.loads((Path(d)/'playlist.json').read_text())['tracks'][0]['title'],'=SUM(1,2)')
            with (Path(d)/'playlist.csv').open(encoding='utf-8-sig',newline='') as f:self.assertEqual(list(csv.reader(f))[1][1],"'=SUM(1,2)")
        p,r=fixture();r['title']='</script><script>alert(1)</script>'
        self.assertNotIn('</script><script>alert(1)</script>',render(p,r))
        with self.assertRaises(ValueError):render(p,r,{'6':'data:image/svg+xml;base64,AAAA'})
if __name__=='__main__':unittest.main()
