# 📏 编码规范 (Coding Standards)

本文档定义项目的编码规范和文件组织标准。

## 🛠️ 工具链

| 工具 | 用途 | 配置文件 |
|------|------|----------|
| Black | 代码格式化 | `pyproject.toml` |
| isort | 导入排序 | `pyproject.toml` |
| Ruff | 代码检查 | `pyproject.toml` |
| pre-commit | Git 钩子 | `.pre-commit-config.yaml` |

### 安装

```bash
pip install -r requirements/requirements-dev.txt
pre-commit install
```

---

## 📁 文件组织

```
root/
├── src/                    # 源代码
│   ├── config/             # 配置管理
│   ├── model/              # 情感分析模型
│   ├── spider/             # 网络爬虫
│   ├── services/           # 业务逻辑
│   ├── tasks/              # 异步任务
│   ├── utils/              # 工具函数
│   ├── views/              # 路由控制器
│   ├── static/             # 静态资源
│   └── templates/          # HTML 模板
├── tests/                  # 测试文件
├── docs/                   # 文档
├── scripts/                # 运维脚本
└── 数据库/                 # 数据库脚本
```

---

## 🐍 Python 规范

### 命名约定

```python
# 变量/函数: snake_case
user_name = "john"
def get_user_data(): pass

# 类: PascalCase
class UserManager: pass

# 常量: UPPER_CASE
MAX_RETRY_COUNT = 3

# 私有成员: 前缀下划线
_internal_cache = {}
def _helper_function(): pass
```

### 文件头模板

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块名称
功能：简要描述
作者：微博舆情分析系统
"""
```

### 导入顺序（isort 自动处理）

```python
# 1. 标准库
import os
import sys
from typing import Optional, List

# 2. 第三方库
import pandas as pd
from flask import Flask

# 3. 本地模块
from config.settings import Config
from utils.query import querys
```

### Docstring 格式

```python
def query_data(sql: str, params: Optional[List] = None) -> List[Dict]:
    """
    执行数据库查询
    
    Args:
        sql: SQL 查询语句
        params: 查询参数
        
    Returns:
        查询结果列表
        
    Raises:
        DatabaseError: 数据库错误
    """
    pass
```

---

## 🔧 使用指南

### 格式化代码

```bash
# 格式化所有文件
black src/ tests/
isort src/ tests/

# 检查代码（不修改）
black --check src/
ruff check src/
```

### 提交代码

```bash
# pre-commit 自动运行检查
git add .
git commit -m "feat: 添加新功能"
```

提交格式: `<type>(<scope>): <description>`

| 类型 | 说明 |
|------|------|
| feat | 新功能 |
| fix | 修复 |
| docs | 文档 |
| style | 格式 |
| refactor | 重构 |
| test | 测试 |

---

**相关文档**: [DEVELOPMENT.md](DEVELOPMENT.md) | [CONTRIBUTING.md](CONTRIBUTING.md)
