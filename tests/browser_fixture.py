import copy
import contextlib
import io
import json
from unittest.mock import patch
from pathlib import Path
from test_workflow import fixture, complete_fixture
from workflow import render, snapshot_hash, main, save_json
from artwork import synthetic_png
from covers import data_url
root=Path(__file__).resolve().parents[1]/'.test-output';root.mkdir(exist_ok=True)
p,r=fixture()
r['insights'][0]['recommendationIds']=[0]
r['insights'][0]['kicker']='MELODY'
r['insights'][0]['direction']='Compare melody, voice and arrangement on the next listen.'
for index in range(7,19):
    p['tracks'].append(dict(index=index,title=f'Synthetic {index}',artists=['Synthetic artist'],artist='Synthetic artist',album='Demo',durationSeconds=0,songId='',songMid=f'fake{index}',sourceUrl='',coverUrl=''))
p['trackCount']=18;r['playlistHash']=snapshot_hash(p)
r['stages']=[dict(range=[13,18],title='Early',tag='早期',body='Synthetic example.',insight='Evidence only.',anchorIds=[18,13]),dict(range=[7,12],title='Middle',tag='中期',body='Synthetic example.',insight='Evidence only.',anchorIds=[12,7]),dict(range=[1,6],title='Latest',tag='近期',body='Synthetic example.',insight='Evidence only.',anchorIds=[6,1])]
r['recommendations']=[dict(title='Test Recommendation',artist='Synthetic candidate',tier='探索',anchorIds=[4,7],reason='For browser testing only.',difference='Synthetic fixture.',source='https://example.org/fixture')]
for t in p['tracks']:t['coverUrl']=f'https://y.gtimg.cn/music/photo_new/synthetic-{t["index"]}.png'
save_json(root/'playlist.json',p);save_json(root/'analysis.json',r)
# The public CLI itself must fetch and embed available artwork, with no --covers argument.
with patch('sys.argv',['workflow.py','render',str(root/'playlist.json'),str(root/'analysis.json'),'--output',str(root/'report.html'),'--preview']),patch('urllib.request.urlopen',side_effect=lambda *a,**k:io.BytesIO(synthetic_png(1))),contextlib.redirect_stdout(io.StringIO()):
    main()
payload=(root/'report.html').read_text().split('<script type="application/json" id="report-data">')[1].split('</script>')[0]
covers=json.loads(payload)['covers']
unknown=copy.deepcopy(r);unknown['order']='unknown';unknown['stages']=[]
(root/'unknown.html').write_text(render(p,unknown,covers,preview=True),encoding='utf-8')
first=copy.deepcopy(r);first['order']='first-oldest';first['stages'].reverse()
(root/'first.html').write_text(render(p,first,covers,preview=True),encoding='utf-8')
hostile=copy.deepcopy(p);hostile['tracks'][0]['title']='</script><img src=x onerror="window.pwned=1">';hostile['tracks'][0]['sourceUrl']='javascript:window.pwned=1';bad=copy.deepcopy(r);bad['title']='<img src=x onerror="window.pwned=1">';bad['playlistHash']=snapshot_hash(hostile)
(root/'hostile.html').write_text(render(hostile,bad,covers,preview=True),encoding='utf-8')
# A different playlist changes data and repeated item counts, never the design.
other,other_report=fixture()
other['name']='另一份虚构歌单'
for track in other['tracks']:
    track['title']=f"另一首作品 {track['index']}"
    track['artists']=['Different artist'];track['artist']='Different artist'
    track['album']='Different album'
other_report['playlistHash']=snapshot_hash(other)
other_report['title']='另一份歌单的听歌地图'
other_report['insights'][0]['body']='不同曲目与分析内容仍然使用同一套版式。'
(root/'different.html').write_text(render(other,other_report,{str(t['index']):data_url(synthetic_png(t['index'])) for t in other['tracks']},preview=True),encoding='utf-8')

full,full_report=complete_fixture()
(root/'complete.html').write_text(render(full,full_report,{str(t['index']):data_url(synthetic_png(t['index'])) for t in full['tracks']}),encoding='utf-8')
