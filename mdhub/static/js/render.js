/* 渲染管线（纯函数模块，node 冒烟脚本也会加载它） */
(function (global) {
  "use strict";

  function createRenderer(markdownit, hljs) {
    var md = markdownit({
      html: false,           // 安全：不渲染原文里的 HTML
      linkify: true,
      typographer: false,
      highlight: function (code, lang) {
        if (lang && hljs.getLanguage(lang)) {
          try {
            return hljs.highlight(code, { language: lang }).value;
          } catch (e) { /* fall through */ }
        }
        return ""; // markdown-it 会转义后包 pre>code
      },
    });
    // 图片相对路径 → 走资源端点（ticket 04 接管具体映射）
    return md;
  }

  function renderMarkdown(text, markdownit, hljs) {
    var md = createRenderer(markdownit, hljs);
    return md.render(text);
  }

  var api = { createRenderer: createRenderer, renderMarkdown: renderMarkdown };
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;   // node 冒烟脚本
  } else {
    global.MdRender = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
