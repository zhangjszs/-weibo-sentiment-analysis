# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `glm-20260930T154700Z`（GLM），UTC 2026-09-30T15:47 ~ 2026-10-01T05:5x。
第二棒，本会话九轮：#30 → #19 → #20 → #15(三轮) → #21 → #16 → #28。
**当前全部 open issue 已清零**，CI 三 job 连续九次全绿。

## 本会话成果总览（六个 issue 关闭，逐 issue 详情见各关闭评论）

| Issue | 内容 | 要点 |
|-------|------|------|
| #30 | integration 27 失效测试 | sys.modules 污染 / patch 目标迁移 / 测试基建两缺陷（勿回退 conftest 的 engine 复用） |
| #19 | 前端 Loading/静默失败/空状态 | request.js 触发条件+计数对称、useTable loadError+竞态、路由 me 缓存 60s、404 public 放行、adminOnly→/403 |
| #20 | WS 死链/SW 缓存鉴权/裸 fetch | socket.io-client 接入+vite/nginx /socket.io、SW 不缓存 /api/*、axios 统一、Inter 本地化 |
| #15 | JWT 会话安全（3 轮） | jti 黑名单+aud/iss、logout 作废、extend 旋转、三套校验统一、401/403、redirect 白名单、失败锁定、审计 |
| #21 | 前端死依赖/配置矛盾 | 5 死依赖删除、死代码、lint 去 --fix 纳入 tests、no-console 收紧、auth-session 入套件 |
| #16 | 后端死代码/文档漂移 | platform_collector 单数版等删除、AGENTS/README/CONTEXT 校正 |
| #28 | scripts/alembic 杂项 | run_migration 走 alembic、env.py 尊重 TEST_DATABASE_URL（SQLite 迁移链实测通）、check 脚本对齐 |

数字基线：后端 fast gate **1261 passed**（删 17 个单数版遗留测试后）、
integration **189 passed**、前端 **10 文件 73 tests**、前端 lint 警告
146→103（0 error）、ruff 0。

## 留白项（有意不做，供下一棒/人工决策）

1. **验证码**（#15）：需前端配合 + 产品决策，建议单独立项。
2. **user.py password String(100) 拓宽 / createTime 驼峰统一**（#16）：
   涉 schema 迁移与全局重命名。
3. **WS 刷新后无 token**：需后端提供刷新后取 token 端点（与 #15 旋转同片区）。
4. **jti 黑名单/失败锁定的多 worker 语义**：Redis 不可用时退化进程内存，
   生产应保证 Redis 可用（token_blacklist.py / login_lockout.py 注释已写明）。
5. **conftest 两套 SQLite 语义**（#28）：会话级共享 vs alert_db StaticPool 隔离，
   属取舍，未动。

## 坑与经验（重要，接力者必读）

1. **commit `fix: #N` 自动关闭 issue**；部分完成想保持 open 就用
   `refactor:`/`feat:`/`test:`/`chore:` 开头（feat 不在 GitHub 关闭关键字表）。
2. **勿回退** conftest `app` fixture 的「不调 database.reset() + 复用 engine」
   （#30 第 3 类根因）；nlp 测试的 `_nlp_tasks_under_test` 私有模块名同理。
3. app fixture 会删 config* 模块重导入：测试里 monkeypatch Config 必须
   在 fixture 之后 `import config.settings` 取新类。
4. mock axios 的 create 要带 interceptors 桩；自定义 adapter 必须回填合并 config。
5. 模块级别名导出会被 ruff F401 --fix 删，需配 `__all__`（authz.py）。
6. 工作区曾有未记录的 pytest.ini 改动（ROS 插件屏蔽），存于本地分支
   `wip/20260930T154700Z`（73cd2a7，未推送），请人工确认去留。

## 下一步建议

- 无待办 issue。下一棒可按协议第七节主动发现（先查重）；
  也可优先核对：nginx /socket.io Upgrade 上线后握手是否 101（#20 留的
  结构性验证）、Security Scan 持续绿是否稳定。

## 环境备注

- 后端 `.venv` 齐全（Python 3.12），fast gate 与 integration 本地均可跑。
- **前端 node 必须走 mise 的 PATH**：`export PATH="$HOME/.local/share/mise/installs/node/22.23.2/bin:$PATH"`。
- 想看全部失败用例要 `-o addopts="-q"`（pytest.ini 的 addopts 自带 `--maxfail=1`）。
- 本地有真实 `.env`（含密钥，**勿提交**），会影响起子进程的用例。
- gh 可用（账号 zhangjszs）。
