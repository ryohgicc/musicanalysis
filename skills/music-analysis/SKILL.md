---
name: music-analysis
description: 将 QQ 音乐分享链接或导出的歌单解析为完整曲库，分析有曲目证据的偏好与风格变化，推荐未收藏作品，生成可离线打开的交互网页报告。用于从歌单到分析网页的完整流程，也支持本地 JSON/CSV；不用于下载音频或控制播放器。
---

# Music Analysis · 歌单到音乐地图

产出完整的结构化歌单、统计、可追溯的分析 JSON 和单文件交互网页。脚本处理数据与渲染，模型负责有证据的解释与推荐，不把自动统计冒充音频分析。

以下 `<skill-dir>` 指本 `SKILL.md` 所在目录；脚本仅需 Python 3.10+ 标准库。

## 获取歌单

优先使用用户给出的链接或文件。没有“复制链接”时，说明这条手动路线：

**QQ 音乐歌单 → 分享到微信或 QQ → 打开分享卡片 → 菜单中用浏览器打开 → 复制浏览器最终地址。** 界面因版本不同可能有差异；也可在桌面端打开卡片复制链接。让用户提供链接，不替用户向联系人发送消息。

支持 `y.qq.com/n/ryqq/playlist/<ID>`、分享页 `?id=<ID>` / `disstid=` / `tid=` 和纯数字 ID。没有 ID 的短链，先在浏览器展开；只读公开曲目元数据，不需要密码、Cookie 或会员凭证。

```bash
python3 <skill-dir>/scripts/workflow.py fetch '<歌单链接或ID>' --out work/snapshot
```

默认直接请求 QQ 公开歌单接口。接口是非官方稳定性契约，可能变化。可选 `--provider playlistout` 会把规范化后的公开歌单链接发送给 Playlist Out 服务；仅在适合使用第三方公开解析服务时选择。默认不会自动把失败请求转发第三方。

本地导入与导出：

```bash
python3 <skill-dir>/scripts/workflow.py normalize '<歌单.json或.csv>' --out work/snapshot
```

支持 QQ 原始 JSON、Playlist Out canonical JSON、规范化 JSON、曲目数组和常见 CSV。导出 JSON / CSV / TXT，保留原顺序与艺人数组。平台总数与实际条目不一致时停止：不要把分享页预览当全量，不用假数据补齐。用户知道总数时加 `--expect-count N`。链接/API 失败后改用 [获取与解析说明](references/acquisition.md) 中的本地导出路线，避免重复重试。

## 统计、解释与推荐

```bash
python3 <skill-dir>/scripts/workflow.py stats work/snapshot/playlist.json --output work/stats.json
python3 <skill-dir>/scripts/workflow.py init-analysis work/snapshot/playlist.json --output work/analysis.json
```

先读 [分析规范与 JSON 契约](references/analysis.md)，然后编辑 `analysis.json`。生成前必须做这些判断：

- **顺序**：未知时问清第 1 首和最后一首哪个更早；继续不依赖此答案的静态统计。未确认前用 `order: unknown`、`stages: []`。确认后才按相邻条目解释阶段，不使用发行日期代替收藏时间。不固定九阶段。
- **事实与假设**：艺人计数含合作，不能相加当风格比例；检查疑似同曲版本、整专加入、别名与翻唱。收藏不是播放次数。每个关键偏好给 2–3 首证据与解释，不做品味高低、人格或心理判断，不编 BPM / 调性 / 匹配分数。
- **听感**：元数据能支持收藏结构，听感联系来自对具体作品的知识或可信来源；不熟悉的作品先查证或省略，不能声称已试听。
- **推荐**：默认 8–12 首，混合大概率合口味、相邻风格和探索。给收藏锚点、相似点与可能不合口味的差异。核实曲名、艺人及官方/可信来源；手工复核译名、别名、合作表记，避免用另一版本冒充新推荐。未收藏不等于未听过，不保证 QQ 当前可播放。

排重工具也可单独使用：

```bash
python3 <skill-dir>/scripts/analyze_playlist.py work/snapshot/playlist.json --candidates work/candidates.json --output work/checked.json
```

`init-analysis` 绑定有序歌单哈希。用户改动歌单、倒序或增减条目后重新分析，不把旧编号绑定到新快照。仅在内容和来源核实后设置 `status: ready`。

## 生成网页与验证

```bash
python3 <skill-dir>/scripts/workflow.py validate work/snapshot/playlist.json work/analysis.json
python3 <skill-dir>/scripts/workflow.py render work/snapshot/playlist.json work/analysis.json --output outputs/music-report.html
```

渲染会校验快照、阶段无遗漏与无重叠、证据编号范围、推荐排重与来源 URL。默认输出自包含 HTML：全屏滚动章节（有确认顺序时）、随滚动同步的固定目录、偏好详解、两种口径的歌手图表、推荐分组与本地反馈导出、完整曲库搜索排序分页。所有数量由输入决定，模板不包含任何用户的歌单或结论。

默认命令自动下载、缓存并内嵌首页、阶段代表与证据卡使用的 QQ 封面（最多 96 个条目），缺少封面 URL 时按歌曲 MID 补查专辑。生成时联网，生成后页面与封面离线可读。终端会输出内嵌数量与失败条目；失败显示原创几何占位，不虚构专辑封面。可选 `--covers covers.json` 接收 `{ "曲目编号": "data:image/jpeg;base64,..." }`；`--offline` 只用已有缓存或提供的图片，`--cover-cache <目录>` 指定缓存位置，默认在输出文件旁。

使用随 skill 发布的 `assets/report.html` 完整模板，保留封面拼贴首页、唱片式阶段和证据缩略图；不要另写简化文本页代替。保留用户指定视觉风格；默认样式参考 Astryx，代码与图形为原创。检查默认命令的封面数量与实际页面，不能将全占位页面宣称为带图报告。需要验证首页/阶段代表封面齐全时加 `--require-covers`，失败后检查元数据、网络或提供图片；若仍不可用，在交付时说明缺失。外部曲目链接仍需联网。

用浏览器打开 `file://` 输出，检查电脑与手机无横向溢出、时间方向、滚动目录、推荐筛选、反馈保存与 JSON 导出、搜索排序分页和控制台错误。验证脚本与用例见仓库 `tests/`；没有浏览器工具时说明未做视觉验证，不声称已通过。

交付网页与必要的数据文件，说明数据时间、顺序和解释边界。新用户的原始数据与报告保持本地；发布到 GitHub 或部署网站按用户给出的范围执行，不能因用户要求生成报告就默认公开其歌单。项目来源与借鉴范围见 [引用说明](references/sources.md)。
