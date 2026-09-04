/* 列表页：按索引根分组、目录树形展示、客户端即时过滤、更新时间 */
(function () {
  var filterBox = document.getElementById("filter");
  var container = document.getElementById("entries");
  var rawData = null;

  function fmtTime(ts) {
    if (!ts) return "";
    var d = new Date(ts * 1000);
    function p(n) { return (n < 10 ? "0" : "") + n; }
    return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()) +
      " " + p(d.getHours()) + ":" + p(d.getMinutes());
  }

  var isAdmin = false;
  if (window.MdHubAdmin && window.MdHubAdmin.refreshMe) {
    window.MdHubAdmin.refreshMe(function (authed) { isAdmin = authed; render(); });
  }

  function matchKw(name, kw) {
    return !kw || name.toLowerCase().indexOf(kw) >= 0;
  }

  function fileLi(href, name, meta, missing, entryId, entry) {
    var li = document.createElement("li");
    if (missing) {
      li.innerHTML = '<span class="name missing">⚠ 源丢失</span><span class="meta"></span>';
      return li;
    }
    var a = document.createElement("a");
    a.href = href;
    a.textContent = name;
    var nameSpan = document.createElement("span");
    nameSpan.className = "name";
    nameSpan.appendChild(a);
    var metaSpan = document.createElement("span");
    metaSpan.className = "meta";
    metaSpan.textContent = meta;
    li.appendChild(nameSpan);
    li.appendChild(metaSpan);
    if (isAdmin && entryId) {
      var btn = document.createElement("button");
      var isWsFile = entry && entry.workspace;
      btn.className = "btn-unshare";
      btn.textContent = isWsFile ? "删除" : "取消共享";
      btn.addEventListener("click", function () {
        if (window.MdHubAdmin) { window.MdHubAdmin.removeEntry(entryId, isWsFile); }
      });
      li.appendChild(btn);
    }
    return li;
  }

  function render() {
    var kw = filterBox.value.trim().toLowerCase();
    container.innerHTML = "";
    if (!rawData || !rawData.entries.length) {
      container.innerHTML = '<div class="empty-hint">暂无共享文档（管理员登录后可添加索引）</div>';
      return;
    }
    rawData.entries.forEach(function (e) {
      var block = document.createElement("div");
      block.className = "entry-block";
      var root = document.createElement("div");
      root.className = "entry-root";
      root.textContent = e.path + (e.missing ? "  ⚠ 源丢失" : "");
      block.appendChild(root);
      var ul = document.createElement("ul");
      ul.className = "file-list";
      if (e.type === "file") {
        if (e.missing || matchKw(e.path, kw)) {
          ul.appendChild(fileLi("/doc/" + e.id + "/", e.path.split("/").pop(),
            fmtTime(e.mtime), e.missing, e.id, e));
        }
      } else if (e.type === "dir" && !e.missing) {
        var shown = 0;
        e.files.forEach(function (f) {
          if (!matchKw(f.rel, kw)) return;
          shown++;
          var name = f.rel.split("/").pop();
          var meta = f.rel.indexOf("/") >= 0
            ? f.rel.slice(0, f.rel.lastIndexOf("/")) + " · " + fmtTime(f.mtime)
            : fmtTime(f.mtime);
          ul.appendChild(fileLi("/doc/" + e.id + "/" + f.rel, name, meta, false, null));
        });
        if (!shown && kw) {
          ul.innerHTML = '<li><span class="meta">（无匹配文件）</span></li>';
        }
      }
      block.appendChild(ul);
      container.appendChild(block);
    });
  }

  function load() {
    return fetch("/api/list").then(function (r) { return r.json(); }).then(function (data) {
      rawData = data;
      render();
    });
  }

  // 暴露给 admin.js：索引变更后刷新列表
  window.MdHubList = { reload: load };

  filterBox.addEventListener("input", render);
  load();
  // 轮询：目录新增/删除文件、源丢失与恢复自动反映
  setInterval(load, 4000);
})();
