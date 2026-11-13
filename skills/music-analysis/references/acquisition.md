# 获取与解析

## 用户需提供的信息

收集歌单链接 / ID 或导出文件时，同时询问“哪个序号是最新收藏的”，例如“第 1 首最新”或“最后一首最新”；只有 ID 时还需注明平台。沿用会话中已有答案；序号必须对应本次解析快照的原始顺序，必要时用首尾曲名核对。时间方向的确认与字段映射见 [完整内容契约](report-contract.md#收藏顺序与章节)。

## 平台支持

| 平台 | `--platform` | 在线解析方式 / 限制 |
| --- | --- | --- |
| QQ 音乐 | `qqmusic` | 长链接 / ID 默认直连 QQ；短链用 Playlist Out |
| 网易云音乐 | `netease` | Playlist Out，支持普通链接、`#/playlist` 和 `163cn.tv` 短链 |
| 酷狗音乐 | `kugou` | Playlist Out；普通版免登录可能只有 10 首预览，必须补齐后分析 |
| 酷狗概念版 | `kugou` | Playlist Out；保留集合链接中的 `global_specialid` 等参数 |
| 酷我音乐 | `kuwo` | Playlist Out |
| 汽水音乐 | `qishui` | Playlist Out，支持汽水 / 抖音分享链接 |
| 咪咕音乐 | `migu` | Playlist Out，支持咪咕短链 |

仅接单个公开歌单，不接用户主页批量解析；Spotify、Apple Music 链接未接入。上表表示已接入的接口能力，不承诺上游实时可用。发布验证包括各平台契约回归、网易云与汽水完整歌单及封面联网实测；其他平台须结合实际链接检查总数，不能将模拟测试描述为逐平台联网实测。

## 没有复制链接按钮

1. 在 QQ 音乐歌单的分享菜单，手动选择微信或 QQ。
2. 打开分享的歌单卡片，使用菜单中的“在浏览器打开”或类似入口。
3. 复制浏览器地址栏最终 URL；可以是很长的分享链接，不需要自行删参数。
4. 提供最终链接或歌单 ID。不同系统/App 版本的按钮位置可能不同；若微信没有浏览器入口，可在 QQ 或桌面端打开卡片。

这是给用户的操作指引，不授权 agent 给联系人发消息。不要要求提供账号密码、登录 Cookie 或导出聊天记录。

## 路由与来源

- `--provider auto`（默认）：QQ 长链接 / ID 访问 `https://c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg`，参数 `type=1,json=1,utf8=1,onlysong=0,disstid=<ID>,format=json`；其他平台和 QQ 短链走 Playlist Out。`--provider qq` 限定 QQ 直连，`--provider playlistout` 强制使用第三方。直连失败不会静默改走第三方。
- Playlist Out 服务：`https://playlistout-api.lengxiqwq.com/api/v1/resolve?q=<链接或ID>&type=playlist&platform=<平台代码>`。本地提取分享文本中的链接，不传其周边文案；已知长链接规范化以去掉追踪参数，短链保留原参数。第三方收到该链接或 ID 与平台标识。返回 canonical JSON，由本项目规范化；保留平台、曲目 ID、详情链接和封面。服务契约见其 [API 文档](https://github.com/LengxiQwQ/playlistout/blob/main/docs/API.md)，字段见 [Canonical Schema](https://github.com/LengxiQwQ/playlistout/blob/main/docs/JSON-SCHEMA.md)。
- 仅有 ID 时指定 `--platform`。无平台的纯数字 ID 为兼容旧命令仍按 QQ 处理，agent 应先确认平台；链接平台与显式参数冲突时拒绝请求。
- 分享页经常只包含首屏。脚本核对声明总数、实际条数、`loadedTrackCount` 与预览标记，拒绝 `retrieval.mode: preview/partial`、`isPartial` 或不完整响应。上游返回错误、平台 / 可确认的 ID 不匹配时不导出。
- 酷狗普通版提示预览 / 需要登录时，用户在 Playlist Out 网页或 CLI 本地登录后导出完整 JSON，再 `normalize`；skill 不接收账号密码、Cookie、Token。`render --preview` 只放宽报告内容契约，不允许把部分歌单当完整曲库。
- 不反复自动重试；连接或接口失败后，保留错误，换用浏览器 / 本地导出。短链解析失败时让用户用浏览器打开最终地址。

```bash
python3 <skill-dir>/scripts/workflow.py fetch 'https://music.163.com/#/playlist?id=<ID>' --out work/snapshot
python3 <skill-dir>/scripts/workflow.py fetch '<ID>' --platform netease --out work/snapshot
python3 <skill-dir>/scripts/workflow.py fetch '<酷狗概念版集合链接>' --out work/snapshot
```

各平台封面从元数据的 `coverUrl` 获取；支持 QQ / gtimg、网易云、酷狗、酷我、汽水图片 CDN 与咪咕域名，旧 HTTP 图片地址升级为 HTTPS。下载前与重定向时检查来源，限制体积并校验 JPEG / PNG / WebP，再缓存内嵌；其他平台缺图时不通过 QQ 歌曲查询借图。

## 本地替代路线

可使用 [Playlist Out 网页](https://playlistout.lengxiqwq.com/) 或其 CLI 导出 JSON/CSV，再调用 `normalize`。使用 CLI 前查看所装版本 `--help` 或上游 README，不照搬可能变动的参数。

仅当用户需要自建 QQ API 服务时，才考虑 [QQMusicApi](https://github.com/jsososo/QQMusicApi)。本项目没有依赖或打包它的实现，也没有实现 MCP 服务器；skill 本身可直接调用脚本完成此流程。

## 完整性与快照

输出 `playlist.json`、电子表格安全的 `playlist.csv`、`playlist.txt`；在线抓取另保存 `source.json`。原始 JSON 可能带昵称等数据，默认仅本地保留，不纳入版本控制。所有导出均为曲目元数据，无音频、歌词或付费下载链接。

保留原顺序、重复条目、同曲不同发行记录与艺人数组。总数不一致时先补全导出；不要静默丢弃无歌名/艺人的条目。Playlist Out canonical JSON 的多艺人字符串按其约定的逗号加空格拆分；艺人名本身含逗号时需要人工复核。CSV 的 `url` / `duration`（秒）可导入；本项目 CSV 另保留 `songId` / `coverUrl`。CSV 无精确艺人数组时，合作分隔可能歧义，应尽量回到原 JSON。

歌单线上可能继续增加歌曲；每次分析绑定本次的完整有序快照，不能把旧报告中的原始编号用于新导出。
