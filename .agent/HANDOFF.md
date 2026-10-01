# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `DeepSeek-V4.1-Flash-20261001T145524Z`（DeepSeek-V4.1-Flash），
UTC 2026-10-01T14:55 ~ 15:0x。第七棒，本会话一轮：#35。

## 本会话做了什么（一个 issue 关闭）

| Issue | 内容 | 要点 |
|-------|------|------|
| #35 | 覆盖率阈值 50%→60% | 门禁更贴近现状、更早发现退化；阈值仍单源于 pyproject |

## 本轮的改动（commit 3276170，仅 `pyproject.toml`）

- `[tool.coverage.report] fail_under` 由 **50 → 60**。
- 保留 ~5% 缓冲（实测 65%），CI 命令无需改动（阈值读取自 pyproject）。

**验证**：
- 本地同 CI 命令：`Required test coverage of 60.0% reached. Total coverage: 65.11%`，退出 0。
- CI run 36880776590 ✅：日志确认 `Required test coverage of 60.0% reached.
  Total coverage: 65.22%`。Security Scan run 36880776716 ✅。

## 覆盖率门禁现状（#34 + #35 累计）

- `ci.yml` backend-fast：`pytest -m "unit or api" -q --maxfail=1 --cov=src --cov-report=term-missing`
- 阈值：`pyproject.toml` `fail_under = 60`（唯一真相）
- 覆盖率：本地 ~65.1% / CI ~65.2%

## 留白项（有意不做，供下一棒/人工决策）

1. **`docs/项目评估与规划.md` 是过时快照，建议加"历史文档"横幅**：其低优先项
   25/26/28、7、16、9 等多已被处理或已不成立，但文档本身无任何提示，屡屡
   误导接力者（上一棒即被 HANDOFF 的该建议带偏）。给它加一条头部说明
   （"本文为某时点评估，已被多轮修复取代，现状以代码/CI 为准"）属低风险改进。
2. **integration job 无覆盖率**：门禁只加在 backend-fast。
3. **pip-audit 未阻断**（见 #32）：依赖 CVE 门禁属独立策略。
4. **safety 需仓库配置 `SAFETY_API_KEY`** 才能真跑（人工操作）。
5. 更早遗留：#15/#16/#20 的验证码、user.py `String(100)`/`createTime`、
   WS 刷新后取 token、nginx `/socket.io` 握手 101（需 Docker）。

## 坑与经验（重要，接力者必读）

1. **`docs/项目评估与规划.md` 是快照，会误导**——见留白 1。
2. **CI 与 Security Scan 是两个独立 workflow**：核对分别用 `gh run list` 与
   `gh run list --workflow=security-scan.yml`。
3. **本地 pytest 必带 `-p no:launch_testing -p no:launch_ros`**（本机 ROS 插件
   collection 崩溃），详见 `.agent/ENV.md`；**勿写进 `pytest.ini`**。
4. **不要盲跑 `black`**：本地 black 会重排 122 个文件，CI 只跑 `ruff check`。
5. **覆盖率阈值唯一真相在 `pyproject.toml`**：CI 只传 `--cov`，不要另写
   `--cov-fail-under`（会双源漂移）。
6. bandit 多行 f-string 的 nosec 放**闭合三引号那行**（写在起始行无效）。
7. `commit fix: #N` 自动关 issue；`chore:` 不是关闭关键字，需另加 `Closes #N`。
8. 后台 `gh run watch` 偶发对成功的 run 返回非 0 —— **以 `gh run view` 的
   conclusion 为准**（本会话两次遇到）。

## 下一步建议

- 无待办 issue。下一棒按协议第七节主动发现（先查重）。
- **首选候选**：给 `docs/项目评估与规划.md` 加"历史快照"横幅（见留白 1）——
  低风险、直接减少后续接力被误导。
- 也可评估给 integration job 加覆盖率，或继续功能类遗留（user.py schema 统一等）。

## 环境备注

- 后端 `.venv` 齐全（Python 3.12）；fast gate 与 integration 本地均可跑。
- fast gate：`.venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -q --maxfail=1`
- **前端 node 必须走 mise 的 PATH**：`export PATH="$HOME/.local/share/mise/installs/node/22.23.2/bin:$PATH"`。
  前端现状：lint 0 error（103 warning）、73 测试全过。
- 想看全部失败用例要 `-o addopts=""`；本地有真实 `.env`（含密钥，**勿提交**）。
- gh 可用（账号 zhangjszs）；bandit/pytest-cov 已装在 `.venv`，safety/pip-audit 未装（勿污染 venv）。
- 本地分支 `wip/20260930T154700Z`（未推送）仍在，请人工确认去留。
