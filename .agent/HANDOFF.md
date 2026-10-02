# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `executor-glm-20261002T1447Z`（GLM，Execution Agent），UTC 2026-10-02T14:47 起。
第十一棒（执行），本会话已完成 **两个 issue：#39、#40**（M2 性能里程碑的主体）。
（背景：`glm-20261002T000100Z` 会话 00:01Z 开工 #39、00:07Z 死亡，留未提交 WIP；
Planning 会话 14:0xZ 验收现场并留接棒清单；本会话按清单续作并连做 #40。）

## 已完成 #39：element-plus 按需加载（commit 33a4c1f，CI 绿、issue 关）

- 修复 WIP 断点（loading 深路径）+ 补 DataLine + 图标守护测试（75 测试基线）
- **真正主因是 manualChunks 把 element-plus 聚合进入口静态依赖**（980KB），
  拆掉后首屏 raw **-76.1% / gzip -72.7%**（1,484,188→354,394B / 418,271→114,171B）
- 四列对比表与证据见 issue #39 评论

## 已完成 #40：大 chunk 排查（commit 442cd22，CI 结果见 issue）

- **visualizer 构成报告**（`VISUALIZER=1 npm run build` → dist/stats.json，基线
  commit 9a56559）：ip chunk **98.6% 是 china.json**（583,919B / gz 197,273B）；
  echarts chunk 586 模块全是真实使用能力（top: core/LineView/TooltipView/
  AxisBuilder/visualMap/MapDraw…），**判定已最优不动**（字节/hash 不变）
- **修复**：新增 `utils/chinaMap.js`（fetch + registerMap 幂等 promise），
  china.json 改运行时按需拉取带 hash 资产（gzip 传输 ~229KB，浏览器缓存）；
  ip 图表 mapReady 门控。**ip chunk 586,429→4,004B（gzip -99.0%）**
- **顺带修了一个真 bug**：大屏地图顺序依赖——mapChartOptions 用
  `map:'china'` 但全仓只有 ip 页 registerMap，直接进大屏地图渲染不出；
  useBigScreen 接入 ensureChinaMap 后消除

## 验证状态

- #39：lint 0/0、75 测试、build、preview HTTP 冒烟、CI 三 job 绿 ✅、issue CLOSED
- #40：lint exit 0、75 测试、build、HTTP 冒烟（ip chunk 200、china.json 200 /
  229KB gzip、SPA 回退）、**CI/Security Scan 结果以 issue #40 状态为准**
- 三条门禁保持：后端覆盖率 ≥60、bandit HIGH 阻断、前端 lint 零告警；
  前端测试基线现为 **75**

## 未做 / 留白（有意不做）

1. 登录后页面（表格页/大屏）无真实浏览器交互冒烟（本机无浏览器后端、后端未起）；
   兜底 = resolver 机械注入 + 样式产物抽查 + 测试 + HTTP 冒烟。需要时人工起后端过一遍。
2. 22 处 `import { ElMessage } from 'element-plus'` 根导入保留（tree-shake 有效，无收益不改）。
3. echarts chunk per-chart 拆分不做（割裂共享缓存，无收益优化，#40 非目标）。
4. china.json 未做数据简化（改地图精度属数据取舍，需产品决策才动）。

## 坑与经验（接力者必读）

1. **「按需加载」做了不等于首屏变小**：先查 chunk 怎么进首屏（manualChunks 聚合 /
   modulepreload = 静态依赖），再谈按需。#39 的 980KB 与 #40 的 585KB 都是此理。
2. **判 lint/pytest 结果必须看退出码/完整输出**：lint 横幅含 `--max-warnings` 字样，
   `grep -E "problem|error|warning"` 会误判；`pytest | tail` 管道退出码是 tail 的。
3. **lint/test 全过 ≠ build 可用**：只有 vite build（rollup 完整解析）能抓住
   不存在的子路径导入。前端三门禁缺一不可。
4. **vitest.config 不含 Components 插件**：单测不覆盖模板级组件解析。
5. `echarts.registerMap` 是全局状态：谁注册谁生效，跨页面共享时用
   `ensureChinaMap()`（幂等 promise），别依赖访问顺序。
6. 判断上一会话死活看文件 mtime 不看锁；陈旧锁可删；WIP 经验证后续作勿重写。
7. jsdom 下 `import.meta.url` 非 file://；用 `process.cwd()`。
8. 沿用：schema 列名三层同步；幂等迁移铁律；重命名 diff 逐行复核；
   `refactor:`/`chore:` 不自动关 issue（需 `Closes #N`）；
   `gh run list --branch <b>` 偶发陈旧缓存；CI 与 Security Scan 是两个 workflow；
   ci.yml 为 cancel-in-progress——同分支连续 push 时前一个 run 显示 cancelled 属正常，
   以最后 HEAD 的 run 为准。

## 下一步建议

- **#41（P2）integration job 覆盖率报告**（D-04：只报告不设阈值）：ci.yml 的
  integration job 加 --cov 并注意 `--cov-fail-under=0` 防 pyproject 全局阈值误伤。
- #42（P3 验证码调研）随时可插队。M2 完成后 Planning 可验收结项。
- **#39/#40 均已含 Closes 关键字，推送即自动关闭；若 CI 红，先 reopen 再修**
  （本地三门禁已全绿，风险低）。

## 环境备注

- 后端 `.venv` 齐全（Python 3.12）；fast gate 1261 / integration 189 本地均可跑。
- fast gate：`.venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -q --maxfail=1`
- 前端：mise node 22 入 PATH；lint 0/0；**75 测试**；visualizer 用法见上。
- 基线对比技巧：`git worktree add /tmp/xx HEAD` + 软链 frontend/node_modules。
- 本地有真实 `.env`（含密钥，**勿提交**）。
- gh 可用（账号 zhangjszs）；bandit/pytest-cov 已装在 `.venv`。
- 本地分支 `wip/20260930T154700Z`（未推送）仍在，请人工确认去留。
