# PLAN — 开发路线图

> Planner 维护；Executor 只读。2026-10-26 规划轮更新（完整规格与验收证据见 GitHub Issues 与 `.agent/TASKS.md`；决定见 D-034 / D-035 / D-036 / D-037）。
> 本轮为**新一天首次规划轮**：昨日（2026-10-25 执行会话 1）交付的 #133、#134 已独立复跑验收**全部通过**并关闭为 `done`；据 `docs/FRONTEND_TS_MIGRATION.md` §2 第一批余项与行为覆盖强度编排 TS 第二批切片 #135 / #136 + 批次文档收尾 #137。

## 当前方向

1. **前端 TS 渐进化的首个生产切片已真实落地并通过验收**：#133（`8b3709c`）交付 `frontend/tsconfig.json`（strict+noEmit，`include` 仅 `src/stores/app.ts`）+ `npm run typecheck`（仅本地）+ eslint `.ts` parser + vitest coverage 纳入 `.ts`，`app.js` → `app.ts` 无 shim。本轮独立复跑证据：`typecheck` exit 0、`--listFiles` 仅列 `app.ts`、47 files / 321 tests 全绿、`app.ts` 四项覆盖率 100、`lint`/`format:check`/`build` exit 0、仓库外类型负例探针复现 `TS2345` + `TS2322`（exit 2）、`package-lock.json` 418 插入 / 0 删除、`8b3709c` 五项 CI `completed/success`。
2. **方向从「建门禁」转为「把既有行为覆盖最强的模块逐个纳入门禁」**：TS 渐进化（D-009/D-018/D-019 已授权）是当前唯一可持续的真实选题——前端测试卫生补强已枯竭（余下仅 8 个声明式 API 薄包装属 mock 复述、`main.js`/`App.vue` 属壳层豁免），M6/M7 仍冻结。第二批选 `utils/echarts.js` + `utils/chinaMap.js`（第一批余项，迁移前覆盖率各 100/100/100/100，6 用例真实锁定）与 `stores/tabs.js`（193 行、41 用例锁定状态机、Lines 97.67 / Funcs 100 / Branch 95.77），两者都能用既有测试做行为回归，不需要发明新验收口径。
3. **边界不变**：`typecheck` 与前端覆盖率**仅限本地**，不纳入 CI / pre-commit，不设 `coverage.thresholds`；不新增依赖大版本、不改 schema / 认证 / 公共 API / 业务行为；M6 依 D-023 A 冻结、M7 依 D-019 A 冻结，#98 冻结现场不重置。

## 今日目标（2026-10-26）

- **#135**：`src/utils/echarts.js` 与 `src/utils/chinaMap.js` 干净迁移为 `.ts` 并进入 `tsconfig` 门禁（`include` 增至 3 项，compilerOptions 不动），同步去掉 `tests/china-map.test.js:34` 的显式 `.js` 扩展名；6 用例与全量 47/321 不缩水、coverage 含两个 `.ts` 且四项等值、`lint`/`build` 全绿。
- **#136**：`src/stores/tabs.js` 迁移为 `tabs.ts` 并入门禁；`TabItem` / `addTab` 最小结构类型 / `router?: { push: ... }` 按 Issue 钉死的契约标注，运行时语义（home 不可关、邻接激活、no-op 守卫、query 拼接、`resetTabs` 清理）逐字不变；41 用例全过、coverage 含 `stores/tabs.ts`。
- **#137**：批次文档收尾——`docs/TEST_PERF.md` §7.1 补 #133/#134 与 #135/#136 四行（状态按执行时点真实 Issue，不预支 `done`），§7.5 把 #133 的过期当前态就地改为时点表述并追加与当次 coverage 日志逐项一致的新快照段。
- Executor 每步完成后按契约 1.7 留固定字段执行报告并转 `in-review`（严禁自行 close），刷新 `STATE.md` / `HANDOFF.md`，在 `.agent/DIARY/2026-10-26.md` 追加日报。

## 当前授权切片：前端 TypeScript 渐进化（D-009；切片验收进度 1 / 3 —— #133 `done`，#135 / #136 待交付验收；#137 为配套文档收尾，不计分母）

> 注：属 D-009 已授权方向的有界推进，不新建 GitHub Milestone，不计入 M6 / M7 分母。

### 目标与验收

- 每个切片只迁移 Issue 钉死的模块，不留 `.js` shim / re-export / 双实现；不改运行时语义、不缩窄既有公共契约（如 `setTheme(string)`、`localStorage` 任意字符串、`icon: string | null`）。
- `frontend/tsconfig.json` 的 `include` 只按已迁移文件逐个增加；`compilerOptions` 保持 `strict` + `noEmit` + `allowJs`/`checkJs:false` + `noUnusedLocals`/`noUnusedParameters`，不新增 `baseUrl`/`paths`/`tsconfig.node.json`/`allowImportingTsExtensions`。
- 类型标注禁止 `any` / `@ts-ignore` / 文件级 suppress 用于掩盖自有代码错误；第三方/DOM 返回的 `any`（`Response.json()`、`JSON.parse`、axios 响应）允许沿用既有守卫并做**最小**断言，且断言须在报告中逐条列明理由。
- 每切片随代码更新 `docs/FRONTEND_TS_MIGRATION.md` §0 的「已迁移 / 尚未迁移」清单（如实写明仍未迁移范围，不承诺全仓类型安全）。
- 迁移必须同步修正指向被改文件的**显式 `.js` specifier**（本轮实测仅两处：`tests/china-map.test.js:34`、`tests/tabbar-icons.test.js:5`），不得用 mock 技巧绕过模块解析变化。

### 完成信号（Success signal）

- 出现以下事实即为本批次完成：`find frontend/src -name "*.ts"` 恰含 `stores/app.ts`、`stores/tabs.ts`、`utils/echarts.ts`、`utils/chinaMap.ts`；`npm run typecheck` exit 0 且 `--listFiles` 不含任何 `.js`/`.vue` 生产文件；前端全量 ≥47 files / 321 tests 全绿且 coverage 报告包含上述 4 个 `.ts` 且各项不低于迁移前实测；`docs/TEST_PERF.md` §7.1 与 §7.5 反映执行时点真实状态。
- 单个切片「完成」的判据是：交付经 Planner **独立复跑**验收通过并 `done`（不是 Executor 自报，也不等于整个 TS 迁移收敛）。

### 明确非目标（Non-goals）

- 不迁移 `plugins/elementPlus.js`、`utils/index.js`、`utils/authSession.js`、其余 store（`user.js`、`analysis.js`）、api/（14）、composables/、router/、`main.js` 与 45 个 `.vue`。
- 不给 `_persist`（`tabs.js:52–54`）加 try/catch / 重试 / 事务（D-034：等真实故障证据）；不改 `ensureChinaMap()` 的失败恢复契约。
- 不改 `.github/workflows/`、pre-commit、CI 矩阵；不把 `typecheck` 或前端覆盖率纳入 CI；不设 `coverage.thresholds`。
- 不为薄包装模块补 mock 复述测试，不为入口/根壳补测试；不重查 V8 coverage 小数抖动根因。
- 不动 #98 冻结现场，不启动 M7 扩展，不降低 M6 阈值。

### 执行队列（给 Executor 的建议顺序，保持 3 个 ready）

1. **[#135 迁移第一批剩余图表工具 echarts.js 与 chinaMap.js 为 TypeScript 并纳入本地类型门禁](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/135)**（P2，`ready`）—— 分支 `agent/issue-135-utils-ts`。
2. **[#136 迁移 stores/tabs.js 为 TypeScript 并保持多标签工作区状态机语义不变](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/136)**（P2，`ready`）—— 分支 `agent/issue-136-tabs-store-ts`（与 #135 无相互依赖，但同改 `tsconfig.json` 的 `include`，须在其后并入以免回退他人条目）。
3. **[#137 收尾 TS 第二批次验收账并追加执行时点覆盖率快照](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/137)**（P4，`ready`）—— 分支 `agent/issue-137-ts-batch2-docs`（硬依赖 #135 / #136 先执行）。

## 保留的 Milestone 事实与成功阈值

### M6 测试性能优化（进度：成员 10 / 10 CLOSED；成功信号 1 / 3；状态：OPEN 未收敛）

- 成员 #88–#95、#106、#107 共 10 项全部 `CLOSED`。
- 三个成功信号：分支覆盖率 `≥68.49%` 已达成（68.5259%–68.63%）；本地串行无 coverage `<30s`（实测 ~34–39s）与完整 CI `<240s`（实测 247–329s）未达成。
- 依 D-023 默认 A：保持 Milestone OPEN，不调低阈值、不重启高成本或触红线方案（契约 3.8：成员关闭 ≠ Milestone 收敛）。

### M7 候选与既有交付纠偏（进度：6 / 11 CLOSED；状态：OPEN 且冻结）

- 已验收关闭（6）：#97、#99、#103、#104、#105、#108。
- 未完成（5）：#98（`in-progress`，D-019 A 有意冻结）、#100（`needs-info`）、#101（`needs-info`）、#102（`needs-info`）、#109（`blocked`）；#96 为 Epic 不计入分母。
- 依 D-019 默认 A：暂停 M7 扩展，保留前端 TS 渐进化方向。

## 已知阻塞与依赖

- **#109（`blocked`）**：本轮 `command -v docker` 仍 exit 1，本机无 Docker、无已授权远程 Docker 主机；环境就绪前不得以 console 探针替代真实 Jaeger / OTLP 验收。
- **#98（`in-progress` 冻结）**：受 D-019 A 冻结，保持现场不重置、不关闭，Executor 不得领取；虽超 24h 无日报活动，仍按既往裁定不标「疑似中断」。
- **#96 / #100 / #101 / #102（`needs-info`）**：受 D-019 A 冻结（#102 同时依赖 #98，且跨版本 CI 矩阵属契约 1.10 红线）。
- **#59（`needs-info`）**：待用户提供具体产品功能需求（D-012 默认 A 有效，不重复追问）。
- **#137 依赖链**：只有 #135 / #136 已交付（无论是否已验收）才可执行 #137；未交付项按 Issue 规定如实登记缺失，不预支状态。

## 下一阶段

- #135 / #136 通过验收后，按 `docs/FRONTEND_TS_MIGRATION.md` §2 继续小步编排：第一批收尾（`plugins/elementPlus.js`）与第二批（`utils/index.js`、`utils/authSession.js`、api/ 层）中行为覆盖最强的模块优先；api/ 类型化需先定响应契约，届时若无明确判定口径则建 `needs-info` 而非硬排。
- 若用户提供 #59 具体产品需求，或对 D-019（M7）/ D-023（M6）/ 「把 `typecheck` 纳入 CI」给出新授权，按用户新决定重排队列。

## 已放弃的方向

- 登录验证码（D-02 暂缓）· 归档 SQL（D-03 保留）· uv/venv 整包缓存（D-013 / D-016 放弃）· session 级训练缓存（D-014 放弃）· 默认开启 xdist / randomly / 全局 pytest-socket（D-024 放弃）· M7 未授权扩展（D-019 A 冻结）· M6 降阈值或改 CI 级联（D-023 A 冻结）· 为 8 个声明式 API 薄包装补 mock 复述测试、为 `main.js`/`App.vue` 补壳层测试（D-031/D-032 非目标）· 凭风格差异给 `_persist` 排容错（D-034 等真实故障证据）。

## 给 Executor 的指令（不超过 2 句）

- 按 **#135 → #136 → #137** 串行执行，`ENV.md` 未设 `WORKFLOW=trunk`，严格用每任务独立分支（`agent/issue-135-utils-ts`、`agent/issue-136-tabs-store-ts`、`agent/issue-137-ts-batch2-docs`）完成验证 → `git pull --rebase` → 合入 `main` → push → 删临时分支。
- 遇到「必须改运行时语义才能过类型检查」或模块解析异常时**立即转 `needs-info` / `blocked` 并写明冲突点**，不要私改语义、不要用 mock/断言链绕开；收尾时按真实 Issue 状态刷新 `STATE.md` / `HANDOFF.md` 并追加 `.agent/DIARY/2026-10-26.md`（`.agent/` 单独 `chore(agent)` 提交）。
