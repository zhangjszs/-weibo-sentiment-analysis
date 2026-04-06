# 🤝 贡献指南 (Contributing Guide)

欢迎为微博舆情分析系统项目做出贡献！我们非常感谢您的帮助。本文档将指导您如何参与项目开发。

## 📋 目录

- [快速开始](#快速开始)
- [开发环境](#开发环境)
- [贡献流程](#贡献流程)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [测试要求](#测试要求)
- [问题反馈](#问题反馈)
- [行为准则](#行为准则)

## 🚀 快速开始

### 1. Fork 项目

点击项目右上角的 "Fork" 按钮，将项目复制到您的 GitHub 账户下。

### 2. 克隆到本地

```bash
# 克隆您的 fork
git clone https://github.com/YOUR_USERNAME/A-_public_opinion_development_system_based_on_Python.git
cd A-_public_opinion_development_system_based_on_Python

# 添加上游仓库
git remote add upstream https://github.com/zhangjszs/A-_public_opinion_development_system_based_on_Python.git

# 创建开发分支
git checkout -b feature/your-feature-name
```

### 3. 环境设置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 数据库设置
mysql -u root -p < 数据库/new.sql
```

### 4. 验证安装

```bash
# 运行测试
python -m pytest tests/

# 启动应用
python app.py
```

## 🛠️ 开发环境

### 推荐工具

#### IDE
- **VS Code** (推荐)
  - Python 扩展
  - Pylint 扩展
  - Black 格式化器
- **PyCharm Professional**
- **Vim/Neovim**

#### 版本控制
- Git 2.0+
- GitHub Desktop (可选)

#### 数据库工具
- MySQL Workbench
- DBeaver
- Navicat

### 环境配置

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
```

## 🔄 贡献流程

### 1. 选择任务

查看 [Issues](../../issues) 页面，选择您感兴趣的任务：

- 🐛 `bug` - 修复错误
- ✨ `enhancement` - 新功能
- 📚 `documentation` - 文档改进
- 🎨 `ui/ux` - 用户界面改进
- 🔧 `refactor` - 代码重构
- 🧪 `testing` - 测试相关

### 2. 创建分支

```bash
# 确保在主分支上
git checkout main
git pull upstream main

# 创建功能分支
git checkout -b feature/your-feature-name
# 或修复分支
git checkout -b fix/issue-number-description
```

### 3. 开发代码

```bash
# 编写代码
# 添加测试
# 更新文档

# 提交更改
git add .
git commit -m "feat: 添加新功能描述"
```

### 4. 推送分支

```bash
# 推送分支到您的 fork
git push origin feature/your-feature-name
```

### 5. 创建 Pull Request

1. 访问您的 GitHub 仓库
2. 点击 "Compare & pull request"
3. 填写 PR 描述：
   - 描述更改内容
   - 关联相关 Issue
   - 添加测试说明
4. 提交 PR

### 6. 代码审查

- 等待维护者审查
- 根据反馈修改代码
- 讨论和完善实现
- 获得批准后合并

## 📏 代码规范

### Python 代码规范

项目遵循 PEP 8 标准，使用 Black 进行代码格式化：

```bash
# 安装格式化工具
pip install black flake8 pylint

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

Author: 您的姓名
Date: 2025-09-20
"""

import os
import sys
from typing import Optional, List, Dict, Any

# 常量定义
DEFAULT_CONFIG = {
    'host': 'localhost',
    'port': 3306
}

class DatabaseManager:
    """
    数据库管理器类

    负责数据库连接和查询操作

    Attributes:
        config: 数据库配置字典
        connection: 数据库连接对象
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化数据库管理器

        Args:
            config: 数据库配置字典，如果为None则使用默认配置
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

    def query(self, sql: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """
        执行查询

        Args:
            sql: SQL 查询语句
            params: 查询参数列表

        Returns:
            List[Dict[str, Any]]: 查询结果列表

        Raises:
            DatabaseError: 数据库操作错误
        """
        # 查询逻辑
        pass
```

### 错误处理

```python
def safe_database_operation() -> Any:
    """
    安全的数据库操作示例

    Returns:
        Any: 操作结果

    Raises:
        DatabaseConnectionError: 数据库连接错误
        QueryError: 查询错误
        SystemError: 系统错误
    """
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

## 📝 提交规范

### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型说明

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复bug |
| `docs` | 文档更新 |
| `style` | 代码格式调整 |
| `refactor` | 代码重构 |
| `test` | 测试相关 |
| `chore` | 构建过程或工具配置 |
| `perf` | 性能优化 |
| `ci` | CI/CD相关 |
| `revert` | 回滚提交 |

### 提交示例

```bash
# 新功能
git commit -m "feat(auth): 添加用户登录功能

- 实现用户名密码登录
- 添加会话管理
- 支持记住登录状态"

# 修复bug
git commit -m "fix(api): 修复用户数据查询错误

修复了用户列表分页查询时的数据偏移问题
Closes #123"

# 文档更新
git commit -m "docs(readme): 更新部署指南

- 添加Docker部署说明
- 更新环境要求
- 补充故障排除指南"
```

### 分支命名

```bash
# 功能分支
feature/add-user-authentication
feature/improve-data-visualization

# 修复分支
fix/database-connection-issue
fix/memory-leak-in-crawler

# 文档分支
docs/update-api-documentation
docs/add-contributing-guide

# 重构分支
refactor/optimize-database-queries
refactor/split-large-functions
```

## 🧪 测试要求

### 单元测试

```python
# tests/test_database.py
import unittest
from unittest.mock import Mock, patch
from utils.query import querys

class TestDatabase(unittest.TestCase):
    """数据库模块单元测试"""

    def setUp(self) -> None:
        """测试前准备"""
        self.test_config = {
            'host': 'localhost',
            'user': 'test',
            'password': 'test',
            'database': 'test_db'
        }

    def tearDown(self) -> None:
        """测试后清理"""
        pass

    @patch('utils.query.pymysql.connect')
    def test_query_success(self, mock_connect: Mock) -> None:
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
    def test_query_error(self, mock_connect: Mock) -> None:
        """测试查询错误情况"""
        mock_connect.side_effect = Exception("Connection failed")

        with self.assertRaises(Exception):
            querys("SELECT * FROM users")

if __name__ == '__main__':
    unittest.main()
```

### 运行测试

```bash
# 运行所有测试
python -m pytest

# 运行特定测试文件
python -m pytest tests/test_database.py

# 运行带覆盖率
python -m pytest --cov=utils --cov-report=html

# 运行特定测试类或方法
python -m pytest tests/test_database.py::TestDatabase::test_query_success -v

# 运行标记的测试
python -m pytest -m "slow"  # 运行慢速测试
python -m pytest -m "not slow"  # 排除慢速测试
```

### 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=. --cov-report=html

# 查看覆盖率报告
# 打开 htmlcov/index.html
```

### 集成测试

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

## 🐛 问题反馈

### 报告 Bug

1. **检查现有 Issues**
   - 搜索是否已有相同问题

2. **创建新 Issue**
   - 使用 `Bug report` 模板
   - 提供详细的错误信息
   - 包含复现步骤
   - 添加环境信息

3. **Bug 报告模板**
   ```markdown
   ## Bug 描述
   简要描述问题

   ## 复现步骤
   1. 进入 '...'
   2. 点击 '....'
   3. 出现错误

   ## 预期行为
   应该发生什么

   ## 实际行为
   实际发生了什么

   ## 环境信息
   - OS: [e.g. Windows 10]
   - Browser: [e.g. Chrome 91]
   - Python: [e.g. 3.9]
   - MySQL: [e.g. 8.0]

   ## 附加信息
   错误日志、截图等
   ```

### 功能请求

1. **检查现有功能**
   - 确认功能不存在

2. **创建功能请求**
   - 使用 `Feature request` 模板
   - 详细描述功能需求
   - 说明使用场景
   - 提供设计建议

## 📋 Pull Request 模板

### PR 标题格式
```
<type>(<scope>): <description>
```

### PR 描述模板
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

## 截图 (如果适用)
添加相关截图

## 关联 Issue
Closes #123
```

## 🎯 行为准则

### 我们的承诺

我们致力于为所有人提供一个无骚扰的社区环境。我们承诺，无论年龄、体型、残疾、民族、性别认同和表达、经验水平、教育背景、社会经济地位、国籍、个人外貌、种族、宗教或性认同和取向如何，都不会对贡献者进行任何形式的骚扰。

### 我们的标准

积极行为包括：
- 使用友好和包容性的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

不允许的行为包括：
- 使用性化语言或图像
- 进行人身攻击或政治攻击
- 公开或私下骚扰
- 发布他人的私人信息，如物理或电子地址
- 其他有理由认为不适当的行为

### 责任和后果

社区维护者负责澄清和执行可接受行为的标准，并对任何不可接受行为采取适当和公平的纠正措施。

社区维护者有权并有责任删除、编辑或拒绝评论、提交、代码、wiki 编辑、问题和其他不符合本行为准则的贡献。

## 📞 获取帮助

如果您有任何问题或需要帮助：

1. 查看 [文档](../../docs)
2. 搜索现有 [Issues](../../issues)
3. 在 [Discussions](../../discussions) 中提问
4. 联系维护者

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者！

---

**最后更新**: 2025年9月20日