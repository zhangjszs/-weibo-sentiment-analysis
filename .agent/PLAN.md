# PLAN — 开发路线图

> 2026-11-23 · Planner 维护。GitHub Issue 是任务权威。原工作树 `main` 为 `c2f33f8`，有六个原有未暂存文件；默认权限下 fetch 因 `.git/FETCH_HEAD` 只读退出 255，pull --rebase 因未暂存改动退出 128。隔离副本已 fetch/prune 并 pull --rebase，规划基线为 `cdb255c`。

## 当前方向

收尾前端依赖审计与覆盖率验证，随后把 D-009 已授权的渐进式 TypeScript 工作转到公共请求层。#145 已核对接口和依赖闭环。下一步验证导航装配与类型门禁，并用可重复的回归测试锁定混合 401 的现有行为。前端 TS 第四批仍为 6/6 已验收。

## 今日目标（2026-11-23）

- [#146](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/146#issuecomment-7091137981) 已通过并关闭。锁文件五项定向更新、五个目标告警消失、47 文件 / 321 用例和原 PR 五项 CI 均已复核。
- [#147](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/147#issuecomment-7091139293) 部分通过，退回 `in-progress`。认可样本内的计数与映射证据；补两个回退分支计数和仓库外探针的干净目录复跑。[#143](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/143#issuecomment-7091138663) 保留历史 auth 双漂移的独立阻塞。
- 推进混合 401 回归基线及请求层编译与入口装配验证，各有独立验收。

## 当前 Milestone · 前端请求层迁移准备（0 / 2）

### 目标与验收

- 公共请求的两种 401 交错仍共享一个导航窗口，首次跳转前清除内存 token、持久化键和 `/me` TTL 缓存。业务码保留新 Error 的消息，HTTP 路径保留拒绝对象身份。
- D-043 候选门禁为 8 个生产 TS / 0 个 JS 或 Vue。入口在 `app.use(router)` 前装配实时路径读取和 `replace`，原有启动过程和响应包络有可核查的等价标准。

### 完成信号

- #150 仅测试增补通过验收，两种到达顺序和导航窗口关闭后的重新跳转均覆盖。
- #151 只在 §9 交付可复核的隔离编译结果、两个负例与入口契约。若发现候选无法满足验收，记录具名阻塞并保留 Milestone 开放。

### 明确非目标

- 本阶段范围限测试与迁移规格。生产 transport、API 包装、router、store 和缓存类型迁移另行立项。
- 保持既有 API、认证权限、数据结构、主要 CI、覆盖配置和阈值。覆盖率合并工具补丁暂缓，待具备跨 transform 组、混合粒度与源分支归属证据。

### 执行队列（2 个 `ready`）

1. [#150](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/150) 锁定公共请求混合 401 的缓存清理与跳转去重（P3）。
2. [#151](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/151) 验证公共请求层的 TypeScript 类型契约与入口接线（P2）。

建议先锁定回归行为，再整理迁移规格。两项均从已验收的 #145 出发，可独立领取。

## 已知阻塞与依赖

- #147 已退回原执行现场。只补 Issue 中的两条差距。
- #143 `blocked`，需要稳定触发 `auth.js` 和 `Login.vue` 历史双漂移的原始输入和顺序。#138 保留为历史现象记录。
- #109 `blocked`，待可用容器环境或已授权测试主机，验收须跑真实 OTLP / Jaeger 链路。
- #98 按 D-019 A 冻结执行现场。#96/#100/#101/#102 维持 `needs-info`，其中 #102 还依赖 #98。#59 按 D-012 A 等待具体产品需求。
- M6 10/10 成员关闭，仍 OPEN。记录中的成功信号为 1/3，串行 <30s 与完整 CI <240s 仍无达标证据。M7 6/11 成员关闭，仍 OPEN 且冻结。

## 下一阶段

请求层准备验收后，按候选证据确定仅迁移公共 transport 的生产切片，再按六个接口逐项定义 API 包络。历史覆盖率数据继续用逐文件和原始计数器作迁移锚点。

## 已放弃的方向

登录验证码暂缓（D-02）、保留归档 SQL（D-03）、跳过整包和训练缓存（D-013/D-014/D-016）、暂缓 M7 扩展（D-019 A）、维持 M6 阈值（D-023 A）、跳过薄包装和壳层复述测试（D-031/D-032）。批次工具治理独立处理（D-042），`deepClone` 断言只观察（D-041）。

## 给 Executor 的指令

从最新 main 的隔离副本领取 #150 → #151，并按 #147 验收评论补证。以实时 Issue 刷新执行快照，并按 [昨日日报所在分支](https://github.com/zhangjszs/-weibo-sentiment-analysis/blob/c9e9e8dc39eb9246606f7da3c47b59e3bb72a324/.agent/DIARY/2026-11-22.md) 延续追加历史。
