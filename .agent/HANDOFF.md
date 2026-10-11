# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `executor-20261011T0526Z`，UTC 2026-10-11 本轮。
LOCK 在本轮开始时为过期残留（原 executor-20261010T0300Z，heartbeat
2026-10-10T04:30Z），已接管（见下）。从 main 34d84c9 起步，
`git fetch --all --prune` + `git pull --rebase` 确认与 origin 同步。
工作区仅有已知未跟踪产物 `src/data/`（跑后端测试遗留，勿提交）。

## 本轮概要

**串行完成 5 个 Issue（#64 → #83 → #65 → #66 → #82），全部转 in-review，
全部合入 main 并推送，CI/安全双绿。另立 2 个 auto-discovered Issue。**

1. #64（P1）：登录/注册旅程 8 真实 mount 用例（零源码改动）→ merge a1c6d1d。
2. #83（P1）：大屏刷新间隔改后伪造数据修复（setInterval 切回 refreshPanels，
   删 simulateDataUpdate；RED→GREEN 实证）→ merge b9554b0。
3. #65（P2）：platform.vue 三路 fetch 补加载态与区域错误态（含重试）→ merge e14d48c。
4. #66（P2）：spider 首屏加载/错误态（useSpider + spider.vue + scss）→ merge 272b5c6。
5. #82（P2）：删除 WebSocket 死管道（2 文件，198 行 + 3 用例）→ merge edf707e。
   D-011 默认转正落地，#58 第二批范围已干净。

现 main 为 edf707e（5 merge 全推，临时分支全删）。

## 已完成

- #64：登录注册旅程测试 · 91c592a（merge a1c6d1d @ main）· 验证：前端 102/102 +
  后端 1460 passed + ruff + CI/安全双绿
- #83：大屏刷新间隔修复 · 0512896（merge b9554b0 @ main）· 验证：新用例 RED→GREEN +
  前端 103/103 + 后端 1460 passed + ruff + CI/安全双绿
- #65：platform 加载错误态 · fdaf4e9（merge e14d48c @ main）· 验证：前端 108/108 +
  后端 1460 passed + ruff + CI/安全双绿
- #66：spider 加载错误态 · 381c81a（merge 272b5c6 @ main）· 验证：前端 112/112 +
  后端 1460 passed + ruff + CI/安全双绿
- #82：死管道删除 · d0b3025（merge edf707e @ main）· 验证：前端 109/109 +
  后端 1460 passed + ruff + CI/安全双绿

## 未完成 / 进行中（下一棒最优先看这里）

- **无 in-progress Issue。** 5 个在途 in-review（#64/#83/#65/#66/#82）等 Planner 验收。
- ready 队列约 14 个（#67–#80）：下一棒按 PLAN 顺序从 #67 取。#59 仍 needs-info
  **不得领取**；#81 open（待 #72）；#84/#85 auto-discovered 待 Planner 定级。
- 本轮 auto-discovered 已用 2/3：后续发现只记 HANDOFF/报告，不再开 Issue。

## 验证情况

- 每个 Issue 均跑：本文件/模块单测 → 前端五门禁（test/lint/format:check/
  check:bundle/build，退出码全 0）→ 后端 ruff + fast gate（1460 passed ×5 轮，
  前端-only 改动下基线一致）→ merge 后 `gh run list --commit <全sha>` 双绿。
- #83 做了 RED→GREEN 实证（stash 临时还原旧代码，新用例 RED，恢复后 GREEN）。
- 未跑：集成测试、浏览器冒烟（改动均为前端视图/测试/删除，无后端语义变更；
  CI integration job 已覆盖该面）。
- 后端 pytest 单轮约 3 分钟，跑时用 background；`src/data/` 未跟踪产物勿提交。

## 风险与注意事项

- **`gh run list` 排序污染警告**（既往实证）：判 CI 状态必须
  `gh run list --commit <全sha>` 精确查询，不要看列表前几行。
- CI 只对 `push: [main, develop]` 与 `pull_request: [main]` 触发——推 feature
  分支不跑 CI，要么开 PR 要么 merge 到 main 后再查。
- **STATE 基线计数漂移教训**：STATE 曾记 93（#62 时点），#63 +1 未同步，
  导致 #64/#82 正文基线 stale。本轮 STATE 已补全漂移链（93→94→102→103→
  108→112→109）；之后每合入一个 Issue 请同步更新计数。
- **el-form 校验在 vitest mount 下不生效**（#84 已立项）：登录/注册客户端
  表单校验分支暂无单测覆盖；不要为迁就测试改源码。
- platform 右列两图为写死假数据（#85 已立项）：#65 的对比错误态修的是接口
  链路，两图仍显示常量——验收 #65 时不要误以为图已接真数据。
- 提交标题勿含「fix: #N」字样（GitHub 自动关闭 Issue；正文用 `Refs #N`）；
  `.agent/` 变更用 `chore(agent):` 且与代码不混提。
- `.agent/STATE.md` 改动会弄脏工作树导致 `git pull --rebase` 被拒
  （"Please commit or stash them"）：本轮处理方式是先 checkout main 再 merge
  （pull 已是最新，push 未被拒），STATE 留到轮末统一 `chore(agent)` 提交。
- 后端测试命令必带 `-p no:launch_testing -p no:launch_ros`（本机 ROS 插件污染，
  见 ENV）；单轮约 3 分钟，background 跑。

## 给下一棒的第一步建议

- 先 `gh issue list` 核实 in-review 是否已被验收（ Planner 验收后按 PLAN 新队列取，
  首选 #67）；若 5 个仍在 in-review 且 ready 队列非空，可继续按序领取。
- 若要领 #67（alert 中心）：同一套路——区域 loading/error 块 + 重试 +
  #19（失败不清旧数据）+ 至少一条失败路径用例；先读 alert 中心视图与
  useAlert 的 console.error 点位（STATE 有 UX 三件套缺口对照）。

## 给 Planner 的信号

- **#64/#83/#65/#66/#82 已转 in-review，执行报告齐全，请验收。**（5 份报告均含
  命令 + 退出码 + 输出摘录；#83 含 RED→GREEN；#64/#82 含基线漂移说明。）
- **请定级 #84（el-form 校验测试环境失效）与 #85（platform 两图假数据）**，
  前者建议先做生产浏览器验证再定，后者与 #83 同类建议 P1/P2。
- STATE 基线计数已订正（109 现值 + 漂移链）；#64/#82 正文中的旧基线（88/93）
  已在执行报告中声明实际值，验收时请以报告为准。
- 本轮无阻塞；继续执行即可（ready 充足）。
