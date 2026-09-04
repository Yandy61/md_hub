# 01 — 项目骨架与启停脚本

**What to build:** MarkdownHub 的最小可运行底座：Flask 应用骨架与健康检查端点、config（端口 18123、绑定 0.0.0.0、workspace 路径等）、nohup 启停脚本（start.sh 拉起后写日志到 logs/ 并留 pid 文件，stop.sh 按 pid 干净停止），以及基于 Flask test client 的 pytest 测试 harness（后续所有 ticket 共用的 HTTP seam 从这里建立）。完成后即可"一条命令拉起、内网其他机器可访问"。

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] start.sh 拉起后健康检查端点可访问，日志写入 logs/，pid 文件存在
- [ ] stop.sh 停止后进程退出、pid 文件清理
- [ ] 绑定 0.0.0.0:18123，内网其他机器可访问
- [ ] pytest 测试套件通过（至少含健康检查端点一条，验证 HTTP seam 可用）
- [ ] conda base 环境直跑，pip 依赖仅 flask
