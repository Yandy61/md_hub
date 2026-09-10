/* 管理区：新增索引、新建文件、取消共享/删除、登出。登录已移到 login.html。 */
(function () {
  function el(id) { return document.getElementById(id); }

  function api(method, url, body) {
    return fetch(url, {
      method: method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    }).then(function (r) {
      return r.json().then(function (data) { return { status: r.status, data: data }; });
    });
  }

  function refreshMe(cb) {
    api("GET", "/api/me").then(function (res) {
      if (!res.data.authenticated) { window.location.href = "/"; return; }
      if (cb) cb(true);
    });
  }

  function logout() {
    api("POST", "/api/logout").then(function () { window.location.href = "/"; });
  }

  function addEntry(e) {
    e.preventDefault();
    var path = el("entry-path").value.trim();
    if (!path) return;
    api("POST", "/api/entry", { path: path }).then(function (res) {
      if (res.status === 201) {
        el("entry-path").value = "";
        el("entry-msg").textContent = "已添加索引";
        if (window.MdHubList && window.MdHubList.reload) { window.MdHubList.reload(); }
      } else {
        el("entry-msg").textContent = "失败：" + (res.data.error || res.status);
      }
      setTimeout(function () { el("entry-msg").textContent = ""; }, 3000);
    });
  }

  function createFile(e) {
    e.preventDefault();
    var name = el("file-name").value.trim();
    if (!name) return;
    api("POST", "/api/file", { name: name, text: "" }).then(function (res) {
      if (res.status === 201) {
        el("file-name").value = "";
        el("entry-msg").textContent = "已创建";
        if (window.MdHubList && window.MdHubList.reload) { window.MdHubList.reload(); }
        window.location.href = "/doc/" + res.data.entry.id + "/";
      } else {
        el("entry-msg").textContent = "失败：" + (res.data.error || res.status);
        setTimeout(function () { el("entry-msg").textContent = ""; }, 3000);
      }
    });
  }

  function removeEntry(id, isWorkspaceFile) {
    var msg = isWorkspaceFile
      ? "删除该文件？（服务内新建的文件，将删除真实文件且不可恢复）"
      : "取消共享该条目？（仅解除索引，不修改原文件）";
    if (!window.confirm(msg)) return;
    var url = isWorkspaceFile ? "/api/file/" + id : "/api/entry/" + id;
    api("DELETE", url).then(function (res) {
      if (res.status !== 200 && res.status !== 409) {
        alert("操作失败：" + (res.data.error || res.status));
      }
      if (window.MdHubList && window.MdHubList.reload) { window.MdHubList.reload(); }
    });
  }

  el("logout-btn").addEventListener("click", logout);
  el("entry-form").addEventListener("submit", addEntry);
  var fileForm = el("file-form");
  if (fileForm) { fileForm.addEventListener("submit", createFile); }
  // 供列表页挂删除按钮、目录选择器填路径
  window.MdHubAdmin = { removeEntry: removeEntry, refreshMe: refreshMe };
  refreshMe();
})();