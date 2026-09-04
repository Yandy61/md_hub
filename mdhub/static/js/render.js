/* 渲染管线（纯函数模块，node 冒烟脚本也会加载它）
 * opts.assetPrefix：非空时，md 中的相对图片/链接将重写到该前缀（资源端点） */
(function (global) {
  "use strict";

  function assetUrl(prefix, rel) {
    // 相对文档目录的路径 → 资源端点 URL。
    // 去掉 "." 与空段；保留 ".." 语义交给服务端边界判定；分段编码保证 URL 合法。
    var segs = rel.split("/").filter(function (p) { return p !== "." && p !== ""; });
    return prefix + segs.map(encodeURIComponent).join("/");
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
      // image 与 link_open 两种 token 携带 src/href
      [["image", "src"], ["link_open", "href"]].forEach(function (pair) {
        var rule = pair[0], attr = pair[1];
        var def = md.renderer.rules[rule];
        md.renderer.rules[rule] = function (tokens, idx, options, env, self) {
          var token = tokens[idx];
          var url = token.attrGet(attr);
          if (url && !isExternal(url)) {
            token.attrSet(attr, assetUrl(prefix, url));
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
    assetUrl: assetUrl,
  };
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;   // node 冒烟脚本
  } else {
    global.MdRender = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
