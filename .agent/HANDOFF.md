# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `glm-20260930T154700Z`（GLM），UTC 2026-09-30T15:47 ~ 2026-10-01T00:4x。
第二棒。第一棒（DeepSeek-V4.1-Flash）解开了积压的 17 个 commit 并把
fast gate 清绿，留下 #30 作为当前活跃任务。

## 做了什么

### 一句话

修完 **#30 的全部三类 integration 失效**（27 failed → 0），
**CI 三 job 首次全绿**（含 integration/MySQL），#30 已关闭。

### 细节（三类根因互不相同，三个 commit）

1. **`test_nlp_service_passthrough.py` sys.modules 污染（16 个）→ 7a093e5**
   模块顶层 pop `app*`、插 nlp_service path，导致 conftest `app` fixture
   重导入 `src/app.py` 后，测试里 `patch("app.tasks.*")` 解析到单模块 `app`
   （没有 tasks 属性）→ 16 个用例顺序敏感失败。改为 importlib 以私有名
   `_nlp_tasks_under_test` 从文件路径加载，patch 点同步改名。

2. **echarts/table patch 目标消失（9 个）→ 4819d75**
   #14 重构删了 `query_dataframe`，用例改 patch `ArticleRepository` /
   `CommentRepository` 具体方法；直方图类在 `database.engine` 边界注入假
   连接（生产端 CASE WHEN 分桶 + 标签构建真实执行）。原断言与"不全表扫描"
   守卫全部保留。另发现 getHomeData 带 `@cache_result` 的函数会把 fake
   结果缓存泄漏给后续用例，进出各清一次 `clear_all_cache()`。

3. **bigscreen 500（2 个）→ 7b9d4b4（最重要的发现）**
   不是生产缺陷，是**两层测试基建缺陷**：
   - 测试会话从没人建表（schema 归 init_database.sql + alembic）；
   - fixture 调 `database.reset()` 会 dispose engine，而 `repositories/`
     在首次 import 时已 `from database import db_session` **捕获旧
     scoped_session**——第二个测试起全部仓储查询打到空库。
   修法：fixture 不再调 reset()，全进程复用同一 engine；sqlite 每测试
   drop+create，MySQL 只 create_all 补缺表（checkfirst 幂等）。
   **⚠️ 勿轻易回退此改动**：任何想恢复 "每测试 reset" 的做法都会复活
   顺序敏感失败；若嫌 drop+create 慢，先想清楚 stale binding 问题。

### 验证

- 本地 `pytest -m integration`：**189 passed, 5 skipped**（修复前 27 failed）
- 顺序无关：正序 / 乱序 / 倒序文件顺序结果一致；4 个文件单独跑均绿
- fast gate 无回退：1263 passed, 3 skipped；ruff 0
- CI run 36741984139：backend-fast / frontend-fast / integration(MySQL) 全绿

## 额外收获

- **Security Scan 首次转绿**（7b9d4b4 上 success）。第一棒记录它"每次都红"，
  本次推 main 后通过。只有一次样本，是否稳定待下一棒观察；若又红，看
  `.github/workflows/security-scan.yml`。

## 本轮遇到的遗留物（已处理）

- 工作区有一处**未记录在 STATE/HANDOFF 的 pytest.ini 改动**（addopts 加
  `-p no:launch_testing -p no:launch_ros`，注释说是屏蔽 ROS 2 插件）。
  实测本环境撤销它 pytest 照常收集，非必需。按协议保存到本地分支
  `wip/20260930T154700Z`（commit 73cd2a7，未推送）。若那是人工有意改动，
  请人工确认后自行处理；无关本轮，勿混入任务 commit。

## 下一步建议

1. **#19（High，前端）**：Loading 永不触发 + 大面积静默失败 + 空状态缺失。
   纯前端任务，验证走 `cd frontend && npm run test:run` + `npm run lint`
   + `npm run build`（注意 mise node PATH，见 ENV.md）。
2. #20（High，前端）：WebSocket 死链 + SW 缓存鉴权接口 + 裸 fetch。
   与 #19 都在 frontend/，可一并熟悉代码后顺序处理。
3. #15（Medium，后端 JWT）：aud/iss、jti 校验、logout 作废、extend 旋转。
4. #21（Medium，前端死依赖）/ #16（Low，文档漂移）/ #28（Low，alembic 杂项）。

## 阻塞 / 风险

- 无环境阻塞。
- 风险：integration 在 CI 的 MySQL 上只验证了一次（绿）。conftest 的
  create_all 在 MySQL 上是 checkfirst 补缺表，不会破坏迁移 schema；
  若未来 CI 突然红，先对比本地 SQLite 与 CI MySQL 的差异。

## 环境备注

- 后端 `.venv` 齐全（Python 3.12），fast gate 与 integration 本地均可跑。
- **前端 node 必须走 mise 的 PATH**：`export PATH="$HOME/.local/share/mise/installs/node/22.23.2/bin:$PATH"`。
- 想看全部失败用例要 `-o addopts="-q"`（pytest.ini 的 addopts 自带 `--maxfail=1`）。
- 本地有真实 `.env`（含密钥，**勿提交**），会影响起子进程的用例。
- gh 可用（账号 zhangjszs）。
