/* 主题选择：body[data-mdtheme] 切换 + localStorage 持久化（按访客各自浏览器记忆） */
(function () {
  var KEY = "mdhub-theme";
  var THEMES = ["clean", "github", "paper", "soft"];

  function apply(t) {
    if (THEMES.indexOf(t) < 0) t = "clean";
    document.body.setAttribute("data-mdtheme", t);
    var sel = document.getElementById("theme-select");
    if (sel) sel.value = t;
  }

  function current() {
    // doc.html 首帧脚本可能已把保存值放到 html 属性上
    var pre = document.documentElement.getAttribute("data-theme-apply");
    if (pre) {
      document.documentElement.removeAttribute("data-theme-apply");
      return pre;
    }
    try { return localStorage.getItem(KEY) || "clean"; } catch (e) { return "clean"; }
  }

  apply(current());

  var sel = document.getElementById("theme-select");
  if (sel) {
    sel.addEventListener("change", function () {
      apply(sel.value);
      try { localStorage.setItem(KEY, sel.value); } catch (e) {}
      // mermaid 已渲染的 SVG 是主题初始化时定格的，切主题后重渲染
      if (window.MdHubDoc && window.MdHubDoc.refresh) { window.MdHubDoc.refresh(); }
    });
  }
})();
