# 🚀 发布检查清单 (Release Checklist)

> **最后更新**: 2026-08-04

本文档是发布前的**唯一检查清单**。每次发布必须逐项通过，任何一项失败应阻止发布。

---

## 1. 准备工作

- [ ] 确认当前分支是 `main` 或 `release/*`
- [ ] 确认没有未提交的改动：`git status --short`
- [ ] 确认与远程同步：`git pull --rebase`

---

## 2. 数据库

### 2.1 迁移（Alembic 单一真相，见 docs/database/README.md）
- [ ] 运行所有等待中的 Alembic 迁移：`alembic upgrade head`
- [ ] 验证新增字段和表结构：`python scripts/check_db.py`
- [ ] 确认 `docs/database/init_database.sql`（已归档，只读）与当前 ORM/迁移一致（如不一致以 Alembic 为准）

### 2.2 备份
- [ ] 备份生产数据库：`mysqldump -u root -p wb > backup_$(date +%Y%m%d).sql`
- [ ] 确认备份文件大于 0 字节

## 3. 环境变量与密钥

- [ ] `.env` 文件存在且包含以下配置（**绝不**提交到版本控制）：
  ```ini
  SECRET_KEY=<随机生成>
  JWT_SECRET_KEY=<随机生成>
  DB_PASSWORD=<生产密码>
  WEIBO_COOKIE=<有效的微博 Cookie>
  ```
- [ ] `SECRET_KEY` 和 `JWT_SECRET_KEY` 使用随机密钥：
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] 生产环境 `FLASK_ENV=production`
- [ ] `ALLOWED_ORIGINS` 配置了正确的前端域名白名单
- [ ] `ADMIN_USERS` 配置了管理员用户名列表

## 4. 数据来源标识

- [ ] 所有 API 响应包含 `meta` 字段（含 `source_type`、`data_count`、`time_range`）
- [ ] 正式模式不会静默返回 mock 数据
- [ ] 演示模式需要显式 `demo=true` 触发
- [ ] 实验功能返回 `source_type: experimental`

## 5. 质量门禁

运行以下命令，全部通过后才能发布：

```bash
# 后端静态检查
python -m ruff check src tests

# 后端门禁测试
python -m pytest -m "unit or api" -q --maxfail=1

# 前端门禁
cd frontend
npm run lint
npm run test:run
npm run build
cd ..
```

- [ ] 全部测试通过
- [ ] 前端构建无报错
- [ ] Ruff 无错误（允许 warnings）

## 6. 构建

### 6.1 Docker 构建
```bash
# 构建并验证
docker compose build --pull
docker compose config
```

- [ ] Docker 构建成功
- [ ] `docker compose config` 无错误

### 6.2 前端构建
- [ ] `npm run build` 输出在 `frontend/dist/`
- [ ] 验证 `dist/index.html` 存在

## 7. Smoke Test

部署到目标环境后执行：

```bash
# 方式 A: 使用 smoke test 脚本
pwsh -NoProfile -File scripts/smoke_test.ps1 -BaseUrl http://your-domain.com

# 方式 B: 手动检查
curl -s http://your-domain.com/health          # 应返回 {"status":"ok"}
curl -s http://your-domain.com/ready            # 应返回 200 或 503（带 checks）
curl -s -o /dev/null -w "%{http_code}" http://your-domain.com/  # 应返回 200
```

- [ ] `/health` 返回 200
- [ ] `/ready` 返回 200（全部依赖正常）或 503（部分降级，带 `checks` 说明）
- [ ] 前端主页可正常打开
- [ ] 前端页面能正常加载 API 数据

## 8. 回滚计划

### 8.1 代码回滚
```bash
# 回滚到上一个版本
git revert HEAD
git push origin main

# 或直接回退
git reset --hard <上一个发布标签>
git push --force-with-lease origin main  # 注意：仅紧急情况下使用
```

### 8.2 数据库回滚
```bash
alembic downgrade -1   # 回滚一个迁移
```

### 8.3 容器回滚
```bash
# 启动上一个镜像
docker compose stop web frontend
docker compose rm web frontend
# 修改 docker-compose.yml 中的镜像标签
docker compose up -d web frontend
```

### 8.4 回滚检查
- [ ] 确认数据库迁移已回滚
- [ ] 确认 API 可访问
- [ ] 确认前端页面可打开

## 9. 发布后检查

- [ ] 日志中无异常错误
- [ ] 审计日志正常记录
- [ ] 采集服务正常运行
- [ ] 情感分析返回合理结果

## 10. 标签

```bash
git tag -a v1.0.0 -m "Release v1.0.0: 微博舆情分析系统"
git push origin v1.0.0
```

- [ ] Git tag 已创建并推送

---

## 快速参考

### 配置检查命令

```bash
# 检查所有配置项
python src/utils/config_validator.py

# 检查环境变量是否完整
python scripts/check_env.py

# 检查文档路径
python scripts/check_documented_paths.py
```

### 常用部署命令速查

| 操作 | 命令 |
|------|------|
| 启动所有服务 | `docker compose up -d` |
| 查看日志 | `docker compose logs -f web` |
| 重启后端 | `docker compose restart web` |
| 重新构建 | `docker compose build --pull web` |
| 停止所有 | `docker compose down` |
| 备份数据库 | `docker exec weibo-mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD} wb > backup.sql` |
| 进入容器 | `docker exec -it weibo-web bash` |

### 目录结构

```
微博舆情分析/
├── docker-compose.yml       # Docker Compose 编排
├── Dockerfile               # 后端容器镜像
├── frontend/
│   ├── Dockerfile           # 前端容器镜像
│   └── nginx.conf           # Nginx 配置（容器内使用）
├── scripts/
│   ├── start.bat            # Windows 本地启动
│   ├── start-frontend.bat   # 单独启动前端
│   ├── verify_project.ps1   # 质量门禁
│   ├── healthcheck.py       # 健康检查
│   └── smoke_test.ps1       # Smoke test
└── docs/
    ├── DEPLOYMENT.md        # 完整部署指南
    ├── LOCAL_DEPLOYMENT.md   # 无 Docker 部署
    └── RELEASE_CHECKLIST.md # 本文件
```