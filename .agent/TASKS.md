# TASKS — Issue 本地镜像（只读镜像，权威来源为 GitHub Issue）

> Planner 每轮整体重写刷新。Executor 改状态时先改 Issue 再同步本行。
> 标签沿用仓库实际标签（`ready-for-agent` 等，见 docs/agents/triage-labels.md）。
> 更新于 2026-10-15（UTC，Planning 轮；Issue 权威重写；#90/#91/#92 已验收关闭，open in-review 为 0）。

## 今日队列（建议执行顺序）

| # | 标题 | P | 状态 | 备注 |
|---|---|---|---|---|
| #95 | 测试侧消灭 /ready 3s×2 等待：conftest 设 REDIS_URL=disabled | P3 | ready-for-agent | 新立（#92 归因驱动；预期 gate -6s；含 TEST_PERF §6/§7 回写；先跑，全程串行） |
| #93 | 测试质量机制包：时长预算告警 + 顺序依赖探针 + unit 层禁网评估 | P3 | ready-for-agent | 后备转正（#91 后执行，顺序扰动与 #95 串行测量错开） |

## 等待验收（in-review）

无。本轮：open in-review 为 0（#90/#91/#92 均于本轮验收关闭）。

## 阻塞 / 待决策

| # | 状态 | 说明 |
|---|---|---|
| #59 | needs-info | 产品功能迭代，等用户具体需求输入（D-012 默认 A 继续有效） |

## Milestone 进度（M6 测试性能优化：原定 #88–#94 共 7 项 + 收敛补项 #95）

- done：#88 #89 #90（部分通过转关闭，D-016） #91 #92 #94（6/7）
- ready：#93 #95（今日队列取其二，全部）
