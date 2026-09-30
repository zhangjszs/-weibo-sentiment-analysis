# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：（空）主干已恢复，等待下一棒按优先级挑选 open issue
- 建议下一步：#14（High，性能）或 #19/#20（前端 Loading / WebSocket 死链）
- 状态：空闲

## 阻塞项
- （无）

## 关键事实（已实测验证）
- `main` 未设分支保护，可直接推送
- origin/main 原停在 b8311a4；本地 #5~#26 的修复全部未推送，本轮已全部推送
- 主干自 2026-08-30 起持续红，根因是 CI `ruff check src/ tests/` 有 1609 个错误
  （即 #29）——#5~#26 的修复因此长期没能进入主干。本轮清零后已恢复
- 冷/热缓存下 `test_staging_is_protected` 曾稳定失败：子进程继承 CI 的
  SECRET_KEY/JWT_SECRET_KEY/ALLOWED_ORIGINS，使 staging 下 validate() 合法通过。
  已改为显式置空四个键，CI 同款 env 下 4/4 通过
- 本地实测门禁：ruff 0；`pytest -m "unit or api"` 1249 passed, 3 skipped；
  `npm run test:run` 4 files/45 tests；`npm run build` 成功
- integration 层需 MySQL+Redis，本地未跑（CI 覆盖）
- 前端 Node 需 mise 的 node 22 在 PATH 中，系统 PATH 无 node/npm

## 已完成
- #29 后端 Ruff 全仓清零（1609 → 0），fast gate 与 CI 恢复可执行
- #29 staging 密钥校验测试改为自证环境，不再依赖「本机无这些变量」的偶然前提
- #25 CI 门禁补齐：前端单测入 CI、集成随 PR 跑、env 补 ALLOWED_ORIGINS/ADMIN_USERS
- 清理死代码：contextual_sentiment 的 base_weight、sentiment_backend 的 last_error、
  sentiment_strategy_selector 的未用 performance 查询、model_version_manager 的
  recent_performance（均为 F841/B007 报出的等价改写，无行为变化）
- tests/ E402 按 issue #29 范围约定设 per-file baseline，src/ 仍必须清零
