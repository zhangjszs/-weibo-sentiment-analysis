# TASKS — GitHub Issue 本地镜像

> 2026-11-28 第二轮按 GitHub open Issues 整体重建；未降级。变更状态先操作 Issue，再同步本文件。没有生命周期标签的记录项不可领取。
> 权威来源是 GitHub Issue，本表是只读镜像。本轮实际写入路径为 `/tmp` 干净克隆 + GitHub 连接器：本地工作树 `.git` 元数据只读，`gh` 在默认沙箱被代理 socket 拦截（令牌本身有效，放开网络后可用）。

## 今日队列（4 项 `ready`）

| 顺序 | Issue | 标题 | 优先级 | 状态 | 依赖与验收入口 |
|---|---|---|---|---|---|
| 1 | [#163](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/163) | 补齐既有 Compose 数据卷的账号迁移路径，避免升级后整栈不可启动 | P0 | `ready` | 无硬前置。只交付仓库内脚本与文档，不在真实实例执行。分支 `agent/issue-163-compose-db-account-migration`。 |
| 2 | [#164](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/164) | 统一管理员用户名校验口径并补齐部署配置模板缺口 | P1 | `ready` | 无硬前置。#158/#159 若已合并则从主干起分支，否则在对应 PR 分支实施。分支 `agent/issue-164-admin-username-normalization`。 |
| 3 | [#156](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/156) | 锁定六个会话 API 包装的真实请求与响应契约 | P3 | `ready` | #145、#150 已 `done`。仅新增 `frontend/tests/auth-api-contract.test.js`。分支 `agent/issue-156-auth-api-contract`。 |
| 4 | [#157](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/157) | 迁移公共请求实例至 TypeScript 并在入口装配导航 | P2 | `ready` | #145、#150、#151 已 `done`。生产 8 TS / 0 JS 或 Vue。分支 `agent/issue-157-request-typescript`。 |

四项均给出范围、排除项、逐条可测标准；无产品取舍、无 §1.10 红线、无相互硬依赖。顺序为建议顺序：#163/#164 是 PR #158/#159 合并带入的缺陷，先于前端工作处理；#156 先以新增文件立起"加载真实 auth 模块"的模式，#157 最后动生产代码。#143 因今日容量顺延一轮（保持 `ready`、不降级、不改验收标准）。开放 P0 = 1，P1 = 1。

## 本轮复验（11-23 已验收项，2026-11-28 独立复跑）

| Issue | 结论 | 关键证据 | 遗留 |
|---|---|---|---|
| [#146](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/146#issuecomment-7091137981) | 维持通过，`done` / CLOSED | 交付 `9deea56` 仅改 `frontend/package-lock.json`（16+/16−），恰 5 条记录、483 个 `node_modules/*` 条目前后相同、registry 主机计数不变、锁哈希 `28c721d7…` 复算一致。PR 头 `9deea56` 五项 CI 5/5 success。 | 合并提交 `5457ab2` 的 push 运行是 4 项 `cancelled` + 1 项 `success`（被 9 秒后合入的 #149 取代），报告与验收评论均未记录；`npm audit` 配对、`typecheck`、47/321 与体积数字只有叙述性证据——`security-scan` 是 Python-only，不跑 npm audit。 |
| [#147](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/147#issuecomment-7104222957) | 维持通过，`done` / CLOSED | 仅 `docs/TEST_PERF.md`（+33 与 +156，0 删除），历史字节未变（blob `e4522cb6…` 至今未动）。6 排列 × 3 算法表、`addTab` 两处回退 L/R/T=0/0/1、`FNDA:19` 与 3+4+12 自洽。四个 SHA 五项 CI 全绿。 | 105 区间 / 45 区间逐项求和与 Vue `startOffset` 负对照**不可由仓库内任何探针复现**（依赖仓库外 `study.mjs`）；`scripts/check_documented_paths.py` **不扫描 `docs/TEST_PERF.md`**，路径门禁对新内容为空转。结论仅对 `1316e15` + 锁 `bab52592…` 成立，不具锁可移植性；未证明 auth 双漂移，未判定 A/B 哪个正确。 |
| [#150](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/150#issuecomment-7104225273) | 维持通过，`done` / CLOSED | `9888bc6` 仅改 `frontend/tests/request-error-paths.test.js`（+118/−0），生产文件零改动。独立复跑：定向 1 文件 / 27 例、全量 47 文件 / 323 例、lint / format:check / typecheck / build / check:bundle 全 exit 0，体积字节数与报告一致。两个 SHA 五项 CI 全绿。 | 仅"423 个包"的 `npm ci` 计数随环境不可确认；不影响验收。 |
| [#151](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/151#issuecomment-7104227740) | 维持通过，`done` / CLOSED | `5e3f799` 仅 `docs/FRONTEND_TS_MIGRATION.md`（+80/−0）。基线独立复现 `tsc --noEmit --listFiles` 为 7 TS / 0 JS / 0 Vue，D-043 纯净度成立；§9.4 接线点、两种 401 等价表、9 个链接目标全部核对存在。两个 SHA 五项 CI 全绿。 | 候选 8/0 门禁、TS2322/TS2739 实际诊断与 Chromium 冒烟是仓库外证据（Issue 自身范围如此）；`check_documented_paths.py` **不扫描 `docs/FRONTEND_TS_MIGRATION.md`**，故其 exit 0 对 §9.4 为空转，已改为逐个核对链接目标。 |

四项均维持 11-23 的验收结论，不 reopen。上述遗留以 Issue 评论追加记录，不改写原验收。

## 未完成任务全表（16 个 Open Issues）

| Issue | 标题 | 优先级 | 状态 | Milestone | 治理结论 |
|---|---|---|---|---|---|
| [#163](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/163) | 补齐既有 Compose 数据卷的账号迁移路径，避免升级后整栈不可启动 | P0 | `ready` | — | **本轮新建（复核缺陷）**：#159 把应用账号从 root 迁到 `weibo` 并改 healthcheck 认证，官方镜像只在空卷初始化时应用该账号，存量卷上整栈不可启动。修复物限于仓库内脚本与文档，不触碰生产实例。 |
| [#164](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/164) | 统一管理员用户名校验口径并补齐部署配置模板缺口 | P1 | `ready` | — | **本轮新建（复核缺陷）**：管理员名单精确匹配与 MySQL 大小写不敏感冲突（可致管理员锁死，无提权）；`.env.example` Docker 段缺 `REDIS_PASSWORD`；`docs/DEPLOYMENT.md` 模板缺 `ADMIN_USERS`；死配置 `DEMO_ADMIN_RESET_PASSWORD`。 |
| [#165](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/165) | 收紧 WebSocket 非用户房间的订阅与投递结果语义 | P2 | `ready` | — | **本轮新建（复核缺陷）**：`keyword`/`global`/`system` 房间未守卫（当前无告警调用方，暂无实际泄漏）；`send_to_user` 对离线收件人返回假阳性。 |
| [#166](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/166) | 收敛 Docker 首次部署的 Alembic schema 漂移 | P2 | `ready` | — | **本轮新建（复核缺陷）**：`init_database.sql` 成为 Docker 唯一初始化来源后，Alembic 从不执行，`create_time` 停留 `date`、三个索引缺失；`user.is_admin` 列与管理员权威来源需在文档中澄清。 |
| [#157](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/157) | 迁移公共请求实例至 TypeScript 并在入口装配导航 | P2 | `ready` | [请求层迁移](https://github.com/zhangjszs/-weibo-sentiment-analysis/milestone/4) | 已有候选、行为基线及可检查边界，生产 8/0。独立复验确认 §9.4 前置充分，可按 Issue 执行。 |
| [#156](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/156) | 锁定六个会话 API 包装的真实请求与响应契约 | P3 | `ready` | [请求层迁移](https://github.com/zhangjszs/-weibo-sentiment-analysis/milestone/4) | 现有页面及 store 测试 mock 整个 auth 模块，本项覆盖真实包装和公共实例。 |
| [#143](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/143) | 稳定 auth 域覆盖率并验证漂移机制（#138） | P3 | `ready` | — | 范围已于 D-052 重新界定为可执行的测试侧隔离修复；本轮因队列容量顺延一轮，不降级。 |
| [#161](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/161) | 评估并决定 PR #158 / #159 的安全加固合并 | P2 | `needs-info` | — | **本轮重开**：D-054（暂不合并）已被用户新指示取代。两份独立复核结论均为 MERGE AFTER FIXES；新增发现的存量卷启动中断风险需用户知情后拍板，默认 A（合并）。选项与影响见 Issue 评论。 |
| [#138](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/138) | [auto-discovered] src/api/auth.js 与 src/views/auth/Login.vue 覆盖率在同 HEAD 下跨运行波动 | P3 | 无生命周期标签 | — | 现象与根因档案（Planner 单文件隔离实测已确认 mock 工厂替换机制）。不作为可领取任务，修复由 #143 承接。 |
| [#109](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/109) | 验证并修正现有 OTLP 链路的 metrics 接收与 Jaeger 展示 | P2 | `blocked` | [M7](https://github.com/zhangjszs/-weibo-sentiment-analysis/milestone/2) | 本机无 Docker/Podman 命令或默认 socket，无已授权远端；不以 console 替代。 |
| [#102](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/102) | [M7-5][P2] CI ABI parity matrix + cross-impl fallback contract tests | P2 | `needs-info` | [M7](https://github.com/zhangjszs/-weibo-sentiment-analysis/milestone/2) | #98 未通过；跨版本矩阵未获授权，D-019 A 冻结。 |
| [#101](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/101) | [M7-4][P3] Streaming summary via SSE（AI layer 切片2） | P3 | `needs-info` | [M7](https://github.com/zhangjszs/-weibo-sentiment-analysis/milestone/2) | 产品入口、数据与成本未授权，D-019 A 冻结。 |
| [#100](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/100) | [M7-3][P3] Qdrant 语义搜索端点（AI layer 切片1） | P3 | `needs-info` | [M7](https://github.com/zhangjszs/-weibo-sentiment-analysis/milestone/2) | 新增服务与长期成本未授权，D-019 A 冻结。 |
| [#98](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/98) | [M7-1][P2] Rust 第一切片迁移：deduplicator + normalize（criterion before/after） | P2 | `in-progress` | [M7](https://github.com/zhangjszs/-weibo-sentiment-analysis/milestone/2) | D-019 A 有意冻结现场，不判中断、不重置。 |
| [#96](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/96) | [M7] Rust-Accelerated Core + Observable AI（炫技重构主轴） | P2 | `needs-info` | — | D-019 A 冻结的扩展 Epic，不计 M7 分母。 |
| [#59](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/59) | [P2] 产品功能迭代：需求收集与规划 | P2 | `needs-info` | — | D-012 A 等具体产品需求，不重复询问。 |

## 本轮治理与记录

- **昨日日报缺失**：11-24 至 11-27 无 Executor 执行会话、无日报。主干最后一份日报是 11-22；11-22 晚间补记与 11-23 日报此前只存在于未合并分支，本轮已归位主干。11-23 的工作由 Issue 评论、PR 与 Git 反推，并经三项独立复验补证。
- **镜像脱节 5 天**：11-23 规划轮的三份文档滞留在 PR #152 未合并，主干 `TASKS.md` 仍把已关闭的 #146/#147 列为 `ready`。该轮已合并 #152 并整体重写本表。此后每轮 Planner 须当轮合并自己的规划 PR。
- **#143 解除阻塞**：原标准要求复现 `ce3ab0d` 时代的历史 auth 双漂移原始样本；Executor 已报告原始日志不在本机，独立复验也确认仓库内无对应样本。该前提已不可获得，继续挂 `blocked` 只会空转。已按契约 4.1 重新界定为可执行的测试侧隔离修复并转 `ready`，#138 保留为现象档案。
- **#158 / #159 复核与缺陷立项**：用户 2026-11-28 指示"先把远程推的代码合并了"，取代 D-054 的"暂不合并"。两份只读独立复核结论均为 **MERGE AFTER FIXES**：核心安全主张逐条核实为真，本地 `ruff` 与 `pytest -m "unit or api"` 全绿；全量 pytest 仅 `test_platform_data_does_not_silent_demo_fallback` 失败且在 `main` `80408d0` 上同样失败（既有/环境问题）。复核新发现存量卷升级后整栈不可启动的风险（账号迁移 + healthcheck 认证方式变更），连同管理员名校验口径、部署模板缺项、WebSocket 房间与投递语义、Docker 首次部署 schema 漂移，共四类缺陷转为 #163–#166，逐条写明范围、排除项与可判定验收标准。
- **合并授权待确认**：#161 重开，`needs-info`。是否在存量卷升级路径补齐前合并属用户取舍（默认 A：合并并把升级路径排为今日第 1 项）；风险细节与三个选项写在 Issue 评论。
- **本机工作树受限**：本地 `.git` 元数据只读，无法 `git fetch`/`git pull`；另有 6 个未提交文件（`mise.toml`、`.github/workflows/ci.yml` 的 py3.11→3.12 与 node20→26、`.github/workflows/security-scan.yml`、`frontend/Dockerfile`、`frontend/vitest.config.js`、`.agent/ENV.md`）。#159 对 `ci.yml` 的 3 行改动与本地 WIP 会在 pull 时冲突，需先提交或 stash。
- **无待转正项**：D-012 A、D-019 A、D-023 A 继续有效。开放 P0 = 1、P1 = 1。M6 10/10 成员关闭（成功信号 1/3）；M7 6/11 且冻结。
