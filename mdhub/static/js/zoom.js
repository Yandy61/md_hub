/* 文档缩放：两组独立控件
 * 1) 整体缩放（zoom 属性）：连图片/图表/公式一起缩放（Chrome/Edge 全量缩放，Firefox 静默降级）
 * 2) 文档宽度：内容栏 max-width = 主题默认宽度 × 1.4 × 比例；100% 刻度即主题默认的 1.4 倍
 * 均按访客持久化到 localStorage。
 */
(function () {
  var body = document.getElementById("doc-body");
  if (!body) return;

  function makeControl(ids, key, min, max, apply) {
    var out = document.getElementById(ids.out);
    var inn = document.getElementById(ids.inn);
    var lvl = document.getElementById(ids.lvl);
    if (!out || !inn || !lvl) return;

    var step = 10;
    var pct = 100;
    try { pct = parseInt(localStorage.getItem(key), 10) || 100; } catch (e) {}
    pct = Math.min(max, Math.max(min, pct));

    function render() { apply(pct); lvl.textContent = pct + "%"; }
    function set(v) {
      pct = Math.min(max, Math.max(min, v || 100));
      try { localStorage.setItem(key, String(pct)); } catch (e) {}
      render();
    }
    out.addEventListener("click", function () { set(pct - step); });
    inn.addEventListener("click", function () { set(pct + step); });
    lvl.addEventListener("click", function () { set(100); });
    render();
  }

  // 整体缩放：zoom 50%–200%
  makeControl({ out: "page-zoom-out", inn: "page-zoom-in", lvl: "page-zoom-level" },
    "mdhub-page-zoom", 50, 200,
    function (pct) { body.style.zoom = pct + "%"; });

  // 文档宽度：内容栏 max-width = 主题默认宽度 × WIDEN × 比例。
  // 刻度重标定：100% = 主题默认的 1.4 倍（原 140% 的宽度成为新默认）。
  var container = document.querySelector(".doc-container");
  if (container) {
    var WIDEN = 1.4;
    var baseW = 860;
    try { baseW = parseFloat(getComputedStyle(container).maxWidth) || 860; } catch (e) {}
    baseW *= WIDEN;
    // 一次性迁移：旧刻度值换算到新刻度（旧 140 → 新 100），避免已调宽用户刷后变 196%
    try {
      if (!localStorage.getItem("mdhub-width-v2")) {
        var oldPct = parseInt(localStorage.getItem("mdhub-width"), 10);
        if (oldPct) { localStorage.setItem("mdhub-width", String(Math.round(oldPct / WIDEN))); }
        localStorage.setItem("mdhub-width-v2", "1");
      }
    } catch (e) {}
    makeControl({ out: "width-out", inn: "width-in", lvl: "width-level" },
      "mdhub-width", 50, 300,
      function (pct) { container.style.maxWidth = (baseW * pct / 100).toFixed(0) + "px"; });
  }
})();