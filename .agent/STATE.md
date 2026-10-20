# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：2026-10-20 执行轮（会话 2）。本席 executor；今日队列 3 项（#117, #118, #119）全部完成转 in-review，ready 队列清空。
- 状态：in-review：#117, #118, #119；in-progress：无；ready：无。
- 本轮起点 main `74e2f4c` → 现 main `ab430f7`（#117 `8f1cc63` + #118 `574aa34` + #119 `ab430f7`；已推送）。
- 后端 fast gate 本机基线（#118 后实测，no-cov）：native（WEIBO_CORE_RUST=1）1495 passed / 69 skipped / 196 deselected / 95 warnings（46.84s）；fallback（WEIBO_CORE_RUST=0）1493/71/196 / 95 warnings（42.59s）；全绿；警告总数较此前（149）净减 54 条（消除全部 7 处自有 `datetime.utcnow()` 及 SQLAlchemy 对应告警）；用例数较前基线 +1。
- 前端测试基线（#119 后实测）：41 files / **190 tests** 全绿（6.89s），stderr `stderr |` 块数彻底归零（32 → 0），彻底收敛 10 个测试文件的预期 `console.error` 噪声。
- 跨天链：正常（2026-10-20）——STATE 已刷新、HANDOFF 于本轮末重写；DIARY 已追加 2026-10-20 当日会话 2 记录。

## 阻塞项
- #84（历史）：曾 blocked，已由 Planner 在上轮关闭，不再是阻塞项；勿重开。
- #109（2026-10-17 仍 blocked）：本机无 Docker、无已知已授权 Docker 主机；console smoke 不替代真实 profile/UI 验收。

## 关键事实（已实测验证）
- **前端规模（#68 后）**：.js 32（api 14 · utils 5 · stores 4 · composables 6 · router 1 · plugins 1 · main.js）· .vue 45（views 6305 行 · components 3322 行）· JS+Vue 合计 13,731 行。
- **前端测试基线（#81 后）**：41 files / **190 tests** 全绿（#86 后 187 → #81 +3 → 190）。
- **Element Plus 3.0 前向兼容（#116 后）**：`report.vue`、`Header.vue`、`PredictInput.vue`、`spider.vue` 中绑定值的 `<el-radio-button>` 和 `<el-checkbox>` 已全部迁移至 `value` 属性，测试 stderr 零废弃警告。
- **大屏数据链路（#62 实测）**：`useBigScreen` 5 处失败路径原仅 `console.error`；`analysisStore.fetchAll` 内部 `allSettled`，**失败不抛出**，失败信息落在 `store.error`（只记第一项）。
- **拦截器兜底（勿重复弹窗）**：`api/request.js:82-166` 对每个失败请求已弹 ElMessage（业务码/HTTP 码/网络错误三类）。
- **#19 失败态语义落地状态**：`useTable.js` 已删；语义已落地在 #62、#65、#66、#67（失败保留旧数据 + 显式错误态/重试）。
- **UX 三件套缺口（#60 调研，逐项对应 Issue）**：BigScreen(#62)、platform(#65)、spider(#66)、alert-center(#67)、tasks(#68) 已全部补齐；
  其余缺 loading：Profile(#70/#71)；
  缺视图级错误态：report(#69)；
  缺空态：BigScreen 热门话题(#78) / comment 热门评论(#80)。
- **响应式**：`Layout/index.vue:53-55` 与 `MobileNav.vue:40-42` 各一份硬编码 <768。R-1（#72）以 Layout 传 prop 实现单源。
- **测试盲区**：持续消化中，新增 `login-journey.test.js` (8)、`alert-center-states.test.js` (5)、`task-list-loading.test.js` (3)。
- **编译器警告**：`home/index.vue:61` 的 `v-model cannot update a const reactive binding filters` 告警经实测已消除（vitest 运行 stderr 匹配数为 0，见 #80 与 2026-10-20 验收记录）。

## 已完成
- **#119 完成转 in-review（2026-10-20）**：在 10 个测试文件中 spy/mock `console.error` 并断言预期错误记录；前端 41 files / 190 tests 全绿，stderr `stderr |` 块数从 32 降为 0，lint 与 build exit 0；提交 `ab430f7` @ main（已推送）；报告 comment 6289797541。
- **#118 完成转 in-review（2026-10-20）**：`tests/test_model_improvements.py` 的 `main()` 增加失败计数与 `sys.exit(1)`；新增 `test_main_exit_code_on_failure` 测试失败退出码（monkeypatch 隔离真实训练）；直跑成功退出码 0；fast gate native 1495/69/196、fallback 1493/71/196 全绿（用例数 +1）；提交 `574aa34` @ main（已推送）；报告 comment 6289685135。
- **#117 完成转 in-review（2026-10-20）**：替换项目中 7 处 `datetime.utcnow()`（5 个模型默认值 + startup_service + comment_repository）为共享 `utils.datetime_utils:utcnow_naive()`；补齐 SQLite 下 naive UTC 回归测试；fast gate native 1494/69/196（95 warnings）、fallback 1492/71/196（92 warnings）双模式全绿，警告数净减 54+ 条；提交 `8f1cc63` @ main（已推送）；报告 comment 6289606009。
- **#116 完成转 in-review（2026-10-20）**：Element Plus 单选与复选组件 label act as value 弃用警告收敛（`report.vue`、`Header.vue`、`PredictInput.vue`、`spider.vue` 统一使用 `value`）；前端 41 files / 190 tests 全绿，stderr 消除相关警告，lint 与 build exit 0；提交 `4a32dbe` → merge `d4bce28` @ main（已推送）；报告 comment 6272114114。
- **#115 完成转 in-review（2026-10-20）**：`tests/conftest.py` 的 app fixture 补全 Celery eager 存储配置（`task_store_eager_result=True` 与环境变量覆盖）；消除任务状态查询测试中的 Celery `RuntimeWarning`；fast gate native 1494/69/196、fallback 1492/71/196 全绿；提交 `9b952cf` → merge `2a3b703` @ main（已推送）；报告 comment 6272071417。
- **#114 完成转 in-review（2026-10-20）**：`tests/test_model_improvements.py` 移除 6 处测试函数末尾 `return <obj>`，消除 `PytestReturnNotNoneWarning`；移除吞异常 `try...except: return False` 假绿反模式并补齐有效断言；支持脚本直跑与 pytest 双通道；fast gate native 1494/69/196、fallback 1492/71/196 全绿；提交 `89a53ce` → merge `b225c32` @ main（已推送）；报告 comment 6272014524。
- **#113 验收关闭（2026-10-19）**：`test_send_invalid_email` 复用 `patch("smtplib.SMTP_SSL")` 模式消除真实出站 DNS/网络调用（`call 0.01s`，`socket.getaddrinfo` 探针验证 0 次网络出站调用；`assert success is False` 与 `mock_ssl.assert_called_once_with` 断言通过）+ 刷新 `docs/TEST_PERF.md` §7.1 议题状态总表（#111/#112 刷新为 done）；未动生产代码/网络全局策略/历史归档；提交 `6c6a0b6` → merge `53a8140` @ main（已推送）；报告 comment 6260549034。
- **#111 验收关闭（2026-10-18）**：同步旧 ruff 命令至各活文档与脚本（`scripts/verify_project.ps1`、`docs/DEVELOPMENT.md`、`docs/RELEASE_CHECKLIST.md`、`README.md`、`docs/CODING_STANDARDS.md` 统一包含 scripts）+ 刷新 `docs/TEST_PERF.md` §7.1 议题状态总表（#106/#107/#108/#110 done，补 #112 in-review，备注 M6 10/10 CLOSED 但保持 OPEN）+ §6.1 增加 #108 关键路径误写更正（实际 run 287s）；提交 `6834534` → merge `73e0074` @ main。
- **#112 验收关闭（2026-10-18）**：M6 残余差距只读分析（为 D-023 准备证据）——本地 fast gate 耗时分解 + 4 个近期 CI run 实测分解 + 5 项候选杠杆深度评估与三类结论归纳；仅改 `docs/TEST_PERF.md`（+92 行）；提交 `0c10122` → merge `33be94a` @ main。
- **#110 验收关闭（2026-10-17）**：`append_api.py` 第 4 行拆分 + 删 UP009 + batch_add_markers/download_bert_model/word_cloud_picture 机械修复 + `scripts` 纳入 ruff 门禁；CI run 38999825154 四 job 绿；提交 `cd0ea53`+`21535bc` → merge `1abfaf0` @ main。
- **#108 验收关闭（2026-10-17）**：Rust 工具链 pin 生效 + `.env.example` 四变量 + ADR-0005 边界 + triage-labels 映射；提交 `1889b6f`…`e2ecb5c` → merge `ddea0a9` @ main。
- **#106 验收关闭（2026-10-17）**：CI backend-fast 步骤真实 `--durations` Top10 写入 step summary + 单例串扰隔离 + socket 审计 + #95 同机前后复测；提交 `cafe8ed`+`2f6790c`+`e23ba43` → merge `9a13987` @ main。
- **#107 验收关闭（2026-10-17）**：可观测模块行为验证恢复——四处失败真因 SDK console exporter 导入期绑定 sys.stdout 修复，覆盖率 native 68.5259% 达成；提交 `1d78f05`+`339c891` → merge `be32bd0` @ main。
- **#105 验收关闭（2026-10-17）**：去重基准真实重复率校正 + 真跑 Criterion；提交 `48e00c0`…`515c8c4` → merge `85f7f44` @ main。
- **#104 验收关闭（2026-10-17）**：Rust bridge Unicode 等价性 + iterator 回退丢数修复；提交 `9a75875` → merge `a88fd7a` @ main。
- **#90 验收关闭（2026-10-14）**：requirements-ml.txt 新建 + ci.yml 两 job 分层安装 + freeze 漂移探针；提交 a023b1d → merge 26ce9ed @ main。
- **#92 验收关闭（2026-10-14）**：sentiment_model 评估 ×2 取 NB+LogReg 子集 + model_training 抽样 500 条；提交 23818f3 → merge 0730b7f @ main。
- **#91 验收关闭（2026-10-14）**：xdist 本机灰度三轮全绿；提交 12336ba → merge 7be3df9 @ main。
- **#89 验收关闭（2026-10-13）**：ci.yml integration needs 去掉 frontend-fast；提交 2caabe8 → merge 3a0471c @ main。
- **#88 验收关闭（2026-10-13）**：conftest 会话级强制 jti 黑名单内存回退；提交 4cd99a6 → merge b19432a @ main。
- **#81 验收关闭（2026-10-12）**：平板档差异化；提交 d5a1312 → merge abb3b98 @ main。
- **#86 验收关闭（2026-10-12）**：formatDuration 收敛 utils 单源；提交 25578f7 → merge 3a0b33a @ main。
- **#80 验收关闭（2026-10-12）**：home filters 受控更新；提交 532d2a9 → merge 1c123c7 @ main。
