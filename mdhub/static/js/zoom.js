/* 文档缩放：调整 #doc-body 字号（标题/代码/表格均用 em 相对，会整体缩放），按访客持久化 */
(function () {
  var MIN = 60, MAX = 180, STEP = 10, DEFAULT = 100, KEY = "mdhub-zoom";
  var body = document.getElementById("doc-body");
  var out = document.getElementById("zoom-out");
  var inn = document.getElementById("zoom-in");
  var lvl = document.getElementById("zoom-level");
  if (!body || !out || !inn || !lvl) return;

  // 基准字号从 CSS 读（对应 mdhub.css 的 #doc-body font-size），避免硬编码不同步
  var base = 15.5;
  try { base = parseFloat(getComputedStyle(body).fontSize) || 15.5; } catch (e) {}

  var pct = DEFAULT;
  try { pct = parseInt(localStorage.getItem(KEY), 10) || DEFAULT; } catch (e) {}

  function clamp(v) { return Math.min(MAX, Math.max(MIN, v)); }

  function render() {
    body.style.fontSize = (base * pct / 100).toFixed(1) + "px";
    lvl.textContent = pct + "%";
  }

  function set(v) {
    pct = clamp(v || DEFAULT);
    try { localStorage.setItem(KEY, String(pct)); } catch (e) {}
    render();
  }

  out.addEventListener("click", function () { set(pct - STEP); });
  inn.addEventListener("click", function () { set(pct + STEP); });
  lvl.addEventListener("click", function () { set(DEFAULT); });

  render();
})();