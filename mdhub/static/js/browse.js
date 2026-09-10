/* 目录选择器：从 home 浏览目录/文件，选中后填入「添加索引」的路径输入框 */
(function () {
  var modal = document.getElementById("browse-modal");
  var btn = document.getElementById("browse-btn");
  if (!modal || !btn) return;

  function el(id) { return document.getElementById(id); }
  var listEl = el("browse-list");
  var currentParent = "";

  function open() { modal.hidden = false; load(""); }
  function close() { modal.hidden = true; }

  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function load(path) {
    var url = "/api/browse";
    if (path) { url += "?path=" + encodeURIComponent(path); }
    fetch(url).then(function (r) {
      if (r.status === 401) { window.location.href = "/"; return null; }
      return r.json();
    }).then(function (data) {
      if (!data) return;
      el("browse-current").textContent = data.current;
      currentParent = data.parent || "";
      render(data);
    });
  }

  function render(data) {
    listEl.innerHTML = "";
    if (!data.dirs.length && !data.files.length) {
      listEl.innerHTML = '<div class="browse-empty">（空目录）</div>';
      return;
    }
    data.dirs.forEach(function (d) {
      var item = document.createElement("button");
      item.className = "browse-item";
      item.innerHTML = '<span class="icon">📁</span><span>' + esc(d.name) + '</span>';
      item.addEventListener("click", function () { load(d.path); });
      listEl.appendChild(item);
    });
    data.files.forEach(function (f) {
      var item = document.createElement("button");
      item.className = "browse-item";
      item.innerHTML = '<span class="icon">📄</span><span>' + esc(f.name) + '</span>';
      item.addEventListener("click", function () {
        el("entry-path").value = f.path;
        close();
      });
      listEl.appendChild(item);
    });
  }

  btn.addEventListener("click", open);
  el("browse-close").addEventListener("click", close);
  el("browse-up").addEventListener("click", function () {
    if (currentParent) { load(currentParent); }
  });
  el("browse-root").addEventListener("click", function () { load(""); });
  el("browse-choose-dir").addEventListener("click", function () {
    el("entry-path").value = el("browse-current").textContent;
    close();
  });
  // 点击遮罩关闭
  modal.addEventListener("click", function (e) {
    if (e.target === modal) { close(); }
  });
})();