# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：2026-10-19 执行轮。本席 executor；领取今日队列 #113。
- 状态：in-review：无（#111/#112 已验收关闭）；in-progress：#113；ready：无。
- 本轮起点 main `4a98069`；分支 `agent/issue-113-mock-invalid-email`。
- CI：最新 run 39123822632 @ `db0f843` 四 job success。
- 后端 fast gate 本机基线（2026-10-19 实测，no-cov）：native（WEIBO_CORE_RUST=1）1494 passed / 69 skipped / 196 deselected（37.02s，wall time 39.33s）；全绿。
- 跨天链：正常（2026-10-19）——STATE 已刷新，领取 #113。

## 阻塞项
- #84（历史）：曾 blocked，已由 Planner 在上轮关闭，不再是阻塞项；勿重开。
- #109（2026-10-17 仍 blocked）：本机无 Docker、无已知已授权 Docker 主机；console smoke 不替代真实 profile/UI 验收。

## 关键事实（已实测验证）
- **前端规模（#68 后）**：.js 32（api 14 · utils 5 · stores 4 · composables 6 · router 1 · plugins 1 · main.js）· .vue 45（views 6305 行 · components 3322 行）· JS+Vue 合计 13,731 行。
- **前端测试基线（#81 后）**：41 files / **190 tests** 全绿（#86 后 187 → #81 +3 → 190）。
  漂移说明：#82 后 109，#67 新增 `alert-center-states.test.js` (+5) → 114，#68 新增 `task-list-loading.test.js` (+3) → 117。
- **大屏数据链路（#62 实测）**：`useBigScreen` 5 处失败路径原仅 `console.error`；`analysisStore.fetchAll` 内部 `allSettled`，**失败不抛出**，失败信息落在 `store.error`（只记第一项）。
- **拦截器兜底（勿重复弹窗）**：`api/request.js:82-166` 对每个失败请求已弹 ElMessage（业务码/HTTP 码/网络错误三类）。
- **#19 失败态语义落地状态**：`useTable.js` 已删；语义已落地在 #62、#65、#66、#67（失败保留旧数据 + 显式错误态/重试）。
- **UX 三件套缺口（#60 调研，逐项对应 Issue）**：BigScreen(#62)、platform(#65)、spider(#66)、alert-center(#67)、tasks(#68) 已全部补齐；
  其余缺 loading：Profile(#70/#71)；
  缺视图级错误态：report(#69)；
  缺空态：BigScreen 热门话题(#78) / comment 热门评论(#80)。
- **响应式**：`Layout/index.vue:53-55` 与 `MobileNav.vue:40-42` 各一份硬编码 <768。R-1（#72）以 Layout 传 prop 实现单源。
- **测试盲区**：持续消化中，新增 `login-journey.test.js` (8)、`alert-center-states.test.js` (5)、`task-list-loading.test.js` (3)。
- **编译器警告**：`home/index.vue:61` `const filters = reactive(...)` 配 `v-model`（模板 `:4`），vitest 持续输出 `v-model cannot update a const reactive binding filters`（归 U-11 #80）。

## 已完成
- **#111 完成转 in-review（2026-10-18）**：同步旧 ruff 命令至各活文档与脚本（`scripts/verify_project.ps1`、`docs/DEVELOPMENT.md`、`docs/RELEASE_CHECKLIST.md`、`README.md`、`docs/CODING_STANDARDS.md` 统一包含 scripts）+ 刷新 `docs/TEST_PERF.md` §7.1 议题状态总表（#106/#107/#108/#110 done，补 #112 in-review，备注 M6 10/10 CLOSED 但保持 OPEN）+ §6.1 增加 #108 关键路径误写更正（实际 run 287s）；未动生产代码/测试代码/历史归档；提交 `6834534` → merge `73e0074` @ main（已推送）；报告 comment 6249412466。
- **#112 完成转 in-review（2026-10-18）**：M6 残余差距只读分析（为 D-023 准备证据）——本地 fast gate 耗时分解（collection 10.94s 占 27%、native 40.62s、fallback 40.12s、最慢 Top15 详情与长尾结构）+ 4 个近期 CI run 实测分解（关键路径 247–329s、pip 缓存 100% 命中但解包方差 54–82s、串行流水线结构为主要耗时瓶颈）+ 5 项候选杠杆深度评估（L1-L5）与三类结论归纳；仅改 `docs/TEST_PERF.md`（+92 行），未改动任何生产代码/测试/CI/阈值；提交 `0c10122` → merge `33be94a` @ main（已推送）；报告 comment 6249381242。
- **#110 完成转 in-review（2026-10-17）**：`append_api.py` 第 4 行拆分 + 删 UP009（**未运行**，`docs/API.md` sha256 前后一致 `71f7dcb8…d9ea1f`）+ batch_add_markers/download_bert_model/word_cloud_picture 机械修复（逐项行为不变已论证）+ `scripts` 纳入 ruff 门禁（AGENTS.md L5/L9 + ci.yml L49，同一 step 不新增 job）；`ruff check src tests scripts` 0 error；CI run 38999825154 四 job 绿、Ruff 步骤按新路径通过；native 1494/69/196、fallback 1492/71/196（+11 = #107 +12 − #106 1）；提交 `cd0ea53`+`21535bc` → merge `1abfaf0` @ main（已推送）；报告 comment 6229255290。
- **#108 完成转 in-review（2026-10-17）**：Rust 工具链 pin 生效（`rust/toolchain.toml`→`rust-toolchain.toml`）+ `rust/weibo_core/pyproject.toml` + README 构建说明（`--release` 强制）+ `.env.example` 四变量 + ADR-0005 边界 + triage-labels 映射；pin 双证据（rustup overridden + A/B 回落），CI runner 未预装 1.99.0、由 pin 触发自动安装后 `rustc 1.99.0`（run 38999122715 四 job 绿）；maturin build/develop + wheel + smoke 全过；native 1494/69/196、fallback 1492/71/196；提交 `1889b6f`…`e2ecb5c` → merge `ddea0a9` @ main（已推送）；报告 comment 6229127684。
- **#106 完成转 in-review（2026-10-17）**：CI backend-fast 步骤真实 `--durations` Top10 写入 step summary（tee + PIPESTATUS 保退出码；>120s 软告警保留；summary 以折叠 group 回显日志供无 UI 验收；演练 4/4）+ 单例串扰隔离（删 `test_predictor_singleton`，autouse fixture 恢复 `_model`，生产缓存未动）+ socket 审计（探针不豁免 localhost：3 来源逐项，不修/仅记录）+ #95 同机前后复测（目标两用例 6.02s→<0.01s；full gate 37.49s→30.54s，-18.5%）+ TEST_PERF §6/§6.1/§7 重写 + .agent 跨天链回填（STATE/ENV/HANDOFF/日报 10-15、10-16 补记 2026-10-17）；提交 `cafe8ed`+`2f6790c`+`e23ba43` → merge `9a13987` @ main（已推送）；CI 38998104877 四 job 绿、step summary 经日志核对；计数变化 −1 已在报告解释。
- **#107 完成转 in-review（2026-10-17）**：可观测模块行为验证恢复——四处失败真因=SDK console exporter 导入期绑定 `sys.stdout`（非未 flush），`_bind_console_streams(out)` 重指已构造 exporter 流；删除 incidental 测试、合并重复探针、拆出 `test_observability_disabled.py`（150 行）；native 1495/69/196、fallback 1493/71/196 双绿；覆盖率 native 68.5259%（11106/16207，JSON 复核）/ fallback 68.51% / CI 68.62% ≥68.49%；`observability.py` 98% stmt / 94% branch；提交 `1d78f05`（test）+ `339c891`（docs）→ merge `be32bd0` @ main（已推送）；CI 38995283704 四 job 绿；`scripts/demo_otel_trace.py` 退出 0。
- **#105 验收关闭（2026-10-17，交付 2026-10-16）**：去重基准真实重复率校正（10k/100k 实测 distinct=1000/10000 + 全唯一对照）+ 真跑 Criterion（7 bench × 100 采样，estimates.json 程序化读回）+ 发现 `maturin develop` dev 构建慢 ~20x（必须 `--release`）；提交 `48e00c0`…`515c8c4` → merge `85f7f44` @ main。
- **#104 验收关闭（2026-10-17，交付 2026-10-16）**：Rust bridge Unicode 等价性（空白谓词改 White_Space ∪ U+001C–U+001F）+ iterator 回退丢数修复；`cargo test` 11 passed；native 1483/69/196、fallback 1481/71/196；提交 `9a75875` → merge `a88fd7a` @ main。
- **#90 部分完成转 in-review（2026-10-14）**：requirements-ml.txt 新建（7 重包 pin verbatim 迁移，union 程序化核对一致）+ ci.yml 两 job 分层安装 + freeze 漂移探针 + Dockerfile/deploy.py/security-scan 双 -r 同步；CI run 38557692302 三 job success；install 90+92=182s → 78+63=141s（-22.5%），<110s 未达成（差 31s）；提交 a023b1d → merge 26ce9ed @ main（已推送）；YAML/py_compile/paths-check 全过。
- **#92 完成转 in-review（2026-10-14）**：sentiment_model 评估 ×2 取 NB+LogReg 子集（5.60/5.63s → 2.53/2.37s，断言未动）+ model_training 抽样 500 条补 2 断言 + 3.01s×2 归因（/ready redis 3s 超时，CI 同样中招，不修）+ test_performance 0.83s 记录；gate 47.98s → 39.33s（计数一致）；提交 23818f3 → merge 0730b7f @ main（已推送）；ruff clean。
- **#91 完成转 in-review（2026-10-14）**：xdist 本机灰度三轮全绿（串行 50.42s → -n 4：30.64s/31.55s → -n 8：25.20s；计数 1460/69 一致，collect-only 1526/1722 选择一致；零顺序污染）+ TEST_PERF §6/§7 回写；结论暂不纳入 AGENTS.md 默认门禁（xdist 未进 requirements）；提交 12336ba → merge 7be3df9 @ main（已推送）；无 src 改动故 ruff/覆盖率全量/CI 逐项说明未跑原因，见执行报告。
- **#89 完成转 in-review（2026-10-13）**：ci.yml integration needs 去掉 frontend-fast（1 行；job 内零前端引用已 grep 实证；YAML 解析通过）；提交 2caabe8 → merge 3a0471c @ main（已推送）；CI 全绿核对通过（integration 紧随 backend 启动，不再等 frontend；本次 frontend 本就更快，1m19s 为结构性收益）。
- **#88 完成转 in-review（2026-10-13）**：conftest 会话级强制 jti 黑名单内存回退（+7 行；定向 43 passed/5s；fast gate 182.9s→34.9s，-81%；ruff clean；计数 1460/69/196 与基线一致）；提交 4cd99a6 → merge b19432a @ main（已推送）；CI backend-fast success 不回归。
- **#81 完成转 in-review（2026-10-12）**：平板档差异化（Layout checkMobile 单源扩展 isTablet + provide；home R-2 条件 sm 中间档；新增 `tablet-tier.test.js` 3 用例；mobile-single-source 计数断言连带更新）；提交 d5a1312 → merge abb3b98 @ main（已推送）；前端五门禁全绿（190/190）+ 后端 ruff clean。
- **#86 完成转 in-review（2026-10-12）**：formatDuration 收敛 utils 单源（2 处本地删除；`format-utils.test.js` +2 用例）；提交 25578f7 → merge 3a0b33a @ main（已推送）；前端五门禁全绿（187/187）+ 后端 ruff clean。
- **#80 完成转 in-review（2026-10-12）**：home filters 受控更新（:model-value + Object.assign，const 保持；告警 1→0；新增 `home-filters-update.test.js` 1 用例）；提交 532d2a9 → merge 1c123c7 @ main（已推送）；前端五门禁全绿（185/185）+ 后端 ruff clean。
- **#79 完成转 in-review（2026-10-12）**：静态 grep 替换真实挂载（icon-registration 重写 + element-plus 三元探针 + tabbar 路由记录挂载；三组 RED→GREEN 实证；只改测试未改源码）；提交 9caacfd → merge 53f8c57 @ main（已推送）；前端五门禁全绿（184/184）+ 后端 ruff clean。
- **#87 完成转 in-review（2026-10-12）**：comment 热门评论空态（.hot-comments-empty/暂无热门评论，仅空非 loading 时显；新增 `comment-empty.test.js` 3 用例）；提交 cde0a13 → merge 5684b80 @ main（已推送）；前端五门禁全绿（184/184）+ 后端 ruff clean。
- **#78 完成转 in-review（2026-10-12）**：BigScreen 热门话题空态（.no-topics/暂无话题，仅空非 loading 非失败时显；新增 `bigscreen-topics-empty.test.js` 3 用例）；提交 0cc904f → merge 89cb8b2 @ main（已推送）；前端五门禁全绿（181/181）+ 后端 ruff clean。
- **#77 完成转 in-review（2026-10-12）**：predict 模型信息错误态（modelInfoError + 重试；空态仅无错无数据时显；新增 `predict-model-error.test.js` 3 用例）；提交 e6383d0 → merge cba3445 @ main（已推送）；前端五门禁全绿（178/178）+ 后端 ruff clean。
