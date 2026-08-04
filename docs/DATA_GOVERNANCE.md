# 数据治理与合规 (Data Governance)

> **最后更新**: 2026-08-03

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

## 配置项

```ini
# .env 中与合规相关的配置
DATA_RETENTION_DAYS=90          # 数据保留天数
AUDIT_LOG_RETENTION_DAYS=90     # 审计日志保留天数
REPORT_TEMP_CLEANUP_HOURS=1     # 报告临时文件清理间隔
LOG_SANITIZE_ENABLED=True       # 是否启用日志脱敏
```