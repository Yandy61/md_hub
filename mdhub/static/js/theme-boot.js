/* 主题清单的唯一权威来源：首帧脚本与 theme.js 都从这里读。
 * 新增主题 = 在 THEMES 加 id + 在 mdhub.css 加变量块（theme.js 的下拉 label 也在此维护） */
(function () {
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
  var DARK = { "paper-dark": 1, midnight: 1, onyx: 1, jade: 1, grape: 1, mocha: 1, ocean: 1, ember: 1 };

  // 首帧应用：读取 localStorage → 校验 → 挂 <html>（CSS 变量立即生效）→ 明暗联动 hljs/cm
  function boot() {
    var t = "clean";
    try { t = localStorage.getItem("mdhub-theme") || t; } catch (e) {}
    var valid = false;
    for (var i = 0; i < THEMES.length; i++) if (THEMES[i].id === t) { valid = true; break; }
    if (!valid) { t = "clean"; }
    document.documentElement.setAttribute("data-mdtheme", t);
    var hl = document.getElementById("hljs-css");
    if (hl) { hl.href = DARK[t] ? "/static/vendor/hljs-github-dark.css" : "/static/vendor/hljs-github.css"; }
    var cm = document.getElementById("cm-theme-css");
    if (cm) { cm.disabled = !DARK[t]; }
  }

  // 暴露给 theme.js（避免清单多处维护）
  window.MdHubThemes = { THEMES: THEMES, DARK: DARK, boot: boot };

  boot();
})();
