# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `DeepSeek-V4.1-Flash-20261001T153535Z`（DeepSeek-V4.1-Flash），
UTC 2026-10-01T15:35 ~ 15:5x。第九棒，本会话一轮：#37。

## 本会话做了什么（一个 issue 关闭）

| Issue | 内容 | 要点 |
|-------|------|------|
| #37 | 前端 lint 不拦 warning，103 条告警可无限增长 | 告警清零 + `--max-warnings 0` 门禁 |

## 本轮的改动

- **lint 门禁**：`frontend/package.json` 的 `lint` 脚本加 `--max-warnings 0`，
  告警从此计入门禁（此前 CI 只拦 error，warning 可无限增长）。
- **告警清零（103 → 0，38 文件，+89/-117）**：
  - `no-unused-vars` 94 条：删未使用 import、解构项、catch 绑定、死函数
    （如 useBigScreen 的 `loadRegionData/loadTrendData` 死代码）。
  - `vue/no-template-shadow` 2 条：Sidebar 两个 `v-for="route in ..."` 改名 `item`。
  - `vue/require-default-prop` 7 条：PredictInput/PredictResult 的 Object/Function
    prop 补 `default`。

**验证**：`npm run lint` 0 error / 0 warning（且以 0 为门禁）；73 测试全过；
`vite build` 成功。后端未动。

## 本轮踩的坑（重要！）

1. **改 `v-for` 循环变量必须全量改名**：Sidebar 第二循环我只改了声明与部分引用，
   漏改 `{{ route.meta.title }}` —— 而 `route` 恰好是外层 `useRoute()` 的当前路由，
   于是模板会静默显示错误标题。**lint（0/0）、build、73 个测试全都发现不了**，
   是逐行复核 diff 才抓到的。教训：重命名类改动必须 review 全部引用，diff 逐行看。
2. **`catch (error)` 数量 ≠ unused 数量**：本会话曾在 useTable.js 误把"用了 error"
   的 catch 也改成 `catch {}`，立刻被 eslint 报 `no-undef`。救场靠的是**改完立即
   跑 lint 看错误数**，而不是相信自己的计数。
3. **eslint 的 vue 插件会追踪模板里的变量使用**：`<script setup>` 中仅模板使用的
   变量不会被 `no-unused-vars` 标记，因此"被标记 unused"即可安全删除；
   但**部分重命名不在此保护范围内**（见坑 1）。

## 留白项（有意不做，供下一棒/人工决策）

1. **integration job 无覆盖率**（沿用上一棒留白）：覆盖率门禁只加在 backend-fast。
2. **pip-audit 未阻断**（见 #32）：依赖 CVE 门禁属独立策略。
3. **safety 需仓库配置 `SAFETY_API_KEY`** 才能真跑（人工操作 secret）。
4. 更早遗留（功能类，较重）：#15/#16/#20 的验证码、user.py `String(100)`/`createTime`
   统一、WS 刷新后取 token、nginx `/socket.io` 握手 101（需 Docker）。
5. **前端仍无 TypeScript / 组件测试**（评估文档 22 条）：属大工程，未动。
6. 本轮删除的 `loadRegionData/loadTrendData` 是死代码（从未被调用）——若 BigScreen
   本应加载真实地区/趋势数据，那是**功能缺失**（评估文档 8 条"前端假数据"），
   需产品决策，不是清理能解决的。

## 坑与经验（重要，接力者必读）

1. **重命名类改动：diff 逐行复核**，自动化检查（lint/build/test）抓不住"改了声明
   漏改引用但名字仍存在"的错。
2. **`docs/项目评估与规划.md` 已加横幅**（#36），动手前先读横幅，条目多为历史状态。
3. **CI 与 Security Scan 是两个独立 workflow**，核对分别看。
4. **本地 pytest 必带 `-p no:launch_testing -p no:launch_ros`**（见 ENV.md）；
   **勿写进 `pytest.ini`**。
5. **不要盲跑 `black`**：本地 black 会重排 122 个文件，CI 只跑 `ruff check`。
6. 覆盖率阈值唯一真相在 `pyproject.toml`（`fail_under=60`），CI 只传 `--cov`。
7. bandit 多行 f-string 的 nosec 放**闭合三引号那行**。
8. `commit fix: #N` 自动关 issue；`chore:`/`docs:`/`refactor:` 不是关闭关键字，
   需另加 `Closes #N`。
9. 后台 `gh run watch` 偶发误报非 0 —— 以 `gh run view` 的 conclusion 为准。

## 下一步建议

- 无待办 issue。下一棒按协议第七节主动发现（先查重）。
- 候选：给 integration job 加覆盖率；或功能类遗留（user.py schema 统一等）。
- 三条门禁现已齐：后端覆盖率 60%、bandit HIGH、前端 lint 零告警——保持住。

## 环境备注

- 后端 `.venv` 齐全（Python 3.12）；fast gate 与 integration 本地均可跑
  （integration 本地实测 189 passed / 5 skipped）。
- fast gate：`.venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -q --maxfail=1`
- 前端：mise node 22 入 PATH；lint 现为 0/0 门禁；73 测试；build ~8s。
- 本地有真实 `.env`（含密钥，**勿提交**）。
- gh 可用（账号 zhangjszs）；bandit/pytest-cov 已装在 `.venv`。
- 本地分支 `wip/20260930T154700Z`（未推送）仍在，请人工确认去留。
