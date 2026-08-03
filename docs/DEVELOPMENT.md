# 🛠️ 开发指南 (Development Guide)

本文档为开发者提供完整的开发环境搭建、代码规范、测试和部署指南。

## 📋 目录

- [开发环境搭建](#开发环境搭建)
- [代码规范](#代码规范)
- [项目结构详解](#项目结构详解)
- [开发工作流](#开发工作流)
- [测试指南](#测试指南)
- [调试技巧](#调试技巧)
- [性能优化](#性能优化)

## 🛡️ 质量门禁 (Quality Gate)

推送或提交 PR 前，**必须**通过项目质量门禁。一条命令完成后端 + 前端全部检查：

```powershell
pwsh -NoProfile -File scripts/verify_project.ps1
```

该脚本按顺序执行：

1. `python -m ruff check src tests` — 静态检查
2. `python -m pytest -m "unit or api" -q --maxfail=1` — 后端快速测试
3. `npm run lint` — 前端 lint
4. `npm run build` — 前端构建

任一步骤失败立即退出，返回原始退出码。

### 测试分层

| Marker | 含义 | 默认运行 | 需要 |
|--------|------|----------|------|
| `unit` | 纯逻辑，无外部服务 | ✅ | 无 |
| `api` | Flask client 测试 | ✅ | 无 |
| `integration` | 数据库集成 | ❌ | SQLite / MySQL |
| `external` | 外部服务 | ❌ | Redis / 微博 Cookie / 远程 NLP |
| `slow` | 性能/压力测试 | ❌ | 无（但耗时） |

```powershell
# 默认门禁（CI backend-fast job）
pytest -m "unit or api" -q

# 集成测试
pytest -m integration -q

# 外部依赖测试
pytest -m external -q

# 全部测试
pytest -q
```

### 健康检查端点

- `GET /health` — Liveness 探针，纯进程存活检查，**无 I/O**，始终返回 `{"status": "ok"}`
- `GET /ready` — Readiness 探针，检查数据库 / Redis（带超时），返回 200 或 503

```bash
# 独立健康检查脚本（用于部署后验证）
python scripts/healthcheck.py
python scripts/healthcheck.py -b http://localhost:5000
```

## 🚀 开发环境搭建

### 1. 环境要求

#### 系统要求
- **Python**: 3.8 - 3.12
- **MySQL**: 5.7+ (推荐 8.0+)
- **Git**: 2.0+
- **Node.js**: 14+ (前端开发时需要)

#### IDE 推荐
- **VS Code** (推荐)
  - Python 扩展
  - Pylint 扩展
  - GitLens 扩展
- **PyCharm Professional**
- **Vim/Neovim** (命令行用户)

### 2. 项目克隆和初始化

```bash
# 克隆项目
git clone https://github.com/zhangjszs/A-_public_opinion_development_system_based_on_Python.git
cd A-_public_opinion_development_system_based_on_Python

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements/requirements.txt

# 安装开发依赖
pip install -r requirements/requirements-dev.txt

# 验证安装
python -c "import flask, pandas, sklearn; print('所有依赖安装成功')"
```

### 3. 数据库设置

```bash
# 创建数据库
mysql -u root -p
CREATE DATABASE wb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit;

# 导入表结构
mysql -u root -p wb < 数据库/new.sql

# 配置数据库连接
cp utils/query.py.example utils/query.py
# 编辑 utils/query.py 中的数据库配置
```

### 4. 环境变量配置

创建 `.env` 文件：

```bash
# Flask 配置
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=True

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=wb

# 应用配置
SECRET_KEY=your-secret-key-here
SESSION_TIMEOUT=3600

# 爬虫配置
WEIBO_COOKIE=your-cookie-here
PROXY_ENABLED=false
```

### 5. IDE 配置

#### VS Code 配置

创建 `.vscode/settings.json`：

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "88"],
    "files.associations": {
        "*.html": "html",
        "*.css": "css",
        "*.js": "javascript"
    },
    "emmet.includeLanguages": {
        "html": "html"
    }
}
```

创建 `.vscode/launch.json`：

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Flask",
            "type": "python",
            "request": "launch",
            "module": "flask",
            "env": {
                "FLASK_APP": "app.py",
                "FLASK_ENV": "development"
            },
            "args": ["run", "--no-debugger"],
            "jinja": true
        }
    ]
}
```

## 📏 代码规范

### Python 代码规范

遵循 PEP 8 标准，使用 Black 格式化：

```bash
# 安装 Black
pip install black

# 格式化代码
black .

# 检查代码质量
flake8 .
pylint app.py
```

### 命名规范

```python
# 变量和函数：snake_case
user_name = "john"
def get_user_data():
    pass

# 类：PascalCase
class UserManager:
    pass

# 常量：UPPER_CASE
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30

# 文件名：snake_case
user_manager.py
database_connection.py
```

### 代码结构

```python
"""
模块文档字符串
描述模块功能和用途
"""

import os
import sys
from typing import Optional, List, Dict

# 常量定义
DEFAULT_CONFIG = {
    'host': 'localhost',
    'port': 3306
}

class DatabaseManager:
    """
    数据库管理器类

    负责数据库连接和查询操作
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化数据库管理器

        Args:
            config: 数据库配置字典
        """
        self.config = config or DEFAULT_CONFIG
        self.connection = None

    def connect(self) -> bool:
        """
        建立数据库连接

        Returns:
            bool: 连接是否成功
        """
        try:
            # 连接逻辑
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False

    def query(self, sql: str, params: Optional[List] = None) -> List[Dict]:
        """
        执行查询

        Args:
            sql: SQL 查询语句
            params: 查询参数

        Returns:
            List[Dict]: 查询结果
        """
        # 查询逻辑
        pass
```

### 错误处理

```python
def safe_database_operation():
    """安全的数据库操作示例"""
    try:
        # 数据库操作
        result = db.query("SELECT * FROM users")
        return result
    except ConnectionError as e:
        logger.error(f"数据库连接错误: {e}")
        raise DatabaseConnectionError("无法连接到数据库") from e
    except SQLSyntaxError as e:
        logger.error(f"SQL语法错误: {e}")
        raise QueryError("SQL查询语法错误") from e
    except Exception as e:
        logger.error(f"未知错误: {e}")
        raise SystemError("系统内部错误") from e
    finally:
        # 清理资源
        if db_connection:
            db_connection.close()
```

## 🏗️ 项目结构详解

### 核心模块说明

#### 1. 应用入口 (`app.py`)
```python
"""
Flask 应用主入口
负责应用初始化、路由注册、配置加载
"""

from flask import Flask
from views.user import user_bp
from views.page import page_bp
from utils.cache import cache

def create_app(config_name='development'):
    """应用工厂函数"""
    app = Flask(__name__)

    # 配置加载
    if config_name == 'development':
        app.config.from_object('config.DevelopmentConfig')
    else:
        app.config.from_object('config.ProductionConfig')

    # 扩展初始化
    cache.init_app(app)

    # 蓝图注册
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(page_bp, url_prefix='/page')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
```

#### 2. 数据库层 (`utils/query.py`)
```python
"""
数据库查询工具模块
提供统一的数据库操作接口
"""

import pymysql
from contextlib import contextmanager
from typing import List, Dict, Any

class DatabasePool:
    """数据库连接池"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool = []

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = None
        try:
            conn = pymysql.connect(**self.config)
            yield conn
        finally:
            if conn:
                conn.close()

def querys(sql: str, params: List = None, operation: str = 'select') -> Any:
    """
    统一数据库查询接口

    Args:
        sql: SQL 语句
        params: 参数列表
        operation: 操作类型 (select/insert/update/delete)

    Returns:
        查询结果或影响行数
    """
    with db_pool.get_connection() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(sql, params or [])

            if operation == 'select':
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.rowcount
```

#### 3. 模型层 (`model/`)
```python
"""
模型处理模块
包含数据预处理、情感分析、词频分析等
"""

# improved_index.py - 数据预处理
class ModelDataProcessor:
    """数据预处理处理器"""

    def __init__(self, model_dir: str):
        self.model_dir = Path(model_dir)
        self.stop_words = self._load_stop_words()

    def clean_and_segment_text(self, data: List[List]) -> str:
        """清洗和分词文本"""
        # 实现逻辑
        pass

# improved_yuqing.py - 情感分析
class SentimentAnalyzer:
    """情感分析器"""

    def __init__(self, model_dir: str):
        self.model_dir = Path(model_dir)
        self.model = None

    def analyze_sentiment(self, texts: List[str]) -> List[Dict]:
        """分析情感"""
        # 实现逻辑
        pass

# improved_ciPingTotal.py - 词频分析
class WordFrequencyAnalyzer:
    """词频分析器"""

    def __init__(self, model_dir: str):
        self.model_dir = Path(model_dir)

    def calculate_frequency(self, text: str, max_results: int = 100) -> List[Tuple[str, int]]:
        """计算词频"""
        # 实现逻辑
        pass
```

#### 4. 爬虫模块 (`spider/`)
```python
"""
网络爬虫模块
负责从微博获取数据
"""

# config.py - 配置管理
class SpiderConfigManager:
    """爬虫配置管理器"""

    def __init__(self):
        self.BASE_HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': 'your-cookie-here'
        }

    def get_random_headers(self) -> Dict[str, str]:
        """获取随机请求头"""
        # 实现逻辑
        pass

# spiderMaster.py - 主控制器
class WeiboSpiderController:
    """微博爬虫控制器"""

    def __init__(self, delay: float = 2.0):
        self.delay = delay
        self.content_completed = False
        self.comments_completed = False
        self.user_completed = False

    def concurrent_spider_mode(self):
        """并发爬取模式"""
        # 实现逻辑
        pass

    def sequential_spider_mode(self):
        """顺序爬取模式"""
        # 实现逻辑
        pass
```

#### 5. 视图层 (`views/`)
```python
"""
视图模块
处理 HTTP 请求和响应
"""

# views/user/user.py - 用户管理
@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # 验证逻辑
        if validate_user(username, password):
            session['user_id'] = get_user_id(username)
            return redirect(url_for('page.home'))
        else:
            flash('用户名或密码错误')

    return render_template('login.html')

# views/page/page.py - 页面路由
@page_bp.route('/home')
@login_required
def home():
    """首页"""
    data = get_home_data()
    return render_template('home.html', data=data)

@page_bp.route('/articles')
@login_required
def articles():
    """文章列表页"""
    page = request.args.get('page', 1, type=int)
    articles = get_articles_paginated(page)
    return render_template('articles.html', articles=articles)
```

## 🔄 开发工作流

### 1. 分支管理

```bash
# 创建功能分支
git checkout -b feature/new-feature

# 定期同步主分支
git checkout main
git pull origin main
git checkout feature/new-feature
git rebase main

# 提交代码
git add .
git commit -m "feat: 添加新功能"

# 推送分支
git push origin feature/new-feature

# 创建 Pull Request
# 在 GitHub 上创建 PR
```

### 2. 提交规范

```bash
# 格式: <type>(<scope>): <subject>

# 常用类型
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建过程或工具配置

# 示例
git commit -m "feat(auth): 添加用户登录功能"
git commit -m "fix(api): 修复数据查询错误"
git commit -m "docs(readme): 更新部署指南"
```

### 3. 代码审查

#### Pull Request 模板
```markdown
## 描述
简要描述这次更改的目的和内容

## 类型
- [ ] 🐛 Bug fix
- [ ] ✨ New feature
- [ ] 💥 Breaking change
- [ ] 📚 Documentation
- [ ] 🎨 Style
- [ ] 🔧 Chore

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 通过了所有测试
- [ ] 在不同浏览器中测试过

## 测试
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 端到端测试通过
```

## 🧪 测试指南

### 1. 单元测试

```python
# tests/test_database.py
import unittest
from unittest.mock import Mock, patch
from utils.query import querys

class TestDatabase(unittest.TestCase):

    def setUp(self):
        """测试前准备"""
        self.test_config = {
            'host': 'localhost',
            'user': 'test',
            'password': 'test',
            'database': 'test_db'
        }

    def tearDown(self):
        """测试后清理"""
        pass

    @patch('utils.query.pymysql.connect')
    def test_query_success(self, mock_connect):
        """测试查询成功情况"""
        # 模拟数据库连接
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        # 设置模拟返回值
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'name': 'test'},
            {'id': 2, 'name': 'test2'}
        ]

        # 执行测试
        result = querys("SELECT * FROM users")

        # 断言
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'test')

    @patch('utils.query.pymysql.connect')
    def test_query_error(self, mock_connect):
        """测试查询错误情况"""
        mock_connect.side_effect = Exception("Connection failed")

        with self.assertRaises(Exception):
            querys("SELECT * FROM users")

if __name__ == '__main__':
    unittest.main()
```

### 2. 运行测试

```bash
# 运行所有测试
python -m pytest

# 运行特定测试文件
python -m pytest tests/test_database.py

# 运行带覆盖率
python -m pytest --cov=utils --cov-report=html

# 运行特定测试类或方法
python -m pytest tests/test_database.py::TestDatabase::test_query_success -v
```

### 3. 测试配置

创建 `pytest.ini`：

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --verbose
    --tb=short
    --cov=.
    --cov-report=html
    --cov-report=term-missing
markers =
    unit: 单元测试
    integration: 集成测试
    slow: 慢速测试
```

### 4. 集成测试

```python
# tests/test_app.py
import pytest
from app import create_app

@pytest.fixture
def app():
    """应用 fixture"""
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    """测试客户端 fixture"""
    return app.test_client()

def test_home_page(client):
    """测试首页"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome' in response.data

def test_login_required(client):
    """测试需要登录的页面"""
    response = client.get('/dashboard')
    assert response.status_code == 302  # 重定向到登录页
    assert '/login' in response.headers['Location']
```

## 🔍 调试技巧

### 1. Flask 调试

```python
# app.py
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### 2. 日志配置

```python
# utils/logger.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_file, level=logging.INFO):
    """设置日志器"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 创建 RotatingFileHandler
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )

    # 设置格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

# 在应用中使用
app_logger = setup_logger('app', 'logs/app.log')
db_logger = setup_logger('database', 'logs/database.log')
```

### 3. 数据库调试

```python
# utils/debug_db.py
def debug_query(sql, params=None):
    """调试数据库查询"""
    print(f"Executing SQL: {sql}")
    if params:
        print(f"Parameters: {params}")

    start_time = time.time()
    try:
        result = querys(sql, params)
        end_time = time.time()

        print(f"Query completed in {end_time - start_time:.3f} seconds")
        print(f"Result count: {len(result) if isinstance(result, list) else 'N/A'}")

        return result
    except Exception as e:
        print(f"Query failed: {e}")
        raise
```

### 4. 性能分析

```python
# utils/profiler.py
import cProfile
import pstats
from functools import wraps

def profile_function(func):
    """函数性能分析装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()

        result = func(*args, **kwargs)

        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(20)  # 显示前20个耗时函数

        return result
    return wrapper

# 使用示例
@profile_function
def slow_function():
    # 一些耗时的操作
    pass
```

## ⚡ 性能优化

### 1. 数据库优化

```python
# utils/query_optimized.py
from functools import lru_cache
import time

class QueryOptimizer:
    """查询优化器"""

    def __init__(self):
        self.query_cache = {}
        self.cache_timeout = 300  # 5分钟

    @lru_cache(maxsize=1000)
    def cached_query(self, sql_hash, sql, params):
        """缓存查询结果"""
        return querys(sql, params)

    def execute_with_retry(self, sql, params=None, max_retries=3):
        """带重试的查询执行"""
        for attempt in range(max_retries):
            try:
                return querys(sql, params)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)  # 指数退避

    def batch_insert(self, table, data_list):
        """批量插入优化"""
        if not data_list:
            return 0

        # 分批处理，避免单次插入过多数据
        batch_size = 1000
        total_inserted = 0

        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]

            # 构建批量插入SQL
            columns = list(batch[0].keys())
            placeholders = ', '.join(['%s'] * len(columns))
            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

            # 批量插入
            values = [tuple(row.values()) for row in batch]
            querys(sql, values, 'insert')
            total_inserted += len(batch)

        return total_inserted
```

### 2. 缓存策略

```python
# utils/cache_strategy.py
from cachetools import TTLCache, LRUCache
from functools import wraps
import hashlib

class CacheManager:
    """缓存管理器"""

    def __init__(self):
        # 内存缓存：快速访问，容量有限
        self.memory_cache = LRUCache(maxsize=1000)

        # TTL缓存：带过期时间
        self.ttl_cache = TTLCache(maxsize=500, ttl=300)

        # 文件缓存：持久化存储
        self.file_cache = {}

    def make_key(self, func_name, args, kwargs):
        """生成缓存键"""
        key_data = f"{func_name}_{str(args)}_{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def cached(self, ttl=300, cache_type='memory'):
        """缓存装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = self.make_key(func.__name__, args, kwargs)

                # 选择缓存类型
                if cache_type == 'memory':
                    cache = self.memory_cache
                elif cache_type == 'ttl':
                    cache = self.ttl_cache
                else:
                    cache = self.memory_cache

                # 尝试从缓存获取
                if cache_key in cache:
                    return cache[cache_key]

                # 执行函数
                result = func(*args, **kwargs)

                # 存入缓存
                cache[cache_key] = result

                return result
            return wrapper
        return decorator

# 使用示例
cache_manager = CacheManager()

@cache_manager.cached(ttl=600, cache_type='ttl')
def get_user_data(user_id):
    """获取用户数据（带缓存）"""
    return querys("SELECT * FROM users WHERE id = %s", [user_id])
```

### 3. 异步处理

```python
# utils/async_processor.py
import asyncio
import concurrent.futures
from functools import partial

class AsyncProcessor:
    """异步处理器"""

    def __init__(self, max_workers=4):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    async def run_in_executor(self, func, *args, **kwargs):
        """在执行器中运行函数"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            partial(func, *args, **kwargs)
        )

    async def process_batch(self, items, process_func, batch_size=10):
        """批量异步处理"""
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            # 创建任务
            tasks = [
                self.run_in_executor(process_func, item)
                for item in batch
            ]

            # 等待批次完成
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

        return results

# 使用示例
async def process_data_async():
    """异步处理数据"""
    processor = AsyncProcessor()

    # 异步批量处理
    data_items = [1, 2, 3, 4, 5]  # 要处理的数据
    results = await processor.process_batch(
        data_items,
        process_single_item,  # 处理单个项目的函数
        batch_size=2
    )

    return results
```

### 4. 监控和告警

```python
# utils/monitor.py
import time
import psutil
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics = {
            'requests_total': 0,
            'requests_failed': 0,
            'response_time_avg': 0,
            'memory_usage': 0,
            'cpu_usage': 0
        }

    def monitor_function(self, func):
        """函数性能监控装饰器"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                self.metrics['requests_total'] += 1

                # 计算响应时间
                response_time = time.time() - start_time
                self._update_response_time(response_time)

                return result

            except Exception as e:
                self.metrics['requests_failed'] += 1
                logger.error(f"Function {func.__name__} failed: {e}")
                raise

        return wrapper

    def _update_response_time(self, response_time):
        """更新平均响应时间"""
        total_requests = self.metrics['requests_total']
        current_avg = self.metrics['response_time_avg']

        # 滑动平均
        self.metrics['response_time_avg'] = (
            (current_avg * (total_requests - 1)) + response_time
        ) / total_requests

    def get_system_metrics(self):
        """获取系统指标"""
        return {
            'memory_usage': psutil.virtual_memory().percent,
            'cpu_usage': psutil.cpu_percent(interval=1),
            'disk_usage': psutil.disk_usage('/').percent
        }

    def log_metrics(self):
        """记录指标"""
        system_metrics = self.get_system_metrics()
        logger.info(f"Performance metrics: {self.metrics}")
        logger.info(f"System metrics: {system_metrics}")

# 使用示例
monitor = PerformanceMonitor()

@monitor.monitor_function
def process_request(request_data):
    """处理请求"""
    # 处理逻辑
    time.sleep(0.1)  # 模拟处理时间
    return {"status": "success"}

# 定期记录指标
import threading
def metrics_logger():
    while True:
        monitor.log_metrics()
        time.sleep(60)  # 每分钟记录一次

# 启动监控线程
threading.Thread(target=metrics_logger, daemon=True).start()
```

---

**最后更新**: 2025年9月20日