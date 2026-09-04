# 06 — mermaid + KaTeX 渲染

**What to build:** 渲染管线扩展支持图表与公式：本地打包 mermaid 与 KaTeX，mermaid 代码块渲染为图，行内/块级数学公式渲染；node 冒烟脚本验证渲染管线（md→HTML 的关键产物断言）。仍保持零 CDN 依赖。

**Blocked by:** 02 — 访客只读最小闭环

**Status:** ready-for-agent

- [ ] mermaid 代码块渲染为图表
- [ ] 行内与块级公式渲染正确
- [ ] node 冒烟脚本覆盖渲染管线关键断言并纳入测试流程
- [ ] 无 CDN 请求，资产本地打包
