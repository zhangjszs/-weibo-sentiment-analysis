# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `executor-glm-20261002T1447Z`（GLM，Execution Agent），
UTC 2026-10-02T14:47 ~ 16:2x。第十一棒（执行）。**本轮消费完 M2 全部 4 个 issue**：
#39、#40、#41 实现完成且关闭（CI 绿），#42 调研交付（保持 open 待 Planning 治理）。
（背景：`glm-20261002T000100Z` 会话曾 00:01Z 开工 #39、00:07Z 死亡留 WIP，
Planning 14:0xZ 验收现场留接棒清单，本会话按清单续作完成。）

## 本会话做了什么

| Issue | 结果 | 要点 |
|-------|------|------|
| **#39** | ✅ 关闭（CI 绿） | element-plus 按需加载。真因是 manualChunks 把 element-plus 聚合进入口静态依赖（980KB）；拆掉后**首屏 raw -76.1% / gzip -72.7%**（1,484,188→354,394B）。含 loading 深路径修复、DataLine 补注册、图标守护测试（前端测试基线 73→**75**） |
| **#40** | ✅ 关闭（CI 绿） | 大 chunk 排查。visualizer 报告证实 **ip chunk 98.6% 是 china.json**（584KB）→ 地图数据改运行时按需拉取（`utils/chinaMap.js` 幂等注册），**ip chunk 586,429→4,004B（gzip -99.0%）**；echarts chunk 构成报告判定**已最优**（字节/hash 不变）。**顺带修复大屏地图顺序依赖 bug**（原先必须先访问 IP 页大屏地图才渲染） |
| **#41** | ✅ 关闭（CI 绿） | integration job 覆盖率报告：`--cov-fail-under=0` 豁免全局阈值（实测 **33%** 不染红），XML artifact 14 天；backend-fast 门禁不变（65.21% reached）。CI run 37024633362 实证三验收全过 |
| **#42** | 📋 调研交付，**保持 open** | 验证码三候选对比表 + 国内可用性核实（Turnstile 官方不支持大陆、reCAPTCHA 被墙）+ 触发条件 3 条 + 推荐**「维持不上」**（相对现有失败锁定+限流+审计边际增益不划算）。实施与否交 Planning/用户 |

提交：`33a4c1f`(#39) → `442cd22`(#40) → `a36aebf`(#41) → `823991b`/后续 chore。
M2 三项验收标准（#39 ≥30% / #40 报告+修复 / #41 报告）**全部达成**，CI 全绿。

## 留白 / 风险

1. 登录后页面（表格页/大屏）无真实浏览器交互冒烟（本机无浏览器后端、后端未起）；
   兜底 = resolver 机械注入 + 样式产物抽查 + 75 测试 + HTTP 冒烟。需要时人工补。
2. #42 推荐「维持不上」——是否采纳属产品决策，Planning 治理该 issue。
3. 22 处 `import { ElMessage } from 'element-plus'` 根导入保留（tree-shake 有效）。
4. echarts per-chart 拆分不做（割裂共享缓存，无收益优化）；china.json 未做精度
   简化（数据取舍需产品决策）。

## 坑与经验（接力者必读）

1. **「按需加载」做了不等于首屏变小**：先查 chunk 怎么进首屏（manualChunks 聚合 /
   modulepreload = 静态依赖），再谈按需。#39 的 980KB 与 #40 的 584KB 都是此理。
2. **判 lint/pytest 结果必须看退出码/完整输出**：lint 横幅含 `--max-warnings` 会
   骗过 grep；`pytest | tail` 管道退出码是 tail 的。
3. **命令行 `-q` 与 pytest.ini addopts 的 `-q` 叠成 `-qq` 时，pytest 抑制
   "N passed" 汇总行**（#41 本地实测）。CI 命令勿重复传 addopts 已有 flag。
4. **lint/test 全过 ≠ build 可用**：只有 vite build（rollup 完整解析）能抓住
   不存在的子路径导入。前端三门禁缺一不可。
5. `echarts.registerMap` 是全局状态：跨页面共享地图用 `ensureChinaMap()`
   （幂等 promise），别依赖访问顺序。
6. 判断上一会话死活看文件 mtime 不看锁；陈旧锁可删；WIP 经验证后续作勿重写。
7. jsdom 下 `import.meta.url` 非 file://；用 `process.cwd()`。
8. 沿用：schema 列名三层同步；幂等迁移铁律；重命名 diff 逐行复核；
   `refactor:`/`chore:` 不自动关 issue（需 `Closes #N`）；
   `gh run list --branch <b>` 偶发陈旧缓存；ci.yml 为 cancel-in-progress——
   连续 push 时前序 run 显示 cancelled 属正常，以最后 HEAD 的 run 为准。

## 下一步建议

- **ready 队列已清空，下一棒是 Planning**：验收 M2（三项验收全达成，可结项），
  治理 #42（采纳推荐则关闭；采纳「上验证码」则凭调研表直接立项），规划下一阶段
  （PLAN 远景：前端 TS 化、REST 契约测试、镜像瘦身等）。
- 三条门禁保持：后端覆盖率 ≥60（65.21%）、bandit HIGH 阻断、前端 lint 零告警；
  前端测试基线 **75**；integration 覆盖率观察起点 33%（不设阈值）。

## 环境备注

- 后端 `.venv` 齐全（Python 3.12）；fast gate / integration 本地均可跑
  （integration 本地 SQLite：189 passed, 5 skipped；CI MySQL：191/3）。
- fast gate：`.venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -q --maxfail=1`
- 前端：mise node 22 入 PATH；lint 0/0；**75 测试**；体积诊断
  `VISUALIZER=1 npm run build` → dist/stats.json；基线对比用
  `git worktree add /tmp/xx HEAD` + 软链 frontend/node_modules。
- 本地有真实 `.env`（含密钥，**勿提交**）。
- gh 可用（账号 zhangjszs）；bandit/pytest-cov 已装在 `.venv`。
- 本地分支 `wip/20260930T154700Z`（未推送）仍在，请人工确认去留。
