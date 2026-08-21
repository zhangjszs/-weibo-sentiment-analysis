# 数据治理与合规 (Data Governance)

> **最后更新**: 2026-08-21（C1 归档：`database/*.sql` → `docs/database/`，Alembic 单一真相）

本文档定义微博舆情分析系统的数据分类、保留策略、脱敏规则和合规要求。

## 数据分类

| 类别 | 示例 | 敏感度 | 保留期 |
|------|------|--------|--------|
| **公开内容** | 文章正文、评论内容 | 低 | 按需（采集目的达成后可删除） |
| **用户信息** | 用户名、昵称、头像 | 中 | 与关联内容同生命周期 |
| **认证凭据** | Password hash、JWT、Cookie | 高 | 会话期间 |
| **审计日志** | 操作者、动作、时间、IP | 中 | 90 天（滚动删除） |
| **采集凭据** | WEIBO_COOKIE、API Token | 高 | 仅限运行时环境变量 |
| **演示数据** | 模拟生成的分析数据 | 低 | 无限制 |

## 脱敏规则

所有日志和输出必须经过以下脱敏：

1. **密码** — 任何形如 `password=...` 的字段替换为 `******`
2. **邮箱** — 保留前 3 字符 + `***` + 域名前 3 字符 + `***`
3. **手机号** — 保留前 3 位 + `***` + 后 2 位
4. **IP 地址** — 保留前两段，后两段替换为 `.***.***`
5. **身份证号** — 保留前 6 位 + `***` + 后 4 位
6. **JWT / Bearer Token** — 替换为 `Bearer ***`
7. **Cookie / Set-Cookie** — 值部分替换为 `***`

## 审计事件

以下操作必须记录审计事件：

| 事件 | 触发条件 | 记录字段 |
|------|----------|----------|
| `login` | 用户登录成功/失败 | user_id, username, ip, 成功/失败 |
| `logout` | 用户登出 | user_id, username |
| `export_report` | 报告导出 | user_id, topic, format |
| `delete_data` | 删除文章/评论/用户 | user_id, resource_type, resource_id |
| `spider_start` | 启动爬虫任务 | user_id, keyword, type |
| `config_change` | 修改关键配置 | user_id, config_key |

**禁止**：Cookie、Authorization header、原始敏感文本写入审计日志。

## 数据保留与删除

### 自动清理策略

- **审计日志**: 超过 90 天的记录自动删除
- **临时文件**: 报告生成产生的临时文件在 1 小时后清理
- **会话数据**: 24 小时无活动自动过期

### 手动删除

管理员可通过 API 或管理界面删除：
- 单条/批量文章
- 单条/批量评论
- 用户及其关联数据

## 合规要求

1. `.env` 和 `WEIBO_COOKIE` 不得提交到版本控制
2. 生产环境必须设置 `SECRET_KEY` 和 `JWT_SECRET_KEY`
3. 生产环境必须配置 `ALLOWED_ORIGINS` 白名单
4. 演示数据必须带 `is_demo: true` 标识和局限性说明
5. 报告必须包含来源、数据范围、局限性和生成时间

## Schema 真相源与归档策略（C1）

- **单一真相**：`alembic` 为建表/变更唯一路径（`alembic upgrade head`）。`src/database.py:init_db()` 仅调用 `Base.metadata.create_all`，不再直读 SQL 文件。
- **已归档**：原 `database/*.sql` 7 文件已冻结归档至 `docs/database/`（见 `docs/database/README.md`），仅作离线种子 / 审计对照，不再参与建表。
- **冻结规则**：归档后禁止再改 `docs/database/*.sql`；后续变更只走 `alembic revision --autogenerate` 并保证幂等（`information_schema` 检查），由 C2 迁移 `align_legacy_sql` 对齐历史差异。
- 参考：`docs/adr/0003-schema-single-truth-alembic.md`、`alembic/env.py`、`alembic.ini`。

## 配置项

```ini
# .env 中与合规相关的配置
DATA_RETENTION_DAYS=90          # 数据保留天数
AUDIT_LOG_RETENTION_DAYS=90     # 审计日志保留天数
REPORT_TEMP_CLEANUP_HOURS=1     # 报告临时文件清理间隔
LOG_SANITIZE_ENABLED=True       # 是否启用日志脱敏
```