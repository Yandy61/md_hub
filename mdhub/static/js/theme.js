/* 主题切换：从 theme-boot.js 读取权威清单，负责下拉框/切换/持久化/联动。
 * 首帧应用由 theme-boot.js 在 head 里完成，这里只在用户切换时接手。 */
(function () {
  var KEY = "mdhub-theme";
  var meta = window.MdHubThemes || { THEMES: [{ id: "clean", label: "清爽" }], DARK: {} };
  var THEMES = meta.THEMES;
  var DARK = meta.DARK;

  function apply(t) {
    var theme = null;
    for (var i = 0; i < THEMES.length; i++) if (THEMES[i].id === t) theme = THEMES[i];
    if (!theme) { theme = THEMES[0]; t = theme.id; }
    // 主题变量挂 <html>（首帧脚本已可能设过，这里保持同步）
    document.documentElement.setAttribute("data-mdtheme", t);
    document.body.setAttribute("data-scheme", DARK[t] ? "dark" : "light");
    // 代码高亮明暗联动
    var hl = document.getElementById("hljs-css");
    if (hl) {
      hl.href = DARK[t]
        ? "/static/vendor/hljs-github-dark.css"
        : "/static/vendor/hljs-github.css";
    }
    // CodeMirror 编辑器明暗联动（material-darker 仅暗色启用）
    var cm = document.getElementById("cm-theme-css");
    if (cm) { cm.disabled = !DARK[t]; }
    var sel = document.getElementById("theme-select");
    if (sel) sel.value = t;
    document.dispatchEvent(new CustomEvent("mdthemechange", { detail: { id: t, dark: !!DARK[t] } }));
  }

  function current() {
    // 首帧脚本已把主题应用到 <html>，直接读取
    var pre = document.documentElement.getAttribute("data-mdtheme");
    if (pre) { return pre; }
    try { return localStorage.getItem(KEY) || "clean"; } catch (e) { return "clean"; }
  }

  // 生成下拉选项
  var sel = document.getElementById("theme-select");
  if (sel) {
    sel.innerHTML = "";
    THEMES.forEach(function (th) {
      var opt = document.createElement("option");
      opt.value = th.id;
      opt.textContent = (DARK[th.id] ? "◐ " : "") + th.label;
      sel.appendChild(opt);
    });
    sel.addEventListener("change", function () {
      apply(sel.value);
      try { localStorage.setItem(KEY, sel.value); } catch (e) {}
      // mermaid SVG 是初始化时定格的，切明暗后重渲染
      if (window.MdHubDoc && window.MdHubDoc.refresh) { window.MdHubDoc.refresh(); }
    });
  }

  // 同步 scheme（首帧只设了 html 上的主题，scheme 供 mermaid/editor 判断）
  apply(current());
})();
