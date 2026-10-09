# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `executor-20261009-r2`，UTC 2026-10-09 本轮。
LOCK 在本轮开始时不存在（无接管现场），从 main caa81af 起步，
`git fetch --all --prune` + `git pull --rebase` 确认与 origin 同步。
工作区仅有已知未跟踪产物 `src/data/`（跑后端测试遗留，勿提交）。

## 本轮概要

**完成 #60：用户体验与技术债务现状调研。**

1. 调查前端现状：24 视图 / 46 views+components Vue / `src/` 17,296 行；
   测试 16 文件 / 88 测试。
2. 产出 `docs/UX_TECH_DEBT_AUDIT.md`（262 行），四维度结论 +
   23 项候选改进清单。
3. 提交 abf466f @ agent/issue-60-ux-tech-debt-audit（已推送），
   merge 9a039c3 @ main（已推送），临时分支已删除，转 in-review。

四维度核心结论（详见 STATE「关键事实」）：

- **维度一 UX 三件套**：5 页缺 loading、5 页缺视图级错误态、3 处子区域缺空态。
  两个全局兜底必须先知道才不会误判：`App.vue:2` 挂了 zh-cn locale（el-table
  空态自带中文「暂无数据」）；`api/request.js:98-163` 拦截器对失败请求会弹
  通用 ElMessage。所以 ❌ 的精确含义是「无区域级错误态、无重试入口、
  HTTP 200 载荷缺失时静默」，不是完全无声。
- **维度二 响应式**：移动端判定有**三份**独立实现——`useResponsive.js`
  （271 行，零消费者，整份死代码）+ `Layout/index.vue:53-55` +
  `MobileNav.vue:40-42`（后两者各一份硬编码 <768）。另有真实缺陷：
  `home/index.vue:26/:34` 固定 `:span="12"`、`hotWords.vue:32/:50` 固定
  `:span="8"/"16"`，手机端并排挤压。平板段 768–1024 全仓无差异化处理。
- **维度三 测试盲区**：24 个视图**零 mount**；16 个测试文件里 3 个是静态
  grep 测试、1 个零 src 依赖；登录/注册、预警中心、任务中心、爬虫管理、
  报告导出、个人中心/收藏、内容预测均无任何自动化覆盖；WebSocket 包装器
  有测试但零消费者（死管道）。
- **维度四 #58 协同**：#58 第二批/第四批计划中含约 **785 行死代码**会被
  类型化（`websocket.js` 198 + `useResponsive.js` 271 + `useTable.js` 171 +
  `composables/index.js` 145）；维度一/二缺口几乎全落在 #58 第六批。

附带发现：7 个零 importer 模块共 **1,225 行死代码**（其中 `useTable.js` /
`websocket.js` 有测试但无消费者）；日期数字格式化 4 份本地重复实现且数字
口径已分裂；`home/index.vue:61` `v-model` 绑 `const reactive` 触发编译器警告。

## 已完成

- #60：UX 与技术债务调研文档 · abf466f（merge 9a039c3 @ main）·
  验证：CI 双绿 + 前端五门禁全绿 + 文档死链门禁 + ruff 全绿

## 未完成 / 进行中（下一棒最优先看这里）

- **无 in-progress Issue。ready 队列为空。** #59 仍为 needs-info（等用户
  输入产品功能需求）。
- #60 已转 in-review，等 Planner 验收。**验收通过后建议按文档 §6 的 23 项
  候选清单立项**，其中：
  - **D-1（死代码清理，P1）宜最先**——它是 #58 第二/四批的前置。注意
    `useTable.js` 的 `loadError` 失败态机制（为 #19 设计）从未被任何视图
    消费，维度一所有 ❌ 错误态页面本可复用它；建议明确「删 useTable 还是
    接上」，而非单纯删掉。
  - **T-4（WebSocket 死管道）需转 needs-info**：删除还是接入实时推送属
    产品决策。
  - #60 的 23 项候选可直接作为 #59 产品功能迭代的方向输入。

## 验证情况

- `gh run list --commit 9a039c3` → **CI: completed / success**、
  **Security Scan: completed / success**（`gh run watch` 退出码 0）
- `npm run test:run` → 退出码 0 · 16 files / 88 tests 全过
- `npm run lint` → 退出码 0（`--max-warnings 0`）
- `npm run format:check` → 退出码 0
- `npm run check:bundle` → 退出码 0（入口 JS 273,352/327,000；首屏 CSS
  81,228/97,000）
- `npm run build` → 退出码 0（8.34s）
- `python3 scripts/check_documented_paths.py` → 退出码 0
- `.venv/bin/python -m ruff check src tests` → 退出码 0
- **未跑**：后端 pytest、集成测试、浏览器冒烟——本 Issue 无源码改动，
  上述对本次变更无验证对象；CI 的 backend-fast job 已覆盖该面。
- 本 Issue 无代码改动，故无 RED→GREEN 证据对象（与 #52/#53 那类修复不同）。

## 风险与注意事项

- **`gh run list` 排序污染警告**（既往实证）：用户会手动 re-run 历史提交的
  旧 run，failure 会顶到列表最前。**判 CI 状态必须
  `gh run list --commit <全sha>` 精确查询，不要看列表前几行。**
- CI 只对 `push: [main, develop]` 与 `pull_request: [main]` 触发。
  **推到 feature 分支不会跑 CI**——要么开 PR，要么 merge 到 main 后再查
  该 commit 的 run。
- 候选清单的优先级是我按用户影响给的建议值；**定级与里程碑归属是 Planner
  职责**，我未擅自设定。
- 死代码判定仅针对 `frontend/src/` 内部 importer。`src/views/page/templates/`
  服务端模板未纳入前端消费方调查（#54 教训：该目录在 SPA 五层扫描之外）。
  若后端模板引用前端构建产物属另一层问题，本轮未核实；Planner 立项 D-1 时
  应确认。
- 文档 §7 已声明边界：未做视觉设计评审、未重做 #58 的 TS 类型安全分析、
  未测性能。
- 跑前端 build 会在 `frontend/dist/` 留产物，已被 .gitignore 覆盖，勿提交。

## 给下一棒的第一步建议

- 先 `gh issue list` 核实 ready 队列：Planner 若已按 §6 清单补新队列则按序
  领取；仍为空则按契约空转收尾，不要自行开工作。
- 若要领 D-1（死代码清理）：动手前先把 7 个模块的零 importer 结论用
  `grep -rn "<模块名>" src/ tests/` 复核一遍（注意排除相对导入的误报），
  并先决定 `useTable.js` / `websocket.js` 是删还是接上——这两个有测试护航，
  直接删会让 7 个测试失去意义。
- 若要领 U-1/U-3/U-4（补 loading/error 态）：注意 `useBigScreen` /
  `useSpider` / `useAlert` 已经维护了 loading 或已有 console.error 点位，
  是「提升为可见反馈」而非「从零加」，改动面比看起来小。

## 给 Planner 的信号

- **#60 已转 in-review，请验收。** 验收标准 5 条已逐条核对（见 Issue 内
  执行报告）。
- **建议按文档 §6 的 23 项候选清单立项**：D-1（死代码，P1，须先于 #58
  第二/四批）→ U-1~U-4 / T-1 / T-2 / R-1 / R-2（P1）→ U-5~U-8 / R-3 /
  T-3 / T-4 / D-2（P2）→ 其余 P3/P4。
- **T-4 需转 needs-info**（WebSocket 删还是接，属产品决策）。
- 本轮无阻塞；无新增 auto-discovered Issue（所有发现已收敛进文档与候选
  清单，未单独开 Issue 以免重复）。
