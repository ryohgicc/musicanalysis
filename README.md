# Music Analysis · 声迹

把你的歌单变成一份音乐品味报告：看懂自己喜欢什么、收藏风格如何变化，以及下一首可以听什么。

**[在线体验原版 Demo →](https://ryohgicc.github.io/musicanalysis/)** · **[体验全屏动效版 →](https://ryohgicc.github.io/musicanalysis/apple-motion-report/)**

**新报告默认使用全屏滚动版，支持高清长截图导出。** 首页、总览、九个阶段、偏好详解、分组推荐与曲库逐屏展示；滚动立即带动画面，长内容先读完再切换下一屏。支持阅读模式、系统减少动态效果与键盘跳转。新歌单只替换内容，直接显示证据和推荐封面。上面的两个在线入口保留同一份已授权报告的历史展示，原版 Demo 不随模板升级覆盖。

## 有哪些功能

- **偏好总结**：分析收藏艺人、作品版本与收藏特征，用具体歌曲解释偏好。
- **风格变化**：确认收藏顺序后，按阶段讲述变化；每个阶段全屏展示，标题、故事、封面与证据铺开；长内容随滚动完整展开。
- **歌曲推荐**：提供 12 首未在歌单中检出的作品，分为“大概率合口味、相邻风格、探索”，附推荐理由与差异。
- **交互网页**：专辑封面、曲目证据、完整曲库搜索、推荐分组跳转、试听反馈保存与导出。
- **长截图导出**：点击顶部“导出长截图”→“生成长截图”，默认 2 倍高清（2160 px），可选 3 倍超清（3240 px）；超长时按完整章节分段下载，全部章节和封面按顺序展开，曲库保留当前筛选与分页。
- **离线阅读**：生成单个 HTML 文件，图片和页面资源内嵌，双击即可打开；跳转外部歌曲链接需要联网。

支持 **QQ 音乐、网易云音乐、酷狗音乐（含概念版）、酷我音乐、汽水音乐、咪咕音乐**，也可导入 JSON / CSV 歌单。

所有歌单使用同一套「声迹」页面设计与板块，只替换曲目、图片和分析内容。在线 Demo 是作者授权公开的原始报告，包含 799 首收藏、9 个阶段、6 条偏好与 12 首推荐。克隆仓库后也可打开 `docs/index.html`；开发用的 [虚构示例](examples/report.html) 只有 6 首歌曲，是内容预览。

## 怎么使用

### 1. 安装 Skill

以 Codex 为例，先安装 Python 3.10+，再将 skill 复制到技能目录：

```bash
git clone https://github.com/ryohgicc/musicanalysis.git
mkdir -p ~/.codex/skills
cp -R musicanalysis/skills/music-analysis ~/.codex/skills/
```

已有同名 skill 时，先备份自己的修改。复制完成后，重新加载技能或开启新会话。

更新时，先在仓库运行 `git pull`，再复制新版 skill 并重新加载；只更新仓库不会更新之前安装的 skill。

### 2. 把歌单交给 Agent

复制下面这段话，填入自己的信息：

```text
用 $music-analysis 分析我的歌单，生成偏好总结、风格变化、歌曲推荐和网页报告。

歌单链接：粘贴你的链接
音乐平台：例如网易云音乐
收藏顺序：按收藏时间排列，第 1 首最新 / 最后一首最新
```

如果不确定收藏顺序，直接写“不确定”。Agent 可以先分析静态偏好，确认顺序后再解释变化。

### 3. 打开报告

Agent 会解析完整歌单、核对数据、撰写分析并生成 HTML 报告。打开交付的 `.html` 文件即可阅读，无需启动网站服务。需要分享图片时，点击顶部“导出长截图”，生成后下载 PNG；手机可打开图片后长按保存。导出默认 2 倍高清，可选 3 倍超清；超长时按章节分段保存，不缩小文字。需要一张整图可选择“整张长图 · 自动适配”。详情弹窗内容不包含在截图中。

**这是供 Agent 使用的 skill。** 脚本负责解析、统计和生成页面，音乐解释与推荐由运行 skill 的模型完成；只运行脚本不会自动产生完整分析。本项目不内置模型账号或密钥。

## 需要提供什么信息

| 信息 | 怎么填写 | 用途 |
| --- | --- | --- |
| **歌单链接或导出文件** | 分享链接、含链接的分享文案，或完整 JSON / CSV | 获取曲目、艺人、封面与原始顺序 |
| **哪个序号是最新收藏的** | “第 1 首最新”“最后一首最新”，或明确的序号 | 确认风格变化的分析方向 |
| **音乐平台** | QQ、网易云等；只提供歌单 ID 时必须注明 | 避免不同平台的 ID 混淆 |
| 歌单总数（可选） | 例如“共 800 首” | 帮助核对是否解析完整 |

序号以本次获取的歌单顺序为准。若 App 和解析结果排序不同，Agent 会用首尾曲名核对。最新歌曲在中间，或歌单经过手动、歌名等排序时，需要进一步确认，不能只凭一个序号推导时间线。

## 如何获得这些信息

### 获取歌单链接

在音乐 App 中打开歌单，进入“分享”，复制链接或整段分享文案即可，无需自己提取歌单 ID、删除参数。

**如果分享菜单没有“复制链接”：**

1. 手动把歌单分享到微信或 QQ。
2. 打开分享卡片，在菜单中选择“在浏览器打开”或类似入口。
3. 复制浏览器地址栏中的链接，发给 Agent。

也可以在电脑端打开分享卡片后复制地址。不同系统与 App 版本的入口可能不同；短链也可以直接提供，解析失败时再用浏览器展开。

例如 QQ 的 `y.qq.com/n/ryqq/playlist/…`、网易云的 `music.163.com/#/playlist?id=…`，以及酷狗、汽水、咪咕等平台的歌单分享短链。

### 确认哪首是最新收藏

查看歌单的排序设置，并对照最近加入的一首歌，说明它位于第几首。例如：“按添加时间排序，第 1 首是我最近收藏的。”

如果不确定，不必猜。歌单顺序只能在确认后用于解释收藏变化，歌曲发行日期不能代替收藏时间。

### 链接解析失败时，导出文件

打开 [Playlist Out 网页](https://playlistout.lengxiqwq.com/)，粘贴歌单链接，导出 **完整 JSON** 后交给 Agent，也支持 CSV。优先 JSON，它能保留更多平台、封面和曲目信息。

酷狗普通版免登录可能只返回前 10 首。遇到这种情况，请在 Playlist Out 网页或 CLI 中自行登录并导出完整歌单。本 skill 会拒绝部分歌单，不把预览当成完整收藏分析；无需向 Agent 提供密码、Cookie 或 Token。

## 参考了哪些项目

| 项目 | 在这里的用途 |
| --- | --- |
| [Playlist Out](https://github.com/LengxiQwQ/playlistout) | 多平台歌单解析与 JSON / CSV 导入；实际调用其统一公开 API，未打包其源码 |
| [QQMusicApi](https://github.com/jsososo/QQMusicApi) | QQ 接口生态的可选参考；本项目未依赖或复制其实现 |
| [Astryx](https://astryx.atmeta.com/) | 页面视觉参考；「声迹」模板由本项目编写，未复制其代码或素材 |
| [Playwright](https://github.com/microsoft/playwright) | 开发时验证页面布局、交互和离线阅读 |

具体借鉴范围与许可见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。自有代码采用 [MIT](LICENSE)，第三方音乐、封面、商标与服务不包含在该授权内。

## 支持范围与数据说明

QQ 长链接 / ID 默认直连 QQ；其他平台与 QQ 短链调用 Playlist Out，第三方会收到歌单链接或 ID 与平台标识，不发送周边分享文案。可识别的长链接会去掉追踪参数，短链保留解析所需参数。接口失败不会反复重试，也不会将 QQ 直连失败的请求自动转发第三方。

Spotify、Apple Music 链接与用户主页批量解析尚未接入。上游接口可能变化：v0.4.0 联网验证过网易云 613 首、汽水 630 首的完整解析与代表封面，以及酷狗预览拦截；其余平台通过接口契约回归，仍需按实际链接核对。

歌单反映收藏，不能自动得知播放次数、首次听歌时间或实际年份。分析会引用具体曲目，不根据歌名猜人格、BPM 或精确匹配率；推荐未在歌单中检出，也不代表你从未听过。

数据与报告默认保存在本地的 `work/`、`outputs/`，这些目录不会提交到 Git。生成网页不等于公开发布；`docs/index.html` 和 `docs/apple-motion-report/index.html` 是作者明确授权公开的同一份真实报告的两个版本，其余开发示例使用虚构曲目与原创几何图片。Demo 的试听反馈只保存在访问者自己的浏览器中。本项目不提供音频或歌词下载。

## 开发与命令行

<details>
<summary>展开：手动工作流、参数与验证命令</summary>

以下命令从仓库根目录运行。解析与生成脚本只需 Python 3.10+ 标准库，Node / Playwright 仅用于开发验证。

### 解析与分析

```bash
python3 skills/music-analysis/scripts/workflow.py fetch '<歌单链接>' --out work/snapshot
python3 skills/music-analysis/scripts/workflow.py stats work/snapshot/playlist.json --output work/stats.json
python3 skills/music-analysis/scripts/workflow.py init-analysis work/snapshot/playlist.json --output work/analysis.json
```

由 Agent 或人工依据具体作品填写 `analysis.json`，完成后将 `status` 从 `draft` 改为 `ready`，再校验与生成：

```bash
python3 skills/music-analysis/scripts/workflow.py validate work/snapshot/playlist.json work/analysis.json
python3 skills/music-analysis/scripts/workflow.py render work/snapshot/playlist.json work/analysis.json --output outputs/report.html --require-covers
```

正式报告要求九个全屏章节、六条偏好、十二首推荐（6 / 4 / 2），每个章节与偏好均有三首不同曲目证据，首页标题最多 18 字符、摘要最多 60 字符。数据不足时使用明确标记的 `--preview`，不强凑内容；该参数不放宽曲库完整性要求。顺序未知时可用 `chapterMode: source-order, order: unknown` 按原序分段，不能声称时间演变。

### 导入与常用参数

```bash
# 本地 JSON / CSV 替代在线解析
python3 skills/music-analysis/scripts/workflow.py normalize '<导出文件.json或.csv>' --out work/snapshot

# 仅提供 ID 时指定平台
python3 skills/music-analysis/scripts/workflow.py fetch '<歌单ID>' --platform netease --out work/snapshot
```

| 参数 | 说明 |
| --- | --- |
| `fetch --platform` | `qqmusic / netease / kugou / kuwo / qishui / migu`；酷狗概念版也用 `kugou`。无平台的纯数字 ID 为兼容旧命令仍按 QQ 处理 |
| `fetch --provider` | 默认 `auto`；`qq` 限定 QQ 直连，`playlistout` 强制使用第三方 |
| `fetch / normalize --expect-count N` | 核对实际条目与预期总数 |
| `render --offline` | 只用已缓存或显式提供的图片 |
| `render --cover-cache <目录>` | 指定封面缓存；默认在输出旁的 `.music-analysis-covers/` |
| `render --covers covers.json` | 显式提供图片，格式为 `{ "曲目编号": "data:image/jpeg;base64,..." }` |
| `render --require-covers` | 所有选定收藏图与推荐图缺失时停止；不加此参数时，正式报告仍要求首页与阶段代表封面齐全 |

渲染默认从各平台元数据获取最多 96 个代表与证据封面，缓存后内嵌；阶段歌曲、偏好证据与推荐卡片直接显示图片。仅 QQ 支持按歌曲 MID 补查专辑。推荐图片需由 Agent 核对具体发行后填写 `recommendations[].artwork`（`kind: album`、`label`、`source`、`imageUrl`），脚本下载并缓存，支持六平台 CDN 与 Apple 目录的图片 CDN。不会自动把收藏图片当成推荐图片，也没有接入 Apple Music 歌单解析。

原条目没有专辑封面时，可在 `trackArtwork` 按曲目编号填写已核实的同一艺人图片，使用 `kind: artist`，页面会标注“艺人图 · 原条目无专辑封面”及来源。数据示例见 [图片与发行版本](skills/music-analysis/references/analysis.md#图片与发行版本)。旧分析未填写推荐图片时，普通 `render` 会报告缺项，卡片显示“封面暂缺”；标准 skill 使用 `--require-covers`，补齐后才交付带图报告。

本地 CSV 支持 Playlist Out 的 `url` / `duration` 字段，本项目导出另保留 `songId` / `coverUrl`。JSON 更适合保留完整艺人数组和歌单信息。

### 验证与示例

```bash
npm install
npx playwright install chromium
npm test                 # 数据、顺序、排重、解析、封面与导出
npm run check            # Python 编译检查
npm run build            # 重建虚构示例
npm run test:browser     # 桌面 / 手机布局、交互、同模板与离线检查
npm run test:demo        # 原版公开 Demo 的图片、阶段链接、手机布局与交互
npm run test:export      # 长截图 PNG、下载、离线与手机导出
npm run test:motion      # 全屏动效 Demo 的封面、滚动、内容与手机布局
```

查看自带示例可直接打开 `examples/report.html`；手动验证和生成预览：

```bash
python3 skills/music-analysis/scripts/workflow.py validate examples/playlist.json examples/analysis.json --preview
python3 skills/music-analysis/scripts/workflow.py render examples/playlist.json examples/analysis.json --output work/demo.html --preview
```

上述手动示例没有真实封面 URL，会显示占位；仓库自带的 HTML 由 `npm run build` 生成，包含原创几何示意图。测试产物位于 `.test-output/`，不发布。

### Demo 托管

在线 Demo 使用 GitHub Pages，发布源为 `main` 分支的 `/docs` 目录。`docs/index.html` 保留用户指定报告的原文件，封面与资源已内嵌；不重新渲染、不随开发示例构建覆盖。推送该目录的更新后，由 GitHub Pages 自动发布。普通歌单报告仍只保存在本地。

Fork 仓库后如需发布自己的 Demo，在 **Settings → Pages → Deploy from a branch** 中选择 `main` 与 `/docs`，并将本 README 的预览链接改为自己的地址。替换报告前确认其中的数据可以公开。

### 进一步阅读

- [Skill 入口](skills/music-analysis/SKILL.md)
- [平台支持与解析说明](skills/music-analysis/references/acquisition.md)
- [分析方法与 JSON 字段](skills/music-analysis/references/analysis.md)
- [完整报告内容契约](skills/music-analysis/references/report-contract.md)
- [开发约定](AGENTS.md) · [更新记录](CHANGELOG.md)

代码位于 `skills/music-analysis/scripts/`，固定网页模板位于 `skills/music-analysis/assets/`，方法与来源位于 `references/`，验证用例位于 `tests/`。新歌单只替换内容，不修改模板和校验文件。

</details>
