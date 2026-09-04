/* 管理功能：登录/登出、新增索引、取消共享（外部条目） */
(function () {
  var adminBox = document.getElementById("admin-box");
  if (!adminBox) return;

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
      var authed = res.data.authenticated;
      el("login-form").hidden = authed;
      el("admin-actions").hidden = !authed;
      if (cb) cb(authed);
    });
  }

  function login(e) {
    e.preventDefault();
    api("POST", "/api/login", {
      username: el("login-username").value,
      password: el("login-password").value,
    }).then(function (res) {
      if (res.status === 200) { refreshMe(); }
      else { el("login-error").textContent = "用户名或密码错误"; }
    });
  }

  function logout() {
    api("POST", "/api/logout").then(function () { refreshMe(); });
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

  function removeEntry(id, isWorkspaceFile) {
    var msg = isWorkspaceFile
      ? "删除该文件？（服务内新建的文件，将删除真实文件且不可恢复）"
      : "取消共享该条目？（仅解除索引，不修改原文件）";
    if (!window.confirm(msg)) return;
    api("DELETE", "/api/entry/" + id).then(function () {
      if (window.MdHubList && window.MdHubList.reload) { window.MdHubList.reload(); }
    });
  }

  el("login-form").addEventListener("submit", login);
  el("logout-btn").addEventListener("click", logout);
  el("entry-form").addEventListener("submit", addEntry);
  // 供列表页挂删除按钮
  window.MdHubAdmin = { removeEntry: removeEntry, refreshMe: refreshMe };
  refreshMe();
})();
