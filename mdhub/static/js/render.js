/* 渲染管线（纯函数模块，node 冒烟脚本也会加载它）
 * opts.assetPrefix：非空时，md 中的相对图片/链接将重写到该前缀（资源端点） */
(function (global) {
  "use strict";

  function normalizeRel(rel) {
    var out = [];
    rel.split("/").forEach(function (p) {
      if (p === "." || p === "") return;
      if (p === "..") out.pop();
      else out.push(p);
    });
    return out.join("/");
  }

  function isExternal(url) {
    return /^(https?:|data:|mailto:|\/\/|\/|#)/.test(url);
  }

  function createRenderer(markdownit, hljs, opts) {
    opts = opts || {};
    var prefix = opts.assetPrefix || "";
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
    if (prefix) {
      ["image", "link"].forEach(function (rule) {
        var def = md.renderer.rules[rule];
        md.renderer.rules[rule] = function (tokens, idx, options, env, self) {
          var token = tokens[idx];
          var attr = rule === "image" ? "src" : "href";
          var url = token.attrGet(attr);
          if (url && !isExternal(url)) {
            token.attrSet(attr, prefix + normalizeRel(url));
          }
          return def ? def(tokens, idx, options, env, self) : self.renderToken(tokens, idx, options);
        };
      });
    }
    return md;
  }

  function renderMarkdown(text, markdownit, hljs, opts) {
    var md = createRenderer(markdownit, hljs, opts);
    return md.render(text);
  }

  var api = {
    createRenderer: createRenderer,
    renderMarkdown: renderMarkdown,
    normalizeRel: normalizeRel,
  };
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;   // node 冒烟脚本
  } else {
    global.MdRender = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
