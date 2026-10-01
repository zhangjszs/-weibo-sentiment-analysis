# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `DeepSeek-V4.1-Flash-20261001T143237Z`（DeepSeek-V4.1-Flash），
UTC 2026-10-01T14:32 ~ 14:4x。第五棒，本会话一轮：#33（清理遗留野文件）。

## 本会话做了什么（一个 issue 关闭）

| Issue | 内容 | 要点 |
|-------|------|------|
| #33 | 删除冗余 `requirements/requirements.audit.txt` | 全仓零引用 + 内容漂移；同步两份目录树文档 |

## 本轮的改动（commit c1db85a）

- `git rm requirements/requirements.audit.txt`：确认 workflow / Dockerfile /
  scripts / pyproject / Makefile **零引用**，且内容已与 `requirements.txt` 漂移
  （27 行 vs 80 行，`circuitbreaker`/`flask-cors` 等版本目标矛盾）。
- `README.md`、`docs/LOCAL_DEPLOYMENT.md` 的目录树子节点同步移除该条目。
- 历史文档（`docs/plans/2026-07-06-sota-upgrade-design.md`、`docs/项目评估与规划.md`）
  属过去时记录，**未改**。

**验证**：`git grep requirements.audit` 现在只剩历史文档与 `.agent/`；
CI run 36877344592 / Security Scan run 36877344451 双绿（见 run 列表）。

## 留白项（有意不做，供下一棒/人工决策）

1. **`docs/项目评估与规划.md` 其余低优先项**（该文档是某时点快照，**先核实再动**）：
   - 25. `list/` 目录误建 venv
   - 26. 双日志目录（`logs/` + `src/logs/`）
   - 28. PyMySQL 仍列主依赖但 `src` 已不直接用
   - 21. requirements 版本未固定（部分已过时，需重估）
2. **pip-audit 未阻断**（见 #32）：依赖 CVE 门禁属独立策略。
3. **safety 需仓库配置 `SAFETY_API_KEY`** 才能真跑（人工操作）。
4. 更早遗留：#15/#16/#20 的验证码、user.py `String(100)`/`createTime`、
   WS 刷新后取 token、nginx `/socket.io` 握手 101（需 Docker）。

## 坑与经验（重要，接力者必读）

1. **CI 与 Security Scan 是两个独立 workflow**：核对时分别用
   `gh run list` 与 `gh run list --workflow=security-scan.yml`。上一棒曾混淆。
2. **本地 pytest 必带 `-p no:launch_testing -p no:launch_ros`**（本机 ROS 插件
   collection 崩溃），详见 `.agent/ENV.md`；**勿写进 `pytest.ini`**。
3. **不要盲跑 `black`**：本地 black 会重排 122 个文件，CI 只跑 `ruff check`。
4. **bandit 多行 f-string 的 nosec 放闭合三引号那行**（写在起始行无效）。
5. `commit fix: #N` 自动关 issue；`chore:` 不是关闭关键字，需另加 `Closes #N`。
6. 删文件用 `git rm`（保持索引一致）；改文档条目后**复查目录树的连线字符**
   （`├──`→`└──`）是否仍正确。

## 下一步建议

- 无待办 issue。下一棒按协议第七节主动发现（先查重）。
- **首选候选**：核实并清理 `docs/项目评估与规划.md` 低优先项 25/26/28
  （`list/` 误建 venv、双日志目录、PyMySQL 依赖）——低风险、可本地闭环。
  注意该文档是快照，动手前先确认现状是否仍成立。
- 也可复核 Security Scan 带门禁后的稳定性（连续几次 push 是否稳定绿）。

## 环境备注

- 后端 `.venv` 齐全（Python 3.12）；fast gate 与 integration 本地均可跑。
- fast gate：`.venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -q --maxfail=1`
- **前端 node 必须走 mise 的 PATH**：`export PATH="$HOME/.local/share/mise/installs/node/22.23.2/bin:$PATH"`。
- 想看全部失败用例要 `-o addopts=""`；本地有真实 `.env`（含密钥，**勿提交**）。
- gh 可用（账号 zhangjszs）；bandit 已装在 `.venv`，safety/pip-audit 未装（勿污染 venv）。
- 本地分支 `wip/20260930T154700Z`（未推送）仍在，请人工确认去留。
