# 07 — 管理员认证

**What to build:** 管理侧的根：set_password 命令设置用户名+密码（PBKDF2 哈希入 config，session 密钥一并生成），登录/登出页面，HttpOnly + SameSite=Strict session cookie，以及所有管理/写接口的鉴权守卫骨架（本票先以受保护的占位接口验证守卫，后续管理票直接继承）。未登录者不能执行任何写操作。

**Blocked by:** 01 — 项目骨架与启停脚本

**Status:** ready-for-agent

- [x] set_password 命令设置凭证后，可用用户名+密码登录成功
- [x] config 中只有哈希与密钥，无明文密码
- [x] 未登录访问管理接口被拒；错误密码被拒；登出后会话失效
- [x] cookie 为 HttpOnly + SameSite=Strict
- [x] HTTP seam 测试覆盖登录/登出/拒绝路径
