/* 文档页：拉取文档 → 渲染 → 轮询刷新 */
(function () {
  var pathEl = document.getElementById("doc-path");
  var bodyEl = document.getElementById("doc-body");
  var entryId = window.location.pathname.split("/")[2];
  var currentMtime = 0, currentSize = 0;

  function fetchDoc() {
    return fetch("/api/doc/" + entryId + "/").then(function (r) {
      if (r.status === 404) { throw new Error("missing"); }
      return r.json();
    });
  }

  function showMissing() {
    bodyEl.innerHTML = '<p class="missing">⚠ 源丢失：文件可能已被移动或删除。</p>';
  }

  function assetPrefix() {
    // /doc/<eid>/<rel> → /api/asset/<eid>/<dir(rel)>/
    var parts = window.location.pathname.split("/");
    var eid = parts[2];
    var rel = parts.slice(3).filter(Boolean).join("/");
    var dir = rel.slice(0, rel.lastIndexOf("/") + 1);
    return "/api/asset/" + eid + "/" + dir;
  }

  function draw(data) {
    currentMtime = data.mtime; currentSize = data.size;
    pathEl.textContent = data.path;
    bodyEl.innerHTML = MdRender.renderMarkdown(data.text, window.markdownit, window.hljs,
      { assetPrefix: assetPrefix() });
  }

  function poll() {
    fetchDoc().then(function (d) {
      if (d.mtime !== currentMtime || d.size !== currentSize) { draw(d); }
    }).catch(function () { showMissing(); });
  }

  fetchDoc().then(draw).catch(function () {
    showMissing();
    // 源恢复后自动回归
    setInterval(poll, 4000);
  });
  setInterval(poll, 4000);
})();
