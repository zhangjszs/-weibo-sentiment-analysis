# TASKS — Issue 本地镜像（只读镜像，权威来源为 GitHub Issue）

> Planner 每轮整体重写刷新。Executor 改状态时先改 Issue 再同步本行。
> 标签沿用仓库实际标签（`ready-for-agent` 等，见 docs/agents/triage-labels.md）。
> 更新于 2026-10-14（UTC，Planning 轮；Issue 权威重写；53104c3 后无新提交）。

## 今日队列（建议执行顺序）

| # | 标题 | P | 状态 | 备注 |
|---|---|---|---|---|
| #91 | 本地并行化评估：引入 pytest-xdist | P2 | in-review | 三轮全绿 50.42s→30.64s/31.55s→25.20s；§6/§7 已回写；结论：暂不纳入默认门禁 |
| #92 | 慢测试治理：sentiment_model ×2 降规模 | P3 | ready-for-agent | 用串行门禁测量，与 #91 错开跑 |
| #90 | CI：Python 依赖安装提速 | P2 | ready-for-agent | CI 迭代慢（每次 push 约 5 分钟），放最后 |

## 后备（ready，本轮不进队列）

| # | 标题 | P | 状态 |
|---|---|---|---|
| #93 | 测试质量机制包：时长预算告警 + 顺序依赖探针 + unit 层禁网评估 | P3 | ready-for-agent |

## 等待验收（in-review）

无。本轮：open in-review 为 0，53104c3 后无新提交，无待验收任务。

## 阻塞 / 待决策

| # | 状态 | 说明 |
|---|---|---|
| #59 | needs-info | 产品功能迭代，等用户具体需求输入（D-012 默认 A 继续有效） |

## Milestone 进度（M6 测试性能优化：#88–#94）

- done：#88 #89 #94（3/7）
- ready：#90 #91 #92 #93（4/7，今日队列取其三）
