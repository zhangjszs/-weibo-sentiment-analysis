# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

两段：
1. **执行会话 `glm-20261002T000100Z`**（GLM），UTC 2026-10-02T00:01 拿锁做 #39，
   **00:07 后无预警中断**——写了核心实现、装了依赖，但没跑验证、没写测试、
   没提交、没评论。遗留工作区未提交 WIP（前端 5 个文件）+ 陈旧锁（Planning 已删）。
2. **Planning 会话**（本会话），UTC 2026-10-02T14:02~14:2x。巡检 + 现场验收 +
   治理落盘，未改任何源代码。

## 现场状态（重要：工作区有未提交 WIP，勿丢弃、勿覆盖）

#39 的实现已大体成型（vite Components 插件 + ElementPlusResolver + 图标
iconResolver + 最小全局注册 + 手工补 JS-API 组件样式），前端 5 文件已改、
`unplugin-vue-components` 已装入 node_modules。Planning 只读验证结论：

- `npm run lint` ✅ 0/0
- `npm run test:run` ✅ 10 文件 73 测试全过
- `npm run build` ❌ 失败于一处：`element-plus/es/components/loading/plugin`
  导入不存在（2.14.2 该目录仅 `index.mjs`）

**接棒清单（详细版见 issue #39 的 Planning 评论，2026-10-02T14:1xZ）**：
1. 修复该 import → build 复核通过
2. 补代码注释里承诺的「ICON_COMPONENTS 测试守护」（尚不存在）
3. 量化对比基线 1.00MB raw / ~330KB gzip，验收 ≥30% 或给出论证
4. 三门禁全过 → 提交（含 `Closes #39`）→ 评论贴体积证据 → CI 三 job 绿

## Planning 本轮做了什么

- 查明死亡会话时间线（锁 00:01Z、文件 mtime 00:06~00:07Z），确认陈旧锁已删
- 对 WIP 做只读验证（lint/测试/构建），根因定位到失效导入路径
- issue #39 发现场状态 + 接棒清单评论
- 更新 PLAN/STATE/HANDOFF；issue #40~#42 审查为定义合格，无需返工

## 坑与经验（接力者必读）

1. **lint/test 全过 ≠ build 可用**：vitest（esbuild）与 eslint 都不完整解析
   模块路径，只有 vite build（rollup）会抓住不存在的子路径导入。前端验证
   必须三门禁全跑，缺一不可。
2. **判断上一会话死活看文件 mtime，不看锁**：锁可能遗留。陈旧锁（长时间无
   任何文件活动）可删；工作区未提交 WIP 经验证后续作，不要重写或丢弃。
3. **改 schema 列名必须三层同步**：ORM、裸 SQL（git grep 全仓）、冻结 SQL。
4. **幂等迁移是本仓库铁律**（CI 每次全新库跑链，必须跳过已新结构），
   写法见 `f6a7b8c9d0e1` / `b2d5a3f9c0e1`。
5. `pytest ... | tail -N` 会截掉汇总行、管道退出码是 tail 的——判断成败看文本。
6. 重命名类改动 diff 逐行复核（Sidebar 教训）；改 v-for 循环变量全量改名。
7. `refactor:`/`chore:`/`docs:` 不自动关 issue（需 `Closes #N`）；
   CI 与 Security Scan 是两个 workflow；本地 pytest 带
   `-p no:launch_testing -p no:launch_ros`；勿盲跑 black；`gh run watch`
   偶发误报以 `gh run view` 为准；`gh run list --branch <b>` 偶发返回陈旧
   缓存（Planning 本轮实测：--branch 过滤给出 8 月旧 run，去掉过滤则正常）。

## 下一步建议

- 第一优先：按 #39 接棒清单恢复并完成（现场已九成，剩验证+量化+提交）。
- 之后队列：#40（大 chunk 排查，注明基线 commit 避免 #39 改动失真）→
  #41（integration 覆盖率报告，D-04 不设阈值）；#42（验证码调研）随时可插队。
- 三条门禁保持：后端覆盖率 ≥60、bandit HIGH 阻断、前端 lint 零告警。

## 环境备注

- 后端 `.venv` 齐全（Python 3.12）；fast gate 1261 / integration 189 本地均可跑。
- fast gate：`.venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -q --maxfail=1`
- 前端：mise node 22 入 PATH；lint 0/0 门禁；73 测试；WIP 已装
  `unplugin-vue-components`（node_modules 就绪，build 待修一处 import）。
- 本地有真实 `.env`（含密钥，**勿提交**）。
- gh 可用（账号 zhangjszs）；bandit/pytest-cov 已装在 `.venv`。
- 本地分支 `wip/20260930T154700Z`（未推送）仍在，请人工确认去留。
