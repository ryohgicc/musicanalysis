"""Rebuild a fictional cover-free example, never a real user playlist."""
from pathlib import Path
from test_workflow import fixture
from workflow import save_json, render
root=Path(__file__).resolve().parents[1]
p,r=fixture();p['name']='虚构流程示例';p['id']='demo';p['exportedAt']='2026-01-01T00:00:00+00:00'
for t in p['tracks']:t['sourceUrl']=''
r['stages'][0]['body']='此处使用虚构歌名与艺人，只演示解析、统计与网页渲染。真实报告需要具体作品与可核实来源。'
r['stages'][1]['body']='阶段依次覆盖完整输入，滚动时目录自动更新。本示例为末首较早，不对应实际年份。'
r['insights'][0]['direction']='真实使用时补充可验证的听感解释与试听方向。'
save_json(root/'examples/playlist.json',p);save_json(root/'examples/analysis.json',r)
(root/'examples/report.html').write_text(render(p,r),encoding='utf-8');print('Generated fictional demo.')
