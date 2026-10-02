# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `executor-glm-20261002T1447Z`（GLM，Execution Agent），
UTC 2026-10-02T14:47 ~ 15:0x。第十一棒（执行），本会话一个 issue：**#39 完成**。
（此前 `glm-20261002T000100Z` 会话 00:01Z 开工 #39、00:07Z 死亡，留下未提交
WIP；Planning 会话 14:0xZ 验收现场并留接棒清单；本会话按清单续作完成。）

## 本会话做了什么（#39 element-plus 按需加载，已完成）

**接手现场**（死亡会话 WIP，lint/测试过、build 差一处）之上的增量：

| 改动 | 说明 |
|------|------|
| 修 loading 导入 | `es/components/loading/plugin` 不存在（2.14.2），改 `…/loading/index`（默认导出即插件，注册 v-loading） |
| 补 DataLine | StatCard 的 icon prop 默认值 `'DataLine'` 走字符串解析，WIP 清单漏了它 |
| 注释校准 | 路由 meta.icon 实为组件引用；字符串路径是 tabs 默认页签 'HomeFilled'、icon="X" prop、动态三元等；路由图标保留注册属稳妥兜底 |
| **移除 manualChunks 的 element-plus 聚合** | **基线 980KB 的真正主因**：聚合 chunk 被入口静态依赖，按需引得多细都进首屏。改按真实依赖分包（echarts 规则保留，#40 范围） |
| 新增图标守护测试 | tests/element-plus-icons.test.js：源码扫描字符串图标引用 ⊆ ICON_COMPONENTS（'Help' 是路由名，白名单） |

**成果**（首屏 = index.html 实载文件，git worktree 构建基线同口径对比）：

| 产物 | 前 raw | 前 gzip | 后 raw | 后 gzip |
|------|--------|---------|--------|---------|
| 首屏 JS | 1,096,238 | 364,458 | 273,166 | 101,068 |
| 首屏 CSS | 387,950 | 53,813 | 81,228 | 13,103 |
| 合计 | 1,484,188 | 418,271 | 354,394 | 114,171 |

即 **raw -76.1% / gzip -72.7%**，远超 ≥30% 验收线。ip/echarts chunk 字节不变
（#40 基线未受扰动）；echarts 聚合规则是 #40 的下一刀。

**验证**：lint 0/0 ✅；测试 11 文件 75 全过 ✅（73+2）；vite build ✅；
preview HTTP 冒烟 ✅（首屏资源 200、SPA 回退、产物引用完整、组件样式在产物中）；
**CI run 37020255603 / Security Scan 37020255065 结果见 issue**（commit 含
`Closes #39`，推送即自动关闭；若 CI 红需 reopen 修复——本地三门禁已全绿，风险低）。

## 未做 / 留白（有意不做）

1. **登录后页面（表格页/大屏）未做真实浏览器交互冒烟**：本机无浏览器后端，
   后端+MySQL 未起。兜底：resolver 按模板标签机械注入（build 过=注入完成）、
   组件样式产物抽查、75 测试、图标守护测试。如需人工全量冒烟，起后端后过一遍
   登录/首页/大屏/表格页即可。
2. dark css-vars 仍全量引入（纯变量，体积可忽略，issue 非目标允许）。
3. 22 处 `import { ElMessage } from 'element-plus'` 根导入保留（sideEffects
   声明下可正常 tree-shake，改深路径无体积收益，徒增 diff）。

## 坑与经验（接力者必读）

1. **「按需加载」做了不等于首屏变小**：manualChunks 把包聚合进入口静态依赖时，
   一切按需都白做。先查 chunk 怎么进首屏（modulepreload 即静态依赖），再谈按需。
2. **lint/test 全过 ≠ build 可用**：vitest（esbuild）与 eslint 都不完整解析模块
   路径，只有 vite build（rollup）能抓住不存在的子路径导入。三门禁缺一不可。
3. **vitest.config 不含 Components 插件**：单测不覆盖模板级组件解析，别把
   「测试全过」当成「页面组件都正常」的证据。
4. 判断上一会话死活看文件 mtime 不看锁；陈旧锁可删；WIP 经验证后续作勿重写。
5. `gh run list --branch <b>` 偶发返回陈旧缓存，去掉过滤即正常；CI 与
   Security Scan 是两个 workflow；`gh run watch` 偶发误报以 `gh run view` 为准。
6. jsdom 下 `import.meta.url` 非 file://；用 `process.cwd()` 定位文件。
7. 沿用：schema 列名三层同步；幂等迁移铁律（写法见 f6a7b8c9d0e1/b2d5a3f9c0e1）；
   `pytest | tail` 看文本不看退出码；重命名 diff 逐行复核；
   `refactor:`/`chore:` 不自动关 issue（需 `Closes #N`）。

## 下一步建议

- **#40（P2）大 chunk 排查**：ip 页 572KB / echarts 695KB（基线 commit `33a4c1f`，
  与更早基线字节一致）。echarts 的 manualChunks 聚合是现成嫌疑，可复用 #39 的
  同款诊断（首屏强依赖 vs 路由按需）。
- 之后 #41（P2，integration 覆盖率报告，D-04 不设阈值）；#42（P3 调研）随时。
- 三条门禁保持：后端覆盖率 ≥60、bandit HIGH 阻断、前端 lint 零告警；
  前端测试基线现为 **75**。

## 环境备注

- 后端 `.venv` 齐全（Python 3.12）；fast gate 1261 / integration 189 本地均可跑。
- fast gate：`.venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -q --maxfail=1`
- 前端：mise node 22 入 PATH；lint 0/0；**75 测试**；`unplugin-vue-components`
  已在依赖中。基线对比可用 `git worktree add /tmp/xx HEAD` + 软链 node_modules。
- 本地有真实 `.env`（含密钥，**勿提交**）。
- gh 可用（账号 zhangjszs）；bandit/pytest-cov 已装在 `.venv`。
- 本地分支 `wip/20260930T154700Z`（未推送）仍在，请人工确认去留。
