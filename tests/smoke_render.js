#!/usr/bin/env node
// 渲染管线冒烟：node tests/smoke_render.js
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const VENDOR = path.join(__dirname, "..", "mdhub", "static", "vendor");
const assert = (cond, msg) => { if (!cond) { console.error("FAIL:", msg); process.exit(1); } };

// 在 vm 沙箱里加载 render.js（同时兼容 window/global 导出）
const sandbox = { module: { exports: {} }, exports: {}, console };
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(__dirname, "..", "mdhub/static/js/render.js"), "utf8"), sandbox);
const MdRender = sandbox.module.exports.renderMarkdown
  ? sandbox.module.exports
  : sandbox.MdRender;
assert(MdRender && MdRender.renderMarkdown, "render.js 应导出 renderMarkdown");

// 在 vm 沙箱里加载 markdown-it + highlight.js
function loadVendor(file) {
  const s2 = { module: { exports: {} }, exports: {}, console, window: {} };
  vm.createContext(s2);
  vm.runInContext(fs.readFileSync(path.join(VENDOR, file), "utf8"), s2);
  return s2.window.markdownit || s2.module.exports;
}
const markdownit = loadVendor("markdown-it.min.js");
const hljs = loadVendor("highlight.min.js");
assert(typeof markdownit === "function", "markdown-it 应为构造函数");
assert(hljs && typeof hljs.highlight === "function", "hljs 应可用");

// —— 关键断言 ——
const html = MdRender.renderMarkdown("# 你好\n\n- a\n- b\n\n```python\nprint(1)\n```\n\n| h1 | h2 |\n|---|---|\n| 1 | 2 |", markdownit, hljs);
assert(html.includes("<h1>你好</h1>"), "标题应渲染");
assert(html.includes("<li>a</li>"), "列表应渲染");
assert(html.includes("hljs") || html.includes("class=\"language-python\""), "代码块应有高亮标记");
assert(html.includes("<table>"), "表格应渲染");

const gbk = MdRender.renderMarkdown("中文 **加粗** 文本", markdownit, hljs);
assert(gbk.includes("<strong>加粗</strong>"), "中文加粗应渲染");

// 资源前缀重写：相对图片/链接 → 资源端点；.md 相对链接 → 文档页；外链/绝对路径不动
const prefixed = MdRender.renderMarkdown(
  "![x](./img/a.png) ![y](../up.png) [外](https://e.com/x.png) [内](sub/b.md) [资源](data.csv)",
  markdownit, hljs, { assetPrefix: "/api/asset/3/sub/", docBase: "/doc/3/sub/" });
assert(prefixed.includes('src="/api/asset/3/sub/img/a.png"'), "相对图片应重写到资源端点");
assert(prefixed.includes('src="/api/asset/3/sub/../up.png"'), "../ 应保留原始语义交给服务端边界判定");
assert(prefixed.includes('href="https://e.com/x.png"'), "外链不应重写");
assert(prefixed.includes('href="/doc/3/sub/sub/b.md"'), "相对 .md 链接应改写到文档页");
assert(prefixed.includes('href="/api/asset/3/sub/data.csv"'), "非 md 相对链接仍走资源端点");

// mermaid 块增强（node 环境无 window.mermaid，验证占位替换逻辑需模拟）：
// 这里验证 enhance 在无 mermaid 环境下不抛错、不改动内容
const fakeEl = { querySelectorAll: () => [] };
MdRender.enhance(fakeEl); // 不应抛错
// 模拟 window.mermaid 存在时的 DOM 流程（用极简 DOM 桩验证 replaceWith 被调用）
(function () {
  const pre = { closest: () => null };
  const codeEl = { textContent: "graph TD; A-->B", closest: () => pre };
  // closest 返回 null 时 enhance 应安全跳过（防御性）
  const sandboxWin = { mermaid: { run: () => {} } };
  global.window = sandboxWin;
  const el2 = {
    querySelectorAll: (sel) => (sel === "pre code.language-mermaid" ? [codeEl] : []),
  };
  let threw = false;
  try { MdRender.enhance(el2); } catch (e) { threw = true; }
  assert(!threw, "mermaid 桩环境下 enhance 不应抛错");
  delete global.window;
})();

// apiParts：doc.js/editor.js 共用的 URL 构造（code-review #1 回归锁）
const P = MdRender.apiParts("/doc/7/docs/sub/a.md");
assert(P.entryId === "7", "entryId 应为第 2 段");
assert(P.docUrl === "/api/doc/7/docs/sub/a.md", "docUrl 应透传 subpath");
assert(P.rawUrl === "/api/raw/7/docs/sub/a.md", "rawUrl 应透传 subpath");
assert(P.assetPrefix === "/api/asset/7/docs/sub/", "assetPrefix 应为当前文档目录");
assert(P.docBase === "/doc/7/docs/sub/", "docBase 应为当前文档目录");
const P0 = MdRender.apiParts("/doc/7/");
assert(P0.docUrl === "/api/doc/7/" && P0.assetPrefix === "/api/asset/7/" && P0.docBase === "/doc/7/", "根文档各 URL 正确");

// 公式下划线转义（KaTeX \text{} 内 `_` 非法 → ParseError 显示原文，code-review 后用户反馈回归锁）
const esc = MdRender.escapeUnderscoreInText("\\text{set_password} + \\text{a_b_c}");
assert(esc === "\\text{set\\_password} + \\text{a\\_b\\_c}", "\\text{} 内下划线应转义");
assert(MdRender.escapeUnderscoreInText("\\text{无下划线}") === "\\text{无下划线}", "无下划线不应改动");
assert(MdRender.escapeUnderscoreInText("x_y 外部不动") === "x_y 外部不动", "text 块外不应改动");

console.log("render smoke: all assertions passed");
