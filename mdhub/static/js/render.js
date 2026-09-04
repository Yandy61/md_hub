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

  function isMarkdownLink(url) {
    return /\.md$/i.test(url.split("#")[0]);
  }

  // 从 /doc/<eid>/<subpath...> 解构出各 API URL（doc.js 与 editor.js 共用）
  function apiParts(pathname) {
    var parts = pathname.split("/").filter(Boolean);
    var eid = parts[1] || "";
    var sub = parts.slice(2).join("/");
    var suffix = sub ? "/" + sub : "/";
    var dir = sub.slice(0, sub.lastIndexOf("/") + 1);
    return {
      entryId: eid,
      subpath: sub,
      docUrl: "/api/doc/" + eid + suffix,
      rawUrl: "/api/raw/" + eid + suffix,
      assetPrefix: "/api/asset/" + eid + "/" + dir,
      docBase: "/doc/" + eid + "/" + dir,
    };
  }

  function createRenderer(markdownit, hljs, opts) {
    opts = opts || {};
    var prefix = opts.assetPrefix || "";
    var docBase = opts.docBase || "";
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
      // image src → 资源端点；相对 .md 链接 → 文档页（渲染+轮询）；其余链接 → 资源端点下载
      [["image", "src", false], ["link_open", "href", true]].forEach(function (item) {
        var rule = item[0], attr = item[1], isLink = item[2];
        var def = md.renderer.rules[rule];
        md.renderer.rules[rule] = function (tokens, idx, options, env, self) {
          var token = tokens[idx];
          var url = token.attrGet(attr);
          if (url && !isExternal(url)) {
            if (isLink && docBase && isMarkdownLink(url)) {
              token.attrSet(attr, docBase + url);
            } else {
              token.attrSet(attr, assetUrl(prefix, url));
            }
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

  // 渲染后的后处理：mermaid 代码块转图表容器、KaTeX 渲染公式。
  // 在浏览器里调用（依赖 window.mermaid / window.renderMathInElement）；
  // node 冒烟环境不注入这两个全局，函数自动跳过。
  var mermaidInited = false;

  function initMermaid() {
    if (mermaidInited || !window.mermaid) return;
    var font = '-apple-system, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif';
    window.mermaid.initialize({
      startOnLoad: false,          // 渲染时机由 enhance() 控制
      theme: "base",
      fontFamily: font,
      themeVariables: {
        fontFamily: font,
        fontSize: "14px",
        primaryColor: "#eef2ff",       // 节点底色：淡靛蓝
        primaryTextColor: "#1f2328",
        primaryBorderColor: "#c7d2fe",
        lineColor: "#94a3b8",
        secondaryColor: "#f6f8fa",
        tertiaryColor: "#ffffff",
        noteBkgColor: "#fffbeb",
        noteBorderColor: "#fde68a",
      },
      flowchart: { curve: "basis", padding: 12, nodeSpacing: 40, rankSpacing: 44 },
    });
    mermaidInited = true;
  }

  // KaTeX 的 \text{} 里 `_` 非法（ParseError → 显示原文）。markdown 已把 \_ 吃成 _，
  // 这里在解析前把 \text{...} 内部的 _ 转回 \_。
  function escapeUnderscoreInText(math) {
    return math.replace(/\\text\s*\{([^{}]*)\}/g, function (m, inner) {
      return "\\text{" + inner.replace(/_/g, "\\_") + "}";
    });
  }

  function enhance(el) {
    var hasMermaid = typeof window !== "undefined" && window.mermaid;
    var hasKatex = typeof window !== "undefined" && window.renderMathInElement;
    if (hasMermaid) {
      initMermaid();
      var blocks = el.querySelectorAll("pre code.language-mermaid");
      blocks.forEach(function (b) {
        var div = document.createElement("div");
        div.className = "mermaid";
        div.textContent = b.textContent;
        b.closest("pre").replaceWith(div);
      });
      try { window.mermaid.run({ nodes: el.querySelectorAll(".mermaid") }); } catch (e) { /* ignore */ }
    }
    if (hasKatex) {
      try {
        window.renderMathInElement(el, {
          delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "\\[", right: "\\]", display: true },
            { left: "$", right: "$", display: false },
            { left: "\\(", right: "\\)", display: false },
          ],
          throwOnError: false,
          preProcess: escapeUnderscoreInText,
        });
      } catch (e) { /* ignore */ }
    }
  }

  var api = {
    createRenderer: createRenderer,
    renderMarkdown: renderMarkdown,
    assetUrl: assetUrl,
    enhance: enhance,
    apiParts: apiParts,
    escapeUnderscoreInText: escapeUnderscoreInText,
  };
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;   // node 冒烟脚本
  } else {
    global.MdRender = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
