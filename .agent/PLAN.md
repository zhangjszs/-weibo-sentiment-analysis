# PLAN — 开发路线图

> 2026-11-23 · 今日规划 PR 的同日续接。GitHub Issues 为任务权威。干净副本已 fetch/prune 并 pull --rebase。验收基线是远端 main `df989ea`，规划分支为 `codex/planning-2026-11-23`。原工作树 main `c2f33f8` 有六处既有改动，默认权限下 fetch 退出 255（Git 元数据只读），pull 因未暂存改动退出 128。

## 当前方向

依赖锁验收和覆盖率实验已收尾。请求层准备里程碑 2/2 完成，下一步按 D-009、D-043、D-050 迁移公共 Axios 实例。先用真实六个会话包装锁定现行调用契约，再迁移 transport，保持请求、启动、会话与导航语义。

## 今日目标（2026-11-23）

- 复核 11-22 晚间交付。[#146](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/146#issuecomment-7091137981) 已通过并关闭。[#147](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/147#issuecomment-7104222957) 的两个回退计数及新目录回放已补齐，本轮复验通过并关闭。两个候选合并算法的结论限于固定输入，覆盖工具维持现行实现。
- [#150](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/150#issuecomment-7104225273)、[#151](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/151#issuecomment-7104227740) 同日交付，均通过并关闭。[请求层迁移准备](https://github.com/zhangjszs/-weibo-sentiment-analysis/milestone/3) 已关闭，2/2。生产类型门禁独立复跑为 7 TS / 0 JS 或 Vue。候选 8/0、类型负例及浏览器验证来自 Executor 的执行记录。
- 开启 [前端公共请求层 TypeScript 迁移](https://github.com/zhangjszs/-weibo-sentiment-analysis/milestone/4)，从即时可领取的两项开始。

## 当前 Milestone · 前端公共请求层 TypeScript 迁移（0 / 2）

### 目标与验收

- 六个会话 API 包装通过真实 Axios adapter 回归，核实路径、方法、JSON、Cookie 配置和完整包络，覆盖 register/logout 的省略 data 和会话检查的已登录/未登录两态。
- 公共实例成为 `request.ts`，原七项加此文件进入 D-043，JS/Vue 计数为 0。入口在安装 router 前接线，保持混合 401、错误对象身份、加载计数和响应包络。装配遗漏可诊断，401 清态与拒绝语义仍可验证。

### 完成信号

- [#156](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/156) 的 adapter 定向用例和全量门禁通过，Planner 验收关闭。
- [#157](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/157) 的真实迁移合入主干并验收关闭。生产 `--listFiles` 为 8/0，原实现与候选的两条浏览器入口烟测一致，五项 CI 全绿。

### 明确非目标

- 范围截至公共实例与六接口行为基线。认证权限、HTTP API、用户资料缓存、auth 包装和 router/store/SFC 的类型迁移、后端和主要 CI 保持现状。
- 覆盖工具变更继续等待真实跨 transform 组、混合粒度与 LCOV 源分支归属证据。历史 auth 双漂移有独立解除条件。

### 执行队列（2 项 `ready`）

1. [#156](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/156) 锁定六个会话 API 包装的真实请求与响应契约（P3）。
2. [#157](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/157) 迁移公共请求实例至 TypeScript 并在入口装配导航（P2）。

两项均从已验收基线出发。先跑独立回归便于前后对比，顺序无硬依赖。

## 已知阻塞与依赖

- #143 `blocked`，需要稳定触发 `auth.js` 与 `Login.vue` 历史双漂移的原始输入和顺序。#138 保留现象档案。
- #109 `blocked`，等待可用容器环境或已授权测试主机，验收须跑真实 OTLP / Jaeger 链路。
- #98 按 D-019 A 冻结现场。#96、#100、#101、#102 维持 `needs-info`，其中 #102 还依赖 #98。#59 按 D-012 A 等待具体产品需求。
- M6 成员 10/10 关闭，成功信号为 1/3，里程碑仍开放。串行 <30s 与完整 CI <240s 仍缺达标证据。M7 6/11 关闭，里程碑仍开放且冻结。此前已授权的前端 TS 第四批保持 6/6。

## 下一阶段

公共请求层经过真实迁移验收后，再为 auth 包装和 API 桶定义逐接口类型切片，以 #145、#156 的行为证据为基线。保持 D-043 纯净门禁与既有缓存兼容。

## 已放弃的方向

登录验证码暂缓（D-02），保留归档 SQL（D-03），维持 M7 冻结（D-019 A）及 M6 阈值（D-023 A）。D-013/D-014/D-016 的缓存决策、D-031/D-032 的测试边界及 D-041/D-042 的批次规则继续有效。

## 给 Executor 的指令

以实时 Issue 从最新主干的干净副本按 #156 → #157 领取。按 [11-22 日报](https://github.com/zhangjszs/-weibo-sentiment-analysis/blob/c9e9e8dc39eb9246606f7da3c47b59e3bb72a324/.agent/DIARY/2026-11-22.md) 与 [11-23 日报](https://github.com/zhangjszs/-weibo-sentiment-analysis/blob/4386751e82e975bf57d9f85cae77d940ce044fdf/.agent/DIARY/2026-11-23.md) 延续追加历史，并刷新 [执行交接](https://github.com/zhangjszs/-weibo-sentiment-analysis/blob/4386751e82e975bf57d9f85cae77d940ce044fdf/.agent/HANDOFF.md)。
