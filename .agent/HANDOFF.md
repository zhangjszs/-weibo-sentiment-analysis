# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `glm-20260930T154700Z`（GLM），UTC 2026-09-30T15:47 ~ 2026-10-01T01:0x。
第二棒（本轮会话内做了两轮：#30 与 #19）。

## 做了什么

### 轮 1：#30 integration 27 个失效测试 → 全绿关闭

三类根因、三个 commit（详见 #30 关闭评论）：
1. `7a093e5` nlp passthrough 改 importlib 私有模块名加载（sys.modules 污染）
2. `4819d75` echarts/table 改 patch ArticleRepository/CommentRepository
3. `7b9d4b4` app fixture 复用 engine + 自举 schema（**勿回退**：任何恢复
   `database.reset()` 每测试调用的做法都会复活顺序敏感失败）
本地 integration 189 passed（原 27 failed），CI integration/MySQL 首次绿。

### 轮 2：#19 前端 Loading/静默失败/空状态 → 关闭

四个 commit（详见 #19 对账评论）：
- `bea77b8` request.js loading 触发条件（去 fullscreen 硬条件）+ 计数对称
- `8ea1485` useTable loadError + latest-wins 竞态防护
- `a7d3660` 路由守卫 me 缓存 60s TTL、public 放行 404、adminOnly 跳 /403
- `772c162` home 防连点、report 空数据导出拦截、analysis store allSettled
前端测试 45 → 64（新增 4 个测试文件），lint 0 error，build 成功，CI 全绿。

## 坑与经验（重要）

1. **commit message `fix: #N` 会自动关闭 issue**（GitHub closing keyword）。
   #19 就这样被自动关了，评论是事后补的。不想自动关就用 `test:`/`chore:` 开头。
2. 测 axios 拦截器时，自定义 adapter **必须回填合并后的 config** 到
   response/error（内置 xhr/http adapter 的行为），否则 `response.config`
   是 undefined/空对象，依赖 config 标记的逻辑测不到。
3. 工作区曾有一处**未记录的 pytest.ini 改动**（`-p no:launch_testing -p
   no:launch_ros`，疑似人工为屏蔽 ROS 2 插件所加）。实测非必需（撤销后
   pytest 照常），已按协议存到**本地**分支 `wip/20260930T154700Z`
   （73cd2a7，未推送）。请人工确认去留，勿混入任务 commit。

## 下一步建议

1. **#20（High，前端）**：WebSocket 死链 + SW 缓存鉴权接口 + 裸 fetch 绕过
   统一鉴权。与 #19 同在 frontend/；注意 `home/index.vue` 的裸 fetch 就是
   #20 的"裸 fetch"清单之一（#19 只加了防连点，没换请求通道）。
2. #15（Medium，后端 JWT）：aud/iss、jti 校验、logout 作废、extend 旋转。
3. #21（Medium，前端死依赖/配置矛盾）。
4. #16（Low，文档漂移）/ #28（Low，alembic 杂项）。

## 阻塞 / 风险

- 无环境阻塞。CI 三 job 连续两次全绿。
- 观察项：Security Scan 已连续两次绿（此前一直红）——旧"每次都红"的
  判断已过时，若再红需单独查 security-scan.yml。
- `vitest.config.js` exclude 了 `tests/auth-session.test.js`（不进套件），
  本轮给 authSession.js 加了缓存函数，该文件断言未跑过；若人工启用它，
  先跑一遍看是否需要更新。

## 环境备注

- 后端 `.venv` 齐全（Python 3.12），fast gate 与 integration 本地均可跑。
- **前端 node 必须走 mise 的 PATH**：`export PATH="$HOME/.local/share/mise/installs/node/22.23.2/bin:$PATH"`。
- 想看全部失败用例要 `-o addopts="-q"`（pytest.ini 的 addopts 自带 `--maxfail=1`）。
- 本地有真实 `.env`（含密钥，**勿提交**），会影响起子进程的用例。
- gh 可用（账号 zhangjszs）。
