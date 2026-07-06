# SOTA 升级执行清单

> **For Claude:** 按 Phase → Task 顺序执行。每个 Task 完成后跑 Verification 命令，绿了再进下一个 Task。详细设计见 [2026-07-06-sota-upgrade-design.md](2026-07-06-sota-upgrade-design.md)。

**Goal:** 把微博舆情分析系统整体升级到 2026 年 SOTA 状态（依赖 + 算法 BERT 化 + 前端现代化 + 配套改造）。

**Tech Stack:** Flask 3.1 / SQLAlchemy 2.0 / Celery 5.3 / Python 3.11 / Vue 3.5 / Vite 7 / ESLint 9 / transformers + ONNX Runtime / Redis / MySQL 8。

**总阶段：** Phase 0（预先修复） → Phase 1（后端依赖） → Phase 2（前端工具链） → Phase 3（BERT 算法） → Phase 4（前端组件） → Phase 5（安全/测试）。

---

## Phase 0：预先修复阻断项

### Task 0.1：修复 wheel 无效版本

**Files:**
- Modify: `requirements/requirements.txt`

**Steps:**
1. 删除 `wheel==0.46.3`（行号 L62）与 `setuptools==65.0.0`（L63），让 pip 自行解析
2. 在文件末尾保留注释说明「构建工具不钉死」

**Verification:**
```bash
pip install --dry-run -r requirements/requirements.txt
# 期望：解析成功，无 ERROR
```

### Task 0.2：修复 spider/nlp Dockerfile 路径

**Files:**
- Modify: `spider_service/Dockerfile`
- Modify: `nlp_service/Dockerfile`

**Steps:**
1. `spider_service/Dockerfile` L6 `COPY requirements/requirements.txt .` → `COPY requirements.txt .`
2. `nlp_service/Dockerfile` L9 同上
3. 两个 Dockerfile 基础镜像统一 `python:3.11-slim`（spider 当前是 3.9-slim，nlp 当前是 3.11-alpine）

**Verification:**
```bash
docker build -t test-spider spider_service/
docker build -t test-nlp nlp_service/
# 期望：两个镜像构建成功
```

### Task 0.3：修复 healthcheck

**Files:**
- Modify: `docker-compose.yml`

**Steps:**
1. 把 `web` / `spider-api` / `nlp-api` / `frontend` 四个服务的 healthcheck 命令从 `curl -f http://...` 改为 python 一行：
   ```yaml
   healthcheck:
     test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"]
     interval: 30s
     timeout: 5s
     retries: 3
   ```
2. 端口按服务调整：web=5000, spider-api=8090, nlp-api=8091, frontend=80
3. frontend 改用 `wget -q --spider http://localhost/`（nginx 镜像自带 wget）

**Verification:**
```bash
docker compose up -d
docker compose ps  # 期望所有服务 STATUS 为 healthy
```

### Task 0.4：清理 improved_* 死代码

**Files:**
- Modify: `src/model/model_pipeline.py`（删除 L59-L61 的 `from .improved_*` import 与相关调用）
- Delete: `src/model/model_examples.py`（整文件依赖 improved_*）

**Steps:**
1. 删除 `model_examples.py`
2. `model_pipeline.py` 删除 `improved_ciPingTotal / improved_index / improved_yuqing` 的 import 与调用，改为直接调原模块

**Verification:**
```bash
python -c "from src.model.model_pipeline import ModelPipeline; print('ok')"
python -c "import src.model.model_examples"  # 期望 ModuleNotFoundError
```

### Task 0.5：明文密码 SQL 清理

**Files:**
- Modify: `database/init_database.sql`
- Modify: `database/new.sql`
- Modify: `database/user.sql`

**Steps:**
1. 用 Python 预生成 bcrypt 哈希：
   ```bash
   python -c "from bcrypt import hashpw, gensalt; print(hashpw(b'Admin123!', gensalt()).decode())"
   ```
2. 把 `database/init_database.sql` L143-L147 等处的明文密码 `'123456'`、`'123123'` 替换为 bcrypt 哈希字符串
3. 同样处理 `new.sql`、`user.sql`
4. 在 SQL 文件顶部加注释说明「密码已 bcrypt 哈希，原始明文为 Admin123! / 123456 等仅用于演示」

**Verification:**
```bash
grep -E "'[0-9]{3,}'" database/*.sql  # 期望无明文数字密码匹配
python -c "import bcrypt; print(bcrypt.checkpw(b'Admin123!', b'$2b$12$...'))"  # 用实际哈希验证
```

### Task 0.6：security-scan 移除 `|| true`

**Files:**
- Modify: `.github/workflows/security-scan.yml`

**Steps:**
1. 删除 L36 / L41 / L46 末尾的 `|| true`
2. 给 `pip-audit` 加 `--ignore-vuln` 参数忽略已知的低危非阻断 CVE（如有）
3. 新增 step：`bandit -r src/ -ll -x tests/`，失败让 CI 红

**Verification:**
```bash
# 模拟 CI 跑一次
bandit -r src/ -ll -x tests/
pip-audit -r requirements/requirements.txt
# 期望：要么全绿，要么列出具体 CVE 待 Phase 1 修复
```

---

## Phase 1：后端依赖升级

### Task 1.1：升级主后端 requirements.txt

**Files:**
- Modify: `requirements/requirements.txt`

**Steps:**
1. 按 design 文档 A1 表格更新版本：
   - Flask ~=3.1.0、SQLAlchemy ~=2.0.40、celery[redis] ~=5.3.6、redis ~=5.0.1
   - pydantic ~=2.5.3、gunicorn ==22.0.0、gevent ==23.9.1
   - pandas ~=2.2.3、numpy ~=2.2.3、scikit-learn ~=1.6.1
   - requests ~=2.32.0
   - 删除 werkzeug / urllib3 / setuptools / wheel 的钉死
2. 新增 BERT 依赖（暂用 CPU 版 torch）：
   ```
   transformers~=4.40
   torch>=2.2,<3.0
   onnxruntime>=1.17
   sentencepiece>=0.2
   huggingface_hub>=0.20
   ```
3. 在 requirements.txt 顶部加注释说明 torch CPU 安装方式：
   ```
   # torch 安装 CPU 版本：
   # pip install torch --extra-index-url https://download.pytorch.org/whl/cpu
   ```

**Verification:**
```bash
pip install -r requirements/requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
pip check  # 期望无依赖冲突
```

### Task 1.2：SQLAlchemy 2.0 迁移

**Files:**
- Modify: `src/database.py`
- Modify: `src/models/*.py`
- Modify: `src/repositories/*.py`
- Modify: 任何 `from sqlalchemy import ...` 且用 `Query.get` / `Session.bind` 的文件

**Steps:**
1. `src/database.py`：
   - `Base.query = db_session.query_property()` 删除
   - `declarative_base` 改为 `class Base(DeclarativeBase): pass`
2. 全仓 grep `\.query\.get(` → 改为 `session.get(Model, id)`
3. 全仓 grep `from flask import Markup` → `from markupsafe import Markup`
4. 全仓 grep `before_first_request` → 移到 `before_serving` 或 app 初始化
5. 全仓 grep `app.json_encoder` → 改为 `app.json.provider`（Flask 3.x）
6. `src/repositories/base_repository.py` 检查 `session.query(Model).filter_by()` 是否仍可用（2.0 仍支持，但推荐 `select(Model).filter_by()`）

**Verification:**
```bash
grep -rn "\.query\.get(" src/  # 期望无匹配
grep -rn "before_first_request" src/  # 期望无匹配
grep -rn "from flask import.*Markup" src/  # 期望无匹配
pytest tests/ -q  # 期望全绿
```

### Task 1.3：Celery 5.3 + Redis 5.0 适配

**Files:**
- Modify: `src/tasks/celery_config.py`
- Modify: `nlp_service/celery_app.py`
- Modify: `spider_service/celery_app.py`

**Steps:**
1. 三个 Celery 配置文件新增 `broker_connection_retry_on_startup=True`
2. 检查 `result_backend_transport_options` 是否需要补 `master_name`（Redis 5.0 + Sentinel 模式）
3. 检查 `redis.Redis.from_url` 调用是否需要补 `decode_responses=True`（5.0 默认行为）

**Verification:**
```bash
python -c "from src.tasks.celery_config import celery_app; print(celery_app.conf.broker_connection_retry_on_startup)"
# 期望 True
pytest tests/test_celery_spider_events.py -q
```

### Task 1.4：升级子服务 requirements

**Files:**
- Modify: `nlp_service/requirements.txt`
- Modify: `spider_service/requirements.txt`

**Steps:**
1. 两个文件统一为：
   ```
   Flask~=3.1.0
   celery[redis]~=5.3.6
   redis~=5.0.1
   requests~=2.32.0
   pydantic~=2.5.3
   ```
2. nlp_service 因 Phase 3 改透传，移除 snownlp / circuitbreaker / pydantic-settings

**Verification:**
```bash
pip install -r nlp_service/requirements.txt
pip install -r spider_service/requirements.txt
pip check
```

### Task 1.5：pyproject.toml + 工具链

**Files:**
- Modify: `pyproject.toml`
- Modify: `.pre-commit-config.yaml`
- Modify: `scripts/check_env.py`

**Steps:**
1. `pyproject.toml`：
   - `requires-python = ">=3.11"`
   - `[tool.black] target-version = ['py311']`
   - `[tool.mypy] python_version = "3.11"`
   - `[tool.ruff] target-version = "py311"`
   - `[tool.coverage.report] fail_under = 50`
   - `filterwarnings` 移除 `ignore::DeprecationWarning`，改为只忽略具体已知 noise（如 `ignore::DeprecationWarning:celery.*`）
2. `.pre-commit-config.yaml`：black / ruff / isort / bandit 都改为 `latest` 或与 requirements-dev.txt 对齐
3. `scripts/check_env.py` L20 Python 最低版本检查从 3.8 提到 3.10

**Verification:**
```bash
python -c "import sys; assert sys.version_info >= (3, 10), 'need 3.10+'"
pre-commit run --all-files
# 期望：可能有格式化 diff，但无 error
```

### Task 1.6：CI 升级

**Files:**
- Modify: `.github/workflows/ci.yml`

**Steps:**
1. L15 `mysql:5.7` → `mysql:8.0`
2. L37 安装依赖改为：
   ```yaml
   - run: pip install -r requirements/requirements.txt -r requirements/requirements-dev.txt
   ```
3. 新增 step（在 pytest 之前）：
   ```yaml
   - run: ruff check src/
   - run: black --check src/ tests/
   - run: mypy src/
   - run: bandit -r src/ -ll -x tests/
   ```
4. 新增 step（构建 spider/nlp 镜像）：
   ```yaml
   - run: docker build -t test-spider spider_service/
   - run: docker build -t test-nlp nlp_service/
   ```

**Verification:**
```bash
# 本地模拟
ruff check src/
black --check src/ tests/
mypy src/
bandit -r src/ -ll -x tests/
docker build -t test-spider spider_service/
docker build -t test-nlp nlp_service/
```

### Task 1.7：Phase 1 验收

**Steps:**
1. 跑完整测试套件
2. 启动后端服务，smoke test 几个核心接口

**Verification:**
```bash
pytest tests/ -q --cov=src --cov-report=term-missing
# 期望：全绿，覆盖率 >= 50%
python run.py &
sleep 5
curl -s http://127.0.0.1:5000/health
curl -s http://127.0.0.1:5000/getAllData/getHomeData
kill %1
```

---

## Phase 2：前端工具链升级

### Task 2.1：升级 Node + ESLint 9

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/Dockerfile`
- Delete: `frontend/.eslintrc.cjs`
- Create: `frontend/eslint.config.js`

**Steps:**
1. `package.json`：
   - `eslint`: `^9.x`
   - `eslint-plugin-vue`: `^10.x`
   - 新增 `globals`: `^15.x`
   - 新增 `engines.node`: `">=20"`
2. `Dockerfile` L2 `node:18-alpine` → `node:20-alpine`，`npm install` → `npm ci`
3. 新建 `eslint.config.js`（flat config）：
   ```js
   import js from '@eslint/js'
   import pluginVue from 'eslint-plugin-vue'
   import globals from 'globals'

   export default [
     js.configs.recommended,
     ...pluginVue.configs['flat/recommended'],
     {
       languageOptions: {
         globals: { ...globals.browser, ...globals.node },
         ecmaVersion: 2022,
         sourceType: 'module',
       },
       rules: {
         'vue/multi-word-component-names': 'off',
       },
     },
     { ignores: ['dist/**', 'node_modules/**'] },
   ]
   ```
4. `package.json` lint 脚本：`eslint "src/**/*.{vue,js,jsx,cjs,mjs}" --fix --ignore-pattern dist`
5. 删除 `.eslintrc.cjs`

**Verification:**
```bash
cd frontend
npm install
npm run lint
# 期望：可能有新告警，但无 error
```

### Task 2.2：Vite + 构建配置

**Files:**
- Modify: `frontend/vite.config.js`
- Modify: `frontend/package.json`

**Steps:**
1. `vite.config.js` L53 `build.target: 'es2015'` → `'es2020'`
2. `package.json`：
   - `sass` 从 dependencies 移到 devDependencies
   - 新增 `unplugin-vue-components`、`unplugin-auto-import`、`vite-plugin-pwa`、`echarts-wordcloud`、`@fontsource/inter`
3. 评估 `vue-echarts` 是否仍需（C4 决定 BaseChart 不基于 vue-echarts 后可移除）

**Verification:**
```bash
cd frontend
npm install
npm run build
# 期望：构建成功，bundle 体积记录基线
```

### Task 2.3：死代码清理

**Files:**
- Delete: `frontend/src/components/HelloWorld.vue`
- Delete: `frontend/src/components/Common/ActionBar.vue`
- Delete: `frontend/src/components/Common/Breadcrumb.vue`
- Delete: `frontend/src/components/Common/EmptyState.vue`
- Delete: `frontend/src/components/Common/PageLoading.vue`
- Delete: `frontend/src/components/Common/ResponsiveTable.vue`
- Delete: `frontend/src/components/Common/Skeleton.vue`
- Delete: `frontend/src/components/Common/TagView.vue`
- Delete: `frontend/src/plugins/errorHandler.js`

**Steps:**
1. 删除上述 9 个文件
2. 全仓 grep 确认无 import：
   ```bash
   grep -rn "ActionBar\|Breadcrumb\|EmptyState\|PageLoading\|ResponsiveTable\|Skeleton\|TagView\|HelloWorld\|errorHandler" frontend/src/
   ```
3. 如有遗漏 import，一并清理

**Verification:**
```bash
cd frontend
npm run build  # 期望无 import error
npm run lint
```

### Task 2.4：Phase 2 验收

**Verification:**
```bash
cd frontend
npm ci
npm run lint
npm run build
npm run dev &  # 启动后人工冒烟 5 个核心 view
sleep 5
curl -s http://localhost:3000 | head
kill %1
```

---

## Phase 3：BERT 算法升级

### Task 3.1：ModelBackend 抽象层

**Files:**
- Create: `src/services/sentiment_backend.py`
- Create: `tests/test_sentiment_backend.py`

**Steps:**
1. 新建 `sentiment_backend.py`，定义 `ModelBackend` ABC + `SklearnBackend` + `BertBackend` + `SnowNLPBackend` + `AutoBackendSelector` + `BACKEND_REGISTRY`
2. `SklearnBackend` 包装现有 `best_sentiment_model.pkl`，predict 调用 `model.predict / predict_proba`，标签映射统一为英文
3. `BertBackend` 占位实现（Phase 3.4 真正实现），先用 mock 返回 `(positive, 0.99)`
4. `SnowNLPBackend` 包装 `SnowNLPStrategy` 核心逻辑
5. 单元测试：mock 三种 backend 的 `predict`，验证 `AutoBackendSelector` 降级链路

**Verification:**
```bash
pytest tests/test_sentiment_backend.py -q
python -c "
from src.services.sentiment_backend import SklearnBackend, SnowNLPBackend
b = SnowNLPBackend()
print(b.predict(['这部电影真好看']))
"
```

### Task 3.2：CustomModelStrategy 重构

**Files:**
- Modify: `src/services/sentiment_service.py`（L701-L944 CustomModelStrategy）
- Modify: `tests/test_sentiment_service.py`

**Steps:**
1. `CustomModelStrategy.__init__` 改为 `self.backend = self._select_backend()`
2. `_select_backend` 根据 `Config.SENTIMENT_BACKEND` 选择 `bert / sklearn / snownlp / auto`
3. `analyze` 调用 `self.backend.predict([text])[0]`，异常时降级到 `SnowNLPBackend`
4. `analyze_batch` 调用 `self.backend.predict_batch(texts)`
5. 删除原 `_load_model / _map_prediction_label / _analyze_batch_with_model` 等 sklearn 强耦合方法
6. 更新 `test_sentiment_service.py` 中 custom mode 测试，mock backend

**Verification:**
```bash
pytest tests/test_sentiment_service.py -q
python -c "
from src.services.sentiment_service import SentimentService
print(SentimentService.analyze('测试文本', mode='custom'))
"
```

### Task 3.3：配置项 + 缓存 key

**Files:**
- Modify: `src/config/settings.py`
- Modify: `.env.example`
- Modify: `src/services/sentiment_service.py`（L457 get_cache_key）

**Steps:**
1. `settings.py` 新增 BERT 配置项（见 design B6）
2. `.env.example` 同步补充
3. `get_cache_key` 把 `sentiment:v3:` 改为 `sentiment:v4:{backend_name}:{mode}:{text}`

**Verification:**
```bash
python -c "
from src.config import Config
print(Config.SENTIMENT_BACKEND, Config.BERT_MODEL_NAME)
"
```

### Task 3.4：BertBackend 真实实现

**Files:**
- Modify: `src/services/sentiment_backend.py`（BertBackend）
- Create: `scripts/download_bert_model.py`

**Steps:**
1. 新建 `scripts/download_bert_model.py`：
   ```python
   from transformers import AutoTokenizer, AutoModelForSequenceClassification
   from optimum.onnxruntime import ORTModelForSequenceClassification
   import os

   model_name = os.getenv("BERT_MODEL_NAME", "IDEA-CCNL/Erlangshen-Roberta-110M-Sentiment")
   out_dir = os.getenv("BERT_MODEL_PATH", "src/model/bert_sentiment_onnx")

   tokenizer = AutoTokenizer.from_pretrained(model_name)
   model = ORTModelForSequenceClassification.from_pretrained(model_name, export=True)
   tokenizer.save_pretrained(out_dir)
   model.save_pretrained(out_dir)
   ```
2. `BertBackend.__init__`：用 `ORTModelForSequenceClassification.from_pretrained(path)` + `AutoTokenizer.from_pretrained(path)` 加载
3. `predict`：tokenize → session.run → softmax → 取 argmax label + max prob score
4. 标签映射：Erlangshen 模型 `id2label = {0: "Negative", 1: "Positive"}`，二分类扩展为三分类：prob > 0.7 → positive，< 0.3 → negative，中间 → neutral
5. `predict_batch`：用 tokenizer 的 padding=True，一次推理多条
6. `is_loaded`：检查 ONNX 文件存在
7. 跑 `python scripts/download_bert_model.py` 下载模型（首次约 400MB）

**Verification:**
```bash
python scripts/download_bert_model.py
python -c "
from src.services.sentiment_backend import BertBackend
b = BertBackend()
print(b.predict(['这部电影真好看', '服务太差了', '今天天气不错']))
# 期望：[('positive', 0.95), ('negative', 0.92), ('neutral', 0.55)]
"
```

### Task 3.5：BERT 训练流水线

**Files:**
- Create: `src/model/train_bert.py`
- Create: `tests/test_bert_train.py`

**Steps:**
1. `train_bert.py`：
   - `load_data(path="src/model/target.csv")` → 统一标签为英文（`正面→positive`、`负面→negative`、`中性→neutral`；整数 `0→negative, 1→neutral, 2→positive`）
   - 如果样本量 < 5000，从 HuggingFace datasets 拉 `ChnSentiCorp` 补充
   - `train(base_model="IDEA-CCNL/Erlangshen-Roberta-110M-Sentiment", output_dir="src/model/bert_finetuned")`：Trainer(epochs=3, lr=2e-5, batch_size=16, max_length=128)
   - `evaluate(model, test_ds)` → 写 `src/model/metrics/bert_eval.json`
   - `export_onnx(model_dir, output_dir="src/model/bert_sentiment_onnx")` 用 optimum
   - `write_model_card(path, metadata)` → 写 `model_card.json`
2. `test_bert_train.py` smoke test：10 条数据，1 step，验证产物结构（不验证准确率）

**Verification:**
```bash
pytest tests/test_bert_train.py -q
# 完整训练（可选，约 1-2 小时/epoch on CPU）：
python -m src.model.train_bert
```

### Task 3.6：ModelVersionManager 重构

**Files:**
- Modify: `src/model/model_version_manager.py`

**Steps:**
1. `save_model_version` 增加 `backend_type` 参数（`sklearn` / `bert`）
2. sklearn 路径保留 `joblib.dump` 单文件
3. bert 路径：复制整个目录到 `versions/<id>/`
4. `current_version.json` 新增 `backend_type` 字段
5. `load_current_version` 根据 `backend_type` 返回不同 backend 实例

**Verification:**
```bash
pytest tests/test_model_improvements.py -q
python -c "
from src.model.model_version_manager import ModelVersionManager
m = ModelVersionManager()
print(m.list_versions())
"
```

### Task 3.7：标签 schema 统一

**Files:**
- Modify: `src/model/yuqing.py`（L150 标签映射）
- Modify: `src/utils/sentiment.py`
- Modify: `src/services/sentiment_service.py`（L745-L750 _map_prediction_label）

**Steps:**
1. `yuqing.py` L150 `{0:负面,1:中性,2:正面}` → `{0:"negative",1:"neutral",2:"positive"}`
2. `src/utils/sentiment.py` 内部用英文 label，新增 `label_to_chinese(label)` 转中文，`get_sentiment_label` 阈值统一 0.6/0.4
3. `_map_prediction_label` 简化为只接受英文
4. 全仓 grep 中文情感标签直接使用处，改为调 `label_to_chinese`

**Verification:**
```bash
grep -rn "['\"]正面['\"]" src/  # 期望：仅展示层，无逻辑判断
pytest tests/test_sentiment_service.py tests/test_sentiment_model.py -q
```

### Task 3.8：nlp_service 改透传

**Files:**
- Modify: `nlp_service/app/tasks.py`
- Delete: `nlp_service/app/sentiment_strategy_selector.py`
- Modify: `nlp_service/app/main.py`
- Modify: `nlp_service/requirements.txt`
- Modify: `nlp_service/Dockerfile`（环境变量）

**Steps:**
1. `tasks.py`：
   - 删除 `analyze_text_sync / analyze_batch_sync / analyze_sequence_sync` 与 `SentimentDictionary` 类
   - 新建 `analyze_text_sync(text, mode)` 改为 HTTP POST 到主后端 `/api/sentiment/analyze`
   - `retrain_model_task` 改为转发到主后端 `/api/sentiment/retrain`
2. 删除 `nlp_service/app/sentiment_strategy_selector.py`
3. `main.py` 移除对 strategy_selector 的 import
4. `requirements.txt` 移除 snownlp / circuitbreaker / pydantic-settings
5. `Dockerfile` 与 `docker-compose.yml` 新增 `NLP_BACKEND_URL=http://web:5000` 环境变量

**Verification:**
```bash
cd nlp_service && pip install -r requirements.txt
python -c "from app.tasks import analyze_text_sync; print(analyze_text_sync('测试'))"
# 期望：HTTP 调用主后端成功
```

### Task 3.9：测试改造

**Files:**
- Modify: `tests/test_sentiment_model.py`
- Modify: `tests/test_sentiment_enhancement.py`（转 pytest 参数化）
- Modify: `tests/test_sentiment_performance.py`（转 pytest，加 slow mark）
- Modify: `tests/test_sentiment_stress.py`（转 pytest，加 slow mark）
- Modify: `pytest.ini`

**Steps:**
1. `test_sentiment_model.py`：保留 sklearn 子集测试，新增 `BertBackend` mock 测试
2. `test_sentiment_enhancement.py`：15 条样例参数化，加 `assert label == expected`
3. `test_sentiment_performance.py` / `test_sentiment_stress.py`：转 pytest，加 `@pytest.mark.slow`
4. `pytest.ini`：
   ```ini
   [pytest]
   pythonpath = src
   testpaths = tests
   addopts = -q -m "not slow"
   markers =
       slow: marks tests as slow (deselect with -m "not slow")
   ```

**Verification:**
```bash
pytest tests/ -q  # 默认跳过 slow
pytest tests/ -q -m slow  # 显式跑 slow
pytest tests/test_sentiment_enhancement.py -q  # 15 条样例准确率 >= 0.85
```

### Task 3.10：Phase 3 验收

**Verification:**
```bash
# BERT 推理性能
python -c "
import time
from src.services.sentiment_service import SentimentService
t0 = time.time()
r = SentimentService.analyze('测试文本', mode='auto')
print(f'latency: {(time.time()-t0)*1000:.0f}ms, source: {r.source}')
assert r.source == 'bert', f'expected bert, got {r.source}'
assert (time.time()-t0) < 2.0, 'BERT latency too high'
"

# 降级链路
SENTIMENT_BACKEND=sklearn python -c "
from src.services.sentiment_service import SentimentService
r = SentimentService.analyze('测试', mode='custom')
assert r.source == 'sklearn'
"

# 15 条样例准确率
pytest tests/test_sentiment_enhancement.py -q
```

---

## Phase 4：前端组件现代化

### Task 4.1：useFetch + usePolling composable

**Files:**
- Create: `frontend/src/composables/useFetch.js`
- Create: `frontend/src/composables/usePolling.js`

**Steps:**
1. `useFetch.js`：
   ```js
   export function useFetch(apiFn, defaultData = null) {
     const loading = ref(false)
     const error = ref(null)
     const data = ref(defaultData)
     async function execute(...args) {
       loading.value = true
       error.value = null
       try {
         const res = await apiFn(...args)
         if (res.code === 200) data.value = res.data
         else error.value = res.msg
       } catch (e) {
         error.value = e.message
       } finally {
         loading.value = false
       }
     }
     return { loading, error, data, execute }
   }
   ```
2. `usePolling.js`：封装 setInterval，含 `maxErrors / backoff / stop`

**Verification:**
```bash
cd frontend && npm run lint && npm run build
```

### Task 4.2：useTable + useChart 重写

**Files:**
- Modify: `frontend/src/composables/useTable.js`
- Modify: `frontend/src/composables/useChart.js`
- Modify: `frontend/src/components/Common/DataTable.vue`（接入 useTable）

**Steps:**
1. `useTable.js` 重写：`pagination / searchParams / sortParams / loadList / loading / data / total`，对接 `DataTable` 组件 props
2. `useChart.js` 改为 `BaseChart` 的伴生 hook，导出 `createLineChartOption / createBarChartOption / createPieChartOption` 工厂
3. `DataTable.vue` 接入 useTable，统一暴露 props/slots

**Verification:**
```bash
cd frontend && npm run lint && npm run build
```

### Task 4.3：WebSocket 修活

**Files:**
- Modify: `frontend/src/utils/websocket.js`

**Steps:**
1. L38 `if (window.io)` → 顶部 `import { io } from 'socket.io-client'`
2. `this.socket = window.io(wsUrl, ...)` → `this.socket = io(wsUrl, ...)`
3. 移除 `console.error('Socket.IO 未加载')` 兜底
4. 联调后端 socket.io 服务端

**Verification:**
```bash
cd frontend && npm run build
# 启动后端 + 前端，登录后看 AlertNotification 是否收到推送
```

### Task 4.4：BaseChart + echarts 注册

**Files:**
- Modify: `frontend/src/utils/echarts.js`
- Modify: `frontend/src/components/Charts/BaseChart.vue`
- Modify: `frontend/src/views/analysis/propagation.vue`（修复内存泄漏）
- Modify: `frontend/src/views/analysis/spider.vue`
- Modify: `frontend/src/views/analysis/ip.vue`

**Steps:**
1. `echarts.js` 补注册：`WordCloudChart`（装 echarts-wordcloud）、`RadarChart`、`ScatterChart`、`HeatmapChart`、`MarkLine/MarkPoint/DataZoom`
2. `BaseChart.vue` 删除 `MutationObserver` 暗黑切换，改为 `theme` prop 注入
3. `propagation.vue` L446 `echarts.init` 改为 `<BaseChart :options="graphOptions" />`
4. `spider.vue` L639 同上
5. `ip.vue` 移除直接 `import echarts`，统一用 `BaseChart`

**Verification:**
```bash
cd frontend && npm run build
# 人工冒烟 propagation / spider / ip / wordCloud 四个 view
# Chrome DevTools Memory 验证 propagation 切换路由后无泄漏
```

### Task 4.5：视图批量改造

**Files:**
- Modify: `frontend/src/views/analysis/comment.vue`
- Modify: `frontend/src/views/analysis/article.vue`
- Modify: `frontend/src/views/system/tasks.vue`
- Modify: `frontend/src/views/user/Favorites.vue`
- Modify: `frontend/src/views/alert/center.vue`
- 其余 7 个含表格 view

**Steps:**
1. 每个 view：
   - 引入 `useTable` + `DataTable`
   - 删除手写 `listLoading / listData / pagination / filters / loadList`
   - 表格部分改为 `<DataTable :table="table" :columns="columns">...</DataTable>`
2. 10 个图表 view 引入 `useChart.createXxxChartOption`，删除手写 tooltip/grid/xAxis/yAxis
3. 14 处 loading try/catch 改为 `useFetch`

**Verification:**
```bash
cd frontend && npm run lint && npm run build
# 人工冒烟所有 24 个 view
```

### Task 4.6：主题系统统一

**Files:**
- Modify: `frontend/src/stores/app.js`
- Modify: `frontend/src/styles/index.scss`
- Modify: `frontend/src/styles/theme.scss`
- Modify: 各组件 `<style scoped>` 中的 `.dark` 覆盖

**Steps:**
1. `app.js` L18 `document.documentElement.className = themeName` → `classList.add/remove`
2. `index.scss` `.dark` 覆盖移到 `theme.scss`
3. `theme.scss` `--el-border-radius-base: 16px` → `8px`，与 variables.scss 统一
4. `index.scss` L4 Google Fonts CDN → `@fontsource/inter` 本地 import
5. 各组件 scoped style 内的 `.dark` 覆盖全部删除

**Verification:**
```bash
cd frontend && npm run build
# 切换暗黑/亮色，验证 high-contrast 等 class 不被清掉
```

### Task 4.7：Element Plus 按需 + PWA

**Files:**
- Modify: `frontend/vite.config.js`
- Delete: `frontend/src/plugins/elementPlus.js`
- Modify: `frontend/src/main.js`
- Delete: `frontend/public/sw.js`
- Delete: `frontend/public/manifest.json`

**Steps:**
1. `vite.config.js` 接入：
   ```js
   import Components from 'unplugin-vue-components/vite'
   import AutoImport from 'unplugin-auto-import/vite'
   import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
   import { VitePWA } from 'vite-plugin-pwa'

   Components({ resolvers: [ElementPlusResolver()] }),
   AutoImport({ resolvers: [ElementPlusResolver()] }),
   VitePWA({ strategies: 'injectManifest', /* ... */ })
   ```
2. 删除 `plugins/elementPlus.js`
3. `main.js` 移除 `installElementPlus(app)` 调用，保留 `dist/index.css` 全量 import
4. 删除 `public/sw.js` 与 `public/manifest.json`，由插件生成
5. `main.js` 移除手写 SW 注册（L21-L32）

**Verification:**
```bash
cd frontend && npm run build
# 期望：bundle 体积较 Phase 2 基线减少 >= 10%
# 验证 PWA：build 后 dist/ 含 sw.js 与 manifest.json
```

### Task 4.8：路由鉴权优化 + i18n 接入

**Files:**
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/stores/user.js`
- Modify: `frontend/src/App.vue`
- Modify: 5 个高频 view（home / Login / Register / Header / Sidebar）

**Steps:**
1. `router/index.js` beforeEach 中的原生 `fetch('/api/auth/me')` 改为走 `request`，加 5 分钟内存缓存
2. `user.js` `initAuth` 与 beforeEach 的 `fetchCurrentUser` 合并为单一入口
3. `App.vue` 接入 `useI18n`，`<el-config-provider :locale="...">` 联动
4. 5 个高频 view 的硬编码中文改为 `t('xxx')`

**Verification:**
```bash
cd frontend && npm run lint && npm run build
# 路由跳转两次，验证只发一次 /api/auth/me
# 切换 zh-CN / en-US，验证 5 个 view 文案变化
```

### Task 4.9：Phase 4 验收

**Verification:**
```bash
cd frontend
npm ci
npm run lint
npm run build
# bundle 体积较 Phase 0 基线减少 >= 10%
# 人工冒烟所有 24 个 view
# Chrome DevTools Memory 验证 propagation 切换路由无泄漏
# WebSocket 实时推送链路打通
# 暗黑/亮色切换不影响 high-contrast
```

---

## Phase 5：安全/测试/卫生

### Task 5.1：加密 + 限流改造

**Files:**
- Modify: `src/utils/encryption.py`
- Modify: `src/utils/rate_limiter.py`

**Steps:**
1. `encryption.py`：
   - L28 密钥派生改为 PBKDF2-HMAC-SHA256（迭代 ≥ 100k）
   - L53 加密失败抛 `EncryptionError`，L68 解密失败抛 `DecryptionError`
   - 调用方（grep `encrypt_string / decrypt_string`）按需 try/except 决定降级
2. `rate_limiter.py`：
   - 改用 Redis 滑动窗口（`ZADD + ZREMRANGEBYSCORE + ZCARD`）
   - 保留内存兜底（Redis 不可用时降级）
   - 单元测试 mock Redis 验证

**Verification:**
```bash
pytest tests/test_security_hardening.py -q
grep -rn "encrypt_string\|decrypt_string" src/  # 检查调用方处理
```

### Task 5.2：服务间鉴权加固

**Files:**
- Modify: `nlp_service/app/main.py`
- Modify: `spider_service/app/main.py`

**Steps:**
1. token 为空时改为「仅允许 localhost」（127.0.0.1 / ::1）+ 拒绝外部 IP
2. 加 `X-Forwarded-For` 头校验（防代理绕过）
3. 单元测试：mock 远程 IP，验证 401

**Verification:**
```bash
pytest tests/test_spider_service_auth.py tests/test_nlp_task_service.py -q
```

### Task 5.3：剩余 sentiment 脚本式测试转 pytest

**Files:**
- Modify: `tests/test_contextual_sentiment.py`
- Modify: `tests/test_strategy_selector.py`
- Modify: `tests/test_sentiment_optimization.py`
- Modify: `tests/test_model_improvements.py`

**Steps:**
1. 每个 `if __name__ == "__main__"` 块中的测试逻辑提取为 `test_xxx()` 函数
2. 加 `assert` 断言（保留原 print 为 `--verbose` 日志）
3. 性能/压力相关加 `@pytest.mark.slow`

**Verification:**
```bash
pytest tests/ -q
# 期望：测试用例数较 Phase 0 增加至少 30%
pytest tests/ -q -m slow  # slow 也跑通
```

### Task 5.4：数据库 SQL 文件去重

**Files:**
- Delete: `database/new.sql`
- Delete: `database/database_indexes.sql`
- Delete: `database/optimize_indexes.sql`
- Delete: `database/user.sql`
- Delete: `database/article.sql`
- Modify: `database/comments.sql`（加 README 注明用途）
- Modify: `docs/DEPLOYMENT.md`

**Steps:**
1. 删除上述 5 个文件
2. `database/comments.sql` 顶部加注释说明用途（如「演示数据，非初始化脚本」）
3. `DEPLOYMENT.md` 更新部署步骤，明确仅 `init_database.sql` 是真相源

**Verification:**
```bash
ls database/  # 期望仅剩 init_database.sql + comments.sql + article.sql（如有保留）+ README
grep -rn "new.sql\|database_indexes.sql\|optimize_indexes.sql\|user.sql" docs/ scripts/  # 期望无引用
```

### Task 5.5：Phase 5 + 全局验收

**Verification:**
```bash
# 后端
pip install -r requirements/requirements.txt -r requirements/requirements-dev.txt --extra-index-url https://download.pytorch.org/whl/cpu
pip check
pytest tests/ -q --cov=src --cov-report=term-missing
ruff check src/
black --check src/ tests/
mypy src/
bandit -r src/ -ll -x tests/
pip-audit -r requirements/requirements.txt

# 前端
cd frontend
npm ci
npm run lint
npm run build

# 容器
cd ..
docker compose up -d --build
sleep 30
docker compose ps  # 期望全部 healthy
curl -s http://localhost:5000/health
curl -s http://localhost:3000 | head

# BERT
curl -s -X POST http://localhost:5000/api/sentiment/analyze -H "Content-Type: application/json" -d '{"text":"测试","mode":"auto"}'

# 收尾
docker compose down
```

---

## 全局完成定义（DoD）

- [ ] Phase 0-5 全部 Task 的 Verification 通过
- [ ] `pytest tests/ -q` 全绿，覆盖率 ≥ 50%
- [ ] `pytest tests/ -q -m slow` 全绿
- [ ] `ruff check src/` 无 error
- [ ] `mypy src/` 无 error
- [ ] `bandit -r src/ -ll -x tests/` 无 high/critical
- [ ] `pip-audit -r requirements/requirements.txt` 无 high/critical
- [ ] `cd frontend && npm run lint && npm run build` 全绿
- [ ] `docker compose up -d --build` 后所有服务 healthy
- [ ] BERT 推理单条 < 200ms，15 条样例准确率 ≥ 0.85
- [ ] bundle 体积较 Phase 0 基线减少 ≥ 10%
- [ ] WebSocket 实时推送链路打通
- [ ] 无明文密码 SQL，无 `|| true` 安全扫描绕过
- [ ] 设计文档 [2026-07-06-sota-upgrade-design.md](2026-07-06-sota-upgrade-design.md) 中「验收标准」全部勾选
