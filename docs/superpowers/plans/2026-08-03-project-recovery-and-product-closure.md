# 微博舆情分析项目收口与稳定化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将当前功能分散、数据来源混杂、文档漂移且验证反馈过慢的微博舆情分析系统，收口为一条可信、可运行、可演示、可持续维护的微博舆情分析主链路。

**Architecture:** 保留现有 Flask + SQLAlchemy + Vue/Vite 架构，不在第一阶段新增微服务。先把“话题 → 采集 → 入库 → 情感/传播分析 → 可视化 → 报告”的主链路收敛到稳定的后端契约，再把 Spider/NLP/Celery 作为可选执行后端接入。真实数据、演示数据和实验模型通过统一 provenance（数据来源元信息）显式区分，前端所有结论都必须能追溯到来源和时间范围。

**Tech Stack:** Python 3.11+, Flask, SQLAlchemy, pytest, Ruff/Black, Vue 3, Vite, Element Plus, ECharts, npm, Docker Compose, MySQL/SQLite test database.

## Global Constraints

- 第一阶段只把微博作为正式数据源；抖音、知乎、B 站、微信保留代码但只能以显式实验/演示能力出现。
- 任何接口不得在正式模式下静默返回 mock 数据；演示数据必须由明确的 `demo=true` 或演示环境开关触发，并在响应中携带来源标识。
- 不删除现有数据库表、迁移和公开 API；需要改变语义时增加版本化响应字段，并保留兼容转换层。
- 不在本计划中引入新的微服务、消息队列或前端状态管理库；先使用现有服务边界解决一致性问题。
- 所有新行为先写失败测试，再写最小实现；每个任务完成后运行该任务的专项测试和项目质量门禁。
- 不提交 `.env`、Cookie、数据库密码、模型私钥或真实微博数据；文档和日志必须脱敏。
- 完成标准不是“页面能打开”，而是主链路能在空数据、真实数据、演示数据、后端依赖不可用四种状态下给出可解释结果。

## 现状基线与验收总表

当前工作区已有未提交修改，执行前必须单独保存或提交现有工作；不得把本计划的实现直接混入未知半成品变更中。

| 阶段 | 主要结果 | 通过条件 |
| --- | --- | --- |
| A. 产品收口 | 产品范围、数据来源和用户主任务定稿 | README、API 文档、前端导航和后端能力一致 |
| B. 数据可信 | 真实/演示/实验数据可追溯 | 每个分析响应带 `provenance`、`time_range`、`data_count` |
| C. 工程基线 | 启动、测试、构建、CI 可重复 | 一条命令完成检查；没有无界等待的 Redis/MySQL 连接 |
| D. 主链路 | 话题到报告完整闭环 | 新用户可在 5 分钟内完成一次分析并导出报告 |
| E. 体验与上线 | 空态、错误态、权限、部署、合规清晰 | 无假数据伪装；CI 和部署 smoke test 通过 |

---

## Task 1: 建立当前基线和质量门禁

**目的:** 先把“现在到底能不能跑”固定下来，防止后续每次改动都在漂移的环境上判断。

**Files:**
- Create: `scripts/verify_project.ps1`
- Create: `scripts/healthcheck.py`
- Modify: `pyproject.toml`
- Modify: `pytest.ini`
- Modify: `frontend/package.json`
- Create: `frontend/vitest.config.js`
- Modify: `.github/workflows/ci.yml`
- Modify: `docs/DEVELOPMENT.md`
- Test: `tests/test_project_health.py`

**Interfaces:**
- `scripts/healthcheck.py` 提供 `GET /health` 和 `GET /ready` 的本地检查逻辑；脚本退出码 `0` 表示通过，非零表示失败。
- `scripts/verify_project.ps1` 顺序执行后端静态检查、后端专项测试、前端 lint、前端 build 和健康检查；任何一步失败立即退出。
- `frontend/package.json` 提供 `npm run test` 和 `npm run test:run`，并增加与当前 Vue 版本匹配的 `vitest`、`jsdom`、`@vue/test-utils` 开发依赖；Vitest 使用 `frontend/vitest.config.js`，不依赖真实后端。
- pytest markers 固定为 `unit`、`api`、`integration`、`slow`、`external`；默认命令只执行 `unit` 和 `api`。

- [ ] **Step 1: 记录当前基线**

运行以下命令并把结果写入临时评审记录，不修改业务代码：

```powershell
git status --short
python --version
pytest --collect-only -q
python -m ruff check src tests
Push-Location frontend
npm ci
npm run test:run
npm run build
Pop-Location
```

记录：收集到的测试数量、首个失败测试、前端构建耗时、缺失环境变量和外部服务依赖。若 `pytest` 或 `npm run build` 超时，必须记录具体卡点，不得把超时当成通过。

- [ ] **Step 2: 写健康检查测试**

在 `tests/test_project_health.py` 中覆盖：

```python
def test_health_endpoint_is_dependency_free(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_ready_endpoint_reports_missing_dependencies(client, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "mysql://invalid-host/invalid")
    response = client.get("/ready")
    assert response.status_code in {200, 503}
    assert "checks" in response.get_json()
```

- [ ] **Step 3: 实现独立于业务查询的 `/health` 和有超时的 `/ready`**

`/health` 只检查进程；`/ready` 检查配置、数据库连接和已启用的可选服务，每项都使用有限超时并返回单项状态，不能因为 Redis 未启动而让 Flask 请求线程无限等待。

- [ ] **Step 4: 写统一验证脚本**

`verify_project.ps1` 至少执行：

```powershell
python -m ruff check src tests
pytest -m "unit or api" -q --maxfail=1
Push-Location frontend
npm run test:run
npm run lint
npm run build
Pop-Location
```

脚本必须保留命令输出，失败时返回原始退出码。

- [ ] **Step 5: 更新 CI 并验证**

GitHub Actions 分成 `backend-fast`、`frontend-fast`、`integration` 三个 job；默认 PR 不启动需要真实微博 Cookie 的测试。运行：

```powershell
pwsh -NoProfile -File scripts/verify_project.ps1
```

Expected: 脚本逐项执行；任一检查失败时整体非零，全部通过时整体为 `0`。

- [ ] **Step 6: Commit**

```bash
git add scripts/verify_project.ps1 scripts/healthcheck.py tests/test_project_health.py pyproject.toml pytest.ini .github/workflows/ci.yml docs/DEVELOPMENT.md
git commit -m "chore: establish reproducible project quality gates"
```

---

## Task 2: 收口产品范围并修正文档漂移

**目的:** 让项目明确“正式能力是什么、实验能力是什么、演示能力是什么”，并保证 README 不再描述不存在的目录或已失效的启动路径。

**Files:**
- Create: `docs/PRODUCT_SCOPE.md`
- Create: `docs/USER_FLOWS.md`
- Create: `scripts/check_documented_paths.py`
- Modify: `README.md`
- Modify: `docs/API.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/DEPLOYMENT.md`
- Test: `tests/test_documented_paths.py`

**Interfaces:**
- `docs/PRODUCT_SCOPE.md` 定义三类能力：`正式数据`、`实验能力`、`演示能力`；每个功能必须归入且只能归入一类。
- `docs/USER_FLOWS.md` 定义唯一主任务：选择微博话题和时间范围 → 查看摘要 → 下钻文章/评论 → 查看传播 → 导出报告。
- `scripts/check_documented_paths.py` 读取 README 和架构文档中的反引号路径，验证路径存在；对已知的 API 路径检查对应蓝图或测试存在。

- [ ] **Step 1: 写产品范围文档**

明确第一版只承诺以下正式闭环：微博文章/评论采集、基础情感分析、热词/趋势、地域分布、传播摘要、报告导出。多平台采集、训练模型、协作和实时 WebSocket 标记为实验或后续能力，不在首页主导航占据同等层级。

- [ ] **Step 2: 写用户任务和验收指标**

在 `docs/USER_FLOWS.md` 固定指标：

```text
主任务完成：用户能从一个入口完成一次话题分析并看到来源说明。
可信性：所有数值都能显示时间范围、数据量、数据源和模型/规则版本。
空数据：没有数据时显示原因和下一步，不显示 0 作为伪结果。
报告：导出内容包含摘要、数据范围、来源说明、局限性和生成时间。
```

- [ ] **Step 3: 清理 README 的真实目录和启动命令**

以 `git ls-files` 和实际运行脚本为唯一来源，删除不存在的目录描述，补充 Windows PowerShell、Docker Compose 和纯后端测试三条确定路径。README 必须明确当前改造期不保证外部 Spider/NLP 服务默认启动。

- [ ] **Step 4: 对文档路径做自动检查**

测试 `check_documented_paths.py` 能发现一个故意写错的路径，并在修正后通过：

```powershell
python scripts/check_documented_paths.py
pytest tests/test_documented_paths.py -q
```

- [ ] **Step 5: Commit**

```bash
git add docs/PRODUCT_SCOPE.md docs/USER_FLOWS.md scripts/check_documented_paths.py tests/test_documented_paths.py README.md docs/API.md docs/ARCHITECTURE.md docs/DEPLOYMENT.md
git commit -m "docs: define product scope and synchronize project documentation"
```

---

## Task 3: 统一数据来源和分析响应契约

**目的:** 解决正式数据、mock 数据和实验模型混在同一套图表里的可信度问题。

**Files:**
- Create: `src/services/analysis_contracts.py`
- Create: `src/utils/data_provenance.py`
- Create: `tests/test_data_provenance.py`
- Modify: `src/views/data/data_api.py`
- Modify: `src/views/api/platform_api.py`
- Modify: `src/views/api/propagation_api.py`
- Modify: `src/views/api/report_api.py`
- Modify: `src/views/api/spider_api.py`
- Modify: `src/utils/getHomeData.py`
- Modify: `src/utils/getEchartsData.py`
- Modify: `src/utils/getTableData.py`
- Modify: `frontend/src/api/index.js`
- Modify: `frontend/package.json`
- Modify: `frontend/vitest.config.js`
- Create: `frontend/src/components/Common/ProvenanceBadge.vue`
- Create: `frontend/src/components/Common/AnalysisEmptyState.vue`
- Test: `frontend/tests/provenance.test.js`

**Interfaces:**
- `src/services/analysis_contracts.py` 定义不可变响应结构 `AnalysisMeta`，字段固定为 `source_type`、`source_name`、`is_demo`、`model_name`、`model_version`、`time_range`、`data_count`、`generated_at`、`limitations`。
- `src/utils/data_provenance.py` 提供 `real_meta(...)`、`demo_meta(...)`、`experimental_meta(...)` 三个构造函数；`source_type` 只能是 `real`、`demo`、`experimental`。
- 所有分析 API 的顶层 `data` 必须包含 `meta`；旧字段保留，前端先兼容旧数据结构再迁移。
- `ProvenanceBadge.vue` 接收 `meta` 属性，明确显示“真实数据/演示数据/实验能力”，不得只靠颜色区分。

- [ ] **Step 1: 写 provenance 单元测试**

覆盖：真实数据不能带 `is_demo=true`；演示数据必须带 `limitations`；缺失时间范围或数据量时构造函数抛出 `ValueError`；未知来源类型拒绝进入响应。

- [ ] **Step 2: 定义并实现后端元信息结构**

不把来源信息散落在每个路由里；所有路由通过构造函数生成 `meta`，并把模型版本、词典版本或规则版本写入响应。

- [ ] **Step 3: 为旧 API 增加 meta，不改变已有业务字段**

逐个改造首页、表格、图表、平台、传播、报告和爬虫接口。正式模式找不到真实数据时返回空结果/404 和原因；只有显式 demo 开关才调用演示 provider。

- [ ] **Step 4: 把 mock provider 与真实 provider 分开**

在 `src/services/platform_collectors/` 中将演示实现放在明确的 `demo` provider，不允许真实 collector 的异常分支直接返回 mock 数据。没有实现的平台返回 `501` 或带 `experimental` 元信息的空结果。

- [ ] **Step 5: 添加前端显式标识和空态**

公共图表卡片和报告页统一使用 `ProvenanceBadge`；数据为空时使用 `AnalysisEmptyState`，显示“没有数据/采集失败/未接入/筛选范围无结果”中的具体原因。

- [ ] **Step 6: 验证并 Commit**

```powershell
pytest tests/test_data_provenance.py tests/test_real_data_apis.py -q
Push-Location frontend
npm run test:run
npm run build
Pop-Location
git add src frontend/src tests frontend/tests
git commit -m "feat: make analysis data provenance explicit"
```

---

## Task 4: 稳定“微博主分析链路”并建立单一分析入口

**目的:** 把现有大量分散的首页、图表和旧查询函数收束为一个可解释的分析快照，减少前端一次页面加载触发多个不一致查询。

**Files:**
- Create: `src/services/analysis_pipeline.py`
- Create: `src/repositories/analysis_repository.py`
- Create: `tests/test_analysis_pipeline.py`
- Create: `tests/test_analysis_api.py`
- Modify: `src/repositories/article_repository.py`
- Modify: `src/repositories/comment_repository.py`
- Modify: `src/services/sentiment_service/__init__.py`
- Modify: `src/services/propagation_analyzer.py`
- Modify: `src/views/data/data_api.py`
- Modify: `frontend/src/api/stats.js`
- Create: `frontend/src/api/analysis.js`
- Modify: `frontend/src/views/home/index.vue`
- Modify: `frontend/src/views/analysis/article.vue`
- Modify: `frontend/src/views/analysis/comment.vue`
- Modify: `frontend/src/views/analysis/sentiment.vue`
- Modify: `frontend/src/views/analysis/propagation.vue`
- Test: `frontend/tests/analysis-contract.test.js`

**Interfaces:**
- `AnalysisPipeline.run(topic: str, start_at: datetime, end_at: datetime, *, demo: bool = False) -> AnalysisSnapshot` 是唯一主链路入口。
- `AnalysisSnapshot` 至少包含 `summary`、`trend`、`sentiment`、`top_articles`、`top_comments`、`propagation`、`meta`。
- `GET /api/v1/analysis` 接收 `topic`、`start_at`、`end_at`、可选 `demo`，返回一个 `AnalysisSnapshot`；旧 `/getAllData/*` 接口通过兼容层读取同一份快照结构。
- repository 只负责查询和聚合原始数据；情感和传播判断由 service 完成；路由只负责参数校验、权限和响应格式。

- [ ] **Step 1: 为快照定义失败测试**

覆盖四种场景：有真实数据、无数据、demo 数据、数据库异常。断言每种场景都有稳定的 HTTP 状态、`meta` 和可解释错误，不允许返回未标注的空数组或硬编码数字。

- [ ] **Step 2: 实现查询边界**

`analysis_repository.py` 只接受 topic、时间范围和分页限制；所有时间条件使用数据库字段和参数绑定；聚合结果明确区分文章量、评论量和去重后的内容量。

- [ ] **Step 3: 实现 `AnalysisPipeline`**

按固定顺序执行：查询 → 规范化 → 情感统计 → 热词/趋势 → 传播摘要 → 组装 provenance。任一可选分析失败时保留主摘要，并把降级原因写入 `limitations`；不吞异常后返回伪成功。

- [ ] **Step 4: 增加版本化 API 和兼容层**

新增 `/api/v1/analysis`，旧接口保留并委托给 pipeline。为旧字段写 contract tests，确保前端现有页面不会因新增 `meta` 而崩溃。

- [ ] **Step 5: 前端改为一次拉取、分区展示**

首页先展示摘要和来源，再按需加载文章、评论、情感和传播下钻；统一处理加载、空数据、降级和权限错误。旧 API 不再由多个组件重复并发调用同一查询。

- [ ] **Step 6: 验证主链路并 Commit**

```powershell
pytest tests/test_analysis_pipeline.py tests/test_analysis_api.py tests/test_api_contract.py -q
Push-Location frontend
npm run lint
npm run build
Pop-Location
git add src frontend/src tests frontend/tests
git commit -m "feat: consolidate the Weibo analysis pipeline"
```

---

## Task 5: 重构测试反馈和外部依赖边界

**目的:** 让测试快、可定位、可重复，不再因为 Redis/MySQL/Celery 默认连接导致全量测试无界等待。

**Files:**
- Create: `tests/factories.py`
- Create: `tests/test_dependency_policy.py`
- Modify: `tests/conftest.py`
- Modify: `tests/test_*.py`（只修改 marker、fixture 和外部依赖声明）
- Modify: `src/config/settings.py`
- Modify: `src/database.py`
- Modify: `src/services/nlp_task_service.py`
- Modify: `src/services/spider_task_service.py`
- Modify: `src/tasks/celery_config.py`
- Modify: `docs/DEVELOPMENT.md`

**Interfaces:**
- `tests/factories.py` 提供无外部服务的文章、评论、用户和分析快照工厂。
- `settings.py` 中所有外部服务都有显式启用开关和连接超时；测试模式默认 `memory://` 或本地 SQLite，不发起网络连接。
- 测试命令固定为：`pytest -m "unit or api" -q`、`pytest -m integration -q`、`pytest -m external -q`。

- [ ] **Step 1: 写依赖策略测试**

断言默认测试配置不会访问 Redis、微博、远程 NLP 或真实数据库；缺少可选依赖时测试给出 skip 原因而不是挂死。

- [ ] **Step 2: 将现有测试按 marker 分类**

不改变业务断言，只为测试补上 marker，并把重复的对象构造移到 factories。任何需要真实服务的测试必须显式标记 `integration` 或 `external`。

- [ ] **Step 3: 修复 fixture 的全局副作用**

保留临时目录隔离，但把环境变量、模块清理、Celery broker/backend 配置限制在 fixture 生命周期内；每个 fixture 结束后恢复 monkeypatch，避免测试顺序改变结果。

- [ ] **Step 4: 对慢测试做可观察化**

在 `pytest.ini` 配置 `--durations=20`；将压力测试和真实模型测试移出默认门禁。对每个超过 2 秒的默认测试记录原因并拆分网络、数据库和纯逻辑部分。

- [ ] **Step 5: 验证速度和隔离**

```powershell
pytest -m "unit or api" -q --maxfail=1
pytest -m "unit or api" -q --maxfail=1
pytest -m "integration" -q
```

Expected: 前两次结果一致，第二次不会依赖第一次产生的缓存或数据库状态；默认测试不连接外部服务。

- [ ] **Step 6: Commit**

```bash
git add tests src/config/settings.py src/database.py docs/DEVELOPMENT.md pytest.ini
git commit -m "test: isolate external dependencies and speed up feedback"
```

---

## Task 6: 前端信息架构和分析体验收口

**目的:** 把前端从“功能导航集合”改成围绕一个分析任务的工作台，同时让真实、演示、实验、空数据和失败状态在视觉上明确可见。

**Files:**
- Create: `frontend/src/components/Analysis/AnalysisSummary.vue`
- Create: `frontend/src/components/Analysis/AnalysisFilters.vue`
- Create: `frontend/src/components/Analysis/AnalysisSection.vue`
- Create: `frontend/src/components/Common/FailureState.vue`
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/components/Layout/Sidebar.vue`
- Modify: `frontend/src/components/Layout/TabBar.vue`
- Modify: `frontend/src/views/home/index.vue`
- Modify: `frontend/src/views/analysis/*.vue`
- Modify: `frontend/src/views/system/report.vue`
- Modify: `frontend/src/styles/index.scss`
- Create: `frontend/tests/navigation-and-empty-state.test.js`

**Interfaces:**
- `AnalysisFilters` 输出 `{ topic, startAt, endAt }`，默认时间范围明确显示，不允许静默使用浏览器本地时区造成日期错位。
- `AnalysisSummary` 接收 `AnalysisSnapshot`，只展示结论、关键数值、来源和限制；公式/原始状态数据放入可展开详情。
- `AnalysisSection` 接收 `title`、`status`、`meta`、`error`，统一处理 loading、empty、degraded、error 四种状态。

- [ ] **Step 1: 为导航和状态写测试**

覆盖主导航只突出“话题分析、趋势/情感、传播、报告”；实验功能必须有实验标识；空态不渲染假图表。

- [ ] **Step 2: 把分析筛选器提升为主入口**

首页顶部固定话题和时间范围，所有下钻页面从同一 query/store 读取上下文，刷新后 URL 可复现同一分析。

- [ ] **Step 3: 实现统一摘要组件**

摘要先展示一句话结论、数据范围、数据量、来源、模型/规则版本和局限性，再展示图表。没有足够数据时明确写“无法判断”，而不是展示空的趋势线。

- [ ] **Step 4: 收拢菜单和实验功能**

多平台、爬虫控制、模型预测、系统诊断移动到“实验/运维”区域；正式分析主流程只保留微博主链路页面。

- [ ] **Step 5: 做一次浏览器验收**

使用本地开发服务检查桌面宽度、窄屏宽度、刷新、无数据、接口 500、未登录、演示数据和真实数据标识。记录截图和问题清单；此步骤不以 `npm run build` 代替。

- [ ] **Step 6: Commit**

```powershell
Push-Location frontend
npm run lint
npm run build
Pop-Location
git add frontend/src frontend/tests
git commit -m "feat: focus frontend on the analysis workflow"
```

---

## Task 7: 报告、审计和合规边界

**目的:** 让导出的结论可解释、可追溯，并把微博 Cookie、个人信息和数据保留风险变成明确的系统行为。

**Files:**
- Create: `docs/DATA_GOVERNANCE.md`
- Create: `src/services/report_contracts.py`
- Create: `tests/test_report_provenance.py`
- Modify: `src/utils/report_generator.py`
- Modify: `src/views/api/report_api.py`
- Modify: `src/services/audit_service.py`
- Modify: `src/utils/log_sanitizer.py`
- Modify: `src/config/settings.py`
- Modify: `.env.example`
- Modify: `docs/DEPLOYMENT.md`
- Test: `tests/test_security_hardening.py`

**Interfaces:**
- 报告必须包含 `topic`、`time_range`、`source`、`data_count`、`generated_at`、`model_version`、`limitations` 和审计事件 ID。
- 审计事件只记录操作者、动作、资源类型、资源 ID、时间和结果；Cookie、Authorization、原始敏感文本不得写入日志。
- `.env.example` 明确 `WEIBO_COOKIE`、数据库密码、JWT secret、演示开关和数据保留天数；生产配置缺少 secret 时启动失败。

- [ ] **Step 1: 写报告契约测试**

测试真实、演示、空数据和降级报告都包含来源说明和限制性声明；没有数据时报告不能生成“分析结论”段落。

- [ ] **Step 2: 改造报告生成器**

报告内容按“范围 → 数据质量 → 结论 → 证据 → 局限性 → 生成信息”组织；每个图表和数字关联同一 `AnalysisSnapshot`，避免报告重新查询得到另一套数据。

- [ ] **Step 3: 完善日志脱敏和审计**

在请求日志、爬虫日志、任务日志和异常日志中统一脱敏 Cookie、Token、密码、手机号和邮箱；对导出、删除、登录失败、爬虫启动记录审计事件。

- [ ] **Step 4: 增加数据保留与删除策略**

文档先定义文章、评论、用户信息、任务日志、报告的保留周期和删除方式；代码只实现已有数据库结构能安全支持的部分，不能为了“合规”盲目删除生产数据。

- [ ] **Step 5: 验证并 Commit**

```powershell
pytest tests/test_report_provenance.py tests/test_security_hardening.py -q
python scripts/check_env.py
git add src docs .env.example tests
git commit -m "feat: make reports traceable and strengthen data governance"
```

---

## Task 8: 部署路径和发布验收

**目的:** 把本地开发、Docker Compose、CI 和演示环境的差异说清楚，并确保依赖不可用时系统优雅降级。

**Files:**
- Create: `docs/RELEASE_CHECKLIST.md`
- Create: `scripts/smoke_test.ps1`
- Modify: `docker-compose.yml`
- Modify: `Dockerfile`
- Modify: `frontend/Dockerfile`
- Modify: `frontend/nginx.conf`
- Modify: `scripts/start.bat`
- Modify: `scripts/start-frontend.bat`
- Modify: `docs/LOCAL_DEPLOYMENT.md`
- Modify: `docs/DEPLOYMENT.md`
- Test: `tests/test_compose_contract.py`

**Interfaces:**
- `scripts/smoke_test.ps1` 接收可选 `-BaseUrl`，依次检查前端首页、后端 `/health`、`/ready`、未登录 API 的 401/403、演示分析和空数据响应。
- Docker Compose 中每个服务必须有 healthcheck、明确依赖条件和非 root 运行约束；可选 Spider/NLP 服务关闭时主后端仍可启动。
- `docs/RELEASE_CHECKLIST.md` 是发布前唯一清单，包含迁移、secret、来源标识、测试、构建、回滚和日志检查。

- [ ] **Step 1: 写 Compose 合约测试**

检查 compose 文件存在 mysql、web、frontend 等声明的服务、健康检查和环境变量占位符；禁止把真实密码硬编码进 YAML。

- [ ] **Step 2: 修正启动依赖和健康检查**

让 web 等待数据库 ready，而不是只等待容器进程启动；Redis/Celery/Spider/NLP 作为可选服务时不能阻塞主站。

- [ ] **Step 3: 编写 smoke test**

在空数据库、演示数据和可选服务关闭三种环境执行 smoke test，检查状态码、响应 `meta` 和页面可打开性。

- [ ] **Step 4: 写发布与回滚清单**

清单必须包含：备份数据库、执行 Alembic、验证新字段、验证数据来源、运行质量门禁、保留上一镜像、回滚迁移/代码策略和停止采集开关。

- [ ] **Step 5: 最终验证并 Commit**

```powershell
python -m pytest -m "unit or api" -q
Push-Location frontend
npm run lint
npm run build
Pop-Location
docker compose config
pwsh -NoProfile -File scripts/smoke_test.ps1 -BaseUrl http://localhost:5000
```

Expected: 所有命令通过；若本机没有 Docker 或外部服务，必须明确记录为环境前置失败，不得伪造通过。

- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml Dockerfile frontend/Dockerfile frontend/nginx.conf scripts docs tests
git commit -m "chore: make deployment and release verification reproducible"
```

---

## 推荐执行顺序和停止条件

不要并行修改同一批 API 和前端页面。按以下顺序执行：

1. Task 1：质量门禁。若默认测试仍会无界等待，停止后续业务改造。
2. Task 2：产品范围和文档。若无法说清正式数据和演示数据边界，停止新增功能。
3. Task 3：provenance 契约。若任一分析接口仍能静默返回 mock，停止前端美化工作。
4. Task 4：主分析链路。只有快照接口通过 contract test 后，才迁移页面。
5. Task 5：测试隔离。默认门禁必须稳定且重复运行结果一致。
6. Task 6：前端体验。以主任务完成为验收，不以页面数量为指标。
7. Task 7：报告和合规。报告没有来源、局限性和审计记录时，不允许作为正式演示出口。
8. Task 8：部署发布。最终 smoke test 通过后，才考虑继续扩展多平台或实时能力。

## 最终 Definition of Done

- 新用户可以从一个入口选择微博话题和时间范围，看到摘要、证据、趋势、情感、传播和报告。
- 每个数值都能回答：来自哪里、覆盖什么时间、用了多少数据、用了什么规则/模型。
- 正式模式绝不静默伪造演示数据；演示和实验能力有文字标识和限制说明。
- `pwsh -NoProfile -File scripts/verify_project.ps1` 能稳定完成后端和前端质量门禁。
- 默认测试不依赖外部 Redis、微博 Cookie、远程 NLP 或真实数据库，并且重复运行结果一致。
- README、API、架构、部署文档与真实文件和命令一致。
- 报告可追溯到分析快照和审计事件，日志不泄露 Cookie、Token 或敏感信息。
- Docker Compose、宿主机启动和 CI 的边界明确，任一可选服务关闭不会让主分析页面直接失效。
- 完成以上条件后，才重新评估多平台真实采集、实时 WebSocket、ML 模型线上化和协作功能。
