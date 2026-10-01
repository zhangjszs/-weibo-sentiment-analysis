# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `DeepSeek-V4.1-Flash-20261001T151034Z`（DeepSeek-V4.1-Flash），
UTC 2026-10-01T15:10 ~ 15:1x。第八棒，本会话一轮：#36。

## 本会话做了什么（一个 issue 关闭）

| Issue | 内容 | 要点 |
|-------|------|------|
| #36 | 给过时评估文档加历史快照横幅 | 防止接力/人工被 `docs/项目评估与规划.md` 的旧条目误导 |

## 本轮的改动（commit d80deb5，仅 `docs/项目评估与规划.md`，纯文档）

- 文档顶部加横幅：**「历史快照 · 勿照单直取」**，说明该文是 2026-07-30 时点评估、
  多条结论已被后续多轮修复取代，动手前须现场核实代码/CI，现状以代码、CI 与
  `.agent/STATE.md` 为准。
- 横幅列出已现场核实的过时条目作示例：25 `list/`、26 双日志目录、28 PyMySQL、
  16 覆盖率门禁、7 `pickle.load`、9 `init_database.sql` 明文密码。

**验证**：纯文档改动，无构建/测试影响；CI + Security Scan 见 run 列表（应绿）。

## 留白项（有意不做，供下一棒/人工决策）

1. **integration job 无覆盖率**：覆盖率门禁只加在 backend-fast（unit+api）。
   如需覆盖 integration，需评估其夹具/DB 依赖，建议单独立项。
2. **pip-audit 未阻断**（见 #32）：依赖 CVE 门禁属独立策略，须先清点 CVE 白名单。
3. **safety 需仓库配置 `SAFETY_API_KEY`** 才能真跑（人工操作 secret）。
4. 更早遗留（功能类，较重）：#15/#16/#20 的验证码、user.py `String(100)`/`createTime`
   统一、WS 刷新后取 token、nginx `/socket.io` 握手 101（需 Docker）。
5. `docs/项目评估与规划.md` 正文条目本身**未逐条改写**（仅加横幅）——若要让其
   重新可用，需逐条复核现状并标注，工作量大，未做。

## 坑与经验（重要，接力者必读）

1. **`docs/项目评估与规划.md` 已加横幅**，动手前先读横幅；其条目多为历史状态。
2. **CI 与 Security Scan 是两个独立 workflow**：核对分别用 `gh run list` 与
   `gh run list --workflow=security-scan.yml`。
3. **本地 pytest 必带 `-p no:launch_testing -p no:launch_ros`**（本机 ROS 插件
   collection 崩溃），详见 `.agent/ENV.md`；**勿写进 `pytest.ini`**。
4. **不要盲跑 `black`**：本地 black 会重排 122 个文件，CI 只跑 `ruff check`。
5. **覆盖率阈值唯一真相在 `pyproject.toml`**（`fail_under=60`）：CI 只传 `--cov`，
   勿另写 `--cov-fail-under`。
6. bandit 多行 f-string 的 nosec 放**闭合三引号那行**（写在起始行无效）。
7. `commit fix: #N` 自动关 issue；`chore:`/`docs:` 不是关闭关键字，需另加 `Closes #N`。
8. 后台 `gh run watch` 偶发对成功的 run 返回非 0 —— **以 `gh run view` 的
   conclusion 为准**（本会话多次遇到）。

## 下一步建议

- 无待办 issue。下一棒按协议第七节主动发现（先查重）。
- **首选候选**：评估给 integration job 加覆盖率（见留白 1）——与近期覆盖率
  工作同片区；需先确认 integration 本地/CI 可跑通并测量覆盖率。
- 备选：功能类遗留（user.py `String(100)`/`createTime` 统一）——较重，涉 schema 迁移。
- 也可顺手确认仓库长期健康（fast gate / frontend / integration 是否稳定绿）。

## 环境备注

- 后端 `.venv` 齐全（Python 3.12）；fast gate 与 integration 本地均可跑。
- fast gate：`.venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -q --maxfail=1`
- 覆盖率本地跑法：上条命令追加 `--cov=src --cov-report=term-missing`（阈值读 pyproject）。
- **前端 node 必须走 mise 的 PATH**：`export PATH="$HOME/.local/share/mise/installs/node/22.23.2/bin:$PATH"`。
  前端现状：lint 0 error（103 warning）、73 测试全过。
- 想看全部失败用例要 `-o addopts=""`；本地有真实 `.env`（含密钥，**勿提交**）。
- gh 可用（账号 zhangjszs）；bandit/pytest-cov 已装在 `.venv`，safety/pip-audit 未装（勿污染 venv）。
- 本地分支 `wip/20260930T154700Z`（未推送）仍在，请人工确认去留。
