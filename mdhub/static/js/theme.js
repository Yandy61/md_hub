/* 主题选择：12 套渲染主题（7 浅 + 5 暗），body[data-mdtheme] 切换 + localStorage 持久化。
 * 暗色主题联动切换代码高亮（hljs）与编辑器主题（CodeMirror）。 */
(function () {
  var KEY = "mdhub-theme";
  var THEMES = [
    { id: "clean", label: "清爽" },
    { id: "github", label: "GitHub" },
    { id: "paper", label: "书卷" },
    { id: "soft", label: "暖沙" },
    { id: "paper-dark", label: "书卷·暗" },
    { id: "midnight", label: "靛夜" },
    { id: "onyx", label: "纯黑 OLED" },
    { id: "jade", label: "墨玉" },
    { id: "grape", label: "葡萄紫" },
    { id: "mocha", label: "摩卡" },
    { id: "ocean", label: "蔚海" },
    { id: "ember", label: "暖砖" },
  ];
  var DARK = { midnight: 1, onyx: 1, jade: 1, grape: 1, mocha: 1, ocean: 1, ember: 1, "paper-dark": 1 };

  function apply(t) {
    var theme = null;
    for (var i = 0; i < THEMES.length; i++) if (THEMES[i].id === t) theme = THEMES[i];
    if (!theme) { theme = THEMES[0]; t = theme.id; }
    document.body.setAttribute("data-mdtheme", t);
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
    var pre = document.documentElement.getAttribute("data-theme-apply");
    if (pre) {
      document.documentElement.removeAttribute("data-theme-apply");
      return pre;
    }
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

  apply(current());
})();
