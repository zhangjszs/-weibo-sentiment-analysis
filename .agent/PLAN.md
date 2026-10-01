# PLAN — 开发路线图

> 规划 Agent 维护，每次会话滚动更新。执行 Agent 只读不写本文件。
> 方向类决策记录在 DECISIONS.md，本文件引用其编号（D-xx）。

## 当前方向

仓库已完成"质量债清偿"阶段（#5~#38 全部关闭，三道门禁全绿），
下一步方向**待用户确认**（候选：前端性能与体验 / 供应链安全二期 / 观察期），
确认后在此更新并引用决策编号。

## 里程碑

### M1：质量债清偿与门禁体系（已完成）

- 目标：主干 CI 稳定绿、测试/覆盖率/安全/lint 门禁全部真实生效。
- 验收标准：CI 三 job 连续绿 ✅（连续 10+ 次）；后端覆盖率门禁 60% ✅（#34/#35）；
  Security Scan 带 Bandit HIGH 门禁 ✅（#31/#32）；前端 lint --max-warnings 0 ✅（#37）；
  fast gate 1261 passed / integration 189 passed / 前端 73 tests。
- 包含 issue：#5~#38（全部 CLOSED，明细见 git 历史）。
- 进度：100%。

### M2：方向待定（本会话向用户征集，见 DECISIONS D-01）

- 候选 A：前端性能与体验 —— element-plus chunk 1.00MB / echarts 712KB / ip 页 585KB
  （gzip 后仍 200/242/199KB），按需加载与组件测试起步。
- 候选 B：供应链安全二期 —— pip-audit CVE 门禁（须先清点白名单）、safety 接
  SAFETY_API_KEY（人工 secret 操作）。
- 候选 C：观察期 —— 不立项，执行 Agent 主动发现模式跑数轮。
- 进度：0%（等 D-01）。

### 留白与人工事项（跨里程碑跟踪）

| 事项 | 来源 | 状态 |
|------|------|------|
| 验证码（登录防撞库） | #15 留白 | 待 D-02 决策；现有缓解：失败锁定 5 次/15min + IP 限流 + 登录审计 |
| docs/database 6 个历史归档 SQL 仍是旧列名 | #38 留白 | 待 D-03 决策（init_database.sql 是 CI 依赖，不可动） |
| integration job 覆盖率策略 | #38 留白 | 待 D-04 决策（现仅在 backend-fast 生效） |
| safety 接 SAFETY_API_KEY | #32 留白 | 人工操作 GitHub secret，无 key 则 safety 输出空报告（已有跳过门禁） |
| nginx /socket.io 握手 101 上线验证 | #20 留白 | 需 Docker/线上环境，本地无法验证 |
| WS 刷新后取 token 是否真缺 | #15 留白 | 执行 Agent 需先核实（getAuthToken 兜底可能已覆盖） |
| conftest 两套 SQLite 语义统一 | #28 留白 | 属测试架构取舍，无需求不动 |

## 远景（粗粒度）

- 前端：TypeScript 化与视图层组件测试（大工程，需单独立项排期）。
- 后端：REST API 契约测试全覆盖；Redis 不可用时的降级行为文档化。
- 运维：镜像多阶段构建瘦身（#27 已修 CUDA torch 拉取）、compose 一键生产化。

## 已放弃的方向

（暂无。后续放弃的方向在此登记并引用决策编号。）
