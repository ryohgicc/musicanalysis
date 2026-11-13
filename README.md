# Music Analysis · 声迹

把一份歌单变成可以阅读、探索与继续发现音乐的网页报告。

**获取分享链接 → 解析完整歌单 → 核对与统计 → 模型分析与推荐 → 交互网页**

**固定使用当前「声迹」页面。新歌单只替换内容，页面风格、板块顺序、布局与交互保持一致。** 模板带版本与完整性校验；不为每位用户重新设计页面。

支持 **QQ、网易云、酷狗（含概念版）、酷我、汽水、咪咕** 的公开歌单链接 / 分享短链 / ID，以及 Playlist Out / 规范化 JSON 与 CSV。只读曲目元数据，不下载音频，分析与网页留在本地。酷狗普通版完整导出可能需要用户在上游工具本地登录；本 skill 不接收账号凭证。

## 安装为 Skill

将仓库中的 `skills/music-analysis/` 文件夹复制到所用 agent 的技能目录。例如 Codex：

```bash
git clone https://github.com/ryohgicc/musicanalysis.git
mkdir -p ~/.codex/skills
cp -R musicanalysis/skills/music-analysis ~/.codex/skills/
```

已有同名 skill 时先比较或备份，避免直接覆盖已有定制。重新加载技能后，可说：

> 用 $music-analysis 分析这个歌单，解释偏好和收藏风格变化，推荐未收藏的歌，生成可离线打开的网页报告。歌单链接：……；按收藏时间排列，第 1 首是最新收藏的。

提供歌单时，请同时说明 **哪个序号是最新收藏的**，例如“第 1 首最新”或“最后一首最新”；仅提供 ID 时还要注明平台。skill 会据此确认分析方向；若歌单经过手动或其他排序，需要进一步确认，不能据此直接推断时间变化。序号以本次解析的原始顺序为准，必要时会用首尾曲名核对。

入口：[SKILL.md](skills/music-analysis/SKILL.md)。运行脚本只需 Python 3.10+ 标准库；音乐解释需要运行 skill 的模型或人工撰写，本仓库不内置模型账号、LLM API 或密钥。

## 没有“复制链接”怎么办

先把歌单**手动分享到微信或 QQ**，打开分享卡片，在菜单里选择**浏览器打开**，再复制地址栏最终链接。也可以在桌面端打开卡片。不同 App 版本界面可能不同；提供最终链接或歌单 ID 即可，不必自行删分享参数。skill 会指导用户操作，不会替用户向联系人发消息。

支持的例子：

- `https://y.qq.com/n/ryqq/playlist/<ID>`
- `https://i2.y.qq.com/.../index.html?id=<ID>`
- `https://music.163.com/#/playlist?id=<ID>` / `https://163cn.tv/<短链>`
- 酷狗 / 概念版集合、酷我、汽水 / 抖音、咪咕的歌单分享链接
- 含链接的分享文案，以及注明平台的歌单 ID

短链默认交给 Playlist Out 解析，失败时可先在浏览器展开。不要把分享页前几首预览当完整歌单。

## 平台与解析路线

| 平台 | `--platform` | 默认路线与限制 |
| --- | --- | --- |
| QQ 音乐 | `qqmusic` | 长链接 / ID 直连 QQ；短链交给 Playlist Out |
| 网易云音乐 | `netease` | Playlist Out |
| 酷狗音乐 | `kugou` | Playlist Out；普通版免登录可能只有 10 首预览，脚本会拒绝 |
| 酷狗概念版 | `kugou` | Playlist Out，支持集合分享链接 |
| 酷我音乐 | `kuwo` | Playlist Out |
| 汽水音乐 | `qishui` | Playlist Out，支持汽水 / 抖音分享链接 |
| 咪咕音乐 | `migu` | Playlist Out |

`--provider auto` 按链接选择上述路线。非 QQ 平台与 QQ 短链会把歌单链接或 ID 发给 Playlist Out，不发送周边分享文案；能规范化的长链接去掉追踪参数。`--provider qq` 限定 QQ 直连；`--provider playlistout` 强制使用第三方。直连失败不自动改走第三方，也不反复重试。

酷狗返回预览时，请在 Playlist Out 网页 / CLI 本地登录，导出完整 JSON 后导入，无需向 agent 提供密码、Cookie 或 Token。Spotify、Apple Music 链接与用户主页批量解析暂未接入。平台能力依赖上游接口，不能保证每条链接实时可用。

## 完整报告要求

固定模板还需要固定内容契约：九个全屏章节、六条完整偏好、十二首推荐（6 / 4 / 2），首页标题最多 18 字符、摘要最多 60 字符。每个章节与偏好均有三首不同曲目证据。`validate` 和 `render` 默认检查这些条件，缺项即停止。见 [完整内容契约](skills/music-analysis/references/report-contract.md)。

收藏方向未知时可以按原歌单顺序做内容分段，使用 `chapterMode: source-order, order: unknown`，明确不代表时间演变。不能为了生成章节假设收藏方向。证据不足的歌单使用 `--preview`，页面明确显示“预览 · 内容未完成”；短歌单不强凑分析。

## 命令行工作流

从仓库根目录运行：

```bash
python3 skills/music-analysis/scripts/workflow.py fetch '<支持平台的歌单链接>' --out work/snapshot
python3 skills/music-analysis/scripts/workflow.py stats work/snapshot/playlist.json --output work/stats.json
python3 skills/music-analysis/scripts/workflow.py init-analysis work/snapshot/playlist.json --output work/analysis.json
```

仅提供 ID 时指定平台，例如 `fetch '<网易云歌单ID>' --platform netease --out work/snapshot`。为兼容已有脚本，无平台的纯数字 ID 仍按 QQ 处理；skill 会先确认用户的平台。

然后由 agent 结合统计与具体作品，填写 `work/analysis.json` 的偏好证据、阶段和已核实推荐；[JSON 契约](skills/music-analysis/references/analysis.md) 提供字段解释。草稿默认 `status: draft`，完成分析后才设为 `ready`。没有确认收藏顺序时保留 `order: unknown`；需要先交付内容结构完整的页面时，按上述 source-order 模式做内容分段，不编造时间演变。

```bash
python3 skills/music-analysis/scripts/workflow.py validate work/snapshot/playlist.json work/analysis.json
python3 skills/music-analysis/scripts/workflow.py render work/snapshot/playlist.json work/analysis.json --output outputs/report.html --require-covers
```

双击 `outputs/report.html` 即可阅读。默认 `render` 会自动从各平台元数据提供的图片域名获取首页、阶段和证据卡用到的封面，缓存后内嵌到 HTML；仅 QQ 缺少封面 URL 时会通过歌曲 MID 查询专辑，其他平台的 ID 不会被当作 QQ MID。生成时需要联网，生成后的数据、封面、CSS 与 JS 均可离线阅读；外部作品链接需联网。

封面缓存默认位于输出文件旁的 `.music-analysis-covers/`，可用 `--cover-cache <目录>` 指定。`--offline` 只使用缓存或显式提供的 `--covers covers.json`；`--require-covers` 在首页或阶段代表封面缺失时终止生成，适合检查可复现效果。正式报告默认也要求首页和阶段代表封面齐全；缺失会停止。次要证据封面或预览中无法取得的图片会列出并显示几何占位，不会伪造专辑图片。默认最多获取 96 个代表与证据条目的封面，不下载全歌单图片。

更新仓库后，也要把新版 `skills/music-analysis/` 同步到实际使用的 skill 目录并重新加载；仅 `git pull` 不会更新之前复制安装的 skill。

本地导入：

```bash
python3 skills/music-analysis/scripts/workflow.py normalize '<已有导出.json或.csv>' --out work/snapshot
```

本地导入支持 Playlist Out canonical JSON 与 CSV 的 `url`、`duration` 字段；本项目 CSV 也保留曲目 ID 和封面 URL。JSON 会保留平台标识，非 QQ 曲目详情优先沿用原链接。无论在线还是本地，声明数量不符、`isPartial` 或上游预览标记都会停止；`render --preview` 仅放宽报告内容要求，不放宽曲库完整性。详见[解析说明](skills/music-analysis/references/acquisition.md)。

## 报告功能

- 封面拼贴首页、唱片式阶段配图、保留编号的偏好证据卡；使用随仓库发布的完整模板。
- 固定保留首页、变化、偏好、推荐、曲库和页脚；缺失信息在原板块显示待补充状态。
- 已确认顺序时：按歌单内容划分的全屏滚动章节、固定目录与当前阶段同步、曲目证据和阶段跳转；正式报告按定稿填九个有依据的相邻分段。
- 偏好：总览、详细解释、具体收藏锚点、下一步试听方向。
- 统计：艺人参与条目、疑似版本合并两种口径，合作计数不当作风格百分比。
- 推荐：大概率合口味 / 相邻风格 / 探索，具体理由、潜在差异、已核实来源；本地反馈保存与 JSON 导出。
- 曲库：全量搜索、正反排序、分页与真实曲目链接。
- 响应式布局、键盘操作、减少动态效果设置、文本安全转义与离线打开。

## 可运行示例

仓库只提交 **6 首虚构曲目** 的示例，不含任何真实用户歌单、昵称或真实专辑封面。预生成示例配有本项目原创的几何示意图：

```bash
python3 skills/music-analysis/scripts/workflow.py validate examples/playlist.json examples/analysis.json --preview
python3 skills/music-analysis/scripts/workflow.py render examples/playlist.json examples/analysis.json --output work/demo.html --preview
```

六首虚构示例使用预览模式，不满足完整报告的数量要求。可直接打开 [examples/report.html](examples/report.html) 查看带原创示意图的布局；上面的 CLI 示例没有真实 QQ 图片来源，因此会提示缺图并显示占位。`npm run build` 可重建带示意图的示例。示例没有伪造真实音乐推荐；推荐、反馈等交互由测试临时构造的合成候选验证。

## 方法与边界

歌单是收藏快照，不能自动得知播放次数、首次听歌时间、实际年份或听歌场景。只有用户确认顺序后才解释变化；不确定就分析静态偏好。版本和整专收藏可能影响数量，元数据不能证明每首都同样喜欢。推荐作品需要来源核实与用户试听，不根据歌名猜人格、BPM 或精确匹配率。

校验绑定有序歌单哈希，避免歌单新增曲目后复用旧编号；声明总数与收到条目不符会停止。自动校验保证数据结构与证据引用，不能替代模型判断、作品核实或用户试听。

私人数据、反馈、生成报告与原始接口响应默认放入被忽略的 `work/`、`outputs/`；不要提交账号凭证或他人的歌单。仓库示例与默认模板均不绑定原作者的个人分析。

## 开发与验证

```bash
npm install
npm test                 # Python 数据、顺序、排重、封面与导出测试
npm run check            # Python 编译检查
npm run build            # 重建虚构示例
npx playwright install chromium
npm run test:browser     # 离线文件与浏览器交互验证
```

Python 测试覆盖各平台路由、分享短链、ID / 平台核对、部分歌单拒绝、CSV 字段、多平台封面下载与离线缓存。浏览器测试覆盖三种顺序状态、滚动目录与跳转、统计切换、推荐筛选、反馈持久化与导出、曲库分页/搜索/排序、不同屏宽、不可信字符串、默认命令自动内嵌封面、四种屏宽的原版字号/颜色/间距基准、不同歌单 / 平台的同模板与同板块校验、偏好到推荐的跳转与生成后无外部资源加载。测试产物写入 `.test-output/`，不发布。Python 测试不需要 Node；Playwright 仅为开发依赖。

0.4.0 联网实测：网易云公开示例完整导出 613 首，汽水分享短链完整导出 630 首，各成功获取 4 张代表封面；酷狗普通版示例的预览响应被正确拒绝。其余平台以接口契约回归覆盖，实际可用性需按用户链接确认，不能将模拟测试视为所有平台的联网保证。

代码结构：`skills/music-analysis/scripts/` 为解析/统计/渲染，`assets/report.html` 为模板，`references/` 为方法与来源，`tests/` 为验证，`examples/` 为虚构示例。

## 引用

多平台解析调用 [Playlist Out](https://github.com/LengxiQwQ/playlistout) 的统一 API，也支持其本地 JSON / CSV；[QQMusicApi](https://github.com/jsososo/QQMusicApi) 是自建接口的可选参考，未打包其代码；视觉参考 [Astryx](https://astryx.atmeta.com/)，模板为本项目编写；浏览器验证使用 [Playwright](https://github.com/microsoft/playwright)。完整借鉴范围和许可见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

自有代码采用 MIT；第三方音乐、封面、商标及上游服务不包含在该授权内。更新见 [CHANGELOG.md](CHANGELOG.md)。
