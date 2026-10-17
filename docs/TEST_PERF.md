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

## 7. 议题状态与待确认建议（2026-10-17 重写）

> M6 主项已收口：本节改为「议题真实状态总表 + 已归档机制决策 + socket 审计结论 + 仍待确认的低风险候选」。状态按 GitHub 真实 state 抄录（2026-10-17）。

### 7.1 议题状态总表

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
| [#106](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/106) | P3 | in-review | M6 预算报告 + socket 审计 + 跨天交接证据（本文件 §6/§6.1/§7 即交付物之一；执行报告见 Issue） |
| [#107](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/107) | P2 | in-review | 可观测模块行为验证恢复 + 分支覆盖率基线（be32bd0 已合入；CI 全绿，见 §6） |
| [#108](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/108) | P3 | ready | rustup 工具链 pin 生效 + maturin/README 构建边界 + `.env.example` 补全 + ADR-0005 |
| [#110](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/110) | P3 | ready | `scripts/` lint 门禁缺口（9 errors，含 `append_api.py` 语法错误）+ 8 项机械修复；不设 milestone |

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

- 前端 vitest 覆盖率配置（#93 遗留项；未配置，纳入下次前端议题时评估）；
- integration 层补用例（196 用例偏薄，低覆盖集中在 `views/user`、`views/api/user_routes`；补 integration 优先于加 unit）；
- 测试规范固化：>1s 用例 PR 需说明理由；mock 样板 >20 行必须提共享 fixture（§3 R3 教训）。
