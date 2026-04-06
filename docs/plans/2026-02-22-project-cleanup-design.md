# 项目系统性整理设计文档

**日期**: 2026-02-22
**作者**: Kiro
**状态**: 已批准，待实施

---

## 背景

项目采用逐步开发方式推进，经审计发现以下问题：

- 部分模块仍残留 pymysql `DatabasePool` 引用（SQLAlchemy 迁移未完全收尾）
- API 响应格式不统一（部分端点未使用 `api_response` 工具函数）
- 错误处理策略分散（try-catch 散落各处，无全局异常处理器）
- 文档与当前代码实现存在偏差（API.md、ARCHITECTURE.md）
- 测试覆盖率目标仅 50%，核心服务缺乏充分测试

---

## 目标

使项目整体达到：结构清晰、规范统一、文档准确、测试充分、易于维护。

---

## 整理方案：顺序分阶段清理

每阶段完成后运行 `pytest` 验证无回归，再进入下一阶段。

---

### 阶段 1 — 代码格式化与风格统一

**后端**
- 对 `src/` 全部 Python 文件运行 `ruff --fix` + `black` + `isort`
- 修复 `pyproject.toml` 中已配置但未强制执行的 lint 规则
- 确保 pre-commit hooks 配置正确可用

**前端**
- 对 `frontend/src/` 下所有 `.vue`/`.js` 文件运行 `prettier --write`
- 统一 `.editorconfig` 与 vite/eslint 配置一致性

**验收标准**: `ruff check src/` 零警告，`prettier --check frontend/src/` 零差异

---

### 阶段 2 — 废弃代码清理 & SQLAlchemy 迁移收尾

- 删除 `src/` 中残留的 pymysql `DatabasePool` 引用，统一使用 SQLAlchemy 2.0
- 删除 `docs/archive/` 中已过时的设计文档
- 清理 `cache/`、`logs/` 目录中的测试遗留文件（非运行时必要文件）
- 删除未使用的 import、死代码、注释掉的代码块

**验收标准**: `grep -r "DatabasePool" src/` 无结果，`pytest` 全部通过

---

### 阶段 3 — API 响应格式 & 错误处理统一

- 所有 `src/views/api/` 端点统一使用 `api_response.ok()` / `api_response.error()`
- 在 `src/app.py` 中建立全局 Flask `errorhandler`，消除散落的重复 try-catch
- 统一 HTTP 状态码使用规范（4xx 客户端错误，5xx 服务端错误）

**验收标准**: 所有 API 端点响应结构一致，`pytest tests/test_api_response.py` 通过

---

### 阶段 4 — 文档与代码对齐

- 更新 `docs/API.md` 使其与当前所有端点（含新增的 alert、report、propagation API）一致
- 更新 `docs/ARCHITECTURE.md` 反映已完成的 DDD 分层迁移现状
- 同步 `README.md` 中的目录结构描述与实际文件结构

**验收标准**: 文档中无失效的文件路径引用，API 文档端点与代码一一对应

---

### 阶段 5 — 测试覆盖率提升

- 将 `pyproject.toml` 中 `fail_under` 从 50% 提升至 80%
- 为以下核心服务补充单元测试：
  - `src/services/alert_service.py`（685 行，当前测试不足）
  - `src/services/sentiment_service.py`（473 行）
  - `src/services/propagation_service.py`（731 行，最大文件）
- 补充 `src/utils/` 关键工具函数的边界条件测试

**验收标准**: `pytest --cov=src --cov-fail-under=80` 通过

---

## 风险与约束

| 风险 | 缓解措施 |
|------|----------|
| 格式化引入语法错误 | 每阶段后运行完整测试套件 |
| 删除"废弃"代码实为仍在使用 | 删除前用 grep 确认无引用 |
| API 响应格式变更影响前端 | 前后端同步修改，保持字段结构不变 |
| 测试补充引入错误的 mock | code review 每个新测试文件 |

---

## 不在本次范围内

- 微服务拆分（长期目标，见 TODO.md Phase 4）
- WebSocket 异步重构
- 新功能开发
