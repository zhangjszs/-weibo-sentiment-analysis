# 微博舆情分析系统：全面审查与改进计划（持续更新）

## 目标
- 安全：最小权限、统一鉴权、避免敏感信息泄露
- 可靠性：可观测、可回滚、可定位（request_id）、健康检查分层
- 功能一致性：统一 API 响应协议与错误语义
- 体验：图表与列表联动、局部加载优先、暗黑模式一致

## 已落地改进（本轮）

### API 协议与数据接口
- `/api/*` 与 `/getAllData/*` 统一返回 `code/msg/data/timestamp`，并新增 `request_id`（同时写入 `X-Request-Id` 响应头）
- 新增 `/api/comments`：评论分页、关键词/用户/文章ID/时间筛选
- `/api/articles` 增强：支持 `type/region` 筛选

相关代码：
- 后端响应封装：[api_response.py](file:///d:/coding/Pycharm/%E5%9F%BA%E4%BA%8Epython%E5%BE%AE%E5%8D%9A%E8%88%86%E6%83%85%E5%88%86%E6%9E%90%E5%8F%AF%E8%A7%86%E5%8C%96%E7%B3%BB%E7%BB%9F/src/utils/api_response.py)
- `/getAllData` 蓝图：[data_api.py](file:///d:/coding/Pycharm/%E5%9F%BA%E4%BA%8Epython%E5%BE%AE%E5%8D%9A%E8%88%86%E6%83%85%E5%88%86%E6%9E%90%E5%8F%AF%E8%A7%86%E5%8C%96%E7%B3%BB%E7%BB%9F/src/views/data/data_api.py)
- `/api` 蓝图：[api.py](file:///d:/coding/Pycharm/%E5%9F%BA%E4%BA%8Epython%E5%BE%AE%E5%8D%9A%E8%88%86%E6%83%85%E5%88%86%E6%9E%90%E5%8F%AF%E8%A7%86%E5%8C%96%E7%B3%BB%E7%BB%9F/src/views/api/api.py)

### 鉴权与安全
- 修复 `/api/session/*` 与 `/api/*` 全局 JWT 拦截冲突：端点语义改为 JWT（避免“不可达/误判”）
- 爬虫管理接口增加管理员权限（overview/crawl/logs/status）
- 健康检查分层：`/health` 对外仅返回最小信息；`/api/health/details` 返回数据库统计并要求管理员
- 安全响应头增强：Referrer-Policy、Permissions-Policy、HSTS（生产且 HTTPS）、HTML 响应 CSP
- 新增 CSRFError 统一处理（页面/接口分别返回友好错误）

相关代码：
- 管理员装饰器：[authz.py](file:///d:/coding/Pycharm/%E5%9F%BA%E4%BA%8Epython%E5%BE%AE%E5%8D%9A%E8%88%86%E6%83%85%E5%88%86%E6%9E%90%E5%8F%AF%E8%A7%86%E5%8C%96%E7%B3%BB%E7%BB%9F/src/utils/authz.py)
- 应用入口/中间件/错误处理：[app.py](file:///d:/coding/Pycharm/%E5%9F%BA%E4%BA%8Epython%E5%BE%AE%E5%8D%9A%E8%88%86%E6%83%85%E5%88%86%E6%9E%90%E5%8F%AF%E8%A7%86%E5%8C%96%E7%B3%BB%E7%BB%9F/src/app.py)
- 爬虫管理 API：[spider_api.py](file:///d:/coding/Pycharm/%E5%9F%BA%E4%BA%8Epython%E5%BE%AE%E5%8D%9A%E8%88%86%E6%83%85%E5%88%86%E6%9E%90%E5%8F%AF%E8%A7%86%E5%8C%96%E7%B3%BB%E7%BB%9F/src/views/api/spider_api.py)

### 前端交互与可用性
- 图表点选联动列表：文章（日期/类型）、评论（用户活跃度）、舆情（饼图/趋势）、IP（地区）
- 任务中心页：爬虫概览/历史、日志查看、Celery task_id 查询与最近记录
- 管理员菜单联动：普通用户隐藏“爬虫管理/任务中心”，路由层也会拦截并回到首页
- 请求层默认不再弹全屏遮罩，仅显式 `fullscreen` 才启用
- 图表组件默认自动跟随暗黑模式
- 基础无障碍：focus-visible、侧边栏折叠按钮 aria 与键盘操作

## 风险清单（建议继续推进）

### 高优先级
- 管理端菜单与权限联动：前端根据登录用户标识隐藏/禁用管理入口（避免普通用户看到 403）
- 统一错误结构的完全收敛：将 `app.py` 中剩余 `jsonify({...})` 逐步替换为 `ok/error`（包含 request_id）
- 对外爬虫依赖与限流：为爬虫触发增加频率限制与并发上限（防止误触导致封号/资源耗尽）

### 中优先级
- 观测：结构化日志（JSON）+ 关键指标（请求耗时、DB 耗时、爬虫耗时）
- 数据层：慢查询治理与索引审查（article/comments 表：created_at、type、region、rootId、user）
- 安全头策略收紧：逐步收紧 CSP（移除 unsafe-inline），并补齐 COOP/CORP 等策略

### 低优先级
- 前端骨架屏体系化：DataTable/卡片统一 Skeleton 组件
- 端到端测试：关键路径（登录、爬虫触发、图表联动、导出）

## 工程化（本轮新增）
- pytest 基础用例：覆盖 `api_response` 的 request_id 注入与 `admin_required` 权限装饰器
- pytest 配置：`pytest.ini` 统一测试入口与 `PYTHONPATH=src`

