import copy
from pathlib import Path
from test_workflow import fixture
from workflow import render, snapshot_hash
root=Path(__file__).resolve().parents[1]/'.test-output';root.mkdir(exist_ok=True)
p,r=fixture()
for index in range(7,19):
    p['tracks'].append(dict(index=index,title=f'Synthetic {index}',artists=['Synthetic artist'],artist='Synthetic artist',album='Demo',durationSeconds=0,songId='',songMid=f'fake{index}',sourceUrl='',coverUrl=''))
p['trackCount']=18;r['playlistHash']=snapshot_hash(p)
r['stages']=[dict(range=[13,18],title='Early',tag='早期',body='Synthetic example.',insight='Evidence only.',anchorIds=[18,13]),dict(range=[7,12],title='Middle',tag='中期',body='Synthetic example.',insight='Evidence only.',anchorIds=[12,7]),dict(range=[1,6],title='Latest',tag='近期',body='Synthetic example.',insight='Evidence only.',anchorIds=[6,1])]
r['recommendations']=[dict(title='Test Recommendation',artist='Synthetic candidate',tier='探索',anchorIds=[6,1],reason='For browser testing only.',difference='Synthetic fixture.',source='https://example.org/fixture')]
(root/'report.html').write_text(render(p,r),encoding='utf-8')
unknown=copy.deepcopy(r);unknown['order']='unknown';unknown['stages']=[]
(root/'unknown.html').write_text(render(p,unknown),encoding='utf-8')
first=copy.deepcopy(r);first['order']='first-oldest';first['stages'].reverse()
(root/'first.html').write_text(render(p,first),encoding='utf-8')
hostile=copy.deepcopy(p);hostile['tracks'][0]['title']='</script><img src=x onerror="window.pwned=1">';hostile['tracks'][0]['sourceUrl']='javascript:window.pwned=1';bad=copy.deepcopy(r);bad['title']='<img src=x onerror="window.pwned=1">';bad['playlistHash']=snapshot_hash(hostile)
(root/'hostile.html').write_text(render(hostile,bad),encoding='utf-8')
