/* 列表页：拉取 /api/list 渲染文档列表，客户端即时过滤 */
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
      root.textContent = e.path;
      block.appendChild(root);
      var ul = document.createElement("ul");
      ul.className = "file-list";
      if (e.type === "file") {
        if (e.missing) {
          ul.innerHTML = '<li><span class="name missing">⚠ 源丢失</span><span class="meta"></span></li>';
        } else if (!kw || e.path.toLowerCase().indexOf(kw) >= 0) {
          var li = document.createElement("li");
          li.innerHTML = '<span class="name"><a href="/doc/' + e.id + '/"></a></span>' +
            '<span class="meta"></span>';
          li.querySelector("a").textContent = e.path.split("/").pop();
          li.querySelector(".meta").textContent = fmtTime(e.mtime);
          ul.appendChild(li);
        }
      }
      block.appendChild(ul);
      container.appendChild(block);
    });
  }

  function load() {
    fetch("/api/list").then(function (r) { return r.json(); }).then(function (data) {
      rawData = data;
      render();
    });
  }

  filterBox.addEventListener("input", render);
  load();
})();
