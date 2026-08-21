# Schema 单一真相：Alembic

`database/*.sql` 7 文件与 `alembic/versions/*` 4 迁移双真相并存，建表来源不清。决定以 Alembic 为唯一真相，现有 `database/*.sql` 归档至 `docs/database/` 仅作离线种子/审计，新增一版 `align_legacy_sql` 迁移对齐两边差异后冻结手写 SQL，后续变更只走迁移。
