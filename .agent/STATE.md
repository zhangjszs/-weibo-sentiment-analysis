# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 更新时间：2026-11-22T13:05:20+08:00
- 当前任务：无；本轮队列无 `ready`。待 Planner 验收：#141、#142、#144、#145（`in-review`）；#143（`blocked`）。
- 分支：业务交付已合入 `origin/main`；续查通过隔离工作树完成，原用户 `main` 工作树未动。
- 未完成工作：#143 历史 auth 双文件漂移未复现；当前聚合分支漂移已定位至 `mergeProcessCovs` 顺序，解除条件见 HANDOFF / Issue。
- 最近业务提交：`b0737dd`（#145 契约盘点）、`d423f3b`（#143 调查台账）、`b6661ad`（#144 锁更新），均已推送、各五项 CI 成功。#141/#142 既有补证及 CI 已在日报恢复。
- 前轮交接 `818860b` 已推送，查得 backend-fast / frontend-fast / integration / rust-core / security-scan 五项均 `completed/success`；续查未领取任务。
- 今日日报：已写 `.agent/DIARY/2026-11-22.md`。
- 已知环境限制：原工作树已有未暂存改动，`git pull --rebase` 退出 128；隔离工作树同步成功。Node 26 干净配置须 `NODE_OPTIONS=--no-webstorage` 才由 jsdom 提供测试存储。

## 阻塞项
- #143（blocked）：需要历史 `auth.js` / `Login.vue` 跳变的 V8 原始输入，或 Planner 独立划定工具链验证范围；不改测试凑指标。
- #109（blocked）：本机无 Docker、无已授权远程 Docker 主机；console smoke 不替代真实 profile/UI 验收。
- #98（M7 冻结）：D-019 默认 A 保持现场不重置，下一棒不得领取。
- #96 / #100 / #101 / #102 / #59（needs-info）：受 D-019 A 冻结或待产品需求确认。

## 历史验证快照（2026-10-27）
- **TS 类型门禁现状（#139 + #140 本会话实测）**：`frontend/tsconfig.json` 的 `include` = `["src/stores/app.ts","src/stores/tabs.ts","src/utils/echarts.ts","src/utils/chinaMap.ts","src/utils/authSession.ts","src/utils/index.ts"]`（**6 项**）；**`lib` 由 ES2020 提升至 ES2021**（`downloadCsv` 沿用既有实现中的 `String.prototype.replaceAll`，`lib: ES2020` 实测 TS2550），**`target` 仍为 ES2020**——故**只影响类型声明、不影响 emit 与运行时**。`npm run typecheck` 仍**仅本地**，不入 CI/pre-commit。
- **运行时语义零改动（#135–#140 全批次，双重自证）**：`tsc --outDir` 转译回 JS + 用**仓库同一份 `.prettierrc.json`** 规范化后与迁移前 `.js` 逐行 diff，剥除空行与注释 → #135 `chinaMap.ts` **差异 0**、`echarts.ts` **纯重命名内容 0 差异**；#136 `tabs.ts` **可执行语句差异 0**；#139 `authSession.ts` **可执行语句差异 0**；#140 `index.ts` **可执行语句差异 2 行**（**恰为已申报的 2 处语义等价改写**：`String(d.getFullYear())`（JS 的 `String.replace` 本就对 replaceValue 做 ToString）、`now.getTime() - target.getTime()`（JS 的 `-` 对 Date 走 ToPrimitive(hint number) → `valueOf()`））。**该自证在本批次抓到了 3 处真实问题**（对象字面量被 prettier 展开、`const source = obj` 多出一行、`tsc --outDir` 绕过 tsconfig 致 lib 不一致）。
- **类型断言审计（本批次）**：#135 断言 **0**（`MapInput` 由 echarts 签名派生，无需 `as`）；#136 断言 **1**（`as TabItem[]`）；#139 断言 **1**（`as SessionUser`）；#140 断言 **5**（全在 `deepClone`）。**全部批次 `any` / `@ts-ignore` / `eslint-disable` / 非空断言 `!.` / 类型谎言 均为 0 处。**
- **类型负例探针（临时文件，均已 rm、未入库；删除后 typecheck 再 0）**：#135 → exit 2 `TS2554`；#136 → exit 2 `TS2559`+`TS2345`；#139 → exit 2 `TS2345`×2+`TS2531`+`TS2571`；#140 → exit 2 `TS2345`×2+`TS2339`。**四个批次错误号全部与 Planner D-038 预验证预测一致。**
- **`@/utils` 桶解析已实测**：`src/utils/index.js` 已不存在，7 个 `from '@/utils'` 消费点（3 个 `.vue` + 2 个 composable + 2 个 view）经 `npm run build` exit 0 与 47/321 全绿证明解析到 `index.ts`。`vite.config.js` 的 `resolve` 只配 `alias` 未覆盖 `extensions`，Vite 默认扩展名链生效。**浏览器端点对点冒烟未做**（已写入 #140 报告剩余风险）。
- **覆盖率口径澄清（#139/#140 本会话实测）**：① `authSession.ts` 87.17/83.33/100/87.17 与基线**四项逐项等值**，lcov 零命中 **10 行 ↔ 10 行**逐条源文本一一对应。② `index.ts` 98.26/97.08/100/98.26 vs 基线 98.23/97.08/100/98.23 —— lcov **FNF 20/FNH 20、BRF 103/BRH 100 逐项相同**；LF 226→230 / LH 222→226（**found +4 / hit +4**），未覆盖 **4 条语句逐字相同**。**98.23→98.26 是分母 +4 的记账效应，不是覆盖率提升**（与 #136 的 97.67→98.56 同源）。
- **验收轮实测（#135/#136/#137 本会话独立复跑）**：`npm ci` 0（lockfile 零改动）；typecheck 0；`--listFiles` 4 个 `.ts`、0 个 `.js`·`.vue`；负例 `TS2554`+`TS2559`+`TS2345`（exit 2）；china-map 6 / tabs-store 41 / tabbar-icons 3；47/321 全绿；coverage 与原报告**逐项等值**；lint/format/build 0；eslint JSON 非 ignored；**`git show --stat` 逐提交核对 + 禁改文件零触碰**；CI 五项 success。三项均已 CLOSED / `done`。
- **跨运行覆盖率抖动已定位（#138 auto-discovered）**：**同一 HEAD 下连续两次** `npm run test:coverage`，`src/api/auth.js`（38.46 → 17.94）与 `src/views/auth/Login.vue`（100|75|50|100 → 97.87|76.92|75|97.87）数值不同 → `All files` 随之漂移；**`stores/tabs.ts` 两次完全相同**。既有 D-034 抖动带只覆盖语句/分支，**未覆盖函数项（Funcs）**。已登记 #138，未定级。
- **TEST_PERF 账目（#137 + 验收回填）**：§7.1 追加 #133/#134/#135/#136 四行（#135/#136 已于 2026-10-27 回填 `done`）；§7.5 就地把 #133 的过期当前态改为时点表述；追加 2026-10-26 执行时点快照段（绑定当次 coverage 原始日志，不入库；路径见当日日报）；**§7.2–§7.4 与 HEAD 逐行 diff 证明 byte-identical**；历史数值与 `app.js`/`tabs.js`/`chinaMap.js` 旧路径全部保留。
- **user store 会话恢复（#127）/ chinaMap 单例（#128）/ tabs 状态机（#131）**：既往实测记录，本会话未改动这些测试文件。

## 已完成（最近）
- #145：`b0737dd` 已推送，盘点 §9，7 TS/0 JS/Vue、49 个链接及五项 CI 成功；报告 7074006035。
- #143：`d423f3b` 已推送，取证台账，未修复；报告 7073909332、CI 补证 7073952654。
- #144：`b6661ad` 已推送，三项目标告警消失，47/321、bundle 和 CI 通过；报告 7073836608。
- #141/#142：历史交付与本日恢复资料补入日报；报告 7067430942、7067407062；`in-review` 待验收。
- **#140 交付转 in-review（2026-10-27 会话 1）**：`src/utils/{index.js => index.ts}`（19 个导出）+ `tsconfig` 的 `lib` ES2020→ES2021（target 不变）+ 2 个测试文件各 1 行 + 策略文档；5 files；typecheck 0/负例 TS2345×2+TS2339/56 用例/47·321/coverage 98.26·97.08·100·98.26/lint·format·build/桶解析实测正常；**2 处语义等价改写已主动申报**；CI 五项绿；提交 `92cd03b` @ main（已推送）；报告 comment 6422665489。
- **#139 交付转 in-review（2026-10-27 会话 1）**：`src/utils/{authSession.js => authSession.ts}` + include 第 5 项 + `auth-session.test.js` 1 行 + 策略文档；4 files；typecheck 0/负例 TS2345×2+TS2531+TS2571/32 用例/47·321/coverage 87.17·83.33·100·87.17/转译 diff 0 差异；CI 五项绿；提交 `f0661bb` @ main（已推送）。
- **#135/#136/#137 验收关闭（2026-10-27）**：独立复跑验收通过；验收 comment 6422214957 / 6422223027 / 6422232092；回填 `docs/TEST_PERF.md` §7.1 状态 `00872f6`。
- **#138 登记（2026-10-26 会话 1）**：auto-discovered——`src/api/auth.js` 与 `src/views/auth/Login.vue` 覆盖率跨运行波动（仅打 `auto-discovered` 标签，未定级/未定 milestone）。
- **#134/#133 验收关闭（2026-10-26）**：`d385af4` / `8b3709c`。
- **#132 验收关闭（2026-10-24）**：`06b194e`。
- **#131 验收关闭（2026-10-24）**：`9a86951` tabs store 41 用例。
- **#130 验收关闭（2026-10-24）**：`73bec15` app store 9 用例。
- **#129/#128/#127 验收关闭（2026-10-24）**：`4d00f9c` / `4cb2519` / `ffe4c5b`。
- **#123 验收关闭（2026-10-23）**：前端 vitest 本地覆盖率可见性；`6812039`。
- **#120/#121/#122 验收关闭（2026-10-22）**：`d7e0c59` / `6a37d95` / `0f2221c`。
- **#113–#119 验收关闭（2026-10-19/20）**：见 git 历史。

## 交接
- 本轮结束以 `.agent/HANDOFF.md` 与 `.agent/DIARY/2026-11-22.md` 为准；历史 10-27 日报不改。
