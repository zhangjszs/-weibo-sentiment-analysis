# ABC 统一：API 前缀/认证、Schema 真相、前端分层

> 来源：2026-08-21 grill-with-docs（app 工厂后第二轮）。已定 Q1–Q7，见 CONTEXT.md 与 ADR 0002–0004。

## 上下文

- 锐评揭示三处承重债务：① `src/app.py:485` 三段 `startswith` 双轨认证与 `/getAllData` vs `/api` 双前缀 ② `database/*.sql` vs `alembic` 双真相 ③ `BigScreen.vue:1` 1399 行等前端单体。
- `0001-explicit-app-factory` 已落地，`run.py:18` 为唯一组合根，为本轮收敛铺垫。

## 目标

- 调用方只认 `/api/*` 单前缀；鉴权只认 JWT 单轨（`src/app.py:before_request` 统一装饰器）；Schema 只认 Alembic；前端按容器/图表/数据三层可复用。

## 非目标

- 不改业务语义（情感/传播/预警逻辑不变）；不一次性重写所有页面样式。

## 决策（已定）

- **A1** `/getAllData/*` 7 路由遷至 `/api/*`，过渡期保留 307 别名一版本，前端下版切完摘除（ADR 0002）。
- **A2** 认证统一 JWT，`/page/*` 仅保留 `/user/login|/register` 直出（ADR 0002）。
- **A3** 蓝图合并：`spider_api`/`spider_routes` 等同名蓝图合并为 `api` 单蓝图。
- **C1** Alembic 单一真相，`database/*.sql` 归档 `docs/database/`（ADR 0003）。
- **C2** 补一版 `align_legacy_sql` 迁移对齐差异后冻结手写 SQL（ADR 0003）。
- **B1** 三层拆分 `components/charts/*` + `composables/useAnalysis`（ADR 0004）。
- **B2** `stores/analysis` SWR 缓存收敛高频轮询（ADR 0004）。

## 范围与阻塞边

```
A1 ──┬─→ B1 ─→ B2
     │
A2 ──┘
     └─→ A3

C1 ─→ C2   (与 A/B 无强依赖，可并行；但 C2 合并前避免与 A 的迁移并发)
```

- A1/A2 为根，无前置；B 依赖 A1（前端改前缀）；A3 依赖 A1/A2（蓝图重命名需前缀/鉴权先定）。
- C 轨与 A/B 无代码直接阻塞，可并行；建议 A1 落地后再合 C2 以避免迁移冲突。

## 验收

- `grep -r /getAllData frontend/src` 仅剩别名/兼容层注释；`curl /getAllData/getHomeData` 307 → `/api/...` 且鉴权同等。
- `src/app.py:before_request` 无三段 `startswith` 分支，改为装饰器/中间件单轨；`/page/*` 未登录直访非白名单返回 401 而非 302（由前端接管）。
- `database/*.sql` 不再被 `init_db`/`create_all` 以外代码引用；`alembic upgrade head` 在空库重放与现有库增量均可。
- `BigScreen.vue` < 400 行，图表抽至 `components/charts/*`，`stores/analysis` 覆盖 `/api/report/data` 等高频接口且测试覆盖 SWR。

## 风险

- 前端一次性改前缀需全量回归（`frontend/src/api/*` 7 文件）；别名期可灰度。
- 补迁移需在 `sqlite:///:memory:` 与 MySQL 双环境验证。

## 票据

见 `.scratch/abc-unification/issues/`（本地）或 GitHub Issues（`gh` 发布后带 blocking 链接）。
