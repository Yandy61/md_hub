/* 编辑模式：CodeMirror 编辑原文 → PUT 写回（管理员；访客看不到按钮） */
(function () {
  var entryId = window.location.pathname.split("/")[2];
  var cm = null;
  var editing = false;
  var pollPaused = false;

  function el(id) { return document.getElementById(id); }

  function authed() {
    return fetch("/api/me").then(function (r) { return r.json(); }).then(function (d) {
      return d.authenticated;
    });
  }

  authed().then(function (ok) {
    if (!ok) return;
    var bar = el("edit-bar");
    bar.hidden = false;
    el("edit-btn").addEventListener("click", startEdit);
    el("cancel-btn").addEventListener("click", cancelEdit);
    el("save-btn").addEventListener("click", save);
  });

  function startEdit() {
    fetch("/api/raw/" + entryId + "/").then(function (r) {
      if (r.status !== 200) { throw new Error("cannot load raw"); }
      return r.json();
    }).then(function (d) {
      pollPaused = true;  // 编辑期间暂停轮询，避免编辑器被刷新打断
      el("doc-body").hidden = true;
      var wrap = el("editor-wrap");
      wrap.hidden = false;
      if (!cm) {
        cm = window.CodeMirror(wrap, {
          value: d.text,
          mode: "markdown",
          lineNumbers: true,
          lineWrapping: true,
        });
      } else {
        cm.setValue(d.text);
      }
      editing = true;
      el("edit-btn").hidden = true;
      el("edit-actions").hidden = false;
    }).catch(function () { alert("无法加载原文"); });
  }

  function cancelEdit() {
    editing = false;
    pollPaused = false;
    el("editor-wrap").hidden = true;
    el("doc-body").hidden = false;
    el("edit-btn").hidden = false;
    el("edit-actions").hidden = true;
  }

  function save() {
    if (!cm) return;
    fetch("/api/doc/" + entryId + "/", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: cm.getValue() }),
    }).then(function (r) {
      if (r.status === 200) {
        cancelEdit();
        // 立即重绘，不等下一轮轮询
        if (window.MdHubDoc && window.MdHubDoc.refresh) { window.MdHubDoc.refresh(); }
      } else if (r.status === 401) {
        alert("登录已失效，请重新登录");
      } else {
        alert("保存失败: " + r.status);
      }
    });
  }

  window.MdHubEditor = {
    isEditing: function () { return editing; },
    pausePoll: function () { return pollPaused; },
  };
})();
