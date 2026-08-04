# 🛠️ 开发指南 (Development Guide)

> **最后更新**: 2026-08-03

本文档为开发者提供当前项目状态的完整开发环境搭建、代码规范、测试和部署指南。

## 📋 目录

- [质量门禁](#-质量门禁-quality-gate)
- [开发环境搭建](#-开发环境搭建)
- [启动服务](#-启动服务)
- [测试分层](#-测试分层)
- [代码规范](#-代码规范)
- [项目结构](#-项目结构)
- [常见问题](#-常见问题)

---

## 🛡️ 质量门禁 (Quality Gate)

推送或提交 PR 前，**必须**通过项目质量门禁。一条命令完成后端 + 前端全部检查：

```powershell
pwsh -NoProfile -File scripts/verify_project.ps1
```

该脚本按顺序执行：

1. `python -m ruff check src tests` — 静态检查
2. `python -m pytest -m "unit or api" -q --maxfail=1` — 后端快速测试
3. `npm run lint` — 前端 lint
4. `npm run test:run` — 前端单元测试
5. `npm run build` — 前端构建

任一步骤失败立即退出，返回原始退出码。

### 跳过前端或后端

```powershell
pwsh -NoProfile -File scripts/verify_project.ps1 -BackendOnly   # 只检查后端
pwsh -NoProfile -File scripts/verify_project.ps1 -FrontendOnly  # 只检查前端
```

### 健康检查端点

- `GET /health` — Liveness 探针，纯进程存活检查，**无 I/O**，始终返回 `{"status": "ok"}`
- `GET /ready` — Readiness 探针，检查数据库 / Redis（带超时），返回 200 或 503

```bash
# 独立健康检查脚本（用于部署后验证）
python scripts/healthcheck.py
python scripts/healthcheck.py -b http://localhost:5000
```

---

## 🚀 开发环境搭建

### 环境要求

- **Python**: 3.11+（当前使用 3.14）
- **Node.js**: 20+（前端开发时需要）
- **MySQL**: 8.0+（可选，单元测试使用 SQLite）
- **Git**: 2.0+

### 1. 克隆并初始化

```bash
git clone <repo-url>
cd 微博舆情分析
```

### 2. 创建虚拟环境并安装依赖

```powershell
# 创建/使用 .venv
python -m venv .venv
source .venv/Scripts/activate   # Git Bash
# 或: .venv\Scripts\activate    # PowerShell / CMD

# 安装依赖
pip install -r requirements/requirements.txt
pip install -r requirements/requirements-dev.txt  # 开发依赖
```

### 3. 环境变量

复制 `.env.example` 为 `.env`，按需修改：

```
FLASK_ENV=development
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=weibo_analysis
```

> 本地开发若没有 MySQL，质量门禁的 `unit + api` 测试不会连接数据库。
> 集成测试需要 MySQL 时使用 `pytest -m integration`。

### 4. 前端依赖

```powershell
cd frontend
npm install
cd ..
```

---

## ▶️ 启动服务

### 方式 A：开发模式（前后端分离）

**终端 1 — 后端：**

```powershell
source .venv/Scripts/activate
python src/app.py
# Flask 运行在 http://localhost:5000
```

**终端 2 — 前端：**

```powershell
cd frontend
npm run dev
# Vite 运行在 http://localhost:3000
```

### 方式 B：一键启动

```powershell
scripts\start.bat
```

> 自动同时拉起 Flask 后端（5000 端口）和 Vite 前端（3000 端口）。
> 停止：`scripts\start.bat stop`

### 方式 C：Docker Compose

```powershell
docker compose up -d
```

> 需要 Docker Desktop。完整部署参考 `docs/DEPLOYMENT.md`。

---

## 🧪 测试分层

| Marker | 含义 | 默认门禁 | 需要的外部服务 |
|--------|------|----------|---------------|
| `unit` | 纯逻辑，无外部服务 | ✅ 运行 | 无 |
| `api` | Flask client 测试 | ✅ 运行 | 无 |
| `integration` | 数据库集成测试 | ❌ 跳过 | SQLite / MySQL |
| `external` | 外部服务测试 | ❌ 跳过 | Redis / 微博 Cookie / 远程 NLP |
| `slow` | 性能/压力测试（>2s） | ❌ 跳过 | 无（但耗时） |

### 常用命令

```powershell
# 门禁测试（单元 + API）
pytest -m "unit or api" -q

# 查看最慢的 20 个测试
pytest -m "unit or api" --durations=20

# 集成测试（需要 MySQL）
pytest -m integration -q

# 全部测试（包含需要外部服务的）
pytest -q

# 单个测试文件
pytest tests/test_project_health.py -v

# 带覆盖率
pytest -m "unit or api" --cov=src --cov-report=term-missing
```

### 测试架构

- `tests/conftest.py` — 全局 fixtures（`app`、`client`、`authed_client`）
- `tests/factories.py` — 测试数据工厂（文章、评论、用户等）
- 所有测试使用 `pytest`，不使用 `unittest`
- 单元测试不依赖 MySQL/Redis，使用 `monkeypatch` 隔离外部服务

---

## 📏 代码规范

### Python

项目使用 **Ruff** 做静态检查和 **Black** 做格式化：

```powershell
# 检查代码
ruff check src tests

# 自动修复
ruff check --fix src tests

# 格式化
black src tests
```

配置在 `pyproject.toml` 中：
- 行长度：88
- Python 目标版本：3.11
- 启用规则：E, W, F, I, B, C4, UP

### 命名规范

```python
# 变量和函数：snake_case
user_name = "tester"
def get_user_data(): ...

# 类：PascalCase
class UserService: ...

# 常量：UPPER_CASE
MAX_RETRY_COUNT = 3
```

### 提交规范

```
<type>(<scope>): <subject>

feat:    新功能
fix:     修复 bug
docs:    文档更新
refactor: 代码重构
test:    测试相关
chore:   构建/工具配置
```

---

## 🏗️ 项目结构

```
微博舆情分析/
├── src/                    # 后端源代码
│   ├── app.py              # Flask 应用入口
│   ├── database.py         # 数据库连接（SQLAlchemy）
│   ├── config/             # 配置（settings.py）
│   ├── models/             # ORM 数据模型
│   ├── repositories/       # 数据访问层
│   ├── services/           # 业务逻辑层
│   ├── views/              # API 路由
│   ├── utils/              # 工具函数
│   ├── spider/             # 微博爬虫模块
│   ├── tasks/              # Celery 异步任务
│   └── model/              # 情感分析模型（离线实验用）
├── frontend/               # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 公共组件
│   │   ├── api/            # API 调用层
│   │   └── router/         # 路由配置
│   └── tests/              # 前端测试
├── tests/                  # 后端测试
├── scripts/                # 工具脚本
├── requirements/           # Python 依赖
├── database/               # SQL 初始化脚本
└── docs/                   # 文档
```

---

## 🔍 常见问题

### 启动时 MySQL 连接失败

质量门禁测试不需要 MySQL。如果只是运行 `pytest -m "unit or api"`，确保 `.env` 中 `DB_HOST` 指向一个可达地址即可（连接会在 5 秒超时后报告失败，不影响测试结果）。

### .venv 中没有 pip

```powershell
python -m ensurepip --upgrade
```

### `npm ci` 失败

```powershell
cd frontend
npm install   # 重新生成 lockfile
```

### Windows Store Python 拦截

确保 PowerShell 中 `python` 指向正确的解释器，或使用 `.venv/Scripts/python.exe`。`scripts/verify_project.ps1` 会自动检测 `.venv`。

---

## 📚 更多文档

- `docs/PRODUCT_SCOPE.md` — 产品能力边界
- `docs/USER_FLOWS.md` — 用户任务和验收标准
- `docs/API.md` — API 接口文档
- `docs/ARCHITECTURE.md` — 系统架构
- `docs/DEPLOYMENT.md` — 部署指南