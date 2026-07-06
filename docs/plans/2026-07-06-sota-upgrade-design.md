# SOTA 升级设计文档

> 创建日期：2026-07-06
> 范围：依赖升级 + 情感分析算法 BERT 化 + 前端组件现代化 + 配套改造（容器/CI/安全/测试）
> 配套执行清单：[2026-07-06-sota-upgrade.md](2026-07-06-sota-upgrade.md)

## Goal

把微博舆情分析系统整体升级到 2026 年的 SOTA（State of the Art）状态：

- 后端依赖与运行时全部对齐到当前稳定主线（Flask 3 / SQLAlchemy 2 / Celery 5.3 / Python 3.11）
- 情感分析从 jieba+snownlp+sklearn 传统管线升级为「BERT 主推理 + 传统模型兜底」三级架构
- 前端工具链与组件组织现代化（ESLint 9 / Node 20 / Element Plus 按需 / 死代码清理 / composable 统一）
- 容器、CI、安全、测试一并修补，使升级后的代码能真正通过自动化门禁

## 现状审计摘要

详细调研见三份内部报告（已并入本设计的事实基础）。关键问题集中如下。

### 后端依赖

[requirements/requirements.txt](../../requirements/requirements.txt) 中：

| 问题 | 位置 | 影响 |
| --- | --- | --- |
| `wheel==0.46.3` 是无效版本（wheel 当前最高 0.45.x） | [L62](../../requirements/requirements.txt#L62) | 全新 `pip install` 直接失败 |
| `setuptools==65.0.0` 严重过时且有 CVE-2024-6345 | [L63](../../requirements/requirements.txt#L63) | 安全风险 |
| `Flask 2.3.3` / `werkzeug 2.3.7` 已停止维护 | [L13-L14](../../requirements/requirements.txt#L13) | 与子服务 Flask 3.1.0 不一致 |
| `SQLAlchemy 1.4.49` 已 EOL | [L15](../../requirements/requirements.txt#L15) | 无法用现代 ORM 写法 |
| `urllib3 1.26.18` 多个 CVE | [L44](../../requirements/requirements.txt#L44) | 安全风险 |
| `gunicorn 20.1.0` CVE-2024-1135（HTTP 请求走私） | [L34](../../requirements/requirements.txt#L34) | 安全风险 |
| `pydantic>=2.0` 未钉上限 | [L24](../../requirements/requirements.txt#L24) | 与 nlp_service 2.5.0 不一致，运行时漂移 |
| `pyproject.toml requires-python = ">=3.8"` | [pyproject.toml#L10](../../pyproject.toml#L10) | 3.8 已 EOL，且数据科学包新版要求 ≥3.10 |

`requirements/requirements.audit.txt` 已是项目自身维护的「目标基线」，本设计直接采用其版本目标。

### 微服务架构

- 主后端 / spider_service / nlp_service 三套 Flask 版本不一致（2.3.3 / 3.1.0 / 3.1.0）
- [spider_service/Dockerfile#L6](../../spider_service/Dockerfile#L6) 与 [nlp_service/Dockerfile#L9](../../nlp_service/Dockerfile#L9) 都 `COPY requirements/requirements.txt .`，但 build context 是子目录、无 `requirements/` 子目录，**两个镜像无法构建**
- 三个 Dockerfile 都未安装 curl，但 docker-compose.yml 的 healthcheck 用 `curl -f`，所有 healthcheck 永远失败
- [src/services/sentiment_strategy_selector.py](../../src/services/sentiment_strategy_selector.py) 与 [nlp_service/app/sentiment_strategy_selector.py](../../nlp_service/app/sentiment_strategy_selector.py) 是近乎逐字拷贝
- 三个服务共用同一 Redis db=0，仅靠 queue 名隔离

### 情感分析

[src/services/sentiment_service.py](../../src/services/sentiment_service.py) 已有 `SentimentStrategy` 抽象层（[L181-L186](../../src/services/sentiment_service.py#L181)），三种策略：

- `SnowNLPStrategy`（[L189-L454](../../src/services/sentiment_service.py#L189)）— 规则 + SnowNLP
- `LLMStrategy`（[L526-L698](../../src/services/sentiment_service.py#L526)）— DeepSeek/OpenAI 兼容，含熔断
- `CustomModelStrategy`（[L701-L944](../../src/services/sentiment_service.py#L701)）— joblib 加载 `best_sentiment_model.pkl`，**强耦合 sklearn `predict/predict_proba`**

`src/model/trainModel.py` 训练管线 = `SocialMediaPreprocessor (jieba) → TfidfVectorizer → {WeightedMultinomialNB, LogisticRegression, LinearSVC, RandomForest}`（[L83-L91](../../src/model/trainModel.py#L83)），是 sklearn 风格，BERT 不能直接塞入。

`nlp_service` 的 [tasks.py#L342-L434](../../nlp_service/app/tasks.py#L342) 重新实现了一份 `analyze_text_sync`，**只支持 SnowNLP+词典**，无法加载 .pkl；`retrain_model_task` 是 sleep 桩函数（[L576-L594](../../nlp_service/app/tasks.py#L576)）。

**仓库内无任何已提交的模型产物**（无 .pkl / .pt / .bin / .safetensors）。`src/model/target.csv` 是无表头训练数据，标签为中文 `正面/负面`，但 [yuqing.py#L150](../../src/model/yuqing.py#L150) 又用 `{0:负面,1:中性,2:正面}` 整数映射，标签体系混乱。

### 前端

核心依赖大体已 SOTA（Vue 3.5 / Vite 7 / Pinia 3 / Element Plus 2.13 / ECharts 6），但工具链与代码组织层落后：

- ESLint 8.57 已 EOL，[.eslintrc.cjs](../../frontend/.eslintrc.cjs) 是传统 eslintrc 风格
- [Dockerfile](../../frontend/Dockerfile) 用 `node:18-alpine`（Node 18 已 EOL），且用 `npm install` 而非 `npm ci`
- [src/plugins/elementPlus.js](../../frontend/src/plugins/elementPlus.js) 手动注册 ~55 个组件 + 全量 CSS，未用 `unplugin-vue-components`
- 9 个 Common 组件 + 5 个 composables **零引用**（[ActionBar/Breadcrumb/DataTable/EmptyState/PageLoading/ResponsiveTable/Skeleton/TagView/HelloWorld](../../frontend/src/components) + [useChart/useForm/useTable/useTheme/composables/index.js](../../frontend/src/composables)）
- [src/plugins/errorHandler.js](../../frontend/src/plugins/errorHandler.js) 写好但 main.js 未挂载（死代码）
- [src/utils/websocket.js#L38](../../frontend/src/utils/websocket.js#L38) 依赖 `window.io`，但 index.html 未引入 socket.io 客户端，**实时推送链路实际未跑通**
- 12 个 view 各写一遍表格+分页+搜索，10 个 view 各写一遍 ECharts options，14 处 loading try/catch 模板
- [src/locales/index.js](../../frontend/src/locales/index.js) 自研 i18n 完整但 0 view 引用
- 暗黑模式样式三处分散（theme.scss / index.scss / 组件 scoped），`appStore.setTheme` 直接覆盖 className 会清掉其它 class
- [public/sw.js](../../frontend/public/sw.js) 手写、未用 Workbox，预缓存只缓存 3 个 URL
- [src/views/analysis/propagation.vue#L446](../../frontend/src/views/analysis/propagation.vue#L446) `echarts.init` 后无 onUnmounted dispose，内存泄漏

### 安全

- [database/init_database.sql#L143](../../database/init_database.sql#L143) 等多处 SQL 含明文密码 `'123456'`、`'123123'`
- [src/utils/encryption.py#L53](../../src/utils/encryption.py#L53) 加密失败时返回明文，[L68](../../src/utils/encryption.py#L68) 解密失败时返回原文（静默失败）
- [src/utils/rate_limiter.py#L23](../../src/utils/rate_limiter.py#L23) 限流基于进程内存，Gunicorn 多 worker 下失效
- [nlp_service/app/main.py#L36](../../nlp_service/app/main.py#L36) 与 [spider_service/app/main.py#L32](../../spider_service/app/main.py#L32) 默认 token 为空时直接放行
- [.github/workflows/security-scan.yml](../../.github/workflows/security-scan.yml) 所有扫描命令加 `|| true`，安全门禁形同虚设
- [src/utils/authz.py](../../src/utils/authz.py) 仅 `admin_required` 装饰器，无 RBAC

### CI/测试

- [.github/workflows/ci.yml#L15](../../.github/workflows/ci.yml#L15) 用 mysql:5.7，但 docker-compose.yml 用 mysql:8.0
- CI 未安装 requirements-dev.txt，ruff/mypy/bandit 在 CI 不运行
- [pyproject.toml#L66](../../pyproject.toml#L66) 显式忽略所有 DeprecationWarning，升级后废弃 API 不可见
- 大量 sentiment 测试是「脚本式」（print + `if __name__`），不会被 pytest 自动收集
- 覆盖率门槛 `fail_under = 30` 偏低

## 范围

### In Scope

1. **依赖升级**：Python / 前端依赖、各服务 requirements、Docker 基础镜像、pre-commit 工具链
2. **算法升级**：引入 BERT 类预训练模型作为情感分析主推理路径，重构 `CustomModelStrategy`，统一标签 schema，引入 `ModelBackend` 抽象
3. **前端现代化**：ESLint 9 flat config、Node 20、Element Plus 按需、死代码清理、composable 统一、修活 WebSocket、修复 propagation 内存泄漏、PWA 用 vite-plugin-pwa
4. **配套改造**：容器构建修复、CI 升级 MySQL 8 + 装 dev 依赖、安全扫描去掉 `|| true`、明文密码清理、限流改 Redis、sentiment 脚本式测试转 pytest

### Out of Scope（明确不做）

- 不重写整个前端组件库（仍用 Element Plus）
- 不引入 Vue 3 之外的框架（不换 React/Solid）
- 不引入 GPU 推理服务（BERT 走 CPU + ONNX Runtime 量化）
- 不替换 MySQL 为其他数据库
- 不引入 Kubernetes（仍用 docker-compose）
- 不引入 RBAC（保留单一 admin 模型，仅修补明文密码等严重问题）
- 不重写爬虫核心逻辑（spider_service 当前是 mock 也保持）
- 不补全 ORM 与 DB schema 的全部差异（仅修升级阻断项）
- 不迁移到 vue-i18n（保留自研 i18n 但接入到 view）

## 总体架构（升级后）

```
┌─────────────────────────────────────────────────────────────────┐
│ Frontend (Vue 3.5 + Vite 7 + Element Plus 按需 + ESLint 9)      │
│  - composables 统一 (useFetch/useTable/useChart/usePolling)     │
│  - 死代码清理完毕，WebSocket 修活，PWA 用 vite-plugin-pwa        │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP + Socket.IO
┌────────────────────────────▼────────────────────────────────────┐
│ Main Backend (Flask 3.1 + SQLAlchemy 2.0 + Celery 5.3)          │
│  - SentimentService → ModelBackend 抽象                          │
│      ├── BertBackend (transformers + ONNX Runtime CPU)          │
│      ├── SklearnBackend (joblib .pkl，原 CustomModel)            │
│      └── SnowNLPBackend (兜底)                                   │
│  - 统一标签 schema: positive/neutral/negative                    │
│  - 缓存 key bump: sentiment:v4:bert:*                           │
│  - 限流改 Redis 滑动窗口                                          │
└──┬──────────────────────┬───────────────────────┬───────────────┘
   │ HTTP (Bearer Token)  │ 共享 MySQL            │ 共享 Redis
┌──▼──────────────┐  ┌───▼─────────────┐  ┌──────▼──────────────┐
│ spider_service  │  │ nlp_service     │  │ Celery workers      │
│ Flask 3.1       │  │ Flask 3.1       │  │  (主后端内置)        │
│ (仍 mock)       │  │ 透传到主后端     │  │  - celery_sentiment │
│ Dockerfile 修复 │  │ 不再重复实现     │  │  - celery_spider    │
└─────────────────┘  └─────────────────┘  └─────────────────────┘
```

关键设计决策：

1. **nlp_service 改为透传**：不再重复实现情感分析逻辑，所有 `/api/nlp/*` 端点直接 HTTP 转发到主后端 `SentimentService`。这样 BERT 升级只需改一处。
2. **ModelBackend 抽象**：新增 `src/services/sentiment_backend.py`，定义 `predict(texts) -> list[(label, score)]` 接口。`CustomModelStrategy` 改为依赖 `ModelBackend`，运行时由 `Config.SENTIMENT_BACKEND` 选择实现。
3. **BERT 推理走 CPU + ONNX**：避免 GPU 依赖，推理延迟通过 ONNX Runtime 量化控制在 50-100ms/条；批量推理 + 队列进一步吞吐。
4. **传统模型保留为兜底**：BERT 加载失败或推理超时降级到 SklearnBackend，再降级到 SnowNLPBackend。
5. **前端 composable 优先**：以 `useFetch` / `useTable` / `useChart` / `usePolling` 为单一入口，view 不再手写样板；DataTable 等组件保留但作为 composable 的薄封装。

## 工作流 A：依赖升级

### A1 Python 主后端

目标版本对齐 [requirements/requirements.audit.txt](../../requirements/requirements.audit.txt)：

| 包 | 当前 | 目标 |
| --- | --- | --- |
| Flask | 2.3.3 | ~=3.1.0 |
| werkzeug | 2.3.7 | 不钉（随 Flask） |
| SQLAlchemy | 1.4.49 | ~=2.0.40 |
| celery[redis] | 5.2.7 | ~=5.3.6 |
| redis | 4.5.4 | ~=5.0.1 |
| pydantic | >=2.0 | ~=2.5.3 |
| gunicorn | 20.1.0 | ==22.0.0 |
| gevent | 22.10.2 | ==23.9.1 |
| pandas | >=1.3.5 | ~=2.2.3 |
| numpy | >=1.21.6 | ~=2.2.3 |
| scikit-learn | >=1.0.2 | ~=1.6.1 |
| urllib3 | 1.26.18 | 不钉（随 requests） |
| setuptools | 65.0.0 | 移除钉死 |
| wheel | 0.46.3 | 移除钉死（无效版本） |
| requests | 2.31.0 | ~=2.32.0 |
| jieba | 0.42.1 | 保留（BERT 仍需分词预处理） |
| snownlp | 0.12.3 | 保留（兜底） |

新增（BERT 工作流用）：

```
transformers~=4.40
torch>=2.2,<3.0          # CPU only，用 --extra-index-url https://download.pytorch.org/whl/cpu
onnxruntime>=1.17
sentencepiece>=0.2
huggingface_hub>=0.20
```

代码改造点：

- [src/database.py](../../src/database.py) `Base.query = db_session.query_property()` 改为 `Session.bind` 显式注入或迁到 2.0 风格 `select(Model).where(...)`
- 全仓 grep `Query.get(` → `session.get(Model, id)`
- 全仓 grep `from flask import Markup` → `markupsafe.Markup`
- 全仓 grep `before_first_request` → `before_serving` 或 app 初始化时执行
- [src/tasks/celery_config.py](../../src/tasks/celery_config.py) 新增 `broker_connection_retry_on_startup=True`
- [src/utils/sentiment.py](../../src/utils/sentiment.py) `get_sentiment_label` 阈值统一为 0.6/0.4，与 `SnowNLPStrategy._determine_label` 一致

### A2 Python 子服务

[nlp_service/requirements.txt](../../nlp_service/requirements.txt) 与 [spider_service/requirements.txt](../../spider_service/requirements.txt) 与主后端统一版本（Flask 3.1、celery 5.3、redis 5.0、requests 2.32、pydantic 2.5.3）。nlp_service 因改为透传，**不再需要 snownlp / circuitbreaker**，但需要 `requests` + `flask` 即可。

### A3 Python 工具链与运行时

- [pyproject.toml#L10](../../pyproject.toml#L10) `requires-python = ">=3.11"`
- [pyproject.toml](../../pyproject.toml) `[tool.black] target-version = ['py311']`、`[tool.mypy] python_version = "3.11"`、`[tool.ruff] target-version = "py311"`
- [pyproject.toml#L66](../../pyproject.toml#L66) 移除 `ignore::DeprecationWarning`，改为只忽略具体已知 noise
- [pyproject.toml#L90](../../pyproject.toml#L90) `fail_under` 从 30 提到 50
- [.pre-commit-config.yaml](../../.pre-commit-config.yaml) black 升 24.x 最新、ruff 升 0.6+、isort 升 5.13+、bandit 升 1.7+（与 requirements-dev.txt 对齐，不再钉死）
- [scripts/check_env.py#L20](../../scripts/check_env.py#L20) Python 最低版本检查提到 3.10

### A4 前端工具链

| 依赖 | 当前 | 目标 |
| --- | --- | --- |
| Node | 18-alpine | 20-alpine |
| eslint | ^8.57.0 | ^9.x |
| eslint-plugin-vue | ^9.27.0 | ^10.x |
| prettier | ^3.3.3 | 保留（已是 3.x） |
| sass | dependencies | devDependencies |

新增：

```
unplugin-vue-components
unplugin-auto-import
vite-plugin-pwa
echarts-wordcloud
@fontsource/inter
globals
```

可能移除（确认零引用后）：

- `vue-echarts` — 已装未用，BaseChart 改为基于原生 echarts 后可移除

代码改造点：

- [.eslintrc.cjs](../../frontend/.eslintrc.cjs) 删除，新建 `eslint.config.js`（flat config）
- [package.json#L10](../../frontend/package.json#L10) `lint` 脚本去掉 `--ext`，改为 `eslint "src/**/*.{vue,js,jsx,cjs,mjs}" --fix`
- [package.json](../../frontend/package.json) 新增 `engines.node: ">=20"`
- [vite.config.js#L53](../../frontend/vite.config.js#L53) `build.target` 从 `'es2015'` 改为 `'es2020'`
- [Dockerfile#L2](../../frontend/Dockerfile#L2) `node:20-alpine` + `npm ci` 替换 `npm install`

## 工作流 B：情感分析算法升级到 BERT

### B1 模型选型

主模型：`IDEA-CCNL/Erlangshen-Roberta-110M-Sentiment`（中文情感 BERT，110M 参数，HuggingFace 开源，CPU 量化后单条推理 50-100ms）。

备选：`uer/roberta-base-finetuned-jd-binary-chinese`（更小，85M）、`uer/roberta-tiny-clue`（蒸馏版，5M，CPU <20ms 但准确率略降）。

策略：默认 Erlangshen-Roberta-110M；提供 `BERT_MODEL_NAME` 配置项允许切换为 tiny 版本以换性能。

### B2 ModelBackend 抽象

新建 [src/services/sentiment_backend.py](../../src/services/sentiment_backend.py)：

```python
class ModelBackend(ABC):
    @abstractmethod
    def predict(self, texts: list[str]) -> list[tuple[str, float]]:
        """返回 [(label, score), ...]，label ∈ {positive, neutral, negative}"""

    @abstractmethod
    def predict_batch(self, texts: list[str], batch_size: int = 32) -> list[tuple[str, float]]:
        """批量推理，默认实现委托 predict"""

    @property
    @abstractmethod
    def backend_name(self) -> str: ...

    @property
    @abstractmethod
    def is_loaded(self) -> bool: ...


class SklearnBackend(ModelBackend):
    """包装现有 best_sentiment_model.pkl"""
    # predict 调用 model.predict / predict_proba，标签映射统一为英文


class BertBackend(ModelBackend):
    """transformers + ONNX Runtime"""
    # 初始化时加载 ONNX 模型，predict 走 ONNX session.run
    # 标签映射: id2label = {0: "negative", 1: "positive"} → 三分类需补充 neutral 阈值


class SnowNLPBackend(ModelBackend):
    """兜底，包装 SnowNLPStrategy 核心逻辑"""
```

### B3 CustomModelStrategy 重构

[src/services/sentiment_service.py#L701-L944](../../src/services/sentiment_service.py#L701) 的 `CustomModelStrategy` 改为：

```python
class CustomModelStrategy(SentimentStrategy):
    def __init__(self):
        self.backend = self._select_backend()

    def _select_backend(self) -> ModelBackend:
        name = Config.SENTIMENT_BACKEND  # bert / sklearn / snownlp / auto
        if name == "auto":
            return AutoBackendSelector().select()  # 优先 bert，失败降级
        return BACKEND_REGISTRY[name]()

    def analyze(self, text):
        try:
            label, score = self.backend.predict([text])[0]
            return SentimentResult(score=score, label=label, source=self.backend.backend_name, ...)
        except Exception:
            # 降级到 SnowNLPBackend
            ...
```

### B4 BERT 训练流水线

新建 [src/model/train_bert.py](../../src/model/train_bert.py)：

- 数据：从 `target.csv` 读取，**统一标签为英文**（preprocess 阶段映射 `正面→positive`、`负面→negative`、`中性→neutral`；整数 `0→negative, 1→neutral, 2→positive`）
- 基模型：`IDEA-CCNL/Erlangshen-Roberta-110M-Sentiment` 或其 tokenizer + 一个新分类头
- 训练：`Trainer(epochs=3, lr=2e-5, batch_size=16, max_length=128)`，CPU 训练可行（约 1-2 小时/epoch，取决于数据量）
- 评估：accuracy / F1 / 混淆矩阵，写入 `src/model/metrics/bert_eval.json`
- 导出 ONNX：`torch.onnx.export` 或 `optimum.onnxruntime.ORModelForSequenceClassification`，输出到 `src/model/bert_sentiment_onnx/`
- 元数据：`model_card.json` 记录基模型、训练数据规模、评估指标、训练时间

补充数据：如果 `target.csv` 样本量 < 5000，从 HuggingFace datasets 拉 `ChnSentiCorp` 作为预训练后微调的补充数据（不替换原数据）。

### B5 ModelVersionManager 重构

[src/model/model_version_manager.py](../../src/model/model_version_manager.py) 当前用 `joblib.dump` 保存单文件。重构为支持两种产物：

- `sklearn` 类型：`versions/<id>/model.pkl`（保留原逻辑）
- `bert` 类型：`versions/<id>/` 目录，含 `model.onnx` + `tokenizer.json` + `config.json` + `model_card.json`

`current_version.json` 新增 `backend_type` 字段，加载时根据类型选择 `SklearnBackend` 或 `BertBackend`。

### B6 配置项扩展

[src/config/settings.py](../../src/config/settings.py) 新增：

```python
SENTIMENT_BACKEND = os.getenv("SENTIMENT_BACKEND", "auto")  # bert / sklearn / snownlp / auto
BERT_MODEL_NAME = os.getenv("BERT_MODEL_NAME", "IDEA-CCNL/Erlangshen-Roberta-110M-Sentiment")
BERT_MODEL_PATH = os.path.join(Config.MODEL_DIR, "bert_sentiment_onnx")  # 本地 ONNX 路径
BERT_MAX_LENGTH = int(os.getenv("BERT_MAX_LENGTH", 128))
BERT_BATCH_SIZE = int(os.getenv("BERT_BATCH_SIZE", 32))
BERT_DEVICE = os.getenv("BERT_DEVICE", "cpu")  # cpu / cuda
BERT_FALLBACK_TO_SKLEARN = os.getenv("BERT_FALLBACK_TO_SKLEARN", "True").lower() == "true"
BERT_INFERENCE_TIMEOUT = float(os.getenv("BERT_INFERENCE_TIMEOUT", 2.0))  # 单条超时
```

`.env.example` 同步补充。

### B7 缓存 key 与降级链路

- [src/services/sentiment_service.py#L457](../../src/services/sentiment_service.py#L457) `get_cache_key` 把 `sentiment:v3:` 改为 `sentiment:v4:{backend}:{mode}:{text}`，避免旧缓存污染
- 降级链路：BERT 推理失败/超时 → SklearnBackend → SnowNLPBackend，每级降级记日志 + metric
- `LLMStrategy` 的 SnowNLP 降级保留不变（LLM 与 BERT 是平行策略，不互相降级）

### B8 nlp_service 改为透传

[nlp_service/app/tasks.py](../../nlp_service/app/tasks.py) 删除 `analyze_text_sync` / `analyze_batch_sync` / `analyze_sequence_sync` 与重复的 `SentimentDictionary`，改为 HTTP 调用主后端：

```python
# nlp_service/app/tasks.py
import requests
from config import NLP_BACKEND_URL  # 主后端地址

def analyze_text_sync(text, mode="auto"):
    resp = requests.post(f"{NLP_BACKEND_URL}/api/sentiment/analyze",
                         json={"text": text, "mode": mode}, timeout=10)
    return resp.json()["data"]
```

[nlp_service/app/sentiment_strategy_selector.py](../../nlp_service/app/sentiment_strategy_selector.py) 删除（不再需要）。`retrain_model_task` 改为转发到主后端 `/api/sentiment/retrain`。

nlp_service 的 requirements.txt 移除 snownlp / circuitbreaker / pydantic-settings，仅保留 flask / celery / redis / requests。

### B9 标签 schema 统一

全链路统一为英文 `positive / neutral / negative`：

- [src/model/target.csv](../../src/model/target.csv) — 不直接改原文件，但在训练脚本 preprocess 阶段映射
- [src/model/yuqing.py#L150](../../src/model/yuqing.py#L150) `{0:负面,1:中性,2:正面}` 改为 `{0:"negative",1:"neutral",2:"positive"}`
- [src/utils/sentiment.py](../../src/utils/sentiment.py) 内部用英文，仅在外部展示时通过 `label_to_chinese(label)` 转中文
- [src/services/sentiment_service.py#L745-L750](../../src/services/sentiment_service.py#L745) `_map_prediction_label` 简化为只接受英文

### B10 测试改造

- [tests/test_sentiment_model.py](../../tests/test_sentiment_model.py) `MODELS` 字典与 `build_pipeline` 假设重写：保留 sklearn 子集测试，新增 `BertBackend` mock 测试（不真正加载模型）
- [tests/test_sentiment_enhancement.py](../../tests/test_sentiment_enhancement.py) 15 条样例转为 pytest 参数化用例，作为升级前后回归基线
- [tests/test_sentiment_performance.py](../../tests/test_sentiment_performance.py) 转 pytest，新增 BERT mode 性能基准（CPU 单条 < 200ms，批量 32 条 < 2s）
- 新增 `tests/test_sentiment_backend.py`：`ModelBackend` 三种实现的单元测试（mock 推理）
- 新增 `tests/test_bert_train.py`：训练流水线 smoke test（仅 10 条数据，1 step，验证产物结构）

## 工作流 C：前端组件现代化

### C1 死代码清理

删除零引用文件：

- [src/components/HelloWorld.vue](../../frontend/src/components/HelloWorld.vue) — 脚手架残留
- [src/components/Common/ActionBar.vue](../../frontend/src/components/Common/ActionBar.vue)
- [src/components/Common/Breadcrumb.vue](../../frontend/src/components/Common/Breadcrumb.vue)
- [src/components/Common/EmptyState.vue](../../frontend/src/components/Common/EmptyState.vue)
- [src/components/Common/PageLoading.vue](../../frontend/src/components/Common/PageLoading.vue)
- [src/components/Common/ResponsiveTable.vue](../../frontend/src/components/Common/ResponsiveTable.vue)
- [src/components/Common/Skeleton.vue](../../frontend/src/components/Common/Skeleton.vue)
- [src/components/Common/TagView.vue](../../frontend/src/components/Common/TagView.vue)
- [src/components/Common/DataTable.vue](../../frontend/src/components/Common/DataTable.vue) — **保留**，C3 改造后接入
- [src/plugins/errorHandler.js](../../frontend/src/plugins/errorHandler.js) — 删除，逻辑已在 [request.js](../../frontend/src/api/request.js) 中

### C2 composable 统一

新建/改造：

- `src/composables/useFetch.js` — 替代 14 处 loading try/catch 模板，封装 `loading / data / error / execute`
- `src/composables/useTable.js` — 重写，对接 `DataTable` 组件，封装 `pagination / searchParams / sortParams / loadList / loading`
- `src/composables/useChart.js` — 已存在但 0 引用，改为 `BaseChart` 的伴生 hook，导出 `createLineChartOption / createBarChartOption / createPieChartOption` 工厂
- `src/composables/usePolling.js` — 新建，统一 4 处 setInterval 轮询（spider/Header/tasks/BigScreen），含 `maxErrors / backoff`
- `src/composables/index.js` — 现有零引用 hooks（useDebounce/useThrottle/useClickOutside 等）保留，加 README 注释说明用途

### C3 视图批量改造

按优先级改造 12 个含表格的 view，统一改用 `useTable` + `DataTable`：

1. [src/views/analysis/comment.vue](../../frontend/src/views/analysis/comment.vue)
2. [src/views/analysis/article.vue](../../frontend/src/views/analysis/article.vue)
3. [src/views/system/tasks.vue](../../frontend/src/views/system/tasks.vue)
4. [src/views/user/Favorites.vue](../../frontend/src/views/user/Favorites.vue)
5. [src/views/alert/center.vue](../../frontend/src/views/alert/center.vue)
6. 其余 7 个

ECharts options 工厂接入：10 个图表 view 改用 `useChart.createXxxChartOption`，删除各 view 内重复的 `tooltip/grid/xAxis/yAxis` 样板。

### C4 BaseChart 与 echarts 注册

- [src/utils/echarts.js](../../frontend/src/utils/echarts.js) 补注册：`WordCloudChart`（+ 装 `echarts-wordcloud`）、`RadarChart`、`ScatterChart`、`HeatmapChart`、`MarkLine/MarkPoint/DataZoom`
- [src/components/Charts/BaseChart.vue](../../frontend/src/components/Charts/BaseChart.vue) 保留原生 echarts 实现，删除 `MutationObserver` 暗黑切换 hack，改为通过 `theme` prop 注入
- [src/views/analysis/propagation.vue#L446](../../frontend/src/views/analysis/propagation.vue#L446) `echarts.init` 改为 `BaseChart` 组件，修复内存泄漏
- [src/views/analysis/spider.vue#L639](../../frontend/src/views/analysis/spider.vue#L639) 同上
- [src/views/analysis/ip.vue](../../frontend/src/views/analysis/ip.vue) 移除直接 `import echarts`，统一用 `BaseChart`

### C5 WebSocket 修活

- [src/utils/websocket.js#L38](../../frontend/src/utils/websocket.js#L38) `window.io` → `import { io } from 'socket.io-client'`
- 联调后端 [src/utils/websocket_server.py](../../src/utils/websocket_server.py) 的 socket.io 服务端版本（4.x 兼容）
- [src/components/Common/AlertNotification.vue](../../frontend/src/components/Common/AlertNotification.vue) 测试实时推送链路

### C6 主题系统统一

- [src/stores/app.js#L18](../../frontend/src/stores/app.js#L18) `document.documentElement.className = themeName` 改为 `classList.add/remove`，与 [useTheme.js](../../frontend/src/composables/useTheme.js) 一致
- [src/styles/index.scss](../../frontend/src/styles/index.scss) `.dark` 覆盖移到 [theme.scss](../../frontend/src/styles/theme.scss)，组件 scoped style 内的 `.dark` 覆盖全部删除
- [src/styles/theme.scss#L43](../../frontend/src/styles/theme.scss#L43) `--el-border-radius-base: 16px` 与 [variables.scss](../../frontend/src/styles/variables.scss) `$border-radius-base: 8px` 统一为 8px
- [src/styles/index.scss#L4](../../frontend/src/styles/index.scss#L4) Google Fonts CDN 改为 `@fontsource/inter` 本地化

### C7 PWA 改造

- 装 `vite-plugin-pwa`
- [vite.config.js](../../frontend/vite.config.js) 接入 `VitePWA` 插件，用 `injectManifest` 策略保留自定义 sw 逻辑
- [public/sw.js](../../frontend/public/sw.js) 与 [public/manifest.json](../../frontend/public/manifest.json) 改由插件生成，补 maskable icon
- [main.js#L21-L32](../../frontend/src/main.js#L21) 手写 SW 注册移除，改由插件自动注册
- 旧 cache 名 `weibo-analytics-v1` 等在激活阶段清理

### C8 i18n 接入

保留自研 [src/locales/index.js](../../frontend/src/locales/index.js)，但：

- [src/App.vue](../../frontend/src/App.vue) `useI18n` 接入，`<el-config-provider :locale="currentLocale === 'zh-CN' ? zhCn : en">`
- 高频文案（nav / common / auth）先接入 5 个 view：home / Login / Register / Header / Sidebar
- 其余 view 留后续 PR 接入（不在本次范围强制全量）

### C9 Element Plus 按需

- 装 `unplugin-vue-components` + `unplugin-auto-import`
- [vite.config.js](../../frontend/vite.config.js) 配置 `ElementPlusResolver()`
- [src/plugins/elementPlus.js](../../frontend/src/plugins/elementPlus.js) 删除手动注册数组
- [src/main.js#L3-L4](../../frontend/src/main.js#L3) 保留 `dist/index.css` 全量（按需 CSS 需配合 unplugin 但收益有限，保留全量 CSS 简化迁移）
- 函数式 API（`ElMessage`/`ElNotification`/`ElMessageBox`/`ElLoading`）样式靠全量 CSS 覆盖，无需额外处理

### C10 路由鉴权优化

- [src/router/index.js#L231](../../frontend/src/router/index.js#L231) beforeEach 中的原生 `fetch('/api/auth/me')` 改为走 axios `request`，加 5 分钟内存缓存
- [src/stores/user.js#L61](../../frontend/src/stores/user.js#L61) `initAuth` 与 router beforeEach 的 `fetchCurrentUser` 合并为单一入口，避免重复请求

## 工作流 D：配套改造

### D1 容器构建修复

- [spider_service/Dockerfile#L6](../../spider_service/Dockerfile#L6) `COPY requirements/requirements.txt .` → `COPY requirements.txt .`
- [nlp_service/Dockerfile#L9](../../nlp_service/Dockerfile#L9) 同上
- 三个服务 Dockerfile 基础镜像统一 `python:3.11-slim`
- 三个 Dockerfile 安装 `curl`（或在 docker-compose.yml 的 healthcheck 改用 `python -c "import urllib.request; urllib.request.urlopen(...)"`）
- [docker-compose.yml](../../docker-compose.yml) healthcheck 命令统一改用 python 一行
- [docker-compose.yml](../../docker-compose.yml) 主后端容器加 `BERT_MODEL_PATH` volume 挂载（避免每次重建容器都重新下载模型）

### D2 CI 升级

- [.github/workflows/ci.yml#L15](../../.github/workflows/ci.yml#L15) `mysql:5.7` → `mysql:8.0`
- [.github/workflows/ci.yml#L37](../../.github/workflows/ci.yml#L37) 安装依赖改为 `pip install -r requirements/requirements.txt -r requirements/requirements-dev.txt`
- [.github/workflows/ci.yml](../../.github/workflows/ci.yml) 新增 step：`ruff check src/`、`black --check src/`、`mypy src/`、`bandit -r src/ -ll`（任一失败让 CI 红）
- [.github/workflows/ci.yml](../../.github/workflows/ci.yml) 新增 step：构建 spider_service 与 nlp_service 镜像（验证 Dockerfile 修复）
- [.github/workflows/security-scan.yml#L36](../../.github/workflows/security-scan.yml#L36) 等三处 `|| true` 移除
- [.github/workflows/security-scan.yml](../../.github/workflows/security-scan.yml) 新增 `pip-audit` 失败阈值（仅 high/critical 失败）

### D3 安全修补

- [database/init_database.sql#L143](../../database/init_database.sql#L143) 等三处明文密码改为 bcrypt 哈希（用 `python -c "from bcrypt import hashpw; print(hashpw(b'Admin123!', gensalt()).decode())"` 预先生成）
- [database/user.sql](../../database/user.sql)、[database/new.sql](../../database/new.sql) 同步清理
- [src/utils/encryption.py#L53](../../src/utils/encryption.py#L53) 加密失败改为抛 `EncryptionError`，[L68](../../src/utils/encryption.py#L68) 解密失败抛 `DecryptionError`，调用方决定降级
- [src/utils/rate_limiter.py](../../src/utils/rate_limiter.py) 改用 Redis 滑动窗口（`INCR + EXPIRE` 或 `ZADD + ZREMRANGEBYSCORE`），保留内存兜底
- [nlp_service/app/main.py#L36](../../nlp_service/app/main.py#L36) 与 [spider_service/app/main.py#L32](../../spider_service/app/main.py#L32) token 为空时改为「仅允许 localhost」（生产环境强制要求 token）
- [src/utils/encryption.py#L28](../../src/utils/encryption.py#L28) 密钥派生改为 PBKDF2-HMAC-SHA256（迭代次数 ≥ 100k）

### D4 测试改造

- 7 个 sentiment 脚本式测试转 pytest：
  - [test_contextual_sentiment.py](../../tests/test_contextual_sentiment.py)
  - [test_strategy_selector.py](../../tests/test_strategy_selector.py)
  - [test_sentiment_enhancement.py](../../tests/test_sentiment_enhancement.py)（参数化 15 条样例）
  - [test_sentiment_optimization.py](../../tests/test_sentiment_optimization.py)
  - [test_sentiment_performance.py](../../tests/test_sentiment_performance.py)
  - [test_sentiment_stress.py](../../tests/test_sentiment_stress.py)
  - [test_model_improvements.py](../../tests/test_model_improvements.py)
- 转换原则：保留原 print 输出（作为 `--verbose` 日志），新增 `assert` 断言；性能/压力测试用 `@pytest.mark.slow` 标记，CI 默认跳过
- [pytest.ini](../../pytest.ini) 新增 `markers = slow: marks tests as slow` 与 `addopts = -q -m "not slow"`

### D5 数据库迁移卫生

- 删除 [database/new.sql](../../database/new.sql)、[database/database_indexes.sql](../../database/database_indexes.sql)、[database/optimize_indexes.sql](../../database/optimize_indexes.sql)、[database/user.sql](../../database/user.sql)、[database/article.sql](../../database/article.sql)
- 保留 [database/init_database.sql](../../database/init_database.sql) 作为唯一 schema 真相源
- [database/comments.sql](../../database/comments.sql)（>504KB）保留但不作为初始化脚本，加 README 注明用途
- [docs/DEPLOYMENT.md](../../docs/DEPLOYMENT.md) 同步更新部署步骤

### D6 重复代码消除

- [src/services/sentiment_strategy_selector.py](../../src/services/sentiment_strategy_selector.py) 与 [nlp_service/app/sentiment_strategy_selector.py](../../nlp_service/app/sentiment_strategy_selector.py) — B8 已处理（nlp_service 改透传后删除该文件）
- [src/model/model_pipeline.py#L59-L61](../../src/model/model_pipeline.py#L59) 引用不存在的 `improved_*` 模块，删除 import 与相关调用
- [src/model/model_examples.py](../../src/model/model_examples.py) 同样引用 `improved_*`，整文件删除

## 阶段化执行计划

按依赖关系分 6 个阶段，每阶段独立可提交、可回滚。详细 Task 见 [2026-07-06-sota-upgrade.md](2026-07-06-sota-upgrade.md)。

| 阶段 | 内容 | 依赖 | 风险 |
| --- | --- | --- | --- |
| Phase 0 | 预先修复阻断项：wheel 无效版本、Dockerfile 路径错、healthcheck、明文密码、`improved_*` 死代码 | 无 | 低 |
| Phase 1 | 后端依赖升级（A1-A2-A3）+ CI 升级（D2） | Phase 0 | 中（SQLAlchemy 2.0 迁移） |
| Phase 2 | 前端工具链升级（A4）+ 死代码清理（C1） | Phase 0 | 中（ESLint 9 flat config） |
| Phase 3 | BERT 算法升级（B1-B10） | Phase 1 | 高（性能、模型产物） |
| Phase 4 | 前端组件现代化（C2-C10） | Phase 2 | 中（视图批量改造） |
| Phase 5 | 安全/限流/加密/测试改造（D3-D4-D5-D6） | Phase 1, 3 | 低-中 |

每个 Phase 完成后跑全量 pytest + ruff + 前端 build，作为阶段验收门禁。

## 风险与回滚

### 主要风险

1. **SQLAlchemy 2.0 迁移**：可能遗漏 `Query.get` / `Session.bind` 等老 API，导致运行时错误。缓解：全仓 grep + mypy 严格模式 + 完整 pytest 覆盖。
2. **BERT 推理性能**：CPU 单条 50-100ms 可能拖慢 sentiment 接口。缓解：ONNX 量化 + 批量推理 + 缓存命中率监控 + 降级链路。
3. **训练数据不足**：`target.csv` 样本量未知，BERT 微调可能过拟合。缓解：补 ChnSentiCorp 数据 + 评估指标对比 + 保留 sklearn 兜底。
4. **ESLint 9 flat config**：首次迁移会冒出一批新告警。缓解：分两步——先升 eslint-plugin-vue@10 + 保留 eslintrc 兼容，再迁 flat config。
5. **视图批量改造**：12 个 view 改 useTable 可能引入回归。缓解：每改一个 view 跑一次该 view 的 Playwright/E2E（如已有）或人工冒烟。
6. **依赖升级触发 transitive 冲突**：例如 Flask 3.1 与某个旧 Flask 扩展不兼容。缓解：先在分支跑 `pip install --dry-run` 验证解析。

### 回滚策略

- 每个 Phase 独立分支，merge 后如出问题可单独 revert
- BERT 模型产物不入库（>100MB），通过 `BERT_MODEL_PATH` 环境变量切换；回滚只需改 `SENTIMENT_BACKEND=sklearn` 重启服务
- 数据库迁移均向后兼容（不删字段，只加），回滚不需 downgrade
- 前端死代码清理单独 commit，可单独 revert

## 验收标准

### 后端

- [ ] `pip install -r requirements/requirements.txt` 全新安装成功（无 wheel 错误）
- [ ] `pytest tests/ -q` 全绿，覆盖率 ≥ 50%
- [ ] `ruff check src/` 无 error
- [ ] `mypy src/` 无 error
- [ ] `bandit -r src/ -ll` 无 high/critical
- [ ] `pip-audit` 无 high/critical
- [ ] `docker compose up -d --build` 全部服务健康（healthcheck 全绿）
- [ ] `python -c "from src.services.sentiment_service import SentimentService; print(SentimentService.analyze('测试', mode='auto'))"` 返回 BERT 推理结果
- [ ] `tests/test_sentiment_enhancement.py` 15 条样例准确率 ≥ 0.85（BERT 模式）

### 前端

- [ ] `npm ci` 成功
- [ ] `npm run lint` 无 error
- [ ] `npm run build` 成功，bundle 体积较升级前减少 ≥ 10%（按需注册收益）
- [ ] `npm run dev` 启动后所有 24 个 view 可访问
- [ ] WebSocket 实时推送链路打通（AlertNotification 收到推送）
- [ ] propagation.vue 不再内存泄漏（Chrome DevTools Memory 验证）
- [ ] 暗黑模式切换不影响 `high-contrast` 等其它 class

### CI

- [ ] CI 全绿（含 ruff/mypy/bandit 步骤）
- [ ] security-scan 失败时 CI 红（无 `|| true`）
- [ ] spider/nlp 镜像在 CI 中构建成功

### 算法

- [ ] BERT 模型训练完成，产物在 `src/model/bert_sentiment_onnx/`
- [ ] `model_card.json` 记录评估指标
- [ ] `SentimentService.analyze(mode='auto')` 默认走 BERT，单条 CPU 推理 < 200ms
- [ ] BERT 推理失败时降级到 sklearn，再降级到 SnowNLP，每级有日志
- [ ] 缓存 key 含 backend 标识，无旧缓存污染

## 不在本次范围内的事

- 全量 ORM 与 DB schema 对齐（仅修升级阻断项）
- 引入 RBAC / 角色层级
- 爬虫核心逻辑重写（spider_service 仍 mock）
- 迁移到 vue-i18n（保留自研）
- SCSS variables → CSS variables 全量迁移（仅修 `setTheme` 与圆角双源）
- 引入 GPU 推理 / Kubernetes / 服务网格
- 全量 i18n 文案接入（仅 5 个高频 view）
- Playwright/E2E 测试新增（如已有则跑通，无则不新增）
