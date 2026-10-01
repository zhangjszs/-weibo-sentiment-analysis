# 微博舆情分析系统

面向微博数据的采集、情感分析、传播与预警的可视化系统上下文。

## Language

### 应用启动

**引导**:
进程就绪前必须完成的幂等工作（配置校验、目录与日志就绪、演示账号检查）。
_Avoid_: 初始化、启动

**预热**:
进程就绪后为降低冷启动而后台执行的非必需优化（并发请求高频接口以填充缓存，配置门控）。
_Avoid_: 初始化、预加载

**启动状态**:
`startup_service` 对外暴露的 `admin_bootstrap + warmup` 可观测快照，供 `/api/startup/status` 查询。
_Avoid_: 健康检查、启动日志

## Architecture

两服务应用：Flask 后端（`src/`，入口 `run.py`）+ Vue 前端（`frontend/`）。
- 请求路径：`/api/*`（旧前缀 `/getAllData/*` 为 307 别名）→ 全局 JWT 单轨中间件（`app.py` before_request）→ 蓝图（`src/views/`）→ Service（`src/services/`）→ Repository（`src/repositories/`）→ SQLAlchemy。
- 情感分析：`sentiment_service/service.py` 按 mode 路由策略（custom=ML / simple=SnowNLP+词典 / smart=LLM / auto=自适应 / contextual），SnowNLP 为兜底。
- 异步：Celery（`src/tasks/`），Broker/Backend 见配置；认证：JWT（`utils/jwt_handler.py`，jti 黑名单撤销）。
- 数据库 schema 唯一真相：`docs/database/init_database.sql` 冻结 SQL + `alembic/` 迁移链。
- 更细的运维约定见 `AGENTS.md`；架构决策见 `docs/adr/`。
