# 数据库 SQL 归档（已冻结）

> 状态：已归档，只读参考 — **不再是建表真相源**

## 归档原因

`database/*.sql`（7 文件）与 `alembic/versions/*`（4 迁移）长期双真相并存，建表来源不清，易导致 ORM ↔ SQL ↔ 迁移不一致。

- ADR：`docs/adr/0003-schema-single-truth-alembic.md`
- 计划：`docs/plans/2026-08-21-abc-unification.md`（C1）

决定以 **Alembic 为唯一真相源**；原 `database/*.sql` 于 `2026-08-21` 归档至 `docs/database/`，仅作 **离线种子 / 审计 / 回溯对照**。

## 当前真相源

- 建表 / 变更唯一路径：`alembic upgrade head`（`alembic/env.py` 读取 `src/database.py:Base.metadata` 与 `Config.get_database_url()`）
- 应用侧 `src/database.py:init_db()` 仅调用 `Base.metadata.create_all(bind=get_engine())`，**不再直读任何 SQL 文件**
- 测试 / CI：`TEST_DATABASE_URL=sqlite:///:memory:` + `Base.metadata.create_all()`；集成环境执行 `alembic upgrade head`

## 冻结策略

- 本目录下 7 个文件已 **冻结**，不再接受 DDL 变更：

  ```
  article.sql
  comments.sql
  database_indexes.sql
  init_database.sql
  new.sql
  optimize_indexes.sql
  user.sql
  ```

- 如需对照：以 Alembic 迁移为准，手写 SQL 仅作差异审计。
- 下一步（C2）：新增一次性迁移 `align_legacy_sql` 对齐两边差异（索引、字段类型等，含 `database_indexes.sql` 等）后，视同冻结完成；通过 `sqlite:///:memory:` 与 MySQL 双环境验证 `alembic upgrade head` 可重放。
- **后续变更规则：只走迁移** — 新建 `alembic revision --autogenerate -m "..."` 并补充幂等逻辑（已上线库 `information_schema` 检查），禁止再改归档 SQL。

## 迁移指南

- 本地空库验证：

  ```bash
  alembic upgrade head          # 或 python -c "from database import Base, get_engine; Base.metadata.create_all(get_engine())"
  ```

- 生产 / Docker：容器启动前执行 `alembic upgrade head`；`docker-compose.yml` 旧有的 `database/init_database.sql` 挂载已改为指向本归档路径，仅为历史兼容，**不应作为初始化依赖**。

- 归档 SQL 的离线使用（可选）：

  ```bash
  mysql -u root -p wb < docs/database/init_database.sql
  ```

  仅用于离线审计/演示种子；正式建表请走 Alembic。

## 验收

- `grep -r "database/.*\.sql\|init_database.sql" src` 0 命中（本 README 属 `docs/` 例外）
- `pytest -m "unit or api" -q` 绿
- `alembic upgrade head` 在空库可重放且与 `Base.metadata` 一致

## 参考

- `alembic.ini` / `alembic/env.py` / `alembic/versions/*`
- `src/database.py`（`init_db`, `Base`, `get_engine`）
