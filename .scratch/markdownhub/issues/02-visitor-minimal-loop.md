# 02 — 访客只读最小闭环

**What to build:** 访客侧的第一条完整路径：registry（JSON 文件、原子写）承载索引条目（稳定 id、原始路径、类型 file）；访客看到文档列表页，点开文档页看到渲染后的 markdown（markdown-it + highlight.js，静态资产全部本地打包由服务提供）；文档读取 UTF-8 为主、GBK 自动兜底；未索引内容对访客完全不可达。此票完成后可用一条手工放入 registry 的单文件索引演示"浏览器读渲染好的文档"。

**Blocked by:** 01 — 项目骨架与启停脚本

**Status:** ready-for-agent

- [x] 手工放置一条单文件索引后，列表页可见、点开渲染正确（标题/表格/列表/代码高亮）——列表与 doc API 已在真实服务验证；渲染管线经 node 冒烟断言（标题/列表/高亮标记/表格/中文）
- [x] GBK 编码的 md 文件正常渲染（后端兜底有 seam 测试；渲染层 markdown-it 输入为解码后文本）
- [x] 未索引路径对访客不可见且不可达（doc 仅按 registry 条目解析 + traversal 拒绝，有 seam 测试）
- [x] 所有前端资产来自本服务，页面无任何 CDN 请求（页面测试断言）
- [x] HTTP seam 测试覆盖：列表、文档原文、不存在条目、非 UTF-8 兜底
