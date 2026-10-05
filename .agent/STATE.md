# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：**本轮 5 个 issue 全部处理完**——#43 浏览器冒烟、#44 GET envelope 契约、
  #47 写接口契约、#45 字段契约、#46 Redis 降级文档，全部完成并转 in-review
  待 Planner 验收；另立 auto-discovered #52（大屏空数据 addColorStop 异常）、
  #53（大屏 trend 形状漂移：前端读 positive/neutral/negative、后端返 counts）
- 状态：执行会话 `executor-glm-20261005T0714Z` 收尾释放锁。
  **ready 队列已清空**（#48~#51 为候补），下一棒应为 Planning：验收 M3
  五项 + 治理 #52/#53 + 决定候补递补

## 阻塞项
- 无阻塞。CI 三 job 绿（#45/#47 推送后实证）；fast gate 基线推进至
  **1461 passed（+1 strict xfail）**；前端三门禁与 75 测试未动。

## 关键事实（已实测验证）
- **真实浏览器冒烟环境可搭建**（#43）：Playwright 已装进 `.venv`（chromium
  用 `~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome` 现成缓存，
  `p.chromium.launch(executable_path=...)` 指定即可）；后端 SQLite 文件库
  （ORM `import models` + `init_db()` 自举，**必须先 import models** 否则
  Base 空注册）；demo admin 需手动造（`ensure_demo_admin` 的 `NOW()` 在
  SQLite 不存在——既有缺陷未修）；AUTO_CREATE_DEMO_ADMIN 等环境变量 shell
  导出可覆盖 .env（python-dotenv 不覆盖已存在变量）
- **契约测试三件套已就位**：`test_api_get_contract.py`（51 GET 路由 ×
  匿名/非管理员/管理员三视角）、`test_api_write_contract.py`（31 写路由 +
  10 成功路径 + broker 降级判例）、`test_api_field_contract.py`（14 端点
  逐字段，来源标注到前端文件:行号）。全部从 url_map 机器枚举，新增路由
  自动纳入契约
- **两处 500-HTML 缺陷已修**：任务状态查询 Redis 不可用（#44，
  TaskStatusUnavailable → 503）；任务提交 broker 不可用（#47，
  spider_task_service/nlp_task_service 提交点转内建 ConnectionError →
  路由既有 503 分支）。修复前这 6 条路由返回 Werkzeug HTML 调试页
- **测试环境 celery 是 eager/memory 模式，不触真实 broker**：测 broker
  降级必须 patch 任务对象抛 OperationalError（`TestBrokerDegradationContract`
  有范例）；同理反例验证不能只靠坏输入
- **探测脚本「token 中毒」坑**：`/api/auth/logout` 在公开白名单且会拉黑
  所带 Bearer 的 jti；`/api/session/extend` 会轮换拉黑旧 jti——按字母序
  探测时这两条会把共享 token 毒掉，其后所有路由假 401。探测需用新 token
  且把这两条排最后
- **大屏 trend 形状漂移（#53，未修）**：前端读 positive/neutral/negative
  （useBigScreen.js:219），后端两条路径都只返 {times, counts}；前端拿不到
  就回退硬编码假数据 → 大屏趋势面板永远显示静态数字。评论表无情感标注列，
  修法需产品决策（后端补标注链路 vs 前端改单系列）
- **登录锁定/限流/WS 广播/通知队列/爬虫运行态从来不用 Redis**（#46 核实）：
  均为进程内存，多 worker 一致性缺口与 Redis 配置无关，详见
  docs/DEPLOYMENT.md「Redis 依赖与降级行为」一节
- **strict-xfail 是钉已知漂移的手段**：#45 用
  `@pytest.mark.xfail(strict=True, reason=...)` 标注 #53 漂移，修复落地时
  XPASS 使门禁变红，强制把断言转正
- Flask `Rule.build()` 在部分 rule 上返回空路径——契约枚举用正则替换
  `<arg>`/`<converter:arg>`（两个契约测试文件里的 `_ARG_RE` 可复用）
- **user 模型自定义 `__init__` 不收 id**：造数用
  `u = User(username=...); u.id = 1` 再 add
- 本轮新装依赖：playwright 进 `.venv`（**未写 requirements-dev.txt**，
  因属本机冒烟工具而非项目测试依赖——如 Planner 认为应入版本控制请指示）
- `main` 未设分支保护，可直接推送
- backend-fast / frontend-fast / integration 全绿；commit 一律 `Refs #N`
  （不自动关闭），`.agent/` 变更单独 `chore(agent):` 提交
- 命令行 `-q` 与 pytest.ini addopts 叠成 `-qq` 会吞汇总行：看计数用
  `-o addopts="" -q`（本会话再次验证）

## 已完成
- **#46 完成转 in-review**：docs/DEPLOYMENT.md 新增「Redis 依赖与降级行为」
  一节（6 类依赖点逐项核实 + 附加发现 _spider_state + 无 Redis 失效保证
  汇总 + 最低部署建议）；零代码变更（1 commit 8930090）
- **#45 完成转 in-review**：字段契约 14 端点逐字段钉住（消费方标注到
  前端文件:行号）；trend 漂移立 #53 并 strict-xfail；反例（改名
  today_articles）红→绿（1 commit c5efd93）；fast gate 1460+1xfail
- **#47 完成转 in-review**：写路由契约 31 条三视角 + 10 成功路径；修复
  broker 不可用 5 条写路由 HTML 500 → 503 envelope；反例红→绿
  （1 commit b2a52e3）；fast gate 1446；CI 绿
- **#44 完成转 in-review**：GET envelope 契约 51 路由三视角 + 5xx 豁免表；
  修复 tasks/status HTML 500 → 503（TaskStatusUnavailable）、
  get_database_stats StaticPool 兼容；反例红→绿（1 commit 7261b53）；
  fast gate 1376；CI run 37280477839 绿
- **#43 完成转 in-review**：真实浏览器冒烟（headless Chromium + Playwright），
  登录→表格页→大屏直达→ip 页全路径，地图渲染/组件解析/console 零新增错误
  全部实证（截图 6 张 + JSON 报告存 .pytest_tmp/smoke/，gitignored）；
  auto-discovered #52（大屏空数据 addColorStop 未捕获异常）；零代码变更
- #42 调研交付（不关闭）：验证码三候选对比表（图形/滑块/云服务 × 5 维度）+
  国内可用性核实（Turnstile 官方不支持大陆、reCAPTCHA 被墙、国产商业方案
  国内最优但与内网部署互斥）+ 触发条件 3 条 + 推荐「维持不上」（相对现有
  失败锁定+限流+审计的边际增益不划算）。评论见 issue #42（2026-10-02T16:2xZ）
