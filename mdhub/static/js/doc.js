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

  function isHtmlPath(path) {
    return /\.html?$/i.test(path || "");
  }

  function draw(data) {
    missing = false;
    currentMtime = data.mtime; currentSize = data.size;
    pathEl.textContent = data.path;
    if (isHtmlPath(data.path)) {
      // HTML 文档：iframe 沙箱渲染（样式隔离，脚本随 sandbox 属性受限执行）
      drawHtml(data);
      return;
    }
    bodyEl.innerHTML = MdRender.renderMarkdown(data.text, window.markdownit, window.hljs, {
      assetPrefix: P.assetPrefix,
      docBase: P.docBase,
    });
    MdRender.enhance(bodyEl);
  }

  function drawHtml(data) {
    // 相对资源（css/js/img）经 srcdoc 内无法直接解析，改为 blob URL 上下文：
    // 通过 /doc/ 相对链接重写后，iframe 内相对路径自然落在 /doc/<eid>/<dir>/ 下由资源端点服务。
    var blob = new Blob([data.text], { type: "text/html" });
    if (drawHtml.prevUrl) { URL.revokeObjectURL(drawHtml.prevUrl); }
    drawHtml.prevUrl = URL.createObjectURL(blob);
    // iframe 高度跟随内容：用 scroll 事件近似自适应
    bodyEl.innerHTML = '<iframe id="html-frame" class="html-frame" sandbox="allow-same-origin"></iframe>';
    var frame = document.getElementById("html-frame");
    frame.src = drawHtml.prevUrl;
    frame.addEventListener("load", function () {
      try {
        var d = frame.contentDocument;
        if (d && d.body) { frame.style.height = Math.max(400, d.body.scrollHeight + 40) + "px"; }
      } catch (e) { /* 跨域沙箱则保持默认高度 */ }
    });
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
