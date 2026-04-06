# 认证与权限加固设计

## 背景

本次修复聚焦两类高风险问题：

1. 系统级预警接口缺少管理员权限控制，普通用户可修改全局规则与全局预警状态。
2. 前端将 JWT 长期存储在 `localStorage`，任意前端 XSS 一旦成立即可直接窃取令牌。

同时，项目当前的开发环境自举逻辑会在应用启动时自动创建或重置默认管理员账号，存在明显的默认口令和启动副作用风险。

## 目标

- 将前端认证从 `localStorage + Authorization` 迁移为 `HttpOnly Cookie` 优先。
- 保留 Bearer Token 兼容路径，避免一次性打断既有接口和 WebSocket 逻辑。
- 为系统级预警接口补齐管理员权限校验。
- 修正会话检查接口的认证语义。
- 关闭危险的默认管理员自举行为。
- 更新 API / 部署 / 前端文档，使实现与文档一致。

## 方案选择

采用“Cookie 优先，Bearer 兼容保留”的迁移方案。

原因：

- 改动面可控，主要集中在认证入口、中间件、前端请求层与路由守卫。
- 现有 JWT 生成/校验逻辑可复用，不需要重做成完整 session 体系。
- 允许前端和 WebSocket 逐步迁移，避免一次性重写所有调用链。

## 认证设计

### 后端

- 登录成功后继续返回现有 JSON 结构中的 `token` 与 `user`，以兼容现有 WebSocket 初始化流程。
- 同时通过 `Set-Cookie` 写入 `weibo_access_token`。
- Cookie 属性：
  - 开发环境：`HttpOnly=True`、`SameSite=Lax`、`Secure=False`
  - 生产环境：`HttpOnly=True`、`SameSite=Strict`、`Secure=True`
- 登出时清空 `weibo_access_token`。
- 认证中间件读取顺序：
  1. `Authorization: Bearer ...`
  2. `weibo_access_token` Cookie

### 前端

- 不再把 token 写入 `localStorage`。
- axios 开启 `withCredentials`，认证依赖浏览器自动带 Cookie。
- 用户信息状态可以继续保存在 store 中，必要时可保留 `weibo_user` 的非敏感缓存，但不再缓存 token。
- 路由守卫从“本地有无 token”改为“尝试通过 `/api/auth/me` 恢复登录态”。

### WebSocket

- 短期内保留显式 token 鉴权。
- 前端仅在当前页面内存里使用登录响应返回的 token 建立 WebSocket，不做持久化。
- 本轮不重构 WebSocket 为 Cookie 握手鉴权，避免扩大修复面。

## 权限模型设计

预警接口按资源性质分层：

- 普通登录用户可访问：
  - `GET /api/alert/rules`
  - `GET /api/alert/history`
  - `GET /api/alert/stats`
  - `GET /api/alert/unread-count`
  - `POST /api/alert/<id>/read`
- 管理员专属：
  - `POST /api/alert/rules`
  - `PUT /api/alert/rules/<id>`
  - `DELETE /api/alert/rules/<id>`
  - `POST /api/alert/rules/<id>/toggle`
  - `POST /api/alert/read-all`
  - `POST /api/alert/test`
  - `POST /api/alert/evaluate`

说明：

- 当前预警历史和未读状态是全局内存结构，不区分用户。因此 `read-all` 必须视为管理员操作。
- `mark_read` 仍保留给普通用户，是因为它只修改单条状态，且本轮先做最小修复；后续应将预警已读状态建模为用户级数据。

## 默认管理员与启动副作用

- `AUTO_CREATE_DEMO_ADMIN` 默认改为 `False`。
- `DEMO_ADMIN_RESET_PASSWORD` 默认改为 `False`。
- 自举逻辑即使开启，也不再默认重置已有账号密码。
- 保留显式开发开关，但禁止“导入应用即重置管理员密码”的危险默认路径。

## 会话接口语义

- `/api/session/check`
  - 未认证：返回 `200` 和 `{ authenticated: false, user: null }`
  - 已认证：返回 `200` 和 `{ authenticated: true, user: ... }`
- `/api/session/extend`
  - 未认证返回 `401`
  - 已认证返回成功

这样前端可以把它当成轻量探测接口，而不是总是得到错误的正向状态。

## 测试策略

先写失败测试，再改实现。

后端测试覆盖：

- Cookie 登录/登出行为
- 中间件从 Cookie 读取 JWT
- 会话检查接口认证语义
- 预警系统级接口的管理员权限限制
- 默认管理员配置的安全默认值

前端验证：

- 请求层启用 `withCredentials`
- `user` store 不再读写 token 到 `localStorage`
- 路由守卫改为依赖用户状态恢复，而不是本地 token 判定

由于仓库当前未配置前端自动化测试框架，本轮以前端构建成功和关键代码路径审查为主。

## 影响范围

- 后端：`src/app.py`、`src/views/api/api.py`、`src/views/api/alert_api.py`、`src/config/settings.py`、`src/services/startup_service.py`
- 前端：`frontend/src/api/request.js`、`frontend/src/stores/user.js`、`frontend/src/router/index.js`
- 测试：`tests/test_auth_jwt.py`、新增预警权限测试
- 文档：`docs/API.md`、`README.md`、`docs/DEPLOYMENT.md`、`frontend/README.md`
