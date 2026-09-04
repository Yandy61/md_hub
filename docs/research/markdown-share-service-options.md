# 内网 Markdown 分享/展示服务开源方案调研

- 调研日期：2026-09-04
- 方法：全部一手资料（官方文档、GitHub README/源码/issue、官方 Release/npm/PyPI registry），每条结论附来源 URL；标"文档"= 官方文档/README 明确，标"源码/issue"= 源码或 issue 证实，标"推断"= 未完全核实的不确定项
- 输出目录：`docs/research/`（本报告）

---

## 1. 需求与目标环境

目标：内网 markdown 分享/展示服务，5 项硬性需求：

| 编号 | 需求 |
|---|---|
| R1 | **索引原始路径**：管理员在界面上输入/选择服务器本地路径，直接索引该 md 文件或整个目录（目录自动索引下所有 md），不复制文件，引用原始路径 |
| R2 | **权限模型**：访客只读、免登录，只能看已索引内容；管理员用户名+密码登录后可新增索引/新建/修改/删除 |
| R3 | **实时反映源文件变更**：原始 md 被外部修改后页面跟着变（文件 watch 自动重渲染，或至少手动刷新读到最新内容） |
| R4 | **部署简单**：单进程 nohup 即可，无 docker/systemd，兼容 CentOS 7 |
| R5 | **渲染质量**：标准 markdown（表格、代码高亮、目录/锚点），mermaid/数学公式加分不强求 |

目标环境：**CentOS 7（内核 3.10，glibc 2.17）**，无 docker、无 systemd；Python 3 / conda 可用。

## 2. 前置事实核查：各运行时在 CentOS 7 上的可用性

| 运行时 | 结论 | 来源 |
|---|---|---|
| Node ≤ 16 官方二进制 | ✅ 官方支持矩阵明确 `kernel >= 3.10, glibc >= 2.17`，支持列表含 "EL 7" | https://raw.githubusercontent.com/nodejs/node/v16.x/BUILDING.md （文档） |
| Node 18+ 官方二进制 | ❌ 要求 `kernel >= 4.18, glibc >= 2.28`（官方公告："Prebuilt binaries for Linux are now built on RHEL 8 … compatible with glibc 2.28 or later"） | https://github.com/nodejs/node/blob/v18.x/BUILDING.md 、https://nodejs.org/en/blog/announcements/v18-release-announce （文档） |
| unofficial-builds（Node 官方组织的实验构建） | ⚠️ 提供 `linux-x64-glibc-217` 变体，覆盖 **v18–v23**；v24+ 不再构建；官方声明 "minimal or no testing"，只可作兜底 | https://github.com/nodejs/unofficial-builds （文档） |
| Go 静态二进制 | ✅ 与 glibc 无关（如 mo） | https://github.com/k1LoW/mo |
| Rust（musl 构建） | ✅ mdBook 官方 Release 提供 musl 静态二进制，与 glibc 无关 | https://github.com/rust-lang/mdBook/releases （文档） |
| VS Code 1.86+ | ❌ 要求 glibc 2.28（连带 code-server 只能用捆绑 Code ≤1.85 的旧版） | https://code.visualstudio.com/updates/v1_86 （文档） |
| Ruby | ⚠️ CentOS 7 自带 2.0.0；gollum 要求 ≥2.6，madness 要求 ≥3.2，均需 rbenv/rvm/SCL 自装 | https://github.com/gollum/gollum/blob/master/gollum.gemspec 、https://rubygems.org/gems/madness （文档） |
| Python（conda） | ✅ 无 glibc 门槛，最省事 | — |

## 3. 核心结论（TL;DR）

1. **R1 的"界面上动态添加任意路径索引"在全部 20+ 个候选中零支持**。所有现成工具都是"启动时用参数/环境变量指定一个根目录"，换路径要改配置重启。R1 现成工具最多满足到"启动时指定任意本地路径"。
2. R2 的"访客只读免登录 + 管理员账密可写"双角色组合，只有 Wiki.js（但 R1/R3 不满足）、Raneto（Node 23.14 门槛或退 0.17.x）具备；文件型小工具中最好的 wikmd 只有单密码、无用户名。
3. **推荐排名**：① 自建 200–400 行 Python 薄后端 + 本地化 docsify 前端（唯一可 100% 满足 R1–R5）；② wikmd（现成最贴合，R2–R5 全 ✅，缺 R1 的界面选路径）；③ mo（Go 单二进制，纯只读展示场景最强）。
4. **自建结论：值得**。理由见 §6。

## 4. 逐候选评估

### 4.1 Wiki 引擎类

#### Gollum（Ruby）

- 语言/运行时：Ruby（Sinatra + gollum-lib），gem 安装，git 适配器 rugged（libgit2，需本地编译）。最新 v6.1.0（2025-01-02），**低频维护**。来源：https://github.com/gollum/gollum/releases.atom

| 需求 | 结论 | 依据 | 来源 |
|---|---|---|---|
| R1 | ❌ | content **必须是单一 git 仓库**（"Gollum is a simple wiki system built on top of Git"），不能索引多个任意路径 | https://github.com/gollum/gollum （文档） |
| R2 | ⚠️ | v5.3.3 与 master 均无 `--basic-auth`；无内置用户名+密码，认证委托 Rack middleware 需自写；`--no-edit` 是全局只读开关，无"访客只读+管理员可编辑"组合 | https://github.com/gollum/gollum/blob/master/bin/gollum 、https://github.com/gollum/gollum/blob/master/lib/gollum/app.rb （源码） |
| R3 | ❌ | 读页面全走 git 对象库（`git cat-file`/`lstree`，无 File.read）——**外部改文件不 commit 页面不可见**；无 watch/livereload；issue #1031 至今 open | https://github.com/gollum/gollum-lib/blob/master/lib/gollum-lib/git_access.rb （源码）、https://github.com/gollum/gollum/issues/1031 （issue） |
| R4 | ⚠️ | gemspec 要求 Ruby ≥2.6（自带 2.0.0 不够），需 rbenv/SCL；rugged 等原生 gem 在老 gcc 4.8 下有编译风险（推断） | https://github.com/gollum/gollum/blob/master/gollum.gemspec （文档） |
| R5 | ✅ | GFM 表格/高亮/锚点 + 内置 Mermaid 11.4 + KaTeX/MathJax | https://github.com/gollum/gollum/blob/master/LATEST_CHANGES.md （文档） |

#### Wiki.js 2.x（Node.js）

- 语言/运行时：Node.js，内容存 DB。最新 2.x = v2.5.314（2026-05-01），维护活跃；3.x beta 推进中（3.0.0-beta.537，2026-09-02，官方标注不可上生产）。来源：https://github.com/requarks/wiki/releases

| 需求 | 结论 | 依据 | 来源 |
|---|---|---|---|
| R1 | ❌ | 内容存 DB（PG/MySQL/MariaDB/MSSQL/SQLite 均支持）；Local File System 存储模块**仅"从 DB 导出"**（definition.yml `supportedModes: push`，无 watch，仅手动 importAll）；Git 模块双向但只针对专门 clone 的仓库，"not possible to use only a subfolder" | https://docs.requarks.io/install/requirements 、https://github.com/requarks/wiki/blob/master/server/modules/storage/disk/definition.yml （源码）、https://docs.requarks.io/storage/git （文档） |
| R2 | ✅ | 内置 Local 用户名+密码（"cannot be disabled as it is required for root administrator login"）；Guests 组默认匿名只读，权限粒度细 | https://docs.requarks.io/auth 、https://github.com/Requarks/wiki-docs-v2/blob/master/groups.md （文档） |
| R3 | ❌ | 以 DB 为准；唯一路径是 git 模块**定时拉远程仓库**（"every 5 minutes by default"），无本地 watch，且不是原始路径直读 | https://docs.requarks.io/storage/git （文档） |
| R4 | ⚠️ | 非 docker 可行：`node server` + nohup（官方 Linux 安装文档）；但当前 2.x 要求 Node 22/24（"version 22.0 or later, since v2.5.302"）→ CentOS 7 只能 unofficial-builds Node 22 glibc-217（实验性），或旧版 2.x 配 Node 16（推断） | https://docs.requarks.io/install/linux 、https://docs.requarks.io/install/requirements （文档） |
| R5 | ✅ | 代码高亮、KaTeX/MathJax、Mermaid、PlantUML 官方内置；TOC 侧栏推断内置 | https://docs.requarks.io/rendering （文档） |

### 4.2 DB-backed 编辑器/知识库（快速排除，内容均存数据库、进入即与原始文件脱钩）

#### Outline（TypeScript/Node + React）

- ❌ 排除：PostgreSQL 14+ 与 Redis 4+ 必需、强制外部 Authentication Provider（无本地账密）、Node 20.12+ 撞 glibc 墙；内容存 Postgres 无本地目录索引概念。非常活跃（v1.10.0，2026-09-02）。
- 来源：https://docs.getoutline.com/s/hosting/doc/requirements-ULdYnwi4wG （文档）、https://github.com/outline/outline/blob/main/package.json （源码）

| R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|
| ❌ | ❌ | ❌ | ❌ | 未评估 |

#### BookStack（PHP/Laravel）

- ❌ 排除：内容存 MySQL/MariaDB（≥8.0/10.6）；要求 PHP ≥8.2（CentOS 7 需 Remi 等第三方仓库，el7 支持未核实）+ Composer；无本地目录索引。非常活跃（v26.05.4，2026-08-24）。
- 来源：https://www.bookstackapp.com/docs/admin/installation/ （文档）

| R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|
| ❌ | ⚠️（有用户体系，未深挖） | ❌ | ❌ | 未评估 |

#### Docmost（Node）

- ❌ 排除：内容存 Postgres；官方 docker-compose 依赖 **postgres:18 + redis:8**，且官方 Release 只有 docker 镜像交付（`docmost-amd64.docker.tar.gz`），无 docker 环境裸机拼装不现实。活跃（v0.95.0，2026-07-03）。
- 来源：https://github.com/docmost/docmost/blob/main/docker-compose.yml （源码）、https://github.com/docmost/docmost/releases （文档）

| R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|
| ❌ | ⚠️（未深挖） | ❌ | ❌ | 未评估 |

#### HedgeDoc（Node）

- ❌ 排除：内容存数据库（支持 PostgreSQL/MySQL/MariaDB/**SQLite**，但 `db` 配置即内容存储，`defaultNotePath` 只是新建空笔记模板）；无"索引本地 md"概念（单文件导入也是一次性拷入 DB）；master 要求 Node 20+（glibc 2.28 墙）。1.x 已宣布 maintenance-only（1.12.0，2026-08-21）。
- 来源：https://docs.hedgedoc.org/configuration/ 、https://docs.hedgedoc.org/setup/manual-setup/ （文档）、https://github.com/hedgedoc/hedgedoc/blob/master/package.json （源码）

| R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|
| ❌ | ⚠️ | ❌ | ❌ | 未评估 |

#### Cowyo（Go）

- ❌ 排除：当前 main 为 cowyo2 重写，数据存**内部 SQLite**（README："cowyo2 uses SQLite by default"），不能指向已有 md 目录；无用户账号体系（仅 per-page lock）；GitHub Release 无预编译产物（v3.0.1 assets 为空），需自备 Go 1.26 工具链编译。提交历史 2023-07→2026-07 有三年断档，"复活"项目长期性存疑。
- 来源：https://github.com/schollz/cowyo （README + go.mod，源码）

| R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|
| ❌ | ❌ | ❌ | ⚠️ | 未评估 |

### 4.3 静态站点生成器

#### mkdocs serve（Python）

- 语言/运行时：Python（`requires-python >= 3.8`），pip/conda 即装；最新 release 1.6.1（2024-08-30），master 提交持续至 2025-10。来源：https://github.com/mkdocs/mkdocs/blob/master/pyproject.toml （源码）

| 需求 | 结论 | 依据 | 来源 |
|---|---|---|---|
| R1 | ❌（有技术替代） | 零管理 UI，无"界面输入路径"；docs_dir 单根，但可用绝对路径 + **symlink 会被 `os.walk(followlinks=True)` 跟随**混入多个任意目录（改路径需手改 mkdocs.yml） | https://www.mkdocs.org/user-guide/configuration/ （文档）、mkdocs/structure/files.py `get_files()` （源码） |
| R2 | ❌ | 完全只读，无 web 编辑、无任何 auth | https://www.mkdocs.org/user-guide/cli/ （文档） |
| R3 | ✅（注意） | watchdog `PollingObserver` 自动 rebuild + 浏览器刷新；⚠️ symlink 目标物理上在 docs_dir 外，轮询监视未必穿透，应对真实目录追加 `-w /真实路径` 兜底（官方 `-w/--watch` 可多次指定） | mkdocs/commands/serve.py（源码）、https://www.mkdocs.org/user-guide/cli/ （文档） |
| R4 | ✅ | conda 环境即装即用，无 glibc 门槛；`nohup mkdocs serve -a 0.0.0.0:8000 &` | https://www.mkdocs.org/user-guide/installation/ （文档） |
| R5 | ✅ | 表格/Pygments 高亮/TOC 锚点内建；mermaid/公式需 mkdocs-material + pymdownx（生态） | https://www.mkdocs.org （文档/生态） |

- 定位：官方 CLI 称 "development server"，但未找到显式"禁止生产"警告（文档）。

#### mdBook（Rust）

- 语言/运行时：Rust；书结构 = `book.toml` + 单一 `src` 目录 + `src/SUMMARY.md`。最新 v0.5.4（2026-07-06），活跃。

| 需求 | 结论 | 依据 | 来源 |
|---|---|---|---|
| R1 | ❌（源码级硬限制） | 章节路径经 `src_dir.join(location)` 解析后执行 `strip_prefix(src_dir).expect("Chapters are always inside a book")`——**src 外路径（含绝对路径）直接 panic**，多根索引彻底无解 | https://rust-lang.github.io/mdBook/format/summary.html （文档）、crates/mdbook-driver/src/load.rs `load_chapter()` （源码） |
| R2 | ❌ | 无 web 编辑、无 auth | https://rust-lang.github.io/mdBook/cli/serve.html （文档） |
| R3 | ⚠️ | `mdbook serve` watch **仅 src 目录**（watcher 只注册 `book.source_dir()`）+ websocket 刷新；src 外文件不触发 | https://rust-lang.github.io/mdBook/cli/serve.html （文档）、src/cmd/watch/native.rs （源码） |
| R4 | ✅（关键发现） | **官方 Release 提供 musl 静态二进制**（`mdbook-v0.5.4-x86_64-unknown-linux-musl.tar.gz`），与 glibc 无关，CentOS 7 直接跑 | https://github.com/rust-lang/mdBook/releases （文档） |
| R5 | ✅ | 表格/highlight.js 高亮/侧栏/锚点/搜索内建；mermaid、公式需 preprocessor | https://rust-lang.github.io/mdBook/ （文档） |

- 定位：官方明说 serve "is not intended to be a complete HTTP server for a website"。

### 4.4 轻量文件型工具（watch 目录 + 只读展示 + 简单 admin 形态）

#### wikmd（Python/Flask）★ 现成工具中综合最接近

- 语言/运行时：Python Flask（`requires-python >= 3.8`），git 做版本控制（`sync_with_remote` 可关）；维护活跃（最近 commit 2026-08）。来源：https://github.com/Linbreux/wikmd 、https://github.com/Linbreux/wikmd/commits/main

| 需求 | 结论 | 依据 | 来源 |
|---|---|---|---|
| R1 | ⚠️ | 内容目录可用 `WIKI_DIRECTORY`/YAML 指向**任意本地路径**，但**启动时固定**，无界面动态添加 | https://raw.githubusercontent.com/Linbreux/wikmd/main/docs/environment%20variables.md （文档）、src/wikmd/wiki.py（源码） |
| R2 | ✅（近似） | `PROTECT_EDIT_BY_PASSWORD` + SHA-256：访客只读、输密码后才能新建/修改/删除；**无用户名、仅单密码** | 同上（文档） |
| R3 | ✅ | 源码证实页面请求内 `open(md_file_path)` **逐请求读盘**（外部改文件刷新即生效）+ Watchdog 文件监控 | https://raw.githubusercontent.com/Linbreux/wikmd/main/src/wikmd/wiki.py （源码） |
| R4 | ✅ | Flask 单进程 nohup；`LOCAL_MODE=True` 自托管全部 css/js，**内网无 CDN 依赖** | 同上（文档） |
| R5 | ✅ | 代码高亮、math/latex、全文搜索、知识图谱、drawio/plantuml/swagger 插件、暗色主题 | 同上（文档） |

#### mo（Go）★ 渲染/watch 最强，但无 auth

- 语言/运行时：Go 单二进制（1057★）；非常活跃（v1.6.7，2026-08-03）。来源：https://github.com/k1LoW/mo

| 需求 | 结论 | 依据 | 来源 |
|---|---|---|---|
| R1 | ⚠️ | CLI 启动时传文件/目录树（侧栏导航/TOC/分组），无界面动态添加 | https://github.com/k1LoW/mo （文档） |
| R2 | ❌ | **完全无认证**；默认仅绑 localhost，远程访问需 `--dangerously-allow-remote-access` 且明示 "without any authentication" | 同上（文档） |
| R3 | ✅ | `--watch` 目录监控 + live reload | 同上（文档） |
| R4 | ✅ | Go 静态二进制，CentOS 7 无压力 | 同上 |
| R5 | ✅（最强档） | GFM + 语法高亮 + **Mermaid + KaTeX** | 同上 |

#### Raneto（Node）★ 唯一"用户名+密码"形态的轻量 admin

- 语言/运行时：Node + Express；活跃（0.18.1，2026-03-11）。来源：https://registry.npmjs.org/raneto

| 需求 | 结论 | 依据 | 来源 |
|---|---|---|---|
| R1 | ⚠️ | `CONTENT_DIR` 可指任意本地路径，但启动时固定，无界面动态添加 | https://github.com/gilbitron/Raneto （README，文档） |
| R2 | ✅ | `AUTHENTICATION` + `ADMIN_USERNAME`/`ADMIN_PASSWORD` 内置登录保护编辑；访客免登录只读；`ALLOW_EDITING` 开关浏览器编辑器（可新建/修改/删除） | 同上（文档） |
| R3 | ✅ | 源码证实每个页面请求都 `fs.readFile` 从磁盘重读，无启动缓存 | https://raw.githubusercontent.com/gilbitron/Raneto/master/app/routes/wildcard.route.js （源码） |
| R4 | ❌→⚠️ | v0.18.1 要求 **node >= 23.14.0**（官方二进制 CentOS 7 不可用）；退回 0.17.1（要求 node >= 10.22.1）配 Node 16 可行，或用 unofficial-builds glibc-217（v18–23）跑新版 | https://registry.npmjs.org/raneto （engines，文档）、https://github.com/nodejs/unofficial-builds |
| R5 | ✅ | marked（GFM）、lunr 全文搜索、代码高亮、锚点；mermaid/公式需自行加 | https://github.com/gilbitron/Raneto （文档 + package.json） |

#### madness（Ruby）

- Ruby "Instant Markdown Server"：serve 一个文档目录、自动生成目录树侧栏、全文搜索、高亮、**Mermaid**、可选 basic auth（`--auth user:password`）；gem 1.3.1（2026-07-18）活跃，但**要求 Ruby ≥ 3.2**（CentOS 7 需自编译 Ruby，摩擦大）。R1 ⚠️（docroot 启动时指定）、R2 ⚠️（整站 basic auth，无角色分离，本来也无编辑功能）、R3 ✅（源码 server.rb 每请求重读磁盘）、R4 ⚠️、R5 ✅。
- 来源：https://github.com/DannyBen/madness 、https://rubygems.org/gems/madness

#### markserv（Node）

- npm 最新 1.17.4 停在 **2019-12-29**（仓库 2026-03 有提交但未发版）；`markserv ./` 可 serve 目录含索引页、WebSocket 热重载、MathJax；无 auth；Node 版本要求未声明。R1 ⚠️（启动参数指定）、R2 ❌、R3 ✅、R4 ⚠️（2019 时代代码，Node 16 大概率可跑但未验证）、R5 ✅（mermaid 未见官方支持）。
- 来源：https://registry.npmjs.org/markserv 、https://github.com/markserv/markserv

#### flatnotes（Python，3.2k★）

- 无数据库笔记应用："a flat folder of markdown files"；官方明确支持**运行中外部增删改文件照常工作**（R3 ✅）；认证四档 none/read-only/username+password/TOTP——但 read-only 与 password 是**整站二选一**，不是"访客只读+管理员登录"并存（R2 ⚠️）；R1 ⚠️（数据目录启动时配置）；R4 ⚠️：**官方推荐 Docker，PyPI 无包**，无 docker 的手工部署路径未文档化（不确定）；R5 ✅。维护活跃。
- 来源：https://github.com/dullage/flatnotes 、https://github.com/dullage/flatnotes/wiki

#### docsify（纯前端）★ 自建方案的现成前端

- 纯客户端 JS（最新 v5.0.0，2026-07-23，活跃）：配任意静态服务器即可；单根目录 + `_sidebar.md` 导航；**客户端每次按需 fetch 原始 md，外部改文件刷新即生效**（R3 ✅）；无 auth/admin（R2 ❌，可反代 basic auth）；mermaid/KaTeX 有插件生态（R5 ✅）；CentOS 7 零压力（R4 ✅）；R1 ❌（侧栏需手工维护）。
- 来源：https://github.com/docsifyjs/docsify/releases 、https://raw.githubusercontent.com/docsifyjs/docsify/develop/docs/configuration.md

#### SilverBullet（Node/TS，Rust 重写中）

- space = **单一目录**（不能索引任意路径，R1 ❌）；内置用户名+密码（R2 ⚠️，"访客只读+管理员编辑"角色分离未在文档确认）；R3 ✅；2.x 已从 Deno 迁回 Node.js（2.6.1 起）且构建前置 Node 24+，glibc 2.17 能否跑**不确定**（R4 ❌/⚠️）；非常活跃（2.10.0，2026-07-28）。
- 来源：https://github.com/silverbulletmd/silverbullet/releases 、https://raw.githubusercontent.com/silverbulletmd/silverbullet/main/bin/silverbullet/src/main.rs （源码）

#### markdown-proxy（Go，19★）

- SSE live reload + Mermaid/KaTeX + 目录列表，但本地模式**只绑 127.0.0.1**，远程模式（绑非环回）会**屏蔽本地文件访问**（SSRF 防护）——无法给内网多用户提供本地 md 展示。排除。
- 来源：https://github.com/patakuti/markdown-proxy

#### 其他快速排除

| 项目 | 排除理由 | 来源 |
|---|---|---|
| grip（Python） | 渲染走 **GitHub Markdown API，必须访问外网 api.github.com**，内网基本不可用；R1 ❌（单文件、无目录索引页）；R2 ❌（`--user/--pass` 是 GitHub API 凭证不是访问控制）；2023-10 后停滞 | https://github.com/joeyespo/grip 、https://pypi.org/pypi/grip/json |
| glow | 纯终端工具，无任何 server/HTTP 模式 | https://github.com/charmbracelet/glow |
| dufs（Rust） | auth 模型本最贴合 R2（路径级 ro/rw），但**无 markdown 渲染**（README 功能列表无此项；issue #475 已关闭未实现） | https://github.com/sigoden/dufs 、https://github.com/sigoden/dufs/issues/475 |
| code-server | VS Code 1.86+ 要求 glibc 2.28 → CentOS 7 冻结在旧版（code-server ≤4.85.x，约 2024 初）；仅全局密码无角色分离；体积数百 MB | https://code.visualstudio.com/updates/v1_86 、https://github.com/coder/code-server/releases/tag/v4.135.0 |
| mdwiki（纯 JS） | 近乎停更（0.7.0，2024-03，此前多年未更）；无 auth、单根目录 | https://github.com/Dynalon/mdwiki/releases/tag/0.7.0 |
| mdserver-web | 同名无关项目：国内服务器运维面板（LNMP 管理），与 markdown 无关 | https://github.com/midoks/mdserver-web |
| PyPI `mdshare` | 同名无关项目：分子动力学（MD）数据集分享工具 | https://pypi.org/project/mdshare/ |

## 5. 横向对比总表

| 候选 | 运行时 | R1 界面索引原始路径 | R2 访客只读+管理员账密 | R3 实时反映外部变更 | R4 CentOS7 nohup | R5 渲染 | 维护状态 |
|---|---|---|---|---|---|---|---|
| **自建（Python + docsify 前端）** | Python | ✅（自实现） | ✅（自实现） | ✅（每请求读盘/轮询） | ✅ | ✅（docsify+插件） | — |
| **wikmd** | Python/Flask | ⚠️ 启动时目录 | ✅（单密码） | ✅ 每请求读盘+watchdog | ✅ | ✅ | 活跃 |
| **mo** | Go 单二进制 | ⚠️ CLI 参数 | ❌ 无认证 | ✅ watch+livereload | ✅ | ✅ 最强（mermaid+KaTeX） | 非常活跃 |
| **Raneto** | Node | ⚠️ 环境变量 | ✅ 用户名+密码 | ✅ 每请求读盘 | ⚠️ 新版要 Node≥23.14（退 0.17.x 或 unofficial-builds） | ✅ | 活跃 |
| Wiki.js 2.x | Node | ❌ DB 为准 | ✅ | ❌（git 定时同步≥5min） | ⚠️ Node22 unofficial | ✅ | 活跃 |
| Gollum | Ruby | ❌ 单 git 仓库 | ⚠️ 需自写中间件 | ❌ 不 commit 不可见 | ⚠️ Ruby≥2.6 | ✅ | 低频 |
| mkdocs serve | Python | ❌ 无界面（symlink 可绕） | ❌ 无 auth | ✅（watch 兜底） | ✅ | ✅ | 存活，发布慢 |
| mdBook | Rust | ❌ src 外路径 panic | ❌ | ⚠️ 仅 watch src | ✅ musl 二进制 | ✅ | 活跃 |
| madness | Ruby ≥3.2 | ⚠️ 启动目录 | ⚠️ 整站 basic auth | ✅ | ⚠️ 自编译 Ruby | ✅ | 活跃 |
| markserv | Node | ⚠️ 启动参数 | ❌ | ✅ | ⚠️ npm 停 2019 | ✅ | 停滞 |
| flatnotes | Python | ⚠️ 启动配置 | ⚠️ 只读/密码二选一 | ✅ | ⚠️ 官方仅 Docker | ✅ | 活跃 |
| docsify（纯前端） | 静态 JS | ❌ 侧栏手工 | ❌ | ✅ | ✅ | ✅ | 活跃 |
| SilverBullet | Node/TS | ❌ 单 space | ⚠️ | ✅ | ❌/不确定 | ✅ | 非常活跃 |
| Outline / BookStack / Docmost / HedgeDoc / Cowyo | Node/PHP/Go | ❌ 内容存 DB | ❌/⚠️ | ❌ | ❌ | — | 活跃但方向错位 |

## 6. 推荐方案与"自建 vs 复用"结论

### 排名

**① 自建：200–400 行 Python 薄后端 + 本地化 docsify 前端（推荐，唯一 100% 满足 R1–R5）**

- 为什么值得自建（两个决定性理由）：
  1. **R1 的"界面动态添加任意路径索引"在全部 20+ 现成候选中零支持**——这是需求与生态的根本错位，不是配置能绕开的。所有工具都是"启动时指定一个根目录"。
  2. R2 的"访客只读免登录 + 管理员用户名+密码可写"双角色组合，在文件型轻量工具里只有 Raneto（撞 Node 23.14 门槛）具备；wikmd 只有单密码。而 R1+R2 恰是本需求的核心。
- 为什么成本低：
  - 后端只需四块功能：索引清单 CRUD（一个 JSON 文件持久化）+ session 认证（管理员账密写配置）+ 按 `safe_join(根路径列表)` 读取 md 原文 + 轮询 mtime 或 watchdog 触发前端刷新（R3 的"手动刷新也行"，逐请求读盘即天然满足）。Flask/FastAPI + markdown-it-py + Pygments，合计约 200–400 行。
  - **前端渲染层不必自研**：直接把 docsify（纯前端、零构建）本地化托管——每次导航 fetch 最新 md 天然满足 R3；mermaid/KaTeX/highlight.js 均可下载为本地静态文件（内网无 CDN，这是唯一要注意的工程点）。R5 直接达标。
- 实施注意：路径安全（所有读盘必须 `safe_join` 且限制在管理员添加的根内，避免目录穿越）；conda 环境装依赖即可，nohup 单进程，完全符合 R4。

**② wikmd（想最快上线、且接受 R1 降级时的现成首选）**

- R2–R5 全 ✅、Python 单进程、`LOCAL_MODE` 自托管静态资源、活跃维护，是现成工具中唯一接近全满足的。R1 缺口有两个折中：(a) 接受"启动时 `WIKI_DIRECTORY` 指定目录 + symlink 汇聚多个任意路径"，改路径需重启；(b) fork 它加一个"索引清单"表——但其内容模型绑定单一 wiki 目录 + git，改造代价与自建相当，收益有限。
- 局限：admin 是单密码而非用户名+密码；知识图谱等自带功能可能用不上。

**③ mo（纯只读展示场景的单二进制方案）**

- 如果"新建/修改/删除"其实可以退化到"管理员直接在服务器上改文件"，只需要给访客一个只读浏览界面，mo 是最轻的：Go 单二进制零依赖、`--watch` + live reload、mermaid/KaTeX 渲染最强。代价是完全无认证，必须靠内网隔离或前置反代 basic auth；且 R1 同样只有 CLI 参数形态。

### 明确结论

**值得自建。** 在 2026 年的方案生态下，"界面添加任意路径索引 + 访客只读/管理员账密 + 外部文件变更实时可见 + CentOS 7 单进程"这个组合不存在现成开源实现——最接近的 wikmd 也缺 R1 的界面化且 admin 形态是单密码。自建的增量成本（1–2 天，200–400 行 Python，渲染复用 docsify 本地化）显著低于 fork/改造任何现有项目（理解其内容模型 + 上游同步负担），且换来对五项需求的完整控制。如果团队希望先验证价值，可以先用 wikmd 跑通 R2–R5，再决定是否替换为自建服务。

---

## 附：来源清单

主要一手来源（正文各表内已逐条标注，此处汇总关键入口）：

- Node glibc：https://raw.githubusercontent.com/nodejs/node/v16.x/BUILDING.md · https://github.com/nodejs/node/blob/v18.x/BUILDING.md · https://nodejs.org/en/blog/announcements/v18-release-announce · https://github.com/nodejs/unofficial-builds
- Gollum：https://github.com/gollum/gollum · https://github.com/gollum/gollum-lib/blob/master/lib/gollum-lib/git_access.rb · https://github.com/gollum/gollum/issues/1031
- Wiki.js：https://docs.requarks.io/install/requirements · https://docs.requarks.io/install/linux · https://docs.requarks.io/storage/git · https://docs.requarks.io/auth · https://docs.requarks.io/rendering
- Outline / BookStack / Docmost / HedgeDoc / Cowyo：https://docs.getoutline.com/s/hosting/doc/requirements-ULdYnwi4wG · https://www.bookstackapp.com/docs/admin/installation/ · https://github.com/docmost/docmost/blob/main/docker-compose.yml · https://docs.hedgedoc.org/configuration/ · https://github.com/schollz/cowyo
- mkdocs / mdBook：https://www.mkdocs.org/user-guide/configuration/ · https://www.mkdocs.org/user-guide/cli/ · https://rust-lang.github.io/mdBook/ · https://github.com/rust-lang/mdBook/releases
- 轻量工具：https://github.com/Linbreux/wikmd · https://github.com/k1LoW/mo · https://github.com/gilbitron/Raneto · https://github.com/DannyBen/madness · https://github.com/markserv/markserv · https://github.com/dullage/flatnotes · https://github.com/docsifyjs/docsify · https://github.com/silverbulletmd/silverbullet · https://github.com/joeyespo/grip · https://github.com/sigoden/dufs · https://github.com/charmbracelet/glow · https://github.com/coder/code-server · https://github.com/Dynalon/mdwiki · https://github.com/patakuti/markdown-proxy
- VS Code glibc 门槛：https://code.visualstudio.com/updates/v1_86
