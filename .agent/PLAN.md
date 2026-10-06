# PLAN — 开发路线图

> 规划 Agent 维护，每次会话滚动更新。执行 Agent 只读不写本文件。
> 方向类决策记录在 DECISIONS.md，本文件引用其编号（D-xx）。

## 当前方向

M3「后端 API 契约与测试强化」已验收结项（2026-10-06，5/5 issue + M2 遗留 #43 全部通过）。
**M4 方向待用户决策（D-06，pending）**；默认方案 = 质量巩固：消费 ready 队列三项低风险收尾
（#52 大屏空数据异常 → #54 死代码清理 → #55 控制台告警清理），#53（大屏趋势语义）按 D-07 待决。
当前无外部阻塞，LOCK 已释放，main 与 origin 同步（本轮起点 HEAD 75c851b）。

## 里程碑

### M1：质量债清偿与门禁体系（已完成）

- CI 三 job 连续绿；后端覆盖率门禁 60%；Bandit HIGH 门禁；前端 lint --max-warnings 0。
- 包含 #5~#38（全部 CLOSED，明细见 git 历史）。

### M2：前端性能与体验（已完成，2026-10-03 验收）

- #39 element-plus 按需加载（首屏 raw -76.1%）；#40 大 chunk 治理（ip chunk gzip -99.0%）
  + 大屏地图顺序依赖修复；#41 integration 覆盖率报告（D-04 不设阈值）。
- 遗留 #43（浏览器冒烟）已在 M3 期间完成并通过验收。

### M3：后端 API 契约与测试强化（已完成，2026-10-06 验收，D-05）

- 验收标准（全部达成）：
  - [x] #44 全量 51 个 `/api/*` GET 端点 envelope 表驱动契约，零未处理 5xx（2 处修复 + contentCloud 空数据语义移交 #45 钉住）
  - [x] #47 写路由契约 31 条三视角 + 10 条成功路径；5 条 broker 降级 HTML 500 全部转 503 envelope
  - [x] #45 14 个前端消费端点字段契约（发现 #53 trend 漂移，strict-xfail 钉住）
  - [x] #46 Redis 降级行为文档（DEPLOYMENT.md「Redis 依赖与降级行为」，6 类依赖点 + 多 worker 影响）
  - [x] 全程 CI 三 job 绿；基线推进：fast gate 1261 → **1463 passed + 1 strict xfail**；前端 75 → **77**
- 附带产出：#43 浏览器冒烟通过（地图截图核验）；新增门禁 3 道（#48 体积预算 / #51 format:check / #50 文档死链）；
  #49 vitest resolver 单源消除模板级解析盲区。
- 验收证据（Planner 本轮独立复验）：契约五套件 238 passed / 67 skipped / 1 xfailed 退出码 0；
  format:check 0、lint 0、test:run 77/77、doc-paths exit 0；#43 截图核验；CI HEAD 75c851b 三 job 全绿。

### M4：方向待定（D-06 pending，默认「质量巩固」）

- 默认范围：#52 + #55 + #54；#53 待 D-07 落地后实施。三项收尾完成后再议正式方向。

## 执行队列（给 Executor 的建议顺序）

1. #52 大屏空数据 addColorStop 未捕获异常修复（P3，ready-for-agent）
2. #55 前端控制台告警清理：TabBar markRaw / el-empty imageSize / favicon 404（P4，ready-for-agent）
3. #54 死代码清理：/api/stats/today、/api/bigscreen/all、AlertNotification.vue（P4，ready-for-agent）

- blocked：#53（needs-info，待 D-07 产品决策；strict-xfail 机制已钉住，修复落地时 XPASS 强制转正）。

## 已知阻塞与依赖

- 无外部阻塞。M4 正式方向等用户输入（D-06）；#53 等产品决策（D-07）；
  Redis 迁移方向记 D-08（pending，默认不动）。

## 下一阶段

- M4 收尾后候选同 D-06 备选：B 前端 TypeScript 渐进化（红线需授权）、
  C 部署/运维生产化（需可验证环境）、D 产品功能迭代（需具体需求）。

## 已放弃的方向

- 登录验证码实施（D-02：暂缓，#42 调研已闭合，触发条件成熟时另立实施 issue）。
- docs/database 归档 SQL 列名同步（D-03：保留不动）。

## 留白与人工事项（跨里程碑跟踪）

| 事项 | 状态 |
|------|------|
| safety 接 SAFETY_API_KEY | 人工操作 GitHub secret；无 key 则 safety 空报告（已有跳过门禁） |
| nginx /socket.io 握手 101 上线验证 | 需 Docker/线上环境，本地无法验证 |
| china.json 精度简化 | 数据取舍需产品决策；资产可缓存，暂不处理 |
| conftest 两套 SQLite 语义统一 | 测试架构取舍，无需求不动 |
| favicon 404 | 已并入 #55 |
| playwright 入库与否 | Planner 自决：暂维持 .venv 本地安装（冒烟非周期任务）；转常备验证手段时升格 dev 依赖并入 CI |
| 登录锁定/限流/WS 广播迁 Redis | D-08 pending（#46 已文档化多 worker 缺口）；默认暂不迁、不改行为 |
| wip/20260930T154700Z 本地分支 | 已核实 git 无此分支（2026-10-06），事项关闭 |

## 给 Executor 的指令

- 代码提交用 `Refs #N`，不用 `Closes`/`fix: #N`（关闭留给 Planner 验收）；`.agent/` 变更用 `chore(agent):` 且与代码不混提。
- 前端改动五门禁全跑（lint --max-warnings 0 / format:check / test:run 基线 77 / build / check:bundle），
  后端改动跑 fast gate（基线 1463 passed + 1 strict xfail）；判结果看退出码（管道用 `PIPESTATUS[0]`）。
- 跑后端测试会在 `src/data/` 留 commentsData.csv 未跟踪产物，勿提交。
