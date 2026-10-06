# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `executor-glm-20261006T0406Z`（GLM，Execution Agent），UTC 2026-10-06T04:06 ~ 05:2x。
第十三棒（执行）。本轮消费完候补四项 **#48 / #49 / #50 / #51**，全部完成并转
**in-review**（未关闭——验收是 Planning 的职责）。

## 本会话做了什么

| Issue | 结果 | 要点 |
|-------|------|------|
| **#48** | ✅ 完成待验收 | 首屏体积预算门禁：`check-bundle-budget.mjs` 解析 dist/index.html 实载资源（raw 判定 / gzip 展示）比对 `bundle-budget.json`（预算 327,000/97,000 = 2026-10-06 实测基线 273,199/81,228 ×1.2 取整，`_meta` 注明来源与调整流程）；`npm run check:bundle` + CI frontend-fast 新步骤。正例 exit 0 / 低预算反例 exit 1 报明细 / 缺 dist exit 1，三态齐全。commit 1f93c25 |
| **#49** | ✅ 完成待验收 | vitest 接入共享 Components resolver：新建 `config/components.mjs` 工厂（vite/vitest 单源，importStyle 参数化——vitest 侧样式导入会崩收集）；**移除 vitest.setup.js 全量 ElementPlus**（会掩盖 resolver 回归）；模板级解析契约测试 2 用例，移除 resolver 时实证全红。前端测试 75 → 77。commit bca6a53 |
| **#50** | ✅ 完成待验收 | 文档路径校验：file:line / file:line-range 归一化 + `<param>` 路由忽略，5 个「缺失」全为误报、仓库无真实死链；+3 单测（7→10，含真实死链仍报出的负例）；接线选 **CI backend-fast 首步**（CI 不跑 pre-commit、脚本零依赖、强制力最强，理由已写进 workflow 注释）。fast gate 1461 → 1463。commit 47b6606 |
| **#51** | ✅ 完成待验收 | Prettier 全量格式化 74 文件（净 -1564 行）+ format:check 入 CI（lint 同级步骤）。**73/74 文件经「≡ prettier(HEAD) 逐字节对比」机器证明仅格式化**（PredictInput.vue 为 prettier 非幂等构造，两轮 write 收敛）；eslint 关闭 5 条与 Prettier 冲突的 vue 纯格式规则（不加依赖）。format 脚本扩至 src/ tests/。commit 66c1d7b |

提交链：1f93c25(#48) → bca6a53(#49) → 47b6606(#50) → 66c1d7b(#51)，全部合入 main。
每轮 CI 三 job + Security Scan 全绿（#48: 37412644222 / #49: 37413473725 /
#50: 37414273592 / #51: 37415279280）。

## 未完成 / 进行中

- 无进行中工作。**ready 队列已空**（#48~#51 全部消费完毕）。

## 验证情况

- 前端门禁全绿：lint 0/0、format:check exit 0、test:run **77/77**、build exit 0、
  check:bundle exit 0（入口 chunk 273,199B 与格式化前字节一致）。
- 后端 fast gate：**1463 passed + 1 strict xfail**（基线 1461 含 xfail = 1460+1；
  #50 新增 3 用例后 1463+1），ruff 全绿。
- CI：上述 4 个 run 三 job 全绿（含 #50 的 Documented paths check 步骤级证据、
  #51 的 Frontend format check 步骤级证据）。
- integration 未在本机跑（CI 实证绿）；本轮无后端业务代码改动（#50 只动
  scripts/ + tests/ + ci.yml）。

## 风险与注意事项

1. **in-review 积压 9 项**：M3 五项（#43/#44/#45/#46/#47）+ 本轮四项，全部待
   Planning 验收；#52/#53 仍待定级（#53 涉产品决策，建议进 DECISIONS）。
2. **格式权威已统一归 Prettier**：eslint 侧关闭了 5 条 vue 纯格式规则——未来
   收紧格式细节应改 `.prettierrc.json`，不要恢复 vue 格式规则（会双标准打架）。
3. **PredictInput.vue 的 prettier 非幂等**：批量 --write 后该文件 --check 可能
   仍报，再跑一遍 `npm run format` 即收敛；提交前确认「第二轮零 diff」。
4. **`frontend/build/` 目录不可用**：根 .gitignore 全局忽略 build/（Python 规则），
   共享构建配置放 `frontend/config/`。
5. **跑后端 fast gate 会在 `src/data/` 留下未跟踪的 commentsData.csv**（测试
   产物）——不要提交；本机当前就有这个残留。
6. 体积预算的调整流程在 `bundle-budget.json` 的 `_meta`：正当增长抬预算要注明
   新基线，误引入则修代码——别只抬数字。
7. `.agent/LOCK` 已释放；工作区干净（除上述测试产物），main 与 origin 同步
   （HEAD 66c1d7b + 本轮 chore 提交）。

## 坑与经验（接力者必读）

1. **管道判退出码必须用 `PIPESTATUS[0]`**：`cmd | tail; echo $?` 拿到的是 tail
   的退出码（本会话两次踩到：vitest 假绿、pytest 假红各一次）。
2. **prettier 对部分 Vue SFC 非幂等**：write → check 仍红 → 再 write 即稳；
   证明「仅格式化」可用 `prettier(HEAD 版本) ≡ 工作区文件` 逐字节对比法。
3. **git 路径与 cwd**：在 frontend/ 子目录里 `git diff --name-only` 返回的仍是
   仓库根相对路径，`cat`/脚本遍历前先 `cd` 回根或剥前缀（本会话踩两次）。
4. **ElementPlusResolver 样式导入会崩 vitest**（`Unknown file extension .css`）：
   共享 resolver 工厂必须参数化 importStyle，测试侧传 false。
5. **「全局注册会掩盖回归」**：给测试环境移除全量 ElementPlus 前，先排查被挂载
   组件的 v-loading / 字符串 icon / ElMessage 依赖（本仓全在应用入口
   plugins/elementPlus.js，组件层干净）。
6. 沿用既有教训：lint/pytest 判结果看退出码；`-qq` 吞汇总行（用
   `-o addopts="" -q`）；commit 用 `Refs #N` 不自动关 issue；`.agent/` 变更
   单独 `chore(agent):` 提交。

## 给下一棒的第一步建议

- **ready 已空，下一棒是 Planning**：验收 in-review 九连（每项 issue 内的执行
  报告含命令/退出码/CI run 链接，可独立复核）+ 定级 #52/#53 + 决定 M3 结项与
  下一阶段（PLAN 的 D-05 备选均需用户输入）。
- 若要继续执行线：无 ready 可领，勿自行扩范围。

## 给 Planner 的信号

- **需要 Planning 介入（验收积压）**：in-review 9 项 + auto-discovered 2 项。
- 前端门禁从 3 道增至 **5 道**（+format:check、+bundle 预算），后端 fast gate
  新增文档死链检查——CI 失败时的排查入口都已写在各步骤注释里。
- #53（大屏 trend 数据语义）与 playwright 是否入版本控制，仍待用户/Planner 决策。
