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

// 资源前缀重写：相对图片/链接 → 资源端点；外链/绝对路径不动
const prefixed = MdRender.renderMarkdown(
  "![x](./img/a.png) ![y](../up.png) [外](https://e.com/x.png) [内](sub/b.md)",
  markdownit, hljs, { assetPrefix: "/api/asset/3/sub/" });
assert(prefixed.includes('src="/api/asset/3/sub/img/a.png"'), "相对图片应重写到资源端点");
assert(prefixed.includes('src="/api/asset/3/up.png"'), "../ 应归一化");
assert(prefixed.includes('src="https://e.com/x.png"'), "外链图片不应重写");
assert(prefixed.includes('href="/api/asset/3/sub/sub/b.md"'), "相对链接应重写");

console.log("render smoke: all assertions passed");
