# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：**候补 4 项全部完成**——#48 体积预算门禁、#49 vitest 共享 resolver、
  #50 文档路径校验误报修复+CI 接线、#51 Prettier 全量格式化+format:check
  入 CI，全部完成转 in-review 待 Planner 验收。**ready 队列已空**。
- 状态：执行会话 `executor-glm-20261006T0406Z` 收尾释放锁。
  下一棒应为 Planning：验收 in-review 累计 **9 项**（#43/#44/#45/#46/#47
  M3 五项 + #48/#49/#50/#51 质量四项）+ 定级 #52/#53 + 规划下一阶段。

## 阻塞项
- 无阻塞。CI 全绿（每项推送后实证）；fast gate 基线推进至
  **1463 passed（+1 strict xfail）**；前端测试 75 → **77**（#49 新增 2）、
  三门禁 + 体积门禁 + 格式门禁全绿。

## 关键事实（已实测验证）
- **前端五道门禁已成型**（CI frontend-fast 顺序）：lint --max-warnings 0 →
  **format:check（#51 新增）** → test:run 77 → build →
  **check:bundle 体积预算（#48 新增）**。backend-fast 首步新增
  **Documented paths check（#50）**。
- **体积预算口径**（#48）：判定用 dist/index.html 实载资源的 raw 字节
  （gzip 展示不判定）；预算 327,000/97,000 = 2026-10-06 实测基线
  273,199/81,228 × 1.2 向下取整千位；`frontend/bundle-budget.json` _meta
  注明来源与超限调整流程；反例（低预算/缺 dist）exit 1 实证。
- **vitest 与生产共用 resolver**（#49）：`frontend/config/components.mjs`
  工厂（importStyle 参数化，vitest 侧 false——样式导入会崩收集）；
  vitest.setup.js **移除全局全量 ElementPlus**（会掩盖 resolver 回归）；
  新测试 template-resolution.test.js 在移除 resolver 时实证变红。
  注意：`frontend/build/` 被 .gitignore 全局 build/ 规则吞掉，共享配置
  放 config/ 目录。
- **文档路径校验**（#50）：file:line 归一化 + <param> 路由忽略；原 5 个
  「缺失」全为误报，仓库无真实文档死链；接线选 CI 非 pre-commit
  （CI 不跑 pre-commit，钩子不保证安装）。
- **Prettier 格式化**（#51）：74 文件、净 -1579 行；**73/74 文件经
  「≡ prettier(HEAD 版本) 逐字节对比」证明仅格式化**（PredictInput.vue
  为 prettier 非幂等构造 `</el-icon`，两版均合法仅空白差异）；
  eslint 关闭 5 条与 prettier 冲突的 vue 纯格式规则（清单见
  eslint.config.js 注释）；format 脚本范围扩至 src/ tests/。
- **prettier 对某些 Vue SFC 非幂等**：批量 --write 后个别文件 --check
  仍可能报错，**再跑一遍 --write 即收敛**（幂等第二轮零 diff 后才提交）。
- **契约测试三件套 + 五道前端门禁之外的新基线**：后端 1463+1xfail、
  前端 77 tests、入口 chunk 273,199B / 首屏 CSS 81,228B（体积门禁盯住）。
- **大屏 trend 形状漂移（#53，未修）**：前端读 positive/neutral/negative
  （useBigScreen.js:219），后端两条路径都只返 {times, counts}；修法需
  产品决策（后端补标注链路 vs 前端改单系列），strict-xfail 钉住。
- **#52（未修）**：大屏空数据 echarts addColorStop 未捕获异常（pageerror
  级），空库/新装环境必现。
- **strict-xfail 是钉已知漂移的手段**：修复落地时 XPASS 使门禁变红，
  强制把断言转正。
- **user 模型自定义 `__init__` 不收 id**：造数用
  `u = User(username=...); u.id = 1` 再 add。
- **探测脚本「token 中毒」坑**：`/api/auth/logout` 与 `/api/session/extend`
  会拉黑/轮换共享 Bearer 的 jti，批量探测须用新 token 且把这两条排最后。
- **测试环境 celery 是 eager/memory 模式**：测 broker 降级必须 patch 任务
  对象抛 OperationalError（`TestBrokerDegradationContract` 有范例）。
- Flask `Rule.build()` 部分规则返回空路径——契约枚举用正则替换
  `<arg>`（契约测试文件里的 `_ARG_RE` 可复用）。
- **本机 shell 有 http_proxy 系变量**：curl localhost 加 `--noproxy '*'`。
- **登录锁定/限流/WS 广播/通知队列/爬虫运行态从来不用 Redis**（#46）：
  均为进程内存，详见 docs/DEPLOYMENT.md「Redis 依赖与降级行为」。
- `main` 未设分支保护，可直接推送；commit 一律 `Refs #N`（不自动关闭），
  `.agent/` 变更单独 `chore(agent):` 提交。
- 命令行 `-q` 与 pytest.ini addopts 叠成 `-qq` 会吞汇总行：看计数用
  `-o addopts="" -q`；管道后判退出码用 `PIPESTATUS[0]`（tail 会吃掉）。
- **跑后端测试会在 `src/data/` 留 commentsData.csv 未跟踪产物**——勿提交。

## 已完成
- **#51 完成转 in-review**：Prettier 全量格式化 74 文件（净 -1579 行，
  73/74 文件 prettier(HEAD) 等价证明）+ format:check 入 CI + eslint 关闭
  5 条冲突格式规则；四门禁 + 入口 chunk 字节一致验证（1 commit 66c1d7b）
- **#50 完成转 in-review**：文档路径校验 file:line/<param> 误报修复 +
  3 新单测（含负例）+ CI backend-fast 首步接线；无真实死链
  （1 commit 47b6606）
- **#49 完成转 in-review**：vitest 接入共享 Components resolver
  （config/components.mjs），移除全局 ElementPlus，模板级解析契约测试
  2 用例（反例变红实证）；前端 75 → 77（1 commit bca6a53）
- **#48 完成转 in-review**：构建体积预算门禁（check-bundle-budget.mjs +
  bundle-budget.json + npm run check:bundle + CI 步骤）；正/反例齐全
  （1 commit 1f93c25）
- **M3 五项（上一棒 2026-10-05）**：#43 浏览器冒烟 / #44 GET envelope
  契约 / #47 写接口契约 / #45 字段契约（立 #53）/ #46 Redis 降级文档，
  全部完成转 in-review；auto-discovered #52/#53 待定级
- #42 调研交付（验证码三候选对比 + 国内可用性核实，维持不上）
