/* 登录页：提交凭证 → 成功跳转主页 */
(function () {
  var form = document.getElementById("login-form");
  if (!form) return;

  function el(id) { return document.getElementById(id); }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: el("login-username").value,
        password: el("login-password").value,
      }),
    }).then(function (r) {
      return r.json().then(function (d) { return { status: r.status, data: d }; });
    }).then(function (res) {
      if (res.status === 200) {
        window.location.href = "/";
      } else {
        el("login-error").textContent = "用户名或密码错误";
      }
    });
  });
})();