/* 文档缩放：两组独立控件
 * 1) 文字缩放（字号）：改 #doc-body font-size，标题/代码/表格用 em 相对会整体缩放文字
 * 2) 整体缩放（zoom 属性）：连图片一起缩放（Chrome/Edge 全量缩放，Firefox 无此属性则静默降级）
 * 两组均按访客持久化到 localStorage。
 */
(function () {
  var body = document.getElementById("doc-body");
  if (!body) return;

  var base = 15.5;
  try { base = parseFloat(getComputedStyle(body).fontSize) || 15.5; } catch (e) {}

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

  // 文字缩放：字号 60%–180%
  makeControl({ out: "zoom-out", inn: "zoom-in", lvl: "zoom-level" },
    "mdhub-zoom", 60, 180,
    function (pct) { body.style.fontSize = (base * pct / 100).toFixed(1) + "px"; });

  // 整体缩放：zoom 50%–200%
  makeControl({ out: "page-zoom-out", inn: "page-zoom-in", lvl: "page-zoom-level" },
    "mdhub-page-zoom", 50, 200,
    function (pct) { body.style.zoom = pct + "%"; });
})();