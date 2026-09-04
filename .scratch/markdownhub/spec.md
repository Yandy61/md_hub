# MarkdownHub — 内网 Markdown 分享服务

- **Labels**: ready-for-agent
- **Created**: 2026-09-04
- **Status**: open
- **来源**: 需求拷问（grilling 13 问）共识，用户已确认

## Problem Statement

在一台内网服务器（CentOS 7）上，markdown 文档散落在各个原始目录里。需要一个方式让内网其他机器的人通过浏览器方便地浏览这些文档（渲染格式、含图片/图表），且**文件必须留在原处**（不复制、不移动）；同时管理动作（共享哪些内容、新建/修改/删除文档）只能由管理员执行，访客纯只读、零门槛（不登录）。

## Solution

一个单进程 Python/Flask 服务（MarkdownHub，端口 18123）：

- 管理员登录后在界面上输入本地路径，把单个 md 文件或整个目录（递归）加入**索引**——服务只引用原始路径，不复制文件。
- 访客打开服务页面，看到按索引根分组的树形文档列表（可即时过滤），点开即见渲染后的 markdown（代码高亮、mermaid 图表、KaTeX 公式、相对路径图片），全部静态资产本地打包，内网离线可用。
- 源文件被外部修改后，浏览器每 ~4 秒轮询检测变更并自动重渲染；目录里新增/删除文件同样自动反映。
- 管理员可在线编辑文档（CodeMirror）直接写回原文件（项目侧自动备份）、在固定 workspace 新建文件、按区分语义删除。

## User Stories

**访客**

1. As a 访客, I want 打开服务就看到所有已共享的 markdown 文档列表, so that 我能知道内网有哪些可读内容
2. As a 访客, I want 列表按索引根分组、目录索引以树形展示, so that 我能按目录结构浏览大量文档
3. As a 访客, I want 顶部有一个客户端即时过滤框, so that 我按文件名快速定位文档而无需服务端搜索
4. As a 访客, I want 每个列表项显示文件的最后更新时间, so that 我能判断内容新鲜度
5. As a 访客, I want 打开文档看到渲染好的 markdown（标题/表格/列表/引用/链接/任务列表）, so that 我读的是排版后的内容而非源码
6. As a 访客, I want 代码块有语法高亮, so that 代码可读
7. As a 访客, I want mermaid 图表被渲染, so that 架构/流程文档正常展示
8. As a 访客, I want 数学公式（KaTeX）被渲染, so that 技术笔记完整可读
9. As a 访客, I want 文档里相对路径引用的图片等资源能正常加载, so that 带图的文档不是残缺的
10. As a 访客, I want 源文件被外部修改后页面在几秒内自动更新, so that 我始终读到当前版本而不用手动刷新
11. As a 访客, I want 被索引目录里新增/删除的文件自动出现在/消失于列表, so that 列表始终与磁盘一致
12. As a 访客, I want 所有 JS/CSS 资产由服务本地提供（不依赖 CDN）, so that 没有外网的机器也能正常使用
13. As a 访客, I want 源文件暂时丢失时看到明确的"源丢失"提示, so that 我知道是内容暂不可用而不是服务坏了
14. As a 访客, I want 只能访问已被索引的内容且无法执行任何写操作, so that 未共享的文件对我是不可见的、服务是安全的

**管理员**

15. As a 管理员, I want 用户名+密码登录, so that 管理功能只对我开放
16. As a 管理员, I want 密码以 PBKDF2 哈希存储、通过 set_password 命令设置, so that 配置文件里没有明文凭证
17. As a 管理员, I want 输入一个本地路径索引单个 md 文件（不复制）, so that 文件留在原处即可被分享
18. As a 管理员, I want 输入一个目录路径递归索引其下所有 md 文件（排除 .git/.svn/node_modules/__pycache__/隐藏目录）, so that 一次操作共享整个文档树
19. As a 管理员, I want 取消索引外部文件/目录时仅解除共享、绝不修改原文件, so that 我不会误删别人的内容
20. As a 管理员, I want 在固定 workspace 目录里新建 md 文件并自动加入索引, so that 我可以直接在服务里创作
21. As a 管理员, I want 在网页编辑器（CodeMirror 5）里编辑任何已索引文档并写回原文件, so that 我从浏览器就能维护内容
22. As a 管理员, I want 每次写回前在项目侧 .backups/ 留时间戳备份（保留最近 N 份）, so that 误改可恢复且不污染原目录
23. As a 管理员, I want 删除服务新建的文件=取消索引+删除真实文件, so that workspace 不留孤儿文件
24. As a 管理员, I want 删除外部索引条目时 UI 文案明确是"取消共享"而非"删除", so that 删除语义不会误导我
25. As a 管理员, I want 源路径丢失时索引条目被保留并标记"源丢失"、恢复后自动回归, so that 挂载盘抖动不会毁掉索引配置
26. As a 管理员, I want 登录会话用 HttpOnly + SameSite=Strict cookie 且所有写接口强制鉴权, so that 访客只能读
27. As a 管理员, I want 可索引服务器任意路径, so that 共享范围完全由我自己决定（内网单人信任场景）

**运维**

28. As a 运维, I want start.sh（nohup 后台 + logs/ 日志 + pid 文件）, so that 一条命令拉起服务
29. As a 运维, I want stop.sh 按 pid 干净停止, so that 一条命令关停服务
30. As a 运维, I want 服务绑定 0.0.0.0:18123, so that 内网其他机器可直接访问
31. As a 运维, I want 服务只依赖 Python 3.9(conda base) + Flask 单包, so that CentOS 7 上部署零负担

## Implementation Decisions

- **技术栈**: Python 3.9 + Flask（conda base 直跑），单进程，pip 依赖仅 flask；渲染全部在前端，后端无重依赖。索引 registry 为项目内 JSON 文件，原子写（写临时文件后 rename）。规模假设：几百文件以内、单管理员。
- **变更检测**: 不用 watchdog/inotify/SSE。浏览器每 ~4 秒轮询 mtime+size，变更即重新拉取重渲染；该机制天然覆盖文件内容变更、目录新增/删除文件、源路径消失与恢复，且对 NFS 挂载盘有效。
- **资源服务边界**: 目录索引 → 服务其整棵子树内任意文件（图片等）；单文件索引 → 服务其同目录文件。路径由管理员选定，管理员负责其内容暴露。
- **目录扫描**: 递归整棵子树，排除 `.git`、`.svn`、`node_modules`、`__pycache__` 及隐藏目录/文件。
- **删除语义（区分）**: 外部索引条目 → 删除 = 仅取消索引，绝不触碰原文件；服务在 workspace 新建的文件 → 删除 = 取消索引 + 删除真实文件。UI 文案区分"取消共享"与"删除"。
- **新建文件**: 只能创建在固定 workspace 目录（默认 `<项目>/workspace/`，配置可改），创建后自动加入索引；不提供任意路径创建。
- **在线编辑**: 直接写回原文件，覆盖式（last-write-wins，无冲突检测）；写回前将原内容存入项目侧 `.backups/`，带时间戳，保留最近 N 份（默认 10）。
- **认证**: config 存用户名 + PBKDF2 哈希 + session 密钥；提供 set_password 命令设密；登录后签发 HttpOnly + SameSite=Strict session cookie；所有写接口强制鉴权。HTTP 明文为已接受的取舍（内网）。
- **路径边界**: 可索引路径不设黑名单——管理员本就持有服务器 shell 权限。
- **API 契约（示意）**: 访客侧 `GET 列表`、`GET 文档原文`、`GET 文档元信息(mtime/size)`、`GET 相对资源`；鉴权侧 `POST 登录/登出`、`POST 新增索引`、`DELETE 索引条目`、`POST 新建文件`、`PUT 写回文档`、`DELETE 文档`。索引条目以稳定 id 标识，registry 记录原始路径与类型（file/dir）。
- **前端**: 静态资产全部本地打包（vendor 到服务下）：markdown-it、highlight.js、mermaid、KaTeX、CodeMirror 5。界面按索引根分组树形浏览 + 客户端过滤 + 更新时间；仅浅色主题（无深色模式）。
- **编码**: 文档读取 UTF-8 为主，GBK 自动兜底。
- **部署**: 端口 18123、绑定 0.0.0.0、服务名 MarkdownHub；start.sh（nohup + logs/ + pid 文件）/ stop.sh。

## Testing Decisions

- **好测试的标准**: 只测外部行为（HTTP 请求/响应、磁盘上的实际文件效果），不测内部实现细节。
- **Seam（已与用户确认）**: 后端唯一 seam = HTTP API，用 Flask test client 驱动全部行为验证——索引增删、目录扫描与排除规则、资源服务边界、鉴权（未登录写操作被拒/错误密码/会话）、编辑写回与备份产物、两种删除语义、源丢失与恢复。前端渲染管线做成纯 JS 模块，用 node 轻量冒烟脚本验证（md→HTML、代码块、表格、公式/mermaid 占位）；其余 UI 人工验收。
- **Prior art**: 绿地项目，无既有测试；首套测试（pytest）即为本项目后续测试的惯例基准。

## Out of Scope

- HTTPS/TLS、challenge-response 等传输安全（内网明文已接受）
- 多用户/多角色、访客侧任何形式的登录
- 服务端全文搜索（仅客户端文件名过滤）
- 版本历史 UI（仅有 .backups/ 落盘备份，不做回滚界面）
- 深色模式
- 文件上传（访客或管理员）、评论/批注、访问统计
- systemd/docker/守护进程（明确 nohup 即可）
- 文档级权限（全部已索引内容对全部内网访客可见）

## Further Notes

- **调研并行进行中**: 一个后台调研正在评估现成开源方案（Gollum、Wiki.js 等）能否满足"索引原始路径+实时+密码管理"的组合。若调研结论为现成方案完全满足需求，本 spec 可能被搁置——实现开工前以调研结论做最终"自建 vs 复用"决策。
- 环境事实（已核实）: CentOS 7 / glibc 2.17、Python 3.9.23（conda base）、Node 22 可用、pypi/npm 镜像可达、端口 18123 空闲。
