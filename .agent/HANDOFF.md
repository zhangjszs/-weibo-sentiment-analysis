# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `DeepSeek-V4.1-Flash-20261001T143939Z`（DeepSeek-V4.1-Flash），
UTC 2026-10-01T14:39 ~ 14:5x。第六棒，本会话一轮：#34。

## 本会话做了什么（一个 issue 关闭）

| Issue | 内容 | 要点 |
|-------|------|------|
| #34 | 覆盖率门禁是死配置 | CI backend-fast 加 `--cov=src`，激活 pyproject 的 `fail_under=50` |

## 本轮的改动（commit 6c11673，仅 `.github/workflows/ci.yml`）

- backend-fast 测试步骤：`pytest -m "unit or api" -q --maxfail=1`
  → 追加 `--cov=src --cov-report=term-missing`。
- 效果：`pyproject.toml` 的 `[tool.coverage.report] fail_under = 50` 从"死配置"
  变为真实门禁（此前 CI 从不传 `--cov`，覆盖率根本不生成）。

**验证**：
- 本地全量 unit+api：覆盖率 **65.11%**，退出 0；单文件低覆盖时 pytest-cov 报
  `FAIL Required test coverage of 50.0% not reached` 退出 1（证明门禁生效）。
- CI run 36879311174 ✅：日志确认 `Required test coverage of 50.0% reached.
  Total coverage: 65.22%`。Security Scan run 36879311203 ✅。

## 重要：`docs/项目评估与规划.md` 是过时快照，不要照单直取

本棒的 HANDOFF/上一棒曾建议清理该文档的低优先项 25/26/28，**现场核实全部已不成立**：

- 25. `list/` 目录误建 venv —— 目录**已不存在**
- 26. 双日志目录 —— `logs/` 已无，仅 `src/logs/`（且被 gitignore，属运行产物）
- 28. PyMySQL 主依赖 —— `src` 无任何直接 `import pymysql`，经 SQLAlchemy URL 使用
- 7. `pickle.load` —— 全仓无命中
- 9. `init_database.sql` 含 DROP DATABASE + 明文密码 —— 该文件是 **schema 唯一真相**
  （CI `sed 's/`wb`/`weibo_test`/'` 后建库、compose 挂载初始化），密码已 bcrypt 哈希
  （注释里的明文仅供开发演示）；属**已缓解的设计**，非待修缺陷。

**教训**：该文档是历史时点评估，动手前必须 `git grep`/`ls` 现场核实。

## 留白项（有意不做，供下一棒/人工决策）

1. **覆盖率阈值只有 50%，实际 65%**：可考虑上调 fail_under（如 60%）作为更紧的门禁，
   但需评估向后兼容，建议单独立项。
2. **integration job 无覆盖率**：只给 backend-fast（unit+api）加了门禁；是否需要给
   integration 也生成覆盖率，属可选。
3. **pip-audit 未阻断**（见 #32）：依赖 CVE 门禁属独立策略。
4. **safety 需仓库配置 `SAFETY_API_KEY`** 才能真跑（人工操作）。
5. 更早遗留：#15/#16/#20 的验证码、user.py `String(100)`/`createTime`、
   WS 刷新后取 token、nginx `/socket.io` 握手 101（需 Docker）。

## 坑与经验（重要，接力者必读）

1. **`docs/项目评估与规划.md` 是快照，会误导**——见上节。
2. **CI 与 Security Scan 是两个独立 workflow**：核对分别用 `gh run list` 与
   `gh run list --workflow=security-scan.yml`。
3. **本地 pytest 必带 `-p no:launch_testing -p no:launch_ros`**（本机 ROS 插件
   collection 崩溃），详见 `.agent/ENV.md`；**勿写进 `pytest.ini`**。
4. **不要盲跑 `black`**：本地 black 会重排 122 个文件，CI 只跑 `ruff check`。
5. **pytest-cov 会读取 pyproject 的 `fail_under`**：只要传 `--cov`，阈值自动生效，
   无需在 CI 重复写 `--cov-fail-under`。
6. bandit 多行 f-string 的 nosec 放**闭合三引号那行**（写在起始行无效）。
7. `commit fix: #N` 自动关 issue；`chore:` 不是关闭关键字，需另加 `Closes #N`。
8. 后台 `gh run watch` 偶发对成功的 run 返回非 0 —— **以 `gh run view` 的
   conclusion 为准**（本会话遇到过）。

## 下一步建议

- 无待办 issue。下一棒按协议第七节主动发现（先查重）。
- **首选候选**：评估把覆盖率阈值从 50% 上调到更贴近现状（65%）的值，
  作为更紧的门禁（见留白 1）；需先决定目标阈值。
- 也可复核 CI 覆盖率门禁稳定性（连续几次 push 是否稳定绿）。
- 功能类候选（更重）：user.py `String(100)`/`createTime` 统一、WS 刷新取 token。

## 环境备注

- 后端 `.venv` 齐全（Python 3.12）；fast gate 与 integration 本地均可跑。
- fast gate：`.venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -q --maxfail=1`
- **前端 node 必须走 mise 的 PATH**：`export PATH="$HOME/.local/share/mise/installs/node/22.23.2/bin:$PATH"`。
  前端现状：lint 0 error（103 warning）、73 测试全过。
- 想看全部失败用例要 `-o addopts=""`；本地有真实 `.env`（含密钥，**勿提交**）。
- gh 可用（账号 zhangjszs）；bandit/pytest-cov 已装在 `.venv`，safety/pip-audit 未装（勿污染 venv）。
- 本地分支 `wip/20260930T154700Z`（未推送）仍在，请人工确认去留。
