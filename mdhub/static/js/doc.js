/* 文档页：拉取文档 → 渲染 → 轮询刷新（源修改自动重渲染，源丢失显示提示、恢复自动回归） */
(function () {
  var pathEl = document.getElementById("doc-path");
  var bodyEl = document.getElementById("doc-body");
  var P = MdRender.apiParts(window.location.pathname); // entryId/subpath 透传，目录条目靠它定位
  var currentMtime = 0, currentSize = 0;
  var missing = false;

  function fetchDoc() {
    return fetch(P.docUrl).then(function (r) {
      if (r.status !== 200) { throw new Error("missing"); }
      return r.json();
    });
  }

  function showMissing() {
    if (!missing) {
      missing = true;
      bodyEl.innerHTML = '<p class="missing">⚠ 源丢失：文件可能已被移动或删除，恢复后本页自动回归。</p>';
    }
  }

  function draw(data) {
    missing = false;
    currentMtime = data.mtime; currentSize = data.size;
    pathEl.textContent = data.path;
    bodyEl.innerHTML = MdRender.renderMarkdown(data.text, window.markdownit, window.hljs, {
      assetPrefix: P.assetPrefix,
      docBase: P.docBase,
    });
    MdRender.enhance(bodyEl);
  }

  function poll() {
    if (window.MdHubEditor && window.MdHubEditor.pausePoll()) { return; } // 编辑中暂停
    fetchDoc().then(function (d) {
      if (missing || d.mtime !== currentMtime || d.size !== currentSize) { draw(d); }
    }).catch(showMissing);
  }

  fetchDoc().then(draw).catch(showMissing);
  setInterval(poll, 4000);

  // 保存后立即重绘
  window.MdHubDoc = {
    refresh: function () {
      fetchDoc().then(draw).catch(showMissing);
    },
  };
})();
