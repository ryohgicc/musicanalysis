# 获取与解析

## 用户需提供的信息

收集歌单链接 / ID 或导出文件时，同时询问“哪个序号是最新收藏的”，例如“第 1 首最新”或“最后一首最新”。沿用会话中已有答案；序号必须对应本次解析快照的原始顺序，必要时用首尾曲名核对。时间方向的确认与字段映射见 [完整内容契约](report-contract.md#收藏顺序与章节)。

## 没有复制链接按钮

1. 在 QQ 音乐歌单的分享菜单，手动选择微信或 QQ。
2. 打开分享的歌单卡片，使用菜单中的“在浏览器打开”或类似入口。
3. 复制浏览器地址栏最终 URL；可以是很长的分享链接，不需要自行删参数。
4. 提供最终链接或歌单 ID。不同系统/App 版本的按钮位置可能不同；若微信没有浏览器入口，可在 QQ 或桌面端打开卡片。

这是给用户的操作指引，不授权 agent 给联系人发消息。不要要求提供账号密码、登录 Cookie 或导出聊天记录。

## 路由与来源

- 默认解析规范化 ID 后访问 QQ 公开接口：`https://c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg`，参数 `type=1,json=1,utf8=1,onlysong=0,disstid=<ID>,format=json`，Referer 为 `https://y.qq.com/`。这是非官方稳定性契约；是否可用受地区、公开状态与平台变化影响。
- 分享页经常只包含首屏曲目。即使能提取 SSR JSON，也必须核对声明总数。脚本拒绝不完整响应。
- 可选 Playlist Out 服务：`https://playlistout-api.lengxiqwq.com/api/v1/resolve?q=<规范化QQ链接>`；第三方会收到公开歌单链接，不转发无关的分享追踪参数。返回 canonical JSON，由本项目规范化。服务版本、限流和可用性见其 [API 文档](https://github.com/LengxiQwQ/playlistout/blob/main/docs/API.md)。
- 不反复自动重试；连接或接口失败后，保留错误，换用浏览器/本地导出。没有 ID 的短链让用户用浏览器打开最终地址。

## 本地替代路线

可使用 [Playlist Out 网页](https://playlistout.lengxiqwq.com/) 或其 CLI 导出 JSON/CSV，再调用 `normalize`。使用 CLI 前查看所装版本 `--help` 或上游 README，不照搬可能变动的参数。

仅当用户需要自建 QQ API 服务时，才考虑 [QQMusicApi](https://github.com/jsososo/QQMusicApi)。本项目没有依赖或打包它的实现，也没有实现 MCP 服务器；skill 本身可直接调用脚本完成此流程。

## 完整性与快照

输出 `playlist.json`、电子表格安全的 `playlist.csv`、`playlist.txt`；在线抓取另保存 `source.json`。原始 JSON 可能带昵称等数据，默认仅本地保留，不纳入版本控制。所有导出均为曲目元数据，无音频、歌词或付费下载链接。

保留原顺序、重复条目、同曲不同发行记录与艺人数组。总数不一致时先补全导出；不要静默丢弃无歌名/艺人的条目。CSV 无精确艺人数组时，合作分隔可能歧义，应尽量回到原 JSON。

歌单线上可能继续增加歌曲；每次分析绑定本次的完整有序快照，不能把旧报告中的原始编号用于新导出。
