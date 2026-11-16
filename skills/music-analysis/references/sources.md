# 项目引用与借鉴范围

核对日期：2026-11-13。以下区分实际流程来源、可选工具与视觉参考，避免把“提到过”写成“代码依赖”。

| 项目 / 来源 | 本项目如何使用 | 许可与范围 |
| --- | --- | --- |
| [Playlist Out · LengxiQwQ/playlistout](https://github.com/LengxiQwQ/playlistout) | 多平台解析实际调用其统一公开 API（网易云、酷狗含概念版、酷我、汽水、咪咕及 QQ 短链），也支持导入 canonical JSON / CSV。QQ 长链接默认直连，可显式选择 Playlist Out。 | 上游仓库标注 MIT。未复制其源码；不打包上游网页、CLI、插件或服务。服务调用不表示服务有可用性承诺。API 契约见 [官方文档](https://github.com/LengxiQwQ/playlistout/blob/main/docs/API.md)。 |
| [QQMusicApi · jsososo/QQMusicApi](https://github.com/jsososo/QQMusicApi) | QQ 接口生态的可选参考；需要自建接口时可自行评估。 | 上游仓库标注 GPL-3.0。本项目不导入、不打包、不复制其实现。默认解析器是本项目对 QQ 公开元数据接口的独立请求与规范化实现。 |
| [Astryx](https://astryx.atmeta.com/) | 网页视觉参考：暖白底、亮蓝强调、柔和色晕、圆角卡片。 | 仅借鉴视觉方向；没有复制其 HTML、CSS、Logo、文案、图片或产品界面。当前模板与几何图形由本项目编写。 |
| [Apple Music](https://music.apple.com/) / iTunes 公开曲目目录 | Demo 与正式 skill 的推荐封面来源：按曲名、艺人和版本人工核对发行，使用 `mzstatic.com` 图片，缓存并内嵌，页面保留发行来源；不自动搜索匹配发行，未下载音频。 | 封面权利归相应权利人；仅用于报告的作品识别，不纳入 MIT 授权。没有接入 Apple Music 歌单解析。 |
| [Apple 产品页](https://www.apple.com.cn/airpods-pro/) 与 [Motion 指南](https://developer.apple.com/design/human-interface-guidelines/motion) | 全屏 Demo 与 v0.6.0 正式模板的滚动叙事及布局参考：单屏重点、卡片转场与长内容阅读。 | 动效和代码由本项目编写，未复制 Apple 的代码、图片、视频或产品素材。正式模板现已采用同一全屏交互。 |
| [Playwright · microsoft/playwright](https://github.com/microsoft/playwright) | 仅用于开发验证：本地文件、滚动目录、手机布局、反馈导出与 DOM 行为。 | Apache-2.0。作为开发依赖通过包管理器安装，用户生成报告不加载它。 |
| [QQ 音乐](https://y.qq.com/)、[网易云音乐](https://music.163.com/)、[酷狗音乐](https://www.kugou.com/)、[酷我音乐](https://www.kuwo.cn/)、[汽水音乐](https://music.douyin.com/)、[咪咕音乐](https://music.migu.cn/) | 用户提供的公开歌单、曲目详情和自动封面来源；除 QQ 直连外通过 Playlist Out 规范化元数据。 | 曲目元数据、封面与音乐作品权利归相应权利人。开发示例使用虚构数据；仓库 `docs/index.html` 与 `docs/apple-motion-report/index.html` 为作者明确授权公开的同一份真实报告的两个版本。不提供音频、歌词或下载能力；第三方内容不在本项目 MIT 授权范围内。 |

`analyze_playlist.py` 来自本次工作流中先行编写的本地 `music-taste` skill，作为本项目自有脚本整合；未复制上述 API 项目的实现。项目不要求另行安装那个本地 skill，也不附带其个人文件指针。

原报告曾额外生成 Sunburst 图片。图片生成不属于本 skill 的必要步骤，仓库不包含第三方图片模型配置、密钥、相关专用 skill 或该个人图片。
