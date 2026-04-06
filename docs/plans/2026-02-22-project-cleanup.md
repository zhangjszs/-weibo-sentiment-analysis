# 项目系统性整理 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 对项目进行全面均衡整理，统一代码风格、清理废弃代码、统一 API 响应格式、同步文档、提升测试覆盖率至 80%+。

**Architecture:** 顺序分阶段执行，每阶段完成后运行 `pytest` 验证无回归。后端使用 Black/isort/Ruff 格式化，前端补充 Prettier + ESLint 配置。API 响应统一通过 `utils/api_response.ok()`/`error()`，全局错误处理器已存在于 `app.py`。

**Tech Stack:** Python 3.8+, Flask 3.1, SQLAlchemy 2.0, Vue 3 + Vite, Pytest, Black, isort, Ruff, Prettier

---

## 阶段 1 — 代码格式化与风格统一

### Task 1: 安装并验证后端格式化工具

**Files:**
- Verify: `pyproject.toml`
- Verify: `.pre-commit-config.yaml`

**Step 1: 确认工具已安装**

```bash
cd "D:\coding\Pycharm\基于python微博舆情分析可视化系统"
pip show black isort ruff
```

Expected: 三个工具均已安装，显示版本信息。

**Step 2: 对全部 Python 文件运行 isort**

```bash
isort src/ tests/ scripts/ --settings-path pyproject.toml
```

Expected: 无错误输出，import 顺序已修正。

**Step 3: 对全部 Python 文件运行 black**

```bash
black src/ tests/ scripts/ --config pyproject.toml
```

Expected: 输出 "reformatted X files" 或 "X files left unchanged"，无错误。

**Step 4: 对全部 Python 文件运行 ruff --fix**

```bash
ruff check src/ tests/ scripts/ --fix --config pyproject.toml
```

Expected: 输出修复数量，无 error 级别问题。

**Step 5: 验证 ruff 零警告**

```bash
ruff check src/ --config pyproject.toml
```

Expected: 无输出（零警告）。

**Step 6: 运行测试确认无回归**

```bash
cd "D:\coding\Pycharm\基于python微博舆情分析可视化系统"
python -m pytest tests/ -x -q 2>&1 | head -50
```

Expected: 所有测试通过或跳过，无新增失败。

**Step 7: Commit**

```bash
git add -A
git commit -m "style: apply black/isort/ruff formatting to all Python files"
```

---

### Task 2: 为前端添加 Prettier 配置

**Files:**
- Create: `frontend/.prettierrc.json`
- Create: `frontend/.eslintrc.cjs`
- Modify: `frontend/package.json`

**Step 1: 创建 Prettier 配置文件**

创建 `frontend/.prettierrc.json`：

```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "vueIndentScriptAndStyle": true
}
```

**Step 2: 创建 ESLint 配置文件**

创建 `frontend/.eslintrc.cjs`：

```js
module.exports = {
  root: true,
  env: { browser: true, es2021: true, node: true },
  extends: ['plugin:vue/vue3-recommended'],
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  rules: {
    'vue/multi-word-component-names': 'off',
    'no-unused-vars': 'warn',
    'no-console': 'warn',
  },
}
```

**Step 3: 在 package.json 中添加 prettier 依赖和脚本**

修改 `frontend/package.json`，在 `devDependencies` 中添加：

```json
"prettier": "^3.3.3",
"eslint": "^8.57.0",
"eslint-plugin-vue": "^9.27.0"
```

在 `scripts` 中添加：

```json
"format": "prettier --write src/",
"format:check": "prettier --check src/"
```

**Step 4: 安装依赖**

```bash
cd "D:\coding\Pycharm\基于python微博舆情分析可视化系统\frontend"
npm install
```

Expected: 安装成功，无 peer dependency 错误。

**Step 5: 运行 Prettier 格式化**

```bash
npm run format
```

Expected: 输出格式化的文件列表。

**Step 6: 验证格式化结果**

```bash
npm run format:check
```

Expected: 无差异输出。

**Step 7: Commit**

```bash
cd "D:\coding\Pycharm\基于python微博舆情分析可视化系统"
git add frontend/.prettierrc.json frontend/.eslintrc.cjs frontend/package.json frontend/package-lock.json
git add frontend/src/
git commit -m "style: add prettier/eslint config and format frontend source files"
```

---

## 阶段 2 — 废弃代码清理

### Task 3: 清理 src/views/user/user.py 中的原始 jsonify 调用

**Files:**
- Modify: `src/views/user/user.py`

**Step 1: 读取文件，定位原始 jsonify 调用**

查看 `src/views/user/user.py` 第 140-190 行，找到以下模式：
- `return jsonify({'code': 200, 'msg': '登出成功'})`
- `return jsonify({...})`（多处）

**Step 2: 确认 api_response 已导入**

检查文件顶部是否有：
```python
from utils.api_response import error, ok
```

若无，添加此导入。

**Step 3: 替换原始 jsonify 调用**

将所有 `return jsonify({'code': 200, 'msg': ...})` 替换为 `return ok(msg=...), 200`。

将所有 `return jsonify({'code': 4xx/5xx, 'msg': ...}), 4xx/5xx` 替换为 `return error(..., code=4xx), 4xx`。

**Step 4: 写一个测试验证响应格式**

在 `tests/test_api_response.py` 中添加（若文件已存在则追加）：

```python
def test_user_logout_response_format(client):
    """验证登出响应使用统一格式"""
    # 假设已登录状态
    resp = client.post('/user/logout')
    data = resp.get_json()
    assert 'code' in data
    assert 'msg' in data
    assert 'timestamp' in data
```

**Step 5: 运行测试**

```bash
python -m pytest tests/test_api_response.py -v
```

Expected: 测试通过。

**Step 6: Commit**

```bash
git add src/views/user/user.py tests/test_api_response.py
git commit -m "refactor: replace raw jsonify with api_response helpers in user.py"
```

---

### Task 4: 清理未使用的 import 和死代码

**Files:**
- Modify: 多个 `src/` 文件（由 ruff 报告确定）

**Step 1: 找出所有未使用的 import**

```bash
ruff check src/ --select F401 --config pyproject.toml
```

Expected: 列出所有未使用 import 的文件和行号。

**Step 2: 自动修复**

```bash
ruff check src/ --select F401 --fix --config pyproject.toml
```

Expected: 自动删除未使用 import。

**Step 3: 找出注释掉的代码块**

```bash
grep -rn "^#.*=\|^# .*def \|^# .*class \|^# .*return " src/ --include="*.py" | head -30
```

手动检查并删除明显的注释掉的代码（非说明性注释）。

**Step 4: 运行测试**

```bash
python -m pytest tests/ -x -q 2>&1 | tail -20
```

Expected: 全部通过。

**Step 5: Commit**

```bash
git add src/
git commit -m "chore: remove unused imports and dead code"
```

---

### Task 5: 清理 docs/archive 和测试遗留文件

**Files:**
- Review: `docs/archive/`
- Review: `cache/` 目录

**Step 1: 列出 archive 目录内容**

```bash
ls -la "docs/archive/"
```

**Step 2: 删除明确过时的文档**

对于每个 archive 文件，确认其内容已被新文档替代后删除：

```bash
git rm docs/archive/<过时文件名>
```

**Step 3: 清理 cache 目录中的测试遗留文件**

```bash
ls cache/
```

删除非运行时必要的测试文件（保留 `.gitkeep` 或目录本身）。

**Step 4: Commit**

```bash
git add -A
git commit -m "chore: clean up archived docs and test leftover cache files"
```

---

## 阶段 3 — API 响应格式统一

### Task 6: 审计所有 API 端点的响应格式

**Files:**
- Read: `src/views/api/*.py`
- Read: `src/views/data/data_api.py`

**Step 1: 搜索所有直接 jsonify 调用**

```bash
grep -rn "return jsonify(" src/views/ --include="*.py"
```

Expected: 列出所有仍使用原始 jsonify 的位置。

**Step 2: 搜索不规范的响应字典**

```bash
grep -rn "{'code':" src/views/ --include="*.py"
```

**Step 3: 对每个发现的不规范调用，替换为 ok()/error()**

规则：
- `jsonify({'code': 200, ...})` → `ok(data, msg=msg), 200`
- `jsonify({'code': 4xx, ...}), 4xx` → `error(msg, code=4xx), 4xx`
- `jsonify({'code': 5xx, ...}), 5xx` → `error(msg, code=5xx), 5xx`

**Step 4: 运行测试**

```bash
python -m pytest tests/ -x -q 2>&1 | tail -20
```

Expected: 全部通过。

**Step 5: Commit**

```bash
git add src/views/
git commit -m "refactor: unify all API endpoints to use api_response helpers"
```

---

### Task 7: 验证全局错误处理器完整性

**Files:**
- Read: `src/app.py` 第 455-540 行

**Step 1: 确认已有错误处理器**

`app.py` 中已有：404、500、403、401、CSRFError 处理器。验证每个处理器对 API 路径返回 JSON，对页面路径返回 HTML。

**Step 2: 检查是否缺少 422（参数验证错误）处理器**

```bash
grep -n "422\|UnprocessableEntity\|ValidationError" src/app.py
```

若无，在 `src/app.py` 的错误处理器区域添加：

```python
@app.errorhandler(422)
def unprocessable_entity(err):
    if request.path.startswith('/api/') or request.path.startswith('/getAllData/'):
        return error('请求参数无效', code=422), 422
    return render_template('error.html', error_message='请求参数无效'), 422
```

**Step 3: 运行测试**

```bash
python -m pytest tests/ -x -q 2>&1 | tail -10
```

**Step 4: Commit**

```bash
git add src/app.py
git commit -m "feat: add 422 error handler for validation errors"
```

---

## 阶段 4 — 文档与代码对齐

### Task 8: 更新 README.md 目录结构

**Files:**
- Modify: `README.md`

**Step 1: 读取当前 README 中的目录结构部分**

找到 README 中描述项目结构的章节。

**Step 2: 对比实际目录结构**

```bash
find src/ -name "*.py" -not -path "*/__pycache__/*" | sort
```

**Step 3: 更新 README 中的目录树**

确保以下新增模块已体现：
- `src/services/alert_service.py`
- `src/services/propagation_service.py`
- `src/services/notification_service.py`
- `src/views/api/alert_api.py`
- `src/views/api/report_api.py`
- `src/views/api/propagation_api.py`
- `src/repositories/` 目录

**Step 4: Commit**

```bash
git add README.md
git commit -m "docs: sync README directory structure with current codebase"
```

---

### Task 9: 更新 docs/ARCHITECTURE.md

**Files:**
- Modify: `docs/ARCHITECTURE.md`

**Step 1: 读取当前 ARCHITECTURE.md**

找到描述"当前问题"和"目标架构"的章节。

**Step 2: 将已完成的迁移标记为完成**

- 将"高耦合"问题标记为已解决（已有 repositories/ 层）
- 将"贫血模型"标记为已解决（已有 services/ 层）
- 将"自定义 pymysql"标记为已迁移至 SQLAlchemy 2.0
- 更新架构图，反映当前 Views → Services → Repositories → Database 分层

**Step 3: Commit**

```bash
git add docs/ARCHITECTURE.md
git commit -m "docs: update ARCHITECTURE.md to reflect completed DDD migration"
```

---

### Task 10: 更新 docs/API.md

**Files:**
- Modify: `docs/API.md`

**Step 1: 列出所有当前 API 端点**

```bash
grep -rn "@bp.route\|@app.route" src/views/ --include="*.py" | grep -v "test"
```

**Step 2: 对比 docs/API.md 中的端点列表**

找出 API.md 中缺失的端点（alert、report、propagation、favorites、audit、platform）。

**Step 3: 为每个缺失端点添加文档条目**

格式：
```markdown
### GET /api/alert/rules
**描述**: 获取所有预警规则
**认证**: 需要 JWT Token
**响应**:
```json
{"code": 200, "msg": "success", "data": {"rules": [...], "total": N}}
```
```

**Step 4: Commit**

```bash
git add docs/API.md
git commit -m "docs: add missing API endpoints to API.md (alert/report/propagation)"
```

---

## 阶段 5 — 测试覆盖率提升

### Task 11: 提升覆盖率目标至 80%

**Files:**
- Modify: `pyproject.toml`

**Step 1: 修改 fail_under**

将 `pyproject.toml` 中：
```toml
fail_under = 50
```
改为：
```toml
fail_under = 80
```

**Step 2: 运行当前覆盖率检查，了解差距**

```bash
python -m pytest tests/ --cov=src --cov-report=term-missing -q 2>&1 | tail -30
```

Expected: 显示当前覆盖率和未覆盖行。记录覆盖率最低的模块。

**Step 3: Commit 配置变更**

```bash
git add pyproject.toml
git commit -m "test: raise coverage target from 50% to 80%"
```

---

### Task 12: 为 alert_service 补充单元测试

**Files:**
- Read: `src/services/alert_service.py`
- Create/Modify: `tests/test_alert_service.py`

**Step 1: 读取 alert_service.py 了解主要方法**

重点关注：`get_rules()`、`create_rule()`、`check_alert()` 等核心方法。

**Step 2: 写失败测试**

创建 `tests/test_alert_service.py`：

```python
import pytest
from unittest.mock import MagicMock, patch
from src.services.alert_service import AlertRule, AlertType, AlertLevel, alert_engine


class TestAlertEngine:
    def test_get_rules_returns_list(self):
        rules = alert_engine.get_rules()
        assert isinstance(rules, list)

    def test_create_rule_with_valid_data(self):
        rule = AlertRule(
            id='test_rule_001',
            name='测试规则',
            alert_type=AlertType('custom'),
            level=AlertLevel('warning'),
            conditions={},
            cooldown_minutes=30
        )
        assert rule.id == 'test_rule_001'
        assert rule.name == '测试规则'

    def test_duplicate_rule_id_raises(self):
        """重复 rule_id 应被拒绝"""
        # 根据实际 alert_engine 接口调整
        pass
```

**Step 3: 运行测试确认失败或通过**

```bash
python -m pytest tests/test_alert_service.py -v
```

**Step 4: 根据实际接口补全测试**

读取 `alert_service.py` 后，为每个公共方法至少写 2 个测试（正常路径 + 边界/错误路径）。

**Step 5: 运行测试确认通过**

```bash
python -m pytest tests/test_alert_service.py -v
```

Expected: 全部 PASS。

**Step 6: Commit**

```bash
git add tests/test_alert_service.py
git commit -m "test: add unit tests for alert_service"
```

---

### Task 13: 为 sentiment_service 补充单元测试

**Files:**
- Read: `src/services/sentiment_service.py`
- Create/Modify: `tests/test_sentiment_service.py`

**Step 1: 读取 sentiment_service.py 了解主要方法**

重点关注：情感分析、批量处理、结果缓存等方法。

**Step 2: 写测试（使用 mock 避免依赖真实模型）**

```python
import pytest
from unittest.mock import patch, MagicMock


class TestSentimentService:
    @patch('src.services.sentiment_service.SentimentService._load_model')
    def test_analyze_positive_text(self, mock_model):
        mock_model.return_value = MagicMock()
        from src.services.sentiment_service import SentimentService
        svc = SentimentService()
        # 根据实际接口调整
        result = svc.analyze('这个产品非常好用')
        assert result is not None

    def test_analyze_empty_text_returns_neutral(self):
        from src.services.sentiment_service import SentimentService
        svc = SentimentService()
        result = svc.analyze('')
        # 空文本应返回中性或错误，不应抛出异常
        assert result is not None
```

**Step 3: 运行并修正测试**

```bash
python -m pytest tests/test_sentiment_service.py -v
```

**Step 4: Commit**

```bash
git add tests/test_sentiment_service.py
git commit -m "test: add unit tests for sentiment_service"
```

---

### Task 14: 为 propagation_service 补充单元测试

**Files:**
- Read: `src/services/propagation_service.py`
- Create/Modify: `tests/test_propagation_service.py`

**Step 1: 读取 propagation_service.py 了解主要方法**

重点关注：传播路径构建、图分析、节点统计等方法。

**Step 2: 写测试（mock 数据库调用）**

```python
import pytest
from unittest.mock import patch, MagicMock


class TestPropagationService:
    @patch('src.services.propagation_service.db_session')
    def test_build_propagation_graph_empty(self, mock_db):
        mock_db.execute.return_value.fetchall.return_value = []
        from src.services.propagation_service import PropagationService
        svc = PropagationService()
        result = svc.get_propagation_graph(article_id=999)
        assert result is not None

    @patch('src.services.propagation_service.db_session')
    def test_propagation_stats_structure(self, mock_db):
        mock_db.execute.return_value.fetchall.return_value = []
        from src.services.propagation_service import PropagationService
        svc = PropagationService()
        stats = svc.get_stats(article_id=1)
        # 验证返回结构包含必要字段
        assert isinstance(stats, dict)
```

**Step 3: 运行并修正测试**

```bash
python -m pytest tests/test_propagation_service.py -v
```

**Step 4: Commit**

```bash
git add tests/test_propagation_service.py
git commit -m "test: add unit tests for propagation_service"
```

---

### Task 15: 验证最终覆盖率达标

**Step 1: 运行完整测试套件含覆盖率**

```bash
python -m pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80 -q 2>&1 | tail -40
```

**Step 2: 若覆盖率未达 80%，找出差距最大的模块**

```bash
python -m pytest tests/ --cov=src --cov-report=term-missing -q 2>&1 | grep -E "^\s+[0-9]+" | sort -k4 -n | head -20
```

**Step 3: 为覆盖率最低的模块补充测试，重复 Task 12-14 的模式**

**Step 4: 最终验证**

```bash
python -m pytest tests/ --cov=src --cov-fail-under=80 -q
```

Expected: 所有测试通过，覆盖率 ≥ 80%。

**Step 5: 最终 Commit**

```bash
git add -A
git commit -m "test: achieve 80%+ test coverage across all core modules"
```

---

## 验收检查清单

- [ ] `ruff check src/` 零警告
- [ ] `prettier --check frontend/src/` 零差异
- [ ] `grep -r "jsonify({" src/views/` 无原始 jsonify 响应
- [ ] `pytest tests/ -q` 全部通过
- [ ] `pytest tests/ --cov=src --cov-fail-under=80` 通过
- [ ] `docs/API.md` 包含所有当前端点
- [ ] `docs/ARCHITECTURE.md` 反映当前架构状态
- [ ] `README.md` 目录结构与实际一致
