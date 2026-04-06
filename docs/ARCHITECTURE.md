# 微博舆情分析系统架构文档 (2026版)

## 1. 历史问题与解决状态

### 1.1 核心问题追踪

| 问题 | 严重等级 | 状态 | 解决方案 |
| ---- | -------- | ---- | -------- |
| **高耦合**: Views 层承担 Controller、Service、DAO 全部职责 | 高 | ✅ 已解决 | 引入 `repositories/` 层解耦数据访问，`services/` 层承接业务逻辑 |
| **贫血模型**: `src/model` 仅用于数据分析，缺乏业务实体定义 | 高 | ✅ 已解决 | `services/` 层封装业务逻辑，定义 `User`、`Article` 等领域实体 |
| **自定义 pymysql**: 使用自定义连接池，缺乏 ORM 支持 | 高 | ✅ 已解决 | 完全迁移至 SQLAlchemy 2.0，自定义 `DatabasePool` 已删除 |
| **同步阻塞**: 爬虫、NLP 等长耗时任务直接阻塞 HTTP 请求 | 中 | ✅ 已解决 | Spider/NLP 接口已支持统一任务编排，主路径通过任务状态接口异步追踪 |
| **部署脆弱**: 缺乏容器化支持，依赖手动部署 | 中 | ✅ 已解决 | 添加 `Dockerfile` 和 `docker-compose.yml`，CI/CD 流水线已配置 |

### 1.2 风险列表（当前状态）
| 风险项 | 严重等级 | 描述 |
| ------ | -------- | ---- |
| 接口变更破坏前端 | 高 | 缺乏契约测试，后端改动容易导致前端白屏 |
| 数据库性能瓶颈 | 中 | 缓存层尚未全面覆盖，复杂查询存在性能风险 |
| 扩展性演进 | 低 | Spider/NLP 已完成服务化入口，后续可按流量拆分部署与独立扩缩容 |

---

## 2. 当前架构

### 2.1 分层架构（已实现）

```
┌─────────────────────────────────────────┐
│           前端 (Vue 3 + Vite)            │
│         src/frontend/  (SPA)            │
└────────────────┬────────────────────────┘
                 │ HTTP / REST API
┌────────────────▼────────────────────────┐
│         Views / Controller 层            │
│  src/views/api/  (路由、参数校验、DTO)   │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│           Services 层                    │
│  src/services/  (业务逻辑、事务编排)     │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│          Repositories 层                 │
│  src/repositories/  (数据访问封装)       │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│            Models 层                     │
│  src/models/  (SQLAlchemy ORM 实体)      │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│            Database                      │
│  MySQL  (via SQLAlchemy 2.0 引擎)        │
└─────────────────────────────────────────┘

异步任务链路：
Views → Spider/NLP Task Service（本地 Celery / 独立服务）→ Queue (Redis) → Worker → Services → Repositories
```

### 2.2 当前技术栈

| 层次 | 技术 | 版本 |
| ---- | ---- | ---- |
| Web 框架 | Flask | 3.1 |
| ORM | SQLAlchemy | 2.0 |
| 异步任务 | Celery + Redis | — |
| 前端 | Vue 3 + Vite | — |
| 容器化 | Docker + Docker Compose | — |
| CI/CD | GitHub Actions + Pytest | — |

---

## 3. 演进路线图 (Milestones)

### Phase 1: 解耦与分层 (已完成)
- [x] 建立 `Repository` 层，封装 SQL 操作。
- [x] 建立 `Service` 层，剥离 `Views` 中的业务逻辑。
- [x] 重构 `Auth` 和 `Article` 相关接口。

### Phase 2: 云原生化 (已完成)
- [x] 添加 `Dockerfile` 和 `docker-compose.yml`。
- [x] 配置 CI/CD 流水线 (`.github/workflows`)。

### Phase 3: 深度 DDD 重构 (已完成)
- [x] 统一数据访问层：使用 SQLAlchemy 2.0 替换自定义 pymysql 连接池。
- [x] 定义 `User`、`Article` 等领域实体。
- [x] 引入 `Domain Event` 解耦业务副作用（已接入 Spider 入库后缓存清理流程）。

### Phase 4: 微服务拆分 (长期目标)
- [x] 将 `Spider` 模块拆分为独立服务（新增 `spider_service` HTTP + Worker 形态，主应用可通过配置切换远程调度）。
- [x] 将 `NLP Analysis` 拆分为独立服务（新增 `nlp_service` HTTP + Worker 形态，主应用通过 `nlp_task_service` 与统一任务状态查询接入远程调度）。

---

## 4. 数据访问层说明

数据访问层统一使用 SQLAlchemy 2.0（`src/utils/query.py`）。`engine`（连接池）和 `db_session`（scoped_session）是唯一的数据库访问入口。`querys()` 和 `query_dataframe()` 提供向后兼容的函数接口，内部均通过 SQLAlchemy engine 执行。

自定义 `DatabasePool`（pymysql）和备用连接机制已于 S10 整改中删除。

---

## 5. 性能基准与验收标准
- **API 延迟**: P99 < 200ms（通过 Redis 缓存实现）。
- **错误率**: < 0.1%。
- **测试覆盖率**: 核心业务模块 > 80%。

---

## 6. 关键目录说明
- `src/repositories/`: 数据访问层，封装所有 DB 查询。
- `src/services/`: 业务逻辑层，事务编排与领域规则。
- `src/views/api/`: 瘦 Controller，仅保留路由与参数校验。
- `src/models/`: SQLAlchemy ORM 实体定义。
- `src/utils/query.py`: SQLAlchemy engine 与 session 统一入口。
- `Dockerfile` / `docker-compose.yml`: 标准化容器交付物。
