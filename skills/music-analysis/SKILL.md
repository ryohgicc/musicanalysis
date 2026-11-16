---
name: music-analysis
description: 将 QQ、网易云、酷狗（含概念版）、酷我、汽水、咪咕的歌单链接或本地 JSON/CSV 解析为完整曲库，分析有曲目证据的偏好与风格变化，推荐未收藏作品，生成可离线打开的交互网页报告。不用于下载音频或控制播放器。
---

# Music Analysis · 歌单到音乐地图

产出完整的结构化歌单、统计、可追溯的分析 JSON 和单文件交互网页。脚本处理数据与渲染，模型负责有证据的解释与推荐，不把自动统计冒充音频分析。

以下 `<skill-dir>` 指本 `SKILL.md` 所在目录；脚本仅需 Python 3.10+ 标准库。

## 固定页面，只替换内容

以随 skill 发布的「声迹」页面为唯一正式模板，固定页面风格、主板块顺序、版式和交互：封面拼贴首页 → 收藏变化总览与全屏阶段 → 偏好总览、统计解读与详细证据 → 分组推荐与试听反馈 → 完整曲库 → 页脚。新用户提交歌单时，只生成或编辑 `playlist.json`、`analysis.json`，并运行既有 `render` 命令。

不要为每份歌单重新设计网页、改变配色/字体/间距/圆角/断点、重排或删除板块、改成简化报告，也不要修改 skill 的 HTML、脚本或模板校验文件。曲目、封面、标题、分析、统计、推荐与有证据的阶段条目数量属于可替换内容。完整交付还必须满足 [完整内容契约](references/report-contract.md)：9 个全屏章节、6 条完整偏好、12 首推荐及短首页文案；模板相同不能替代这项检查。确实缺少证据时只生成标注预览，不编造内容。

正式模板从 v0.6.0 起默认采用全屏滚动叙事：全部主板块逐屏展示，阶段故事与证据直接展开，桌面两列撑满可用高度，无底部导航。滚动从第一段位移就同步推动画面；内容超出一屏时先实时滚完正文，再切换下一屏。保留阅读模式、系统减少动态效果与键盘跳转。不要为实现这些效果临时生成第二套页面或依赖工作目录中的原型脚本。

`assets/report-template.json` 固定模板版本与 SHA-256，渲染器会检查完整模板。校验失败时恢复该版本的文件，不通过重写校验值绕过。只有用户明确要求改版时，才在一次单独的模板更新中修改设计、更新版本与校验值并运行验证。

## 获取歌单

请用户同时提供 **歌单链接 / ID 或导出文件**，以及 **最新收藏的歌曲在歌单中的序号**。仅提供 ID 时还需明确音乐平台。建议一次问清：“请提供歌单链接或导出文件，并告诉我哪个序号是最新收藏的，例如‘第 1 首最新’或‘最后一首最新’；如果只提供 ID，请注明平台。”会话中已经明确的信息直接沿用，不重复询问。

序号以本次解析快照的原始顺序为准；若用户看到的排序与解析结果可能不同，用首尾曲名核对。确认歌单按收藏时间排列后：第 1 首最新 → `order: last-oldest`；最后一首最新 → `order: first-oldest`。最新曲目在中间、歌单经过手动 / 其他排序或用户不确定时，仅凭一个序号不能推导完整时间线，需进一步确认排序；确认前保持 `order: unknown`，可以先解析和做静态统计。

优先使用用户给出的链接或文件。没有“复制链接”时，说明这条手动路线：

**QQ 音乐歌单 → 分享到微信或 QQ → 打开分享卡片 → 菜单中用浏览器打开 → 复制浏览器最终地址。** 界面因版本不同可能有差异；也可在桌面端打开卡片复制链接。让用户提供链接，不替用户向联系人发送消息。

支持 QQ、网易云、酷狗普通版 / 概念版、酷我、汽水和咪咕的公开歌单链接、分享短链或含链接的分享文案。QQ 无法复制链接时用上面的路线；其他平台也可先分享再用浏览器打开。仅有 ID 时用 `--platform` 指定 `qqmusic / netease / kugou / kuwo / qishui / migu`；脚本为兼容旧命令仍将无平台的纯数字 ID 解释为 QQ，agent 不应据此猜用户的平台。Spotify / Apple Music 链接尚未接入。

```bash
python3 <skill-dir>/scripts/workflow.py fetch '<歌单链接或ID>' --out work/snapshot
# 仅提供网易云歌单 ID 时：
python3 <skill-dir>/scripts/workflow.py fetch '<歌单ID>' --platform netease --out work/snapshot
```

默认 `--provider auto`：能提取 ID 的 QQ 链接直接请求 QQ 公开接口；其他平台与 QQ 短链调用 Playlist Out 的统一解析 API。调用时第三方收到歌单链接或 ID、平台标识，不发送周边分享文案；可识别的长链接去掉追踪参数，短链保留解析所需参数。可用 `--provider qq` 限定 QQ 直连，或 `--provider playlistout` 显式使用第三方。直连失败不会自动转发或重复重试。接口可用性受平台变化影响。

酷狗普通版免登录可能只返回前 10 首；发现 `retrieval.mode: preview`、`isPartial` 或数量不符时停止，不生成完整收藏分析。让用户在 Playlist Out 网页 / CLI 本地登录并导出完整 JSON，再导入；不要索要密码、Cookie 或 Token。酷狗概念版集合链接走同一 `kugou` 平台。详见 [平台支持与解析边界](references/acquisition.md)。

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

先读 [分析规范与 JSON 契约](references/analysis.md) 和 [完整内容契约](references/report-contract.md)，然后编辑 `analysis.json`。生成前必须做这些判断：

- **顺序**：按上面的最新收藏序号与排序确认结果设置方向；缺少信息时补问，继续不依赖此答案的静态统计。未确认时保持 `order: unknown`，不能默认第 1 首较早或较新。可用 `chapterMode: source-order` 按歌单原序做九个相邻内容分段，明确“不代表收藏时间”；无法有依据地分段时仅做预览。确认后用 chronological 模式解释变化，不使用发行日期代替收藏时间。
- **事实与假设**：艺人计数含合作，不能相加当风格比例；检查疑似同曲版本、整专加入、别名与翻唱。收藏不是播放次数。完整报告写六条不同偏好，每条填写总览、具体解释、下一步试听方向、试听问题与关联推荐，并给 3 首不同证据与逐曲解释，不做品味高低、人格或心理判断，不编 BPM / 调性 / 匹配分数。
- **听感**：元数据能支持收藏结构，听感联系来自对具体作品的知识或可信来源；不熟悉的作品先查证或省略，不能声称已试听。
- **推荐**：完整报告固定 12 首（大概率合口味 6、相邻风格 4、探索 2），混合大概率合口味、相邻风格和探索。给收藏锚点、相似点与可能不合口味的差异。核实曲名、艺人及官方/可信来源；手工复核译名、别名、合作表记，避免用另一版本冒充新推荐。同时核对每首对应发行的封面，填写 `artwork`（图片 URL、发行来源与版本标签），不要用收藏锚点的图片代替推荐封面。未收藏不等于未听过，不保证用户所在平台当前可播放。

排重工具也可单独使用：

```bash
python3 <skill-dir>/scripts/analyze_playlist.py work/snapshot/playlist.json --candidates work/candidates.json --output work/checked.json
```

`init-analysis` 绑定有序歌单哈希。用户改动歌单、倒序或增减条目后重新分析，不把旧编号绑定到新快照。仅在内容和来源核实后设置 `status: ready`。

## 生成网页与验证

```bash
python3 <skill-dir>/scripts/workflow.py validate work/snapshot/playlist.json work/analysis.json
python3 <skill-dir>/scripts/workflow.py render work/snapshot/playlist.json work/analysis.json --output outputs/music-report.html --require-covers
```

渲染会校验快照、阶段无遗漏与无重叠、证据编号范围、推荐排重与来源 URL。默认输出自包含 HTML：固定变化板块与全屏滚动章节（时间演变或明确标注的原序内容分段）、随滚动同步的顶部导航与手机目录、偏好详解、两种口径的歌手图表、推荐分组场景与本地反馈导出、完整曲库搜索排序分页。正式版按定稿的九章节、六偏好与十二推荐填充，具体曲目、范围和结论由输入支持。`render` 默认拒绝缺项；仅预览可加 `--preview`，首页会明确标注未完成，不能冒充完整交付。模板不包含个人数据。

默认命令下载、缓存并内嵌首页、阶段代表、每首阶段证据、偏好证据的封面（最多 96 个收藏条目），以及 `recommendations[].artwork` 指定的推荐封面；这些图片直接显示在页面。只访问已支持的平台图片域名与 Apple 目录的 `mzstatic.com` CDN，不自动猜推荐对应发行。QQ 缺少封面 URL 时可按歌曲 MID 补查专辑，其他平台不把曲目 ID 当 QQ MID，不跨平台借图。原条目没有专辑封面时可人工核实同一艺人的图片，在 `trackArtwork` 中标记 `kind: artist`、标签和来源；页面显示“艺人图 · 原条目无专辑封面”。字段示例见 [分析契约](references/analysis.md)。

生成时联网，生成后页面与图片离线可读。终端分别报告收藏与推荐图片数量及失败项。图片缺失时明确显示占位或“封面暂缺”，不虚构封面。`--require-covers` 检查所有选定收藏图片和每首推荐图片，任一缺失就停止，不写出新报告。可选 `--covers covers.json` 接收 `{ "曲目编号": "data:image/jpeg;base64,..." }`；若是艺人图也必须提供相应 `trackArtwork` 标签。`--offline` 只用已有缓存或提供的图片，`--cover-cache <目录>` 指定缓存位置，默认在输出文件旁。

页面固定使用 `assets/report.html`，视觉沿用已定稿「声迹」页面，最初灵感来自 Astryx，代码与图形为原创。检查默认命令的封面数量与实际页面，不能将全占位页面宣称为带图报告。正式模式默认要求首页/阶段代表封面齐全；预览需要同样检查时加 `--require-covers`。失败后检查元数据、网络或提供图片，无法解决时只交付明确说明缺失的预览。外部曲目链接仍需联网。

按完整内容契约检查实际新歌单生成的文件：九章节、六偏好、十二推荐与短首页文案都必须出现。逐页检查 27 首阶段线索、18 条偏好证据和 12 首推荐图片实际解码、直接显示，核对现场/翻唱/不同发行版本；艺人图有显式标注。用浏览器打开 `file://` 输出，检查电脑与手机图片不遮挡文字、无横向溢出、时间方向、滚动目录、推荐筛选、反馈保存与 JSON 导出、搜索排序分页和控制台错误。验证脚本与用例见仓库 `tests/`；没有浏览器工具时说明未做视觉验证，不声称已通过。

交付网页与必要的数据文件，说明数据时间、顺序和解释边界。新用户的原始数据与报告保持本地；发布到 GitHub 或部署网站按用户给出的范围执行，不能因用户要求生成报告就默认公开其歌单。项目来源与借鉴范围见 [引用说明](references/sources.md)。
