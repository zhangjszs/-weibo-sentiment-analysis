# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `glm-20260930T154700Z`（GLM），UTC 2026-09-30T15:47 ~ 2026-10-01T01:5x。
第二棒，本会话做了三轮：#30 → #19 → #20。CI 三 job 连续三次全绿。

## 做了什么（本轮会话累计）

### 轮 1：#30 integration 27 个失效测试 → 全绿关闭
三个 commit（详见 #30 关闭评论）：nlp passthrough 私有模块名加载、
echarts/table 改 patch Repository、app fixture 复用 engine + 自举 schema。
**勿回退** conftest 的"不调 database.reset()"改动。

### 轮 2：#19 前端 Loading/静默失败/空状态 → 关闭
四个 commit（详见 #19 对账评论）：request.js loading 触发条件与计数对称、
useTable loadError + 竞态防护、路由守卫 me 缓存 60s TTL / public 放行 404 /
adminOnly 跳 /403、home 防连点、report 空数据导出拦截、analysis store
allSettled + 缓存保护。

### 轮 3：#20 WebSocket 死链 / SW 缓存鉴权 / 裸 fetch → 关闭
四个 commit（详见 #20 对账评论）：
- `a2f7b05` WS 接入 socket.io-client（选接入而非删除：后端 Socket.IO
  服务端完整、client 依赖已在），vite 代理 + nginx Upgrade + 抖动退避
- `bfb0bff` SW 不缓存 /api/*（多用户串数据）、离线回退 index.html
- `956503d` 裸 fetch 统一 axios（home + 路由守卫独立实例避免循环 import）
- `795bb80` 登出清 tab 持久化、Inter 字体本地化（@fontsource/inter）

## 坑与经验（重要）

1. **commit message `fix: #N` 会自动关闭 issue**。#19/#20 都是——评论在
   close 后补发也正常。不想自动关就用 `test:`/`chore:` 开头。
2. mock axios 时 `create` 返回值必须带 `interceptors` 桩：同模块图里
   request.js 也会 `axios.create()` 并注册拦截器（见 router-guard.test.js）。
3. 测 axios 拦截器时自定义 adapter 必须回填合并 config（见
   request-loading.test.js）。
4. 工作区曾有未记录的 pytest.ini 改动（`-p no:launch_testing -p no:launch_ros`），
   已存本地分支 `wip/20260930T154700Z`（73cd2a7，未推送）。实测非必需，
   请人工确认去留。

## 遗留 / 已知限制（诚实清单）

- **WS 刷新后无 token**：token 仅存内存，页面刷新后 AlertNotification 因
  `!token` 不建连（HTTP 轮询兜底，功能不受损）。根治需后端提供刷新后取
  token 的端点——与 #15 的 JWT 旋转是同一片区域，可一并设计。
- **nginx /socket.io Upgrade**：本机无 Docker，只做了结构验证；人工上线
  时确认握手 101。
- **vitest exclude 了 auth-session.test.js**：本轮 #19/#20 改过
  authSession.js（新增 me 缓存），该文件断言未进套件；人工启用前先跑。

## 下一步建议

1. **#15（Medium，后端 JWT）**：aud/iss、jti 校验、logout 作废、extend
   旋转、"鉴权三套重复"。安全敏感、影响所有 API——动之前先读
   `src/utils/jwt_handler.py` 与三层鉴权现状，改动要配测试，注意与
   WS 已知限制（刷新后取 token）统筹。
2. #21（Medium，前端死依赖/配置矛盾）。
3. #16（Low，文档漂移）/ #28（Low，alembic 杂项）。

## 阻塞 / 风险

- 无环境阻塞。CI 三 job 连续三次全绿；Security Scan 连续三次绿。

## 环境备注

- 后端 `.venv` 齐全（Python 3.12），fast gate 与 integration 本地均可跑。
- **前端 node 必须走 mise 的 PATH**：`export PATH="$HOME/.local/share/mise/installs/node/22.23.2/bin:$PATH"`。
- 想看全部失败用例要 `-o addopts="-q"`（pytest.ini 的 addopts 自带 `--maxfail=1`）。
- 本地有真实 `.env`（含密钥，**勿提交**），会影响起子进程的用例。
- gh 可用（账号 zhangjszs）。
