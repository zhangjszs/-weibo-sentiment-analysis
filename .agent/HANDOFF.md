# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `glm-20260930T154700Z`（GLM），UTC 2026-09-30T15:47 ~ 2026-10-01T04:0x。
第二棒，本会话做了六轮：#30 → #19 → #20 → #15(三轮)。**四个 issue 全部关闭**。
CI 三 job 连续六次全绿。

## 本会话累计成果

### 轮 1：#30 integration 27 个失效测试 → 全绿关闭
nlp passthrough 私有模块名加载 / echarts-table 改 patch Repository /
app fixture 复用 engine + 自举 schema（**勿回退** conftest 的"不调
database.reset()"）。详见 #30 关闭评论。

### 轮 2：#19 前端 Loading/静默失败/空状态 → 关闭
request.js loading 触发条件与计数对称、useTable loadError+竞态、路由守卫
me 缓存 60s TTL / public 放行 404 / adminOnly 跳 /403、home 防连点、report
空导出拦截、analysis store allSettled。详见 #19 对账评论。

### 轮 3：#20 WebSocket 死链 / SW 缓存鉴权 / 裸 fetch → 关闭
WS 接入 socket.io-client（后端服务端完整，选接入而非删除）+ vite/nginx
/socket.io 通道 + 抖动退避；SW 不缓存 /api/*、离线回退 index.html；裸 fetch
统一 axios；登出清 tab；Inter 字体本地化。详见 #20 对账评论。

### 轮 5：#15 统一三套校验 → 完成（issue 保持 open）
jwt_required 升级单轨标准实现（Bearer+Cookie、统一 error envelope）、
require_jwt 真别名（__all__ 防 ruff 删）、中间件 401 文案区分、ADMIN_USERS
空 dev 启动告警。refactor: 6135bb2，+4 测试，fast gate 1278 / CI 绿。

### 轮 4：#15 JWT 撤销/旋转核心 → 部分完成，**已 reopen**
- 新增 utils/token_blacklist.py（Redis 优先/内存兜底），verify_token 查
  jti 黑名单；create_token 补 aud/iss 并强制验签
- 两处 logout 作废 token；extend 旋转；预热不再伪造 user_id=0 管理员 token
- admin_required 401/403 区分；g.user_id 挂载使限流 user 键生效
- 登录 redirect 白名单（//evil.com）；X-Request-Id 消毒
- 新增 test_jwt_revocation.py 11 例；fast gate 1274 / integration 189 /
  CI 全绿。对账评论里有逐项清单与未完成理由。

### 轮 6：#15 登录锁定 + 审计 → 关闭
utils/login_lockout.py（username+IP 5 次失败锁 15 分钟，成功清零，两条登录
轨都覆盖）；logout 审计补齐（api_logout 在撤销前解析用户）。feat a548221
+ test_login_lockout.py 5 例。验证码留白：需产品决策（建议另行立项）。

## 下一步建议（下一棒从这里接）

1. **#21（Medium，前端）**：死依赖/死代码与相互矛盾的配置。注意 vite.config
   里 /getAllData 代理已删（ADR 0002）、#20 刚动过字体与 WS，先看现状再动手。
2. #16（Low，后端死代码与文档漂移）。
3. #28（Low，scripts/alembic 杂项）。
4. #15 若有后续：验证码选型（需产品决策）。

## 坑与经验（重要）
1. **commit `fix: #N` 自动关闭 issue**：#19/#20/#15 都被自动关；部分完成的
   在评论后 `gh issue reopen` 即可。
2. app fixture 会删 config* 模块重导入：测试里 monkeypatch Config 必须
   **在 fixture 之后** `import config.settings` 取新类，顶层 import 到旧类。
3. Werkzeug 测试客户端在边界就拒绝带换行的头值；测日志注入用超长值。
4. mock axios 的 create 返回值要带 interceptors 桩（router-guard.test.js）；
   自定义 adapter 必须回填合并 config（request-loading.test.js）。
5. 工作区曾有未记录的 pytest.ini 改动，存于本地分支
   `wip/20260930T154700Z`（73cd2a7，未推送），请人工确认去留。

## 遗留 / 已知限制
- WS 刷新后无 token（AlertNotification 回退 HTTP 轮询）：与 #15 的 token
  旋转同片区，后续可加"刷新后换 token"端点一并解决。
- nginx /socket.io Upgrade 本机无 Docker 只做了结构验证，上线确认握手 101。
- jti 黑名单 Redis 不可用时退化为进程内存（多 worker 有半失效窗口），
  部署侧保证 Redis 可用；已在 token_blacklist.py 注释说明。
- vitest exclude 了 auth-session.test.js，改 authSession 时留意。

## 环境备注

- 后端 `.venv` 齐全（Python 3.12），fast gate 与 integration 本地均可跑。
- **前端 node 必须走 mise 的 PATH**：`export PATH="$HOME/.local/share/mise/installs/node/22.23.2/bin:$PATH"`。
- 想看全部失败用例要 `-o addopts="-q"`（pytest.ini 的 addopts 自带 `--maxfail=1`）。
- 本地有真实 `.env`（含密钥，**勿提交**），会影响起子进程的用例。
- gh 可用（账号 zhangjszs）。
