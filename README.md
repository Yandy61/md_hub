# MarkdownHub

内网 Markdown 分享服务：引用原始路径（不复制文件）、实时轮询刷新、管理员密码管理、访客零门槛只读。

## 快速开始

```bash
cd ~/data/dev3

# 1. 安装依赖（仅 flask）
pip install -r requirements.txt   # conda base 环境直跑

# 2. 设置管理员密码（首次必须，PBKDF2 哈希写入 data/config.json）
python -m mdhub.cli set_password

# 3. 启动（nohup 后台，日志写 logs/，pid 写 data/mdhub.pid）
./start.sh

# 4. 浏览器访问
#    本机:     http://127.0.0.1:18123
#    内网他机:  http://10.41.167.37:18123

# 5. 停止
./stop.sh
```

## 功能

| 角色 | 能力 |
|---|---|
| 访客（无登录） | 浏览已共享文档列表（按索引根分组、文件名即时过滤）、阅读渲染后的文档（代码高亮/表格/mermaid 图/KaTeX 公式/相对图片）、页面每 4 秒自动刷新 |
| 管理员（右上角登录） | 输入绝对路径添加索引（单文件或整个目录，递归排除 .git/node_modules/隐藏目录）、固定 workspace 新建文件、在线编辑写回原文件（自动备份到 data/backups/，保留 10 份）、删除/取消共享（语义区分：服务新建的文件真删，外部文件仅解除索引，绝不碰原文件） |

## 目录结构

```
dev3/
├── start.sh / stop.sh      # 启停脚本（nohup、日志、pid）
├── mdhub/                  # Flask 应用
│   ├── app.py              # 路由与边界检查（realpath 防穿越/软链越界）
│   ├── registry.py         # 索引存储（JSON 原子写 + 线程锁）
│   ├── scanner.py          # 目录递归扫描（排除规则）
│   ├── reader.py           # UTF-8/GBK 编码兜底；写回保留原编码
│   ├── backup.py           # 写回前备份（sha1 路径键 + 保留 N 份轮转）
│   ├── cli.py              # set_password 命令
│   ├── static/             # 前端（全部本地打包，零 CDN 依赖）
│   │   ├── vendor/         # markdown-it / highlight.js / mermaid / KaTeX / CodeMirror
│   │   └── js/             # render（渲染管线）/ list / doc / editor / admin
│   └── templates/
├── data/                   # 运行期状态（config.json / registry.json / backups/）— 已 gitignore
├── workspace/              # 服务内新建文件的固定目录（config.json 可改）
├── tests/                  # pytest（HTTP seam）+ node 渲染冒烟
└── docs/research/          # 现有方案调研报告
```

## 配置（data/config.json）

```json
{
  "host": "0.0.0.0",
  "port": 18123,
  "workspace": "<项目>/workspace",
  "backup_keep": 10
}
```

改完重启生效（`./stop.sh && ./start.sh`）。

## 测试

```bash
conda activate base
python -m pytest tests/ -q      # 69 个 HTTP seam 测试
node tests/smoke_render.js      # 渲染管线冒烟
```

## 安全边界（内网单人信任场景的设计取舍）

- HTTP 明文（已接受的取舍）；管理员密码 PBKDF2 哈希存储，session cookie HttpOnly + SameSite=Strict
- 资源边界：目录索引服务整棵子树；单文件索引服务同目录；realpath 检查防路径穿越与符号链接越界
- 外部文件只共享不复制、删除只松绑——服务绝不修改/删除索引来源的原文件（服务内新建的除外）
- 访客侧无任何写接口可达（全部管理端点强制鉴权）
