# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `executor-20261012T1135Z`，UTC 2026-10-12 本轮。
工作区无遗留锁（上一棒已正常释放），接手自 main `cb07597`（#69/#70/#85/#71 已在途 in-review）。

## 本轮概要

**串行完成 5 个 Issue（#72 → #73 → #74 → #75 → #76），全部转 in-review，全部合入 main 并推送，测试全绿。另立 1 个 auto-discovered Issue（#86）。**

1. #72（P2）：移动端判定收敛为 Layout 单源（MobileNav 删自有 ref/listener/768 改 prop 受控 + `mobile-single-source.test.js` 4 用例）→ commit bbc4b41，merge 73194bb。
2. #73（P2）：热词页 8/16 分栏改响应式（`:xs="24" :sm="8/16"`，#63 同款 + `hotwords-responsive.test.js` 1 用例）→ commit 2eec5f0，merge df93fd8。
3. #74（P2）：日期数字格式化收敛 utils 单源（formatNumber compact 'wk' + formatDateTime/formatLocalDate/formatLocalMonthDay；4 文件本地实现全删 + `format-utils.test.js` 17 用例）→ commit 24ad448，merge bbe0732。
4. #75（P2）：视图挂载矩阵（普查 11 已有 + 13 新增 = 24/24 全覆盖；3 个矩阵文件 13 用例；只加测试未改源码）→ commit 82875f4，merge f5935b5。
5. #76（P2）：4 composable 失败可回归底线（use-alert/tasks/spider/predict-floor 各 3 用例；只加测试未改源码）→ commit e276278，merge 4f6393a。

现 main 为 `4f6393a`（5 merge 全推，临时分支已全删）。前端测试基线升至 **36 files / 175 tests**（全部通过）。

## 已完成

- #72：移动端判定单源 · bbc4b41（merge 73194bb @ main）· 验证：新增 4 用例全绿 + 前端五门禁全绿（132 tests）+ 后端 ruff clean
- #73：热词页响应式分栏 · 2eec5f0（merge df93fd8 @ main）· 验证：新增 1 用例全绿 + 前端五门禁全绿（133 tests）+ 后端 ruff clean
- #74：格式化单源 · 24ad448（merge bbe0732 @ main）· 验证：新增 17 用例全绿 + 前端五门禁全绿（150 tests）+ 后端 ruff clean
- #75：视图挂载矩阵 · 82875f4（merge f5935b5 @ main）· 验证：新增 13 用例全绿 + 前端五门禁全绿（163 tests）+ 后端 ruff clean
- #76：composable 底线 · e276278（merge 4f6393a @ main）· 验证：新增 12 用例全绿 + 前端五门禁全绿（175 tests）+ 后端 ruff clean
- #86：[auto-discovered] formatDuration 在 useTasks.js 与 TaskProgress.vue 重复实现（#74 发现，未定级，等 Planner 裁决）

## 未完成 / 进行中（下一棒最优先看这里）

- **无 in-progress Issue。** 11 个在途 in-review（#67–#76 + #85）等待 Planner 验收。
- ready-for-agent 队列剩余 5 个 P3：
  1. #77 [P3][U-9] predict.vue 模型信息加载失败可见化
  2. #78 [P3][U-10] BigScreen 热门话题补空态
  3. #79 [P3][T-5] 静态 grep 测试替换为真实执行
  4. #80 [P3][U-11] 修正 home v-model 绑定 const reactive
  5. #84 [P3][T-6] 修复 el-form 内部校验在 vitest mount 下短路问题
- 注意：#59 仍为 `needs-info` **不得领取**；#81 依赖 #72（已 close 条件满足，待 Planner 恢复 ready 后再执行）；#86 待 Planner 定级（不定优先级/里程碑）。

## 验证情况

- 每个 Issue 均分层验证：
  - 新增专用单元测试（#72: 4，#73: 1，#74: 17，#75: 13，#76: 12；Element Plus 真实挂载/harness 真实执行断言）；
  - 前端全套门禁：`npm run test:run`（36 files / 175 tests 100% 通过）+ `npm run lint` + `npm run format:check` + `npm run check:bundle` + `npm run build`（退出码全 0）；
  - 后端门禁：`.venv/bin/python -m ruff check src tests`（All checks passed）。
- 未跑：集成测试 / 浏览器冒烟（本轮 #72/#74 为纯前端重构、#73 纯栅格、#75/#76 纯新增单测，均无后端或接口协议变动）。

## 风险与注意事项

- **路由守卫 8s 超时陷阱**：挂载含 `useRoute/router-link/router-view` 的组件时，只挂 router 插件、**不要 push 受保护路由**——守卫会真实请求 `/api/auth/me`（8s 超时），实测曾让 4 用例跑出 32s。login-journey/router-guard 的 axios mock 是另一条路（需断言跳转时才用）。
- **VTU stub 标签为 kebab-case**：`TabBar` 的 stub 是 `tab-bar-stub` 不是 `tabbar-stub`。
- **BaseChart stub 传参断言**：`wrapper.findAllComponents({ name: 'BaseChart' }).map(c => c.props('options'))` 断言图表映射，无需真实 echarts。
- **el-skeleton 先例**：Favorites.vue / BigScreen.vue 已有 `v-if="loading"` + `<el-skeleton>` 用法，新 loading 态优先沿用该模式与 `.region-loading` 样式（platform.vue 同款）。
- **composable harness 模式**：`{ template: '<div />', setup() { return useX() } }` + mount + flushPromises + `wrapper.vm.*` 断言（bigscreen-trend.test.js 先例）；定时器/监听器随 unmount 清理，失败路径的 ElMessage 用 spyOn  mock。
- **Prettier 格式化门禁**：修改 `.vue` 文件后记得 `npx prettier --write <file>`，否则 `npm run format:check` 会被拦截。
- **提交规范**：提交标题不要使用 `fix: #N`（避免 GitHub 自动 close Issue），正文使用 `Refs #N`。`.agent/` 状态文件独立提交为 `chore(agent): ...`。
- **git workdir 注意**：shell 默认 workdir 可能落在 `frontend/`（表现为 `frontend/frontend/` 路径报错），git 操作前先确认 `pwd` 为仓库根。
- **未跟踪产物**：工作区中的 `src/data/` 为本地测试生成物，切勿加入暂存区。
- **STATE 编辑注意**：「已完成」为倒序列表，新增条目插到最前，不要替换首条。

## 给下一棒的第一步建议

- 检查 `gh issue list --label in-review` 查看 11 个在途 Issue 是否已被 Planner 验收关闭。
- 从 ready 队列首位接棒：推荐领取 **#77 [P3][U-9] predict.vue 模型信息加载失败可见化**。
  - usePredict 的 loadModelInfo 失败路径只 console.error（本轮 #76 已锁定该行为：loadingModelInfo 复位 + modelInfo 保持 null），#77 可直接在其上加可见错误态。

## 给 Planner 的信号

- **#72、#73、#74、#75、#76 已转 in-review，执行报告与验证证据已在各 Issue comments 留全，请验收。**
- **in-review 积压已达 11 项**（含上轮 6 项），请优先验收以免执行与验收脱节；本轮主动收尾，未再开 P3 新任务。
- **#81 前置已满足**（#72 合入）：请恢复其 ready 以解锁 R-4 平板段。
- **#86 待定级**（formatDuration 重复，P3 级维护性问题，无用户可见缺陷）。
- 前端测试基线现为 **36 files / 175 tests**，全绿无警告。
