# TEST_PERF.md — 测试性能基准与优化记录

> 测试性能优化工作日志：基准测量 → 合理性审计 → 加速方案 → 实施回写。
> **幂等规则**：本文件存在时始终作为对照基准，不重建；每次实施优化后仅在
> [§6 优化记录](#6-优化记录) 追加条目。重置基准 = 手动删除本文件。

- 基准日期：2026-10-13
- 基准 commit：`a03c720`
- 本机环境：Linux，24 核 / 20G，Python 3.12.14（mise venv），pytest 9.1.1
- CI 环境：GitHub Actions `ubuntu-latest`（2 核），Python 3.11 / Node 20
- 覆盖率红线：**基准 68.49%**（branch），后续任何改动不得低于此值（现有门禁 `fail_under=60`，本文件口径更严）

---

## 1. 基准（Baseline）

### 1.1 本地后端 fast gate（`pytest -m "unit or api"`）

| 次数 | 配置 | 总时长 | 结果 |
|---|---|---|---|
| Run 1 | `--durations=30 --cov=src` | **231.74s** | 1460 passed / 69 skipped / 196 deselected / 160 warnings |
| Run 2 | 无覆盖率 | **183.21s** | 同上 |
| Run 3 | 无覆盖率（`-rs`） | **182.89s** | 同上 |

- 无覆盖率口径中位 **~183s**；`--cov` 开销 ~49s。
- 覆盖率（Run 1 实测）：**68.49%**（branch，`fail_under=60` 通过）。

### 1.2 本地前端（`npm run test:run`）

- **41 文件 / 190 用例全部通过**，墙钟 ~5.1s（本机 24 核掩盖了开销）。
- vitest 阶段分解（多 worker 累计）：transform 8.3s / **collect 47.1s** / tests 12.3s / environment 23.5s → CI 2 核上即表现为 38s 步骤耗时的主要来源。

### 1.3 CI 拆解（gh run 38261098231，2026-10-12，全绿）

关键路径 **≈ 4m20s**：backend-fast(1m53s) ∥ frontend-fast(1m19s) → integration(2m24s) 串行垫底。

| Job | Step 耗时（>1s 部分） |
|---|---|
| backend-fast | install deps **64s**，pytest(+cov) **39s**，setup-python 5s，ruff <1s |
| frontend-fast | vitest **38s**，build **13s**，npm ci 7s（有缓存），lint 3s，format 4s |
| integration | 容器启动 **33s**，install deps **75s**（与 backend 重复安装），pytest **19s**，init db 1s |

- 最新 run（`a03c720`）：frontend-fast 在 lint 步骤 3s 即红（本地未跑 lint 的回声），backend-fast pytest 步骤 73s（CI 正常方差 39-73s），integration 因 `needs` 被 skip。
- 已有的优化：`concurrency.cancel-in-progress` ✅、`setup-python` pip 缓存 ✅、`setup-node` npm 缓存 ✅。

### 1.4 测试计数 / 通过率 / 覆盖率

| 指标 | 值 |
|---|---|
| 全量收集 | **1722** 用例 / 85 文件 |
| fast gate 实跑 | 1460 passed + 69 skipped（1529 执行，**通过率 100%**（执行口径）） |
| deselected | 196（integration / external / slow 层） |
| 跳过构成 | **66** = 契约测试按设计抽样（`test_api_get_contract` 39 + `test_api_write_contract` 27）；**3** = 模块级外部依赖（test_cookie 需真实 cookie、test_spider_system 需外部 spider、test_sentiment_stress 需真实 NLP，250s+） |
| 后端覆盖率 | **68.49%**（branch）/ gate 60% |
| integration 覆盖率 | 仅出报告不设阈值（`--cov-fail-under=0`，D-04 决策） |
| 前端覆盖率 | 未配置 |

### 1.5 最慢 Top 10（fast gate，Run 1 实测）

| # | 耗时 | 阶段 | 测试 |
|---|---|---|---|
| 1 | **134.33s** | call | `tests/test_a1_api_prefix_alias.py::TestApiPrefixAlias::test_new_prefix_returns_200_with_auth` ← 根因见 K1 |
| 2 | 5.44s | call | `tests/test_sentiment_model.py::TestModelEvaluation::test_evaluate_models` |
| 3 | 5.40s | call | `tests/test_sentiment_model.py::TestModelEvaluation::test_cross_validation_splits` |
| 4 | 3.48s | call | `tests/test_sentiment_optimization.py::test_performance` |
| 5 | 3.01s | call | `tests/test_a2_auth_single_track.py::TestPublicPassthrough::test_root_and_health_are_public` |
| 6 | 3.01s | call | `tests/test_project_health.py::test_ready_endpoint_reports_missing_dependencies` |
| 7 | 1.69s | call | `tests/test_api_write_contract.py::TestWriteRoutesContract::test_admin_bad_payload[POST /api/model/retrain]` |
| 8 | 1.07s | call | `tests/test_model_improvements.py::test_model_training` |
| 9 | 0.90s | call | `tests/test_strategy_selector.py::test_smart_strategy_selector` |
| 10 | 0.54s | call | `tests/test_model_improvements.py::test_sentiment_analysis` |

其余 ~1450 用例均在 0.5s 以下（分布健康）。

### 1.6 数据来源与局限

- 本地 3 次实跑（有效样本 2 次同配置取中位）+ CI 历史日志（`gh run view` step 时间戳）。
- **integration / external / slow 层未本地实测**：需 MySQL + Redis / 微博 cookie，本机不具备；其规模仅由收集数（196）与 CI pytest 步骤（19s）估算。
- 本机 `PYTHONPATH` 含 ROS2 路径会使 pytest 插件加载崩溃，测量时用 `env -u PYTHONPATH` 规避（纯本机噪音，不影响 CI 与结论）。
- Run 1 含 `--cov --durations`，与 Run 2/3 口径不同，已在表中分列。

---

## 2. 关键发现（根因分析）

### K1：首个鉴权测试阻塞 134s —— 测试连了真实 Redis（#88）

faulthandler 线程栈实证（卡住 45s 时转储）：

```
tests/test_a1_api_prefix_alias.py:67 authed_client.get("/api/getHomeData")
→ src/app.py:554 before_request → src/app.py:165 _require_jwt_auth
→ src/utils/jwt_handler.py:127 verify_token
→ src/utils/token_blacklist.py:72 is_jti_revoked
→ src/utils/token_blacklist.py:42 _get_client → redis ping
→ redis/connection.py:627 _connect（阻塞中）
```

- 本机 iptables 对 `127.0.0.1:6379` 是 **DROP**（SYN 丢弃 → 单次 TCP ~127s 才超时）；CI 上是即时 ECONNREFUSED，所以只在本地爆发；
- `_get_client` 有 `_client_checked` 进程级单次语义 → 每个测试进程只有**第一个鉴权请求**付出该代价（与 durations 只见一个 134s 吻合）；
- conftest 只把 Celery 切到了 `memory://`，`token_blacklist` 被遗漏；
- 独立复现：单测 wall 2m23.9s / user CPU 5.9s → ~98% 时间在等网络。
- **量化**：该测试 134.33s ÷ 231.74s = **总时长 58%**；本地与 CI 的 pytest 步骤差距（183s vs 39-73s）绝大部分由它解释。

### K2：CI 流水线结构 —— integration 白等 frontend（#89）

集成测试只依赖后端（MySQL + Redis + alembic），却被 `needs: [backend-fast, frontend-fast]` 挡住，关键路径多付 1m19s；且 integration 重复安装同一套 Python 依赖（75s vs backend 的 64s）。

### K3：依赖安装是 CI 第二大头（#90）

两个 Python job 各付 64-95s 安装费；pip 缓存已开但 torch 系大包仍是瓶颈。

### K4：前端 vitest 的开销在 collect/environment，不在用例本身

本机 tests 实跑仅 12.3s（累计口径）；collect 47.1s（累计）+ environment 23.5s（累计）在 2 核 CI 上放大为 38s 步骤。

### K5：跳过构成健康，无 flaky 证据

3 次运行计数完全一致；69 个 skip 全部有明确归因（66 设计抽样 + 3 模块级外部依赖）。

### K6：覆盖率现状

fast gate 68.49%（branch），门禁 60%；`src/views/user/user.py`（24%）、`src/views/api/user_routes.py`（54%）等是显著低覆盖模块（后续补测试的优先方向，非性能议题）。

---

## 3. 阶段一：测试合理性审计（只分析，未改动）

**总体结论**：套件质量较高——无 flaky 证据（3 次全量运行结果一致）、无空断言用例（抽查）、层级划分（unit/api/integration/external/slow 标记体系）清晰。问题集中在**个别重测试的规模**与**测试环境隔离缺口**。

### 🔴 建议删除（0 项）

- 未发现 flaky / 重复 / 过时 / 无断言 / 过度 mock 的删除候选。
- 依据：3 次运行计数与结果一致；跳过全部有归因（§1.4）；抽样阅读最慢用例均有行为断言。

### 🟡 建议重构（4 项）

| 项 | 测试 | 判断依据 | 预计节省 | 去向 |
|---|---|---|---|---|
| R1 | `test_sentiment_model.py::test_evaluate_models`（5.44s）/ `test_cross_validation_splits`（5.40s） | 层级错误：单元层内做全量训练+评估多模型，属集成级工作量 | ~10.8s | #92 |
| R2 | `test_sentiment_optimization.py::test_performance`（3.48s） | 名实不符：语义即性能测试，混在 fast gate | ~3.5s（标 slow）或降规模 | #92 |
| R3 | `test_a1_api_prefix_alias.py`（130+ 行 monkeypatch 样板在 3 个用例间重复） | 测行为但 fixture 粒度过粗，重复 mock 集合应提共享 fixture | 可维护性收益，非时长 | 随 #88 顺手 |
| R4 | `test_a2_auth_single_track.py::test_root_and_health_are_public`（3.01s）与 `test_project_health.py::test_ready_endpoint_reports_missing_dependencies`（3.01s） | 待归因：public 端点不应 3s，疑触碰隐藏 I/O（warmup/bcrypt），需先 profiling | 待定（若同源可再 -6s） | #92 |

### 🟢 保留（其余全部）

- ~1450 用例 <0.5s，符合单元/API 层预算；
- 契约测试（`test_api_get_contract` 151 例、`test_api_write_contract` 97 例参数化）抽样跳过设计合理，保留。

---

## 4. 阶段二：加速方案（全部待确认，映射 issue）

| # | 维度 | 方案 | 预计收益 | 风险 | Issue |
|---|---|---|---|---|---|
| 1 | I/O 优化 | conftest 会话级强制 `token_blacklist` 内存回退（diff 已附） | 本地 **-134s（58%）**，fast gate 183s→<60s | 低（既有降级路径） | **#88**（ready-for-agent，P1） |
| 2 | 流水线结构 | `integration.needs` 去掉 `frontend-fast` | CI 关键路径 **-1m19s**（4m20s→~3m） | 低 | **#89**（ready-for-agent，P2） |
| 3 | 缓存 | 依赖安装提速：迁移 uv（仓库已有 `uv.lock`）或 requirements 分层 | 两个 job 合计 **-80~110s** | 中（版本漂移需对比） | **#90**（needs-triage） |
| 4 | 并行化 | 本地引入 pytest-xdist（`-n 4` 灰度两轮）；CI 暂不分片 | 本地 183s→预估 30-60s | 中（顺序依赖需验证，历史有 #22/#30 先例） | **#91**（needs-triage） |
| 5 | 慢测试 | §3 R1/R2/R4 降规模或标 slow | fast gate 再 **-8~12s** | 低-中（防弱断言化） | **#92**（needs-triage） |
| 6 | 环境加速（前端） | 评估 vitest `isolate`/`pool` 配置压 collect/environment 开销；CI build 13s 暂不动 | CI vitest 38s→预估 -10~20s | 中（isolate 影响隔离语义） | 并入 #93 评估项 |
| 7 | 增量执行 | pytest-testmon / 路径触发 | 视本地工作流收益 | 中（testmon 稳定性） | 暂不立项，观察 #88/#91 落地后再评估 |

**不立项说明**：

- runner 规格 / 镜像瘦身：CI 单 job ≤2m24s，upgrade 不划算；
- Docker layer 缓存：CI 不构建镜像（Docker 仅本地 compose），无对象。

### 预期叠加效果（方案 1+2+5 全部落地后）

| 指标 | 基准 | 预期 |
|---|---|---|
| 本地 fast gate | ~183s | **<50s** |
| CI 关键路径 | 4m20s | **~2m50s** |
| 覆盖率 | 68.49% | ≥68.49%（红线） |

---

## 5. 阶段三：补充建议（测试之外的机制）

见 **#93**（needs-triage）：

1. **测试时长监控与预算告警**：CI pytest 步骤 >120s 输出 warning + step summary 附 `--durations` Top10，防止恶化无声无息；
2. **Flaky / 顺序依赖治理**：`pytest-randomly` 定期探针跑（seed 固定可重放），复现 #22/#30 类跨文件污染；
3. **unit 层禁真实出网**：评估 `pytest-socket`，从源头杜绝「测试静默连 Redis/外网」（K1 的机制化防线）；
4. **团队规范**：新增测试 >1s 需在 PR 说明理由；mock 样板 >20 行必须提共享 fixture（§3 R3 教训）；
5. **测试金字塔长期方向**：integration 层仅 11 文件 / 196 用例偏薄，且低覆盖集中在 `views/user`、`views/api/user_routes`——补 integration 用例优先于加 unit；
6. **前端**：vitest 覆盖率未配置，建议纳入 #93 一并评估。

## 6. 优化记录

> 每实施一项优化后重测并追加一行。格式：日期 | 改动 | 指标前→后 | commit | issue。

| 日期 | 改动 | 指标前→后 | commit | issue |
|---|---|---|---|---|
| 2026-10-13 | conftest 会话级强制 jti 黑名单内存回退（fast gate 无覆盖率口径） | 182.9s → 34.9s（-81%），1460 passed / 69 skipped / 196 deselected 计数不变 | b19432a | #88 |
| 2026-10-14 | pytest-xdist 本地灰度（同机无覆盖率口径；串行基线 50.42s，与 #88 行机器不同不可直接对比） | 串行 50.42s → -n 4：30.64s / 31.55s（两轮，-39%）→ -n 8：25.20s（-50%）；三轮计数均为 1460 passed / 69 skipped（collect-only 核对 1526/1722，196 deselected 与串行一致），零顺序污染暴露 | （评估未合入，无代码提交） | #91 |
| 2026-10-14 | 慢测试降规模：sentiment_model 评估取 NB+LogReg 子集 + model_training 抽样 500 条补断言（无覆盖率口径） | 47.98s → 39.33s（-18%），计数不变 1460 passed / 69 skipped / 196 deselected | 0730b7f (merge) | #92 |
| 2026-10-14 | requirements 分层：requirements-ml.txt 新建 + ci 两 job 分层安装 + freeze 探针；CI install 182s → 141s（<110s 未达成，wheel 解包天花板，归档 D-016） | install 182s → 141s（-22.5%）；本地 gate 不变 39.33s | 26ce9ed (merge) | #90 |
| 2026-10-15 | conftest 测试会话 REDIS_URL=disabled（/ready 3s×2 消除，纯测试侧，零产品改动） | 39.33s → 27.71s（-29.6%，-11.62s），计数不变 1460 passed / 69 skipped / 196 deselected | 本次 commit | #95 |
| 2026-10-17 | #95 同机前后复测（补记：上表 #95 行"本次 commit"= `3b4da68`；用原提交 worktree `cc0cfe7` → `3b4da68`，同机串行无覆盖率，WEIBO_CORE_RUST=1） | 目标两用例 call 6.02s → <0.01s；full gate 37.49s（37.45/37.53 两次）→ 30.54s（31.23/29.85 两次），-6.95s / -18.5%；计数 1460/69/196 双端一致 | （复测，无代码提交） | #106 |
| 2026-10-17 | 可观测模块行为验证恢复（#107）：enabled 路径进程内隔离 fixture、disabled/降级拆独立文件、删除 incidental 测试 | `src/utils/observability.py` 主进程覆盖 33% → 98% stmt / 94% branch；branch 口径 local native 68.5259%（11106/16207，JSON 复核）/ CI 68.62%（fallback 口径）；两文件共 17 用例 | be32bd0 (merge) | #107 |
| 2026-10-17 | CI backend-fast 步骤：真实 `--durations` Top10 写入 step summary（tee + PIPESTATUS 保退出码；>120s 软告警保留；summary 以折叠 group 回显日志供无 UI 验收） | 机制 wiring：四场景临时 shell 演练通过（正常/超预算/失败/无 durations）；真实 CI 绿 | cafe8ed | #106 |

### 6.1 M6 成功阈值现状（2026-10-17）

| 阈值 | 目标 | 现状（同机实测 / CI 实测） | 判定 |
|---|---|---|---|
| 串行无覆盖率 fast gate | <30s | 当前 HEAD（2f6790c）：34.65s（native）/ 35.75s（fallback）；同机在 #95 后快照（3b4da68，1460 用例）重测 29.85–31.23s | **未达成**（当前 HEAD 差 ~5s；旧快照接近线） |
| 完整 CI 关键路径 | <240s | run 38998104877（本交付 merge 9a13987）= **304s**（created 03:15:45Z → integration 完成 03:20:49Z；backend-fast job 160s 含安装、步骤 elapsed 65s → integration 139s 垫底）；近期 best run 38995283704 = 247s（backend-fast 107s） | **未达成**（差 64s；run 间方差主要在 install 107→160s；历史 302s / 315s） |
| branch 覆盖率（--cov=src） | ≥68.49% | local native 68.5259–68.66%（文件缓存状态敏感）；local fallback 68.5259%；CI 68.62%–68.63%（fallback 口径，两 run） | **达成**（余量薄，+0.03pp 级） |

**口径分列（不得混用）**：
- **raw 秒数**：同机串行、无覆盖率、`-m "unit or api"`，本机 24 核 / Python 3.12.14。
- **cov 口径**：同命令加 `--cov=src`，本机 ~80–86s（插桩开销 ~45–50s，与 §1.1 基准的 49s 一致）；CI backend-fast 步骤另含安装时间，不与 raw 秒数混用。
- **full CI 关键路径**：run created → 最后 job 完成（墙钟），不以单 job 时长冒充。
- CI 与 local 为不同机器 / Python（CI 3.11.17）条件，数值不可互作性能差。
- **事实口径更正（2026-10-18，#111）**：#108 执行报告曾将 backend-fast job 耗时 2m37s 误写为完整 CI 关键路径；实际 run 38999122715 为 created 03:31:41Z → integration 完成 03:36:28Z，完整关键路径墙钟实为 **287s**（分项详见 §6.2.2 表格）。文档刷新以此为准，不重算历史性能数据。

### 6.2 M6 残余差距只读分析（#112，2026-10-18）

> 本小节为 D-023 决策提供只读事实依据。只分析、不改生产代码、不改测试用例、不改 CI 配置、不改阈值。

#### 6.2.1 本地 Fast Gate 耗时分解（当前 HEAD 实测）

- **测试环境**：AMD 24 核 / Python 3.12.14 / Linux 6.18 WSL2 / HEAD `b130e4d`（基线 `048af63`）
- **Collection / 模块导入开销**：
  - 命令：`time .venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros --collect-only`
  - 结果：`1560/1756 tests collected (196 deselected) in 10.94s`（real 12.66s, user 10.69s, sys 1.64s）
  - 归因：pytest 单是遍历 1756 个用例并完成模块 import（含 torch, transformers, sklearn, spacy, jieba 等重量级库）即需 **~11s**，占 fast gate 总耗时（~40s）的 **27%**。

- **Native 模式（WEIBO_CORE_RUST=1，无覆盖率）**：
  - 命令：`WEIBO_CORE_RUST=1 time .venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros --durations=30`
  - 退出码：0；计数：**1494 passed, 69 skipped, 196 deselected, 159 warnings**
  - 耗时：pytest 自报 **40.62s**，进程 wall time **42.72s**（user 46.08s, sys 5.03s）
  - `--durations=30` 最慢 Top 15 详情（单位：秒）：
    1. `2.86s call  tests/test_sentiment_model.py::TestModelEvaluation::test_evaluate_models`
    2. `2.65s call  tests/test_sentiment_model.py::TestModelEvaluation::test_cross_validation_splits`
    3. `1.16s call  tests/test_api_write_contract.py::TestWriteRoutesContract::test_admin_bad_payload[POST /api/model/retrain]`
    4. `0.96s call  tests/test_sentiment_optimization.py::test_performance`
    5. `0.47s call  tests/test_observability.py::test_enabled_emits_real_span_for_request`
    6. `0.41s call  tests/test_startup_service.py::test_ensure_demo_admin_creates_user_sqlite`
    7. `0.37s setup tests/test_api_write_contract.py::TestWriteRoutesContract::test_anonymous[POST /api/alert/read-all]`
    8. `0.35s setup tests/test_auth_jwt.py::TestLoginAPI::test_api_logout_clears_auth_cookie`
    9. `0.34s call  tests/test_api_write_contract.py::TestWriteRoutesContract::test_admin_bad_payload[POST /api/spider/comments]`
    10. `0.30s setup tests/test_api_get_contract.py::TestGetEndpointsEnvelope::test_anonymous[/api/sentiment/strategy/stats]`
    11. `0.30s call  tests/test_model_improvements.py::test_model_training`
    12. `0.29s setup tests/test_api_get_contract.py::TestGetEndpointsEnvelope::test_authenticated_non_admin[/api/spider/overview]`
    13. `0.26s call  tests/test_sentiment_monitoring.py::TestCleanupMemoryCache::test_expired_and_overflow_combined`
    14. `0.26s setup tests/test_observability.py::test_console_probe_serves_real_requests`
    15. `0.25s call  tests/test_report_charts.py::test_pdf_with_charts_larger_than_without`
  - 耗时结构汇总：
    - Collection / 导入：~10.9s（27%）
    - 最慢 Top 30 用例总耗时：13.2s（32.5%），其中 Top 2 占 5.51s
    - 其余 ~1530 个轻量用例长尾总计：~16.5s（40.5%，平均每个用例 ~10.8ms）
    - 合计：10.9s + 13.2s + 16.5s ≈ 40.6s

- **Fallback 模式（WEIBO_CORE_RUST=0，无覆盖率）**：
  - 命令：`WEIBO_CORE_RUST=0 time .venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros --durations=30`
  - 退出码：0；计数：**1492 passed, 71 skipped, 196 deselected, 156 warnings**
  - 耗时：pytest 自报 **40.12s**，进程 wall time **42.30s**（user 46.98s, sys 4.50s）
  - 最慢用例分布与 native 一致：Top 2 仍为 `test_evaluate_models`（2.73s）与 `test_cross_validation_splits`（2.52s），Top 30 合计 12.9s。

- **本地 <30s 差距成因诊断**：
  - 从 #95 时的 27.71s（1460 用例）到当前 40.62s（1563 用例），增加了 103 个用例（#104/#105/#107/#110 及可观测性测试等）；
  - 测试用例执行时间净值约为 29.7s（非常接近 30s 阈值），但 **Collection 阶段固定消耗 10.9s**，使得串行总时长始终停留在 40s 左右。
  - **核心结论**：在当前 1560 个用例规模下，即使把 Top 2 慢用例（5.5s）优化至 1s，总时长仍约为 10.9s + 8.7s + 16.5s = 36.1s，单凭局部慢测试治理无法将串行总时间稳定压进 <30s。

#### 6.2.2 CI 关键路径实测表（近期 4 个 Run 逐 Run 分解）

数据源自 GitHub Actions REST API（`gh api /repos/zhangjszs/-weibo-sentiment-analysis/actions/runs/<id>/jobs` 及 `--allow-escape-sequences` 读取 step 日志）：

| Run ID | Commit / 事件 | 关键路径墙钟 (created→最后 job 完成) | backend-fast 耗时 | backend-fast: Install 步骤 | backend-fast: Pytest 步骤 | rust-core | frontend-fast | integration | pip 缓存判定与证据 |
|---|---|---|---|---|---|---|---|---|---|
| [38995283704](https://github.com/zhangjszs/-weibo-sentiment-analysis/actions/runs/38995283704) | merge be32bd0 (#107) | **247s** (02:31:55Z→02:36:02Z) | 107s (02:31:57Z→02:33:44Z) | **54s** (02:32:05Z→02:32:59Z) | **43s** (02:32:59Z→02:33:42Z) | 55s | 72s | 136s (02:33:46Z→02:36:02Z) | **Cache Hit**: `Cache restored from key: setup-python-...-pip-d06c0e...`；379 wheels cached，0 download |
| [38998104877](https://github.com/zhangjszs/-weibo-sentiment-analysis/actions/runs/38998104877) | merge 9a13987 (#106) | **304s** (03:15:45Z→03:20:49Z) | 160s (03:15:48Z→03:18:28Z) | **82s** (03:15:58Z→03:17:20Z) | **65s** (03:17:20Z→03:18:25Z) | 42s | 58s | 139s (03:18:30Z→03:20:49Z) | **Cache Hit**: 同一 primary key 命中；379 wheels cached，0 download |
| [38999122715](https://github.com/zhangjszs/-weibo-sentiment-analysis/actions/runs/38999122715) | merge ddea0a9 (#108) | **287s** (03:31:41Z→03:36:28Z) | 157s (03:31:43Z→03:34:20Z) | **80s** (03:31:49Z→03:33:09Z) | **69s** (03:33:09Z→03:34:18Z) | 53s | 65s | 126s (03:34:22Z→03:36:28Z) | **Cache Hit**: 同一 primary key 命中；379 wheels cached，0 download（#108 报告误将 backend-fast 2m37s 当关键路径，真实为 287s） |
| [38999825154](https://github.com/zhangjszs/-weibo-sentiment-analysis/actions/runs/38999825154) | merge 1abfaf0 (#110) | **329s** (03:42:44Z→03:48:13Z) | 148s (03:43:16Z→03:45:44Z) | **73s** (03:43:26Z→03:44:39Z) | **61s** (03:44:40Z→03:45:41Z) | 51s | 77s | 146s (03:45:47Z→03:48:13Z) | **Cache Hit**: 同一 primary key 命中；379 wheels cached，0 download |

- **CI <240s 差距成因诊断**：
  1. **流水线拓扑串行是数学瓶颈**：`.github/workflows/ci.yml:140` 规定 `integration` 的 `needs: [backend-fast]`。完整关键路径 = `backend-fast` 耗时 + runner 调度排队 + `integration` 耗时。即使在最理想的 Run 38995283704 中，backend-fast (107s) + integration (136s) 已经达到 243s，加上排队即达 247s。
  2. **Install 步骤解包耗时方差大**：即使 pip cache 100% 命中，runner 解包 600MB+ 大轮子（PyTorch/Transformers/SciPy）的耗时在 54s 与 82s 之间剧烈波动（受 GitHub 免费 runner 宿主机磁盘 I/O 影响），为关键路径引入高达 28s 的不可控方差。

#### 6.2.3 候选优化杠杆深度评估表

| 杠杆编号 | 方案名称与具体做法 | 预期收益 | 验证方式 | 主要风险与副作用 | 契约 1.10 / D-019 红线判断 | 需否用户批准 / 决策归类 |
|---|---|---|---|---|---|---|
| **L1** | **本地 fast gate 默认开启 pytest-xdist（如 `-n 4`）**：在 `pytest.ini` 或门禁命令加入 `-n 4`。 | 本地 fast gate 从 40s 降至 **~22–26s**（#91 灰度实测 50s→30s，-39%）。直接达成 <30s。 | 本地同机多轮测试，核对计数 1494/69/196 与 0 退出码。 | **概念冲突**：M6 成功信号定义为「**串行**无覆盖率 <30s」；启用 xdist 本质上是改变了衡量口径，非串行优化；需保证 in-memory DB 与单例并发安全。 | 不触犯 1.10 红线；但**属于成功信号口径修订**。 | **需用户批准**（分类三：需修订信号） |
| **L2** | **慢测试重点治理与 Collection 优化**：精简 Top 2 慢用例（`test_evaluate_models` 2.86s + `test_cross_validation_splits` 2.65s，改用更小合成数据）；按需延迟导入重量级模块压缩 collection。 | 慢用例压缩 ~3–4s；Collection 压缩 ~1–2s；合计本地减少 **4–6s**（40s 降至 ~34–36s）。 | `git worktree` 对照测量，断言数不减少，测试逻辑不弱化。 | 进一步降低样本可能影响分类器评测边界；且仍受制于 1500+ 用例的长尾底噪，**无法单独达成 <30s 目标**。 | 无红线；纯测试内部优化。 | **无需授权即可实施，但无法彻底闭合差距**（分类一：可缩小） |
| **L3** | **CI 虚拟环境整包缓存（actions/cache 缓存 .venv）**：跳过 pip install 解包，直接从 cache 还原整个已安装的 python 虚拟环境。 | Install 步骤耗时从 70–80s 降至 **10–15s**（净减 **55–65s**）；backend-fast 从 150s 降至 ~90s。 | CI 观察 cache hit 后的安装耗时与 pip freeze 校验。 | venv 包含解释器硬编码路径与依赖符号链接，runner 镜像微小变更可能导致环境损坏；且 D-016 已明确记录「接受 141s，不重启 venv 整包缓存」。 | 触碰 D-016 决策约束；需推翻已归档决策。 | **需用户批准**（分类二：需授权） |
| **L4** | **CI 流水线解耦（移除 integration.needs: [backend-fast]）**：让 integration 与 backend-fast / frontend-fast / rust-core 并行启动。 | 消除 107–160s 串行等待，CI 关键路径从 287–329s 直接降至 **~160–180s**（彻底达成 <240s 目标）。 | 修改 ci.yml 查看关键路径墙钟与各 job 并发状态。 | 若 backend 发生语法或基础错误，integration 仍会启动并拉起 MySQL/Redis 服务容器，浪费少量 Actions runner 配额；改变级联失败行为。 | 属于**主要 CI/CD 流程变化**（契约 1.10 红线项）。 | **需用户明确批准**（分类二：需授权） |
| **L5** | **CI 覆盖率门禁分流（fast gate 去除 --cov 或单独拆 job）**：`backend-fast` 仅跑 `--no-cov`（35s），覆盖率统计移至单独非阻塞或定时 job。 | `backend-fast` 步骤减少 **25–30s**（插桩与 term-missing 打印开销）。 | CI job 时长对比。 | 降低 PR 期的覆盖率实时反馈强度，可能导致低于 68.49% 的代码被更晚发现。 | 变更核心质量门禁策略。 | **需用户批准**（分类二：需授权） |

#### 6.2.4 结论分类与 D-023 建议

为支撑 D-023 决策，将上述杠杆归为三类：

1. **可在不改变成功信号、无需用户特殊授权下缩小的差距（分类一）**：
   - **L2 慢测试与 Collection 治理**：可将本地串行 fast gate 从 ~40s 进一步压缩至 ~34–36s。但由于 10.9s Collection 开销与 1500+ 用例长尾（16s+），**在当前测试规模与串行口径下，不可能仅靠测试优化稳定进入 <30s**。
2. **能实质达成目标、但必须获得用户红线授权的杠杆（分类二）**：
   - **L4 CI integration 并行化**：这是**唯一**能将完整 CI 关键路径彻底打进 <240s（降至 ~160–180s）的高 ROI 杠杆；但需用户批准变更 CI/CD 级联规则。
   - **L3 venv 整包缓存**：可节省 ~55s，但需推翻 D-016 并承担 runner 漂移风险。
3. **必须修订成功信号才能“达成”的杠杆（分类三）**：
   - **L1 xdist 并行**：能轻易把本地时间降到 ~22s，但它改变了“串行”的承诺。如果用户决定修订目标为“本地多核并行 <30s”，则当前技术栈已完全就绪（#91 已验证无冲突）。

**给 Planner 与用户的建议（供 D-023 参考）**：
- **关于本地 <30s**：在用例数达到 1560+ 时，11s collection + 30s 执行是健康的单元/API 覆盖常态。建议 D-023 采纳以下二选一：
  - **路径 A1**：接受现状并将 M6 串行阈值修订为 `<40s`（已非常接近），保持串行严谨性；
  - **路径 A2**：将成功信号修订为「本地 `-n auto` 并行稳定 `<30s`」（技术上已达成，实测 ~25s），更贴合 2026 年多核开发习惯。
- **关于 CI <240s**：只要 `integration` 串行依赖 `backend-fast`，在现有 379 个依赖解包开销下几乎不可能稳定 <240s。建议 D-023 授权 **L4**（解除 integration 依赖），一步达成 ~170s 且零依赖风险。

## 7. 议题状态与待确认建议（2026-10-26 刷新）

> M6 主项已收口：本节改为「议题真实状态总表 + 已归档机制决策 + socket 审计结论 + 仍待确认的低风险候选 + 前端覆盖率基线」。状态按 GitHub 真实 state 抄录（2026-10-26 刷新）。

### 7.1 议题状态总表（2026-10-26 刷新）

| Issue | 优先级 | 状态 | 摘要 |
|---|---|---|---|
| [#88](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/88) | P1 | done | conftest 强制 jti 黑名单内存回退（本地 -134s / 58%，b19432a 已合入） |
| [#89](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/89) | P2 | done | CI integration 解耦 frontend-fast（关键路径结构性 -1m19s，已合入） |
| [#90](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/90) | P2 | done (partial) | CI 依赖安装提速（requirements 分层，install 182s→141s；<110s 未达成 → D-016 归档） |
| [#91](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/91) | P2 | done | pytest-xdist 本地灰度（数据入 §6；结论=不纳入默认门禁，见 7.2） |
| [#92](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/92) | P3 | done | 慢测试降规模（sentiment_model ×2 + model_training；gate 47.98s→39.33s） |
| [#93](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/93) | P3 | done (partial) | 机制包：时长预算告警**已落地**（cafe8ed：CI step summary 真实 Top10 + >120s 软告警）；顺序依赖探针结论=不引入 randomly；unit 层禁网评估 → socket 审计（7.3） |
| [#95](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/95) | P3 | done | conftest REDIS_URL=disabled（gate 39.33s→27.71s；#106 同机前后复测 -6.95s / -18.5%，入 §6） |
| [#94](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/94) | P4 | done | chore：`.gitignore` 增加 `src/data/`（已合入） |
| [#106](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/106) | P3 | done | M6 预算报告 + socket 审计 + 跨天交接证据（已于 2026-10-18 验收关闭；M6 成员全关闭但两个阈值未达） |
| [#107](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/107) | P2 | done | 可观测模块行为验证恢复 + 分支覆盖率基线（已于 2026-10-18 验收关闭；覆盖率 68.5259% 达成） |
| [#108](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/108) | P3 | done | rustup 工具链 pin 生效 + maturin/README 构建边界 + `.env.example` 补全 + ADR-0005（已于 2026-10-18 验收关闭；附关键路径误写更正：实际 run 287s） |
| [#110](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/110) | P3 | done | `scripts/` lint 门禁缺口 + 8 项机械修复（已于 2026-10-18 验收关闭；不设 milestone） |
| [#112](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/112) | P2 | done | M6 残余差距只读分析（本地 gate 耗时分解 + CI 关键路径实测 + 5 项候选杠杆，见 §6.2；已于 2026-10-18 验收关闭；为 D-023 准备依据） |
| [#111](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/111) | P4 | done | 同步旧 ruff 命令至各活文档/脚本，刷新 TEST_PERF 议题状态表并更正 #108 关键路径口径（已于 2026-10-18 验收关闭） |
| [#113](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/113) | P4 | done | 消除 test_send_invalid_email 的真实出站依赖（SMTP_SSL patch），刷新 TEST_PERF 议题状态表（已于 2026-10-19 验收关闭） |
| [#114](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/114) | P3 | done | 消除 test_model_improvements.py 的 PytestReturnNotNoneWarning 告警与假绿吞异常反模式（已于 2026-10-20 验收关闭） |
| [#115](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/115) | P4 | done | conftest 补全 Celery task_store_eager_result 配置以消除 eager 任务查询告警（已于 2026-10-20 验收关闭） |
| [#116](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/116) | P3 | done | 收敛前端单选与复选组件的 Element Plus 3.0 label act as value 弃用警告（已于 2026-10-20 验收关闭） |
| [#117](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/117) | P3 | done | 消除后端源码中全部 7 处 datetime.utcnow() 弃用告警，提供共享 utcnow_naive helper（已于 2026-10-20 验收关闭） |
| [#118](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/118) | P4 | done | test_model_improvements.py 脚本直跑在用例失败时返回非零退出码 sys.exit(1)（已于 2026-10-20 验收关闭） |
| [#119](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/119) | P4 | done | 收敛前端错误态测试的预期 console.error 噪声，vitest stderr 块数归零（已于 2026-10-20 验收关闭） |
| [#120](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/120) | P4 | done | 前端 Sass `@import` 迁移为 `@use`，消除 Dart Sass 3.0 废弃警告（d7e0c59；已于 2026-10-22 验收关闭） |
| [#121](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/121) | P4 | done | 模型评估 `classification_report` 显式 `zero_division=0`，消除 UndefinedMetricWarning（6a37d95；已于 2026-10-22 验收关闭） |
| [#122](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/122) | P4 | done | 刷新 TEST_PERF §7.1 议题总表并补齐 #113–#119 状态（0f2221c；已于 2026-10-22 验收关闭） |
| [#123](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/123) | P3 | done | 前端 vitest 本地覆盖率可见性（reporter-only，无阈值门禁、不动 CI；基线见 §7.5；6812039；已于 2026-10-23 验收关闭） |
| [#124](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/124) | P3 | done | 补齐 `src/utils/index.js` 未覆盖函数单元测试（37 用例；utils/index.js Stmts 98.23% / Branch 97.08% / Funcs 100%；d58fa71；已于 2026-10-23 验收关闭） |
| [#125](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/125) | P3 | done | 补齐 `src/api/request.js` 拦截器错误分支测试（25 用例；request.js Stmts 94.15% / Branch 95.74%；2ab34b3；已于 2026-10-23 验收关闭） |
| [#126](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/126) | P4 | done (partial) | 刷新 TEST_PERF §7.1/§7.4 并记录前端覆盖率基线（c0d7e22；已于 2026-10-23 验收关闭；0% 清单漏 `src/App.vue`，缺口由 #129 承接） |
| [#127](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/127) | P3 | done | 补齐 `src/stores/user.js` 会话恢复/登出分支测试（13 用例；user.js Lines 97.97% / Branch 81.57% / Funcs 100%；ffe4c5b；已于 2026-10-24 验收关闭） |
| [#128](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/128) | P3 | done | 补齐 `src/utils/chinaMap.js` 单例注册与失败重试语义测试（6 用例；chinaMap.js Lines / Branch / Funcs 均 100%；4cb2519；已于 2026-10-24 验收关闭） |
| [#129](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/129) | P4 | done | 刷新 TEST_PERF §7.1/§7.5（补 #124–#126 三行、App.vue 0% 口径与会话 2 实测，双段并存口径；4d00f9c；已于 2026-10-24 验收关闭） |
| [#130](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/130) | P3 | done | 补齐 `src/stores/app.js` 主题切换与侧栏行为测试（9 用例；app.js Stmts/Branch/Funcs/Lines 均 100%；73bec15；已于 2026-10-24 验收关闭；模块已于 #133 迁移为 `app.ts`） |
| [#131](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/131) | P3 | done | 补齐 `src/stores/tabs.js` 多标签工作区状态机测试（41 用例；tabs.js Lines 97.67% / Funcs 100% / Branch 95.77%–95.83%；9a86951；已于 2026-10-24 验收关闭） |
| [#132](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/132) | P4 | done | 刷新 TEST_PERF §7.1/§7.5（补 #127–#129 三行与 47/321 新基线段；06b194e；已于 2026-10-24 验收关闭） |
| [#133](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/133) | P2 | done | 启用本地 TypeScript 类型检查并迁移 app store 首个生产切片（`stores/app.js`→`stores/app.ts` + 最小严格 `frontend/tsconfig.json` + `npm run typecheck` 仅本地、不入 CI；8b3709c；已于 2026-10-26 规划轮独立复跑验收通过并关闭） |
| [#134](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/134) | P4 | done | 收尾 TEST_PERF 验收状态并明确覆盖率快照时点（§7.1 补 #130/#131/#132 三行、§7.5 清过期当前态 + 追加 2026-10-25 快照段；d385af4；已于 2026-10-26 规划轮独立复跑验收通过并关闭） |
| [#135](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/135) | P2 | done | 迁移第一批剩余图表工具 echarts.js 与 chinaMap.js 为 TypeScript 并纳入本地类型门禁（`utils/echarts.ts` + `utils/chinaMap.ts`，`tsconfig.json` include 扩至 3 项、compilerOptions 零改动；1be01af；2026-10-26 交付并合入 main，**已于 2026-10-27 独立复跑验收通过并关闭**） |
| [#136](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/136) | P2 | done | 迁移 stores/tabs.js 为 TypeScript 并保持多标签工作区状态机语义不变（`stores/tabs.ts`，tsc 转译后与原 `.js` 逐行 diff 可执行语句差异 = 0；ce3ab0d；2026-10-26 交付并合入 main，**已于 2026-10-27 独立复跑验收通过并关闭**） |
| [#138](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/138) | P3 | 现象记录（open，无生命周期标签） | 保留 2026-10 的历史漂移；#143 承接修复。 |
| [#143](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/143) | P3 | in-progress（执行取证时） | 已复现聚合分支读数受覆盖率合并顺序影响；尚未复现历史 auth 两文件漂移，不将测量一致视为修复。 |

> **状态说明**：M6 成员 10/10 CLOSED（#88–#95、#106、#107），但因串行 gate <30s 与 CI <240s 仍有两个阈值未达成，M6 里程碑保持 OPEN（成员关闭 ≠ 里程碑收敛，见 D-017 / D-023）。

### 7.2 已归档的机制决策（回应 §5 待办）

1. **pytest-xdist 不纳入默认门禁**（#91 结论）：灰度两轮 -39%~-50% 且零顺序污染暴露，但默认门禁保持串行，与 CI 计数/覆盖率口径对齐；本地需要时手动 `-n` 即可。
2. **requirements 分层止步于 install 141s**（#90 → D-016）：<110s 受 wheel 解包天花板限制；uv/venv 迁移已归档为方向，未获授权不实施。
3. **时长预算告警已机制化**（#93 → cafe8ed）：CI backend-fast 步骤把真实 `--durations` Top10 写入 step summary，>120s 软告警保留；无 UI 环境经日志折叠 group 验收。
4. **不引入 pytest-randomly**（#93 结论）：K5 无 flaky 证据，串行 gate 下顺序探针无可观测收益，避免为探针引入测试顺序变量。

### 7.3 socket 审计结论（#106；审计 only，未改代码）

方法：临时探针拦截 AF_INET/AF_INET6（不设 localhost 白名单），native/fallback 双模式跑 fast gate，逐条抓取真实连接尝试。三个来源：

| # | 来源 | 时机 | 现状 / 处置建议 |
|---|---|---|---|
| 1 | urllib3 导入期 IPv6 能力探测 | import | 上游行为、不可控且无副作用；不修 |
| 2 | `src/services/sentiment_service/cache.py:49` 导入期 `redis_client.ping()` | import | fail-fast 且有降级路径；不修 |
| 3 | `tests/test_notification_service.py::test_send_invalid_email` → `smtplib.SMTP_SSL("invalid.host", 465)` 无 timeout | 用例内 | 仅记录；如修，加 timeout 即可，留待后续低风险批次 |

**建议（待 Planner 确认）**：暂不引入 pytest-socket 全局禁网——现存 3 来源均属可控（上游探测 / fail-fast 降级 / 单点用例），全局封锁需白名单机制且易掩盖 Redis 类真实等待，维护成本高于收益；#93 的「unit 层禁网」评估至此收口。

### 7.4 仍待确认的低风险候选

- 前端 vitest 覆盖率配置**已交付**（#123，2026-10-23 验收关闭）：`test:coverage` + v8 provider（reporter-only），基线见 §7.5；覆盖率阈值与 CI 纳入仍未获授权；
- integration 层补用例（196 用例偏薄，低覆盖集中在 `views/user`、`views/api/user_routes`；补 integration 优先于加 unit）；
- 测试规范固化：>1s 用例 PR 需说明理由；mock 样板 >20 行必须提共享 fixture（§3 R3 教训）。

### 7.5 前端覆盖率基线（2026-10-26 刷新，#123 起）

命令：`cd frontend && npm run test:coverage`（v8 provider，reporter-only；**未设 thresholds 门禁、未纳入 CI**）。

**#123 验收时基线**（41 files / 190 tests）：

| 指标 | 覆盖率 |
|---|---|
| Stmts | 80.55% |
| Branch | 72.66% |
| Funcs | 30.95% |
| Lines | 80.55% |

0% 模块清单（实测）：`src/api/` 下 alert / content / favorites / platform / predict / propagation / report / user 共 8 个声明式包装模块；`src/main.js` 为应用入口、`src/App.vue`（0/14 行）为根组件壳，二者同列豁免（不为壳层补 mock 测试）。

**2026-10-23 执行轮更新**：#124（`utils/index.js` 补测）与 #125（`request.js` 错误分支补测）已验收关闭；当时实测 **43 files / 252 tests**，总覆盖率 **Stmts 82.48% · Branch 75.30% · Funcs 34.22% · Lines 82.48%**。

**2026-10-23 执行会话 2 更新**：#127（`stores/user.js` 会话恢复/登出分支）与 #128（`utils/chinaMap.js` 单例/重试语义）已合入 main，并于 2026-10-24 规划轮验收通过、已验收关闭；当时实测 **45 files / 271 tests**，总覆盖率 **Stmts 83.22% · Branch 75.83% · Funcs 35.55% · Lines 83.22%**（`stores/user.js` Lines 97.97% / Branches 81.57% / Funcs 100%；`utils/chinaMap.js` 100% / 100% / 100%）。0% 模块清单不变。

**2026-10-24 执行会话 2 更新**：#130（`stores/app.js` 主题切换/侧栏测试，73bec15）与 #131（`stores/tabs.js` 多标签状态机测试，9a86951）已合入 main，并已于 2026-10-24 规划轮验收关闭；当时实测 **47 files / 321 tests**，总覆盖率 **Stmts 83.79% · Branch 77.35% · Funcs 37.55% · Lines 83.79%**（`stores/app.js` Stmts/Branch/Funcs/Lines 均 100%，此前 71.79% 行 / 25% 函数；`stores/tabs.js` Stmts 97.67% / Branch 95.83% / Funcs 100% / Lines 97.67%，未覆盖行 40-41、190-191 为 `localStorage` getItem/removeItem 抛错 catch，jsdom 真实对象下无自然构造方式，按 #131 约定不 mock）。0% 模块清单不变（8 个 `src/api/` 包装模块 + `main.js` + `App.vue`）。以上 45/271 与 43/252 等历史段保留原值与时点标注，与本段并存，不互相覆盖。

**2026-10-25 执行会话更新（#134；绑定当次 `npm run test:coverage` 日志）**：#130/#131/#132 现均 `done`/CLOSED（§7.1 已补三行）；#133（app store `app.js`→`app.ts` 迁移，8b3709c，**已于 2026-10-26 规划轮验收关闭**）已合入 main——主题 store 现为 TS 模块 `stores/app.ts`（`useAppStore` 与全部主题/侧栏行为不变），迁移后运行时行为经复测一致。本轮实测 **47 files / 321 tests**，总覆盖率 **Stmts 83.88% · Branch 77.33% · Funcs 37.72% · Lines 83.88%**（`stores/app.ts` Stmts/Branch/Funcs/Lines 均 100%，自迁移前 `app.js` 的 100% 无衰减；`stores/tabs.js` 97.67 / 95.77 / 100 / 97.67，未覆盖行 40-41、190-191；`stores/user.js` 97.97 / 81.57 / 100 / 97.97）。`All files` 语句/分支小数随 V8 运行在 83.79–83.90 / 77.32–77.35 间微抖动（D-034 已记录，非回归），本段数值即当次日志快照，与上文各历史段并存、不互相覆盖。0% 模块清单不变（8 个 `src/api/` 声明式包装 + `main.js` + `App.vue`）。

**2026-10-26 执行会话更新（#137；绑定当次 `npm run test:coverage` 日志，原始日志留存于 `/tmp/cov137.log`，不入库）**：#133/#134 现均 `done`/CLOSED（§7.1 已补两行）；#135（`utils/echarts.js`→`utils/echarts.ts` + `utils/chinaMap.js`→`utils/chinaMap.ts`，1be01af）与 #136（`stores/tabs.js`→`stores/tabs.ts`，ce3ab0d）已于 2026-10-26 执行完成并合入 main，**截至本段时点均为 `in-review`**（当时待 Planner 验收，**未预支 `done`**；**二者已于 2026-10-27 独立复跑验收通过并关闭**）。本轮实测于提交 **`ce3ab0d`**：**47 files / 321 tests**，总覆盖率 **Stmts 83.85% · Branch 77.32% · Funcs 37.44% · Lines 83.85%**（`stores/app.ts` 100 / 100 / 100 / 100；`stores/tabs.ts` 98.56 / 95.77 / 100 / 98.56，未覆盖行 **53、208**；`utils/echarts.ts` 100 / 100 / 100 / 100；`utils/chinaMap.ts` 100 / 100 / 100 / 100；`stores/user.js` 97.97 / 81.57 / 100 / 97.97，未覆盖行 39-40；`stores/analysis.js` 100 / 91.11 / 100 / 100，未覆盖行 38、48；`utils/index.js` 98.23 / 97.08 / 100 / 98.23，未覆盖行 69-70、203-204；`utils/authSession.js` 87.17 / 83.33 / 100 / 87.17）。`stores/tabs.ts` 的两处未覆盖（53、208）是 `loadActiveFromStorage` 与 `resetTabs` 中 `localStorage` 抛错的 catch 分支，与迁移前 `stores/tabs.js` 的 40-41、190-191 **为同一代码区域**（行号位移源于新增的 interface/注释/多行类型标注），按 #131 约定不 mock。0% 模块清单不变（8 个 `src/api/` 声明式包装：alert / content / favorites / platform / predict / propagation / report / user，加 `main.js` 与 `App.vue`，后二者为入口与根壳豁免）。

同 HEAD（`ce3ab0d`）连续复跑一次得 `All files 83.75 | 77.33 | 37.55 | 83.75`，差异**全部**来自 `src/api/auth.js`（38.46 → 17.94）与 `src/views/auth/Login.vue`（100 | 75 | 50 | 100 → 97.87 | 76.92 | 75 | 97.87）两个与本批次无关的既有模块——已实测确认为**同一 HEAD 下连续两次运行的差异**（非 #135/#136 迁移引入；`stores/tabs.ts` 两次均为 98.56 / 95.77 / 100 / 98.56）。故 `All files` 汇总值除语句/分支小数抖动（83.79–83.90 / 77.32–77.35，D-034 已记录）外，**函数项亦存在同源抖动**，本段各模块明细值一律以本段绑定的单次日志为准。

**2026-11-22 执行快照（#143，未修复）**：锁基线 `b6661ad`，Vitest / `@vitest/coverage-v8` 3.2.7，默认 `forks`、`isolate: true`；前两次使用 Node 26.13.1 加 `NODE_OPTIONS=--no-webstorage`（仅避免 Node 存储全局名覆盖 jsdom，不改调度）。两次 `npm run test:coverage` 均为 47 文件 / 321 用例，退出 0；比较项为 Stmts / Branch / Funcs / Lines（%）：

| 覆盖对象 | 默认运行 1 | 默认运行 2 |
|---|---|---|
| `frontend/src/api/auth.js` | 17.94 / 100 / 0 / 17.94 | 17.94 / 100 / 0 / 17.94 |
| `frontend/src/views/auth/Login.vue` | 97.87 / 76.92 / 75 / 97.87 | 97.87 / 76.92 / 75 / 97.87 |
| `All files` | 83.73 / 77.33 / 37.55 / 83.73 | 83.73 / 77.33 / 37.55 / 83.73 |

D-034 原记录的 83.79–83.90 / 77.32–77.35 只描述历史语句/分支波动；#138 在同一旧提交另观察到 Funcs **37.44–37.55**。本轮两次均为 37.55，不改历史数值，也不把历史观测扩成验收带。

- 同锁 Node 22.23.2 两次结果与表相同；Node 22.23.5 两次默认运行的 `All files` Branch 为 **77.35 → 77.33**，Node 26 三个文件 shuffle seed（7 / 19 / 143）均为 77.35，两个 auth 文件四项保持不变。在旧提交 `ce3ab0d` 上用 Node 22.23.2 重建也得到 77.35 → 77.33，两个 auth 文件未漂移。历史重建不混作同锁对照。
- 当前锁单跑 `login-journey`、`user-store`，`auth.js` 均为 0 / 0 / 0 / 0；单跑 `router-guard` 为 17.94 / 100 / 0 / 17.94。追踪每套件的 V8 记录确认真实模块与工厂 mock 的载入差异，没有观察到默认隔离跨套件污染。
- 此次可重现的聚合差异在 `stores/tabs.ts`：LCOV 的 BRF/BRH 从 71/68 变为 72/69，其他文件的 FNF/FNH/BRF/BRH/LF/LH 相同。固定 `router-guard`、`login-journey`、`tabs-store` 三套件的原始 V8 输入，只反转 `mergeProcessCovs` 的逐步合并顺序，`addTab` 的 `[2119,2196)` 计数范围就从被合入上一范围变为单独保留（计数 16）；这是合并顺序的证据，不是应用行为或用例通过数变化。
- 不修改 mock、生产分支、调度或覆盖范围来改变报表。历史 auth 双文件漂移的根因仍未证实；目前相同的两次读数不是修复后验收。复跑命令、退出码及证据边界见 #143 执行报告。

#### 2026-11-22 · #147 同一批 V8 数据的合并顺序对照

基线 `1316e15f5d843b9fe7e915e5f8fb554f2df0b3ef`，Node 26.13.1、npm 11.20.0、Vitest 与 `@vitest/coverage-v8` 3.2.7、`@bcoe/v8-coverage` 1.0.2。`npm ci` 前后 `frontend/package-lock.json` SHA-256 均为 `bab52592904dfccd8d48c6f9a4c6acb1e6645479ff4b3d5eed0f165aa8c59474`。三个套件在默认调度及隔离下通过 54 个测试。下表是本轮正式回放的输入指纹，原始 JSON 含工作目录和 V8 脚本 ID，重新采集时可产生不同指纹。

| 标识 | 套件（`frontend/tests/` 下） | project / transformMode | 脚本数 / 字节 | 原始 JSON SHA-256 |
| --- | --- | --- | --- | --- |
| L | `login-journey.test.js` | 默认 / web | 43 / 49,194 | `0099c282db4e683626b433b50f5037103101249c561ff3e18228a325154fac91` |
| R | `router-guard.test.js` | 默认 / web | 54 / 50,084 | `ddac0f9cd40f0c2ca15caac15c1e9dbbb2b7442fa51a8b61f6f54e9b60ddf8d0` |
| T | `tabs-store.test.js` | 默认 / web | 3 / 12,788 | `2b82e2676d31d4e43ca2673097556bc748feb73e301c490b8f5105b5b04c8bba` |

| 三个原始输入的排列 | provider 逐步合并 | 按相对套件路径排序后逐步合并 | 每组一次性合并 |
| --- | --- | --- | --- |
| LRT | 71/68 · A | 71/68 · A | 72/69 · B |
| LTR | 72/69 · B | 71/68 · A | 72/69 · B |
| RLT | 71/68 · A | 71/68 · A | 72/69 · B |
| RTL | 72/69 · B | 71/68 · A | 72/69 · B |
| TLR | 72/69 · B | 71/68 · A | 72/69 · B |
| TRL | 72/69 · B | 71/68 · A | 72/69 · B |

数值为 `stores/tabs.ts` 的 LCOV `BRF/BRH`，复现 #143 的两档。三套件报告中，其他文件的 LCOV 记录相同，只有 `tabs.ts` 改变，`All files` Branch 随之由 164/210（78.09%）变为 165/211（78.19%）。这些比例基于三套件和 provider 的 `all: true`，全量基线仍见上文。

- **`addTab` 的范围差异。** A 的外层 `[1957,2196)` 为 16。B 分为 `[1957,2044)` 和 `[2119,2196)` 两个各为 16 的范围。三种算法都保留其中的 `[2044,2119)=4`（第 82–86 行，已有标签页），以及 `[2119,2189)=12` 和 `[2189,2196)=11`（进入新标签页及 `meta?.title`）。在 provider 的映射里，A 的 16 覆盖 `79:38–90:34`。B 的两个 16 分别映到 `79:38–82:18` 和 `86:4–90:34`（行从 1 起，列从 0 起）。B 的外层范围 `[2119,2196)` 计数为 16，内层进入新建对象的计数仍为 12。
- **独立核对计数。** 三个套件的函数入口计数分别为 3、3、13，LCOV `FNDA:19,addTab` 一致。按原始范围核对，19 次入口里有 3 次第 79 行守卫返回、4 次第 82–86 行激活既有标签页、12 次走到新建对象，`3 + 4 + 12 = 19`。`tabs-store` 中的三种无效输入、同名激活、新建以及有/空 query 的现有断言提供了独立的命中证据。第 93–95 行 query 拼接和不拼接的 V8 范围分别命中 4 和 8 次。`addTab` 在本样本没有单独报告的零计数范围。合并前后对 `tabs.ts` 的 27 个函数和 105 个最小区间逐段求和，18 次均零差异，因此多一条 LCOV 分支没有增加实际执行次数。
- **`Login.vue` 的组、源映射和计数。** L/R 各有两个同 URL 的脚本记录，T 没有该组件记录。按原始记录各取一次，按函数根范围核对 22 个函数、45 个最小区间，18 次均零差异。三份输入属于同一个默认项目 / `web` 组。回放以 `(projectName, transformMode)` 分组并逐组交给 provider 转换，样本未覆盖两个真实 transform 组同时存在的情况。该组的 `startOffset` 恒为 209，映射回原 `Login.vue`，三种算法的 Istanbul 文件计数和 LCOV 记录逐项相同（`BRF/BRH=13/10`、`FNF/FNH=4/3`、`LF/LH=94/92`）。现有登录用例的 5 次有效提交对应 `FNDA:5,handleLogin`。源码第 102 行成功分支 3 次、第 106 行失败分支 2 次，第 90、94 行的提前返回和第 107 行的默认错误文案均为 0。负对照只将 Vue 的 `startOffset` 改为 0，源映射输入及原始区间不变，LCOV 变为 `8/6` 且丢失 `handleLogin`。偏移必须随每组的 URL 保留。

**回放方法。** 在 `frontend/` 运行 `npm ci` 安装同一锁，Node 26 本轮使用 `NODE_OPTIONS=--no-webstorage` 让 jsdom 提供 Storage。外部探针用 `vitest/node` 的 `createVitest('test', { watch: false, coverage: { enabled: true, reportsDirectory } })` 创建同一配置，初始化 provider，在 `onAfterSuiteRun` 复制 `coverage` 并记录 `testFiles`、`projectName`、`transformMode`，然后调用原方法。用 `ctx.start()` 传入表中的三个文件，只运行一轮，将 `JSON.stringify(coverage)` 保存为组内原始输入。可在同一个 Vite 上下文按下列步骤回放，保留当次的 sourcemap 缓存。

1. 枚举六种排列，按 `(projectName, transformMode)` 分组。替换 provider 的 `readCoverageFiles`，原序和排序版本分别把每组的原始输入副本按原序或相对路径顺序交给 `onFileRead`，每组结束调用 `onFinished(project, transformMode)`。使用副本是因为 `mergeProcessCovs` 会修改输入。
2. 一次性版本对每组调用一次 `mergeProcessCovs`，按 URL 从原始输入回填 `startOffset`，同组同 URL 的偏移不一致即报错。该结果直接交给该组的原 `convertCoverage`，跳过组内累计合并，仍用 `generateCoverage({ allTestsRun: true })` 的组间映射与合并，以及 `generateReports` 的 `lcovonly` 输出。
3. 在 `convertCoverage` 入口记录原始范围与合并后范围。对每个 `(组, URL, 函数根范围)`，收集每个输入区间的全部端点，取相邻端点间各原始输入最内层覆盖范围的计数之和，缺席作 0，与合并后相同区间比较。用 provider 的 `v8ToIstanbul` 对 `addTab` 单独取一次源位置，并用完整转换结果的 `BRDA`、`BRF/BRH`、`FNDA` 复核。同法重跑一次性合并，唯独令 `Login.vue` 偏移为 0，验证映射负对照。

**建议。** 同一批样本内，两个候选均满足六次排列稳定、原始区间逐点计数和 Vue 映射一致。排序固定了 A 的区间表达，一次性合并稳定保留 B，现有证据无法确定哪种额外的 LCOV 记录应视为源代码分支。另用锁定的 `mergeProcessCovs` 做单函数合成反例，同根范围的函数级入口 2 与块级入口 3（子范围 1）在两个输入顺序下均只保留 3/1。此样本不含该类计数丢失，但稳定合并无法保证任意输入的入口次数相加。先保留现有工具链，若另立工具修正任务，应覆盖混合粒度、跨 transform 组和源分支归属。#143 的历史 auth 双漂移仍需自己的原始样本。

#### 2026-11-23 · #147 复跑与回退分支计数

以原实验提交 `1316e15f5d843b9fe7e915e5f8fb554f2df0b3ef` 新建临时工作树。Node 26.13.1、npm 11.20.0、Vitest 与 V8 provider 3.2.7。离线 `npm ci --offline --no-audit` 退出 0、安装 423 个包，锁 SHA-256 前后均为 `bab52592904dfccd8d48c6f9a4c6acb1e6645479ff4b3d5eed0f165aa8c59474`。下方探针从该临时树的 `frontend/` 运行，退出 0，实际执行 3 文件 / 54 用例与 18 次回放。原算法复现 A 71/68 与 B 72/69，排序逐步合并六次均为 A，一次性合并六次均为 B。

| addTab 回退 | A、B 的原始 V8 半开范围 | 三套件命中 L / R / T | provider 源映射（行从 1 起，列从 0 起） | 完整 LCOV 的 BRDA（A；B） |
| --- | --- | --- | --- | --- |
| 第 90 行 `\|\| route.name` | `[2197,2210)` | 0 / 0 / 1 | `90:25–90:45`，1 次 | `90,26,0,1`；`90,27,0,1` |
| 第 96 行 `\|\| null` | `[2373,2380)` | 0 / 0 / 1 | `96:24–96:37`，1 次 | `96,31,0,1`；`96,32,0,1` |

在 provider 的 `convertCoverage` 映射过程中，使用同一份 Vite `web` 转译源码、sourcemap 和 `tabs.ts` 的 `startOffset=209`，将单个 `addTab` 的范围交给同一 `v8ToIstanbul`，再用完整报告的 LCOV 对照。V8 另记录前置的可选属性读取，第 90 行 `[2189,2196)=11`、第 96 行 `[2366,2372)=11`。A/B 多出的一条范围移位了 LCOV 的编号，两处回退的原始范围和命中数均一致。

以下命令从任意已获取该提交的仓库根目录执行。将后面的 JavaScript 块保存为 `$study_dir/replay147.mjs`。从临时工作树的 `frontend/` 启动可以让 Vitest 使用该快照的配置。探针以这个目录的 `package.json` 建立模块解析基准，用它解析 `vitest/node` 和 `@vitest/coverage-v8`，再从 provider 入口解析它自己的 `@bcoe/v8-coverage`。

```bash
study_dir=$(mktemp -d)
git worktree add --detach "$study_dir/baseline" 1316e15f5d843b9fe7e915e5f8fb554f2df0b3ef
cd "$study_dir/baseline/frontend"
node --version
npm --version
sha256sum package-lock.json
npm ci --no-audit
sha256sum package-lock.json
NODE_OPTIONS=--no-webstorage node "$study_dir/replay147.mjs" "$study_dir/results"
```

Node 26 使用上述 Storage 开关。若缓存包含完整锁，`npm ci --offline --no-audit` 可复用缓存。输出目录包含采集的三份 JSON、原生 LCOV、各排列的映射数据和 LCOV。下列探针聚焦本次两项补证，原实验的 Vue 负对照和逐区间检查步骤见上一段。

```js
import assert from 'node:assert/strict'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

const requireFrontend = createRequire(resolve('package.json'))
const providerEntry = requireFrontend.resolve('@vitest/coverage-v8')
const { mergeProcessCovs } = createRequire(providerEntry)('@bcoe/v8-coverage')
const { createVitest } = await import(pathToFileURL(requireFrontend.resolve('vitest/node')).href)
const out = resolve(process.argv[2])
await mkdir(out, { recursive: true })
const suites = ['login-journey', 'router-guard', 'tabs-store']
const ctx = await createVitest('test', {
  watch: false,
  coverage: { enabled: true, reportsDirectory: resolve(out, 'native'), reporter: ['lcovonly'] },
})
try {
  await ctx.initCoverageProvider()
  const provider = ctx.coverageProvider
  assert.equal(provider.version, '3.2.7')
  const captured = new Map()
  const afterSuite = provider.onAfterSuiteRun.bind(provider)
  provider.onAfterSuiteRun = (event) => {
    const index = suites.findIndex((name) =>
      event.testFiles.some((file) => file.endsWith('/' + name + '.test.js')))
    assert.ok(index >= 0 && event.coverage && !captured.has('LRT'[index]))
    assert.equal(event.transformMode, 'web')
    captured.set('LRT'[index], structuredClone(event))
    return afterSuite(event)
  }
  const result = await ctx.start(suites)
  assert.equal(process.exitCode ?? 0, 0)
  assert.equal(result.testModules.length, 3)
  assert.equal(captured.size, 3)
  assert.equal(new Set([...captured.values()].map((event) => event.projectName)).size, 1)
  const { projectName, transformMode } = captured.get('L')
  const project = ctx.getProjectByName(projectName)
  const convert = provider.convertCoverage.bind(provider)
  const native = await readFile(resolve(out, 'native/lcov.info'), 'utf8')
  const tabsRecord = (lcov) => lcov.split('end_of_record\n')
    .find((record) => record.includes('src/stores/tabs.ts\n'))
  const outcome = (lcov) =>
    tabsRecord(lcov).match(/^BRF:(\d+)\nBRH:(\d+)$/m).slice(1).join('/')
  assert.ok(['71/68', '72/69'].includes(outcome(native)))
  const targets = [[2197, 2210, 90], [2373, 2380, 96]]
  for (const [startOffset, endOffset] of targets) {
    const counts = [...'LRT'].map((key) => {
      const script = captured.get(key).coverage.result
        .find(({ url }) => url.endsWith('/src/stores/tabs.ts'))
      return script.functions.find(({ functionName }) => functionName === 'addTab')
        .ranges.find((range) => range.startOffset === startOffset && range.endOffset === endOffset)
        .count
    })
    assert.deepEqual(counts, [0, 0, 1])
  }
  for (const [key, { coverage }] of captured) {
    await writeFile(resolve(out, key + '.json'), JSON.stringify(coverage))
  }
  for (const order of ['LRT', 'LTR', 'RLT', 'RTL', 'TLR', 'TRL']) {
    for (const mode of ['incremental', 'sorted', 'batch']) {
      const inputs = [...(mode === 'sorted' ? 'LRT' : order)]
        .map((key) => structuredClone(captured.get(key).coverage))
      let batch
      if (mode === 'batch') {
        const offsets = new Map()
        for (const { result } of inputs) {
          for (const { url, startOffset = 0 } of result) {
            assert.equal(offsets.get(url) ?? startOffset, startOffset)
            offsets.set(url, startOffset)
          }
        }
        batch = mergeProcessCovs(inputs)
        for (const script of batch.result) script.startOffset = offsets.get(script.url)
      }
      provider.readCoverageFiles = async ({ onFileRead, onFinished }) => {
        if (!batch) inputs.forEach(onFileRead)
        await onFinished(project, transformMode)
      }
      let addTab, mapped, tabsOffset
      provider.convertCoverage = (merged, project, transformMode) =>
        convert(batch ?? merged, project, transformMode)
      const v8ToIstanbul = provider.v8ToIstanbul.bind(provider)
      provider.v8ToIstanbul = async (url, offset, sources, functions) => {
        if (url.endsWith('/src/stores/tabs.ts') && functions.some((fn) => fn.functionName === 'addTab')) {
          addTab = structuredClone(functions.find((fn) => fn.functionName === 'addTab'))
          tabsOffset = offset
          const isolated = await v8ToIstanbul(url, offset, sources, [addTab])
          mapped = isolated[Object.keys(isolated)[0]]
        }
        return v8ToIstanbul(url, offset, sources, functions)
      }
      try {
        const report = await provider.generateCoverage({ allTestsRun: true })
        provider.options.reportsDirectory = resolve(out, order + '-' + mode)
        await provider.generateReports(report, true)
        const lcov = await readFile(resolve(provider.options.reportsDirectory, 'lcov.info'), 'utf8')
        const expected = mode === 'sorted' || (mode === 'incremental' && ['LRT', 'RLT'].includes(order))
          ? '71/68' : '72/69'
        assert.equal(outcome(lcov), expected)
        assert.equal(addTab.ranges[0].count, 19)
        assert.equal(Object.keys(mapped.branchMap).length, addTab.ranges.length)
        const ranges = Object.values(mapped.branchMap).map(({ loc }, i) => ({
          ...addTab.ranges[i], loc, mappedCount: mapped.b[i][0],
        }))
        for (const [startOffset, endOffset, line] of targets) {
          const range = ranges.find((entry) => entry.startOffset === startOffset)
          assert.equal(range.endOffset, endOffset)
          assert.equal(range.loc.start.line, line)
          assert.equal(range.loc.end.line, line)
          assert.equal(range.count, 1)
          assert.equal(range.mappedCount, 1)
          assert.ok(tabsRecord(lcov).split('\n')
            .some((record) => record.startsWith('BRDA:' + line + ',') && record.endsWith(',0,1')))
        }
        await writeFile(resolve(out, order + '-' + mode + '.json'),
          JSON.stringify({ outcome: expected, startOffset: tabsOffset, ranges }, null, 2))
        console.log(order, mode, expected)
      } finally {
        provider.v8ToIstanbul = v8ToIstanbul
      }
    }
  }
} finally {
  await ctx.close()
}
```

**授权边界**：未设 `coverage.thresholds`、未把覆盖率纳入 CI；两项均需用户明确授权。
