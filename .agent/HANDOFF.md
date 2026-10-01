# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `DeepSeek-V4.1-Flash-20261001T141002Z`（DeepSeek-V4.1-Flash），
UTC 2026-10-01T14:10 ~ 14:2x。第四棒，本会话一轮：#32（承接上一棒 #31）。

## 本会话做了什么（一个 issue 关闭）

| Issue | 内容 | 要点 |
|-------|------|------|
| #32 | Security Scan 转绿但无门禁 | 加 Bandit HIGH/CRITICAL 阻断步骤；safety 无 secret 显式跳过 |

**背景**：上一棒 #31 把 Security Scan 从长期全红修成绿，但发现它"只会报告、
从不阻断"——等于没牙齿。本棒补上真正的信号。

## 本轮的改动（commit 557e97f，仅 `.github/workflows/security-scan.yml`）

- 新增步骤 **Bandit gate (HIGH/CRITICAL 阻断)**：`bandit -c .bandit -r src/ -lll`。
  `-lll` 只报 HIGH，退出码反映过滤后结果（已实测：有 HIGH→1，仅 LOW→0）。
  当前代码库 0 条 → 仍绿；将来引入 HIGH 会红。
- Safety 步骤读取 `secrets.SAFETY_API_KEY`：未配置时打 `::notice::` 跳过并写入
  占位 `safety-report.json`，不再留误导性空报告；配置该 secret 后自动启用。
- pip-audit 维持报告模式（依赖 CVE 阻断属另一策略，未动）。

**验证**：本地 YAML 校验通过；`bandit -lll` 退出 0；safety 跳过分支实测。
CI run 36874451853 ✅ / Security Scan run 36874452700 ✅，且已在日志确认
第 6 步 "Bandit gate" 实跑成功、safety 打了 `##[notice]` 跳过。

## 留白项（有意不做，供下一棒/人工决策）

1. **`requirements/requirements.audit.txt` 冗余**：无任何 workflow/脚本引用，
   内容与 `requirements/requirements.txt` 已漂移（versions 不一致），
   `docs/项目评估与规划.md` 第 195 条也记为"冗余"。候选：清理或立项。
2. **pip-audit 未阻断**：如需依赖 CVE 门禁，须先清点当前 CVE 并决定
   `--ignore-vuln` 白名单，属独立策略，建议单独立项。
3. **safety 仍要 secret 才有用**：若要让 CI 真正跑 Safety，需在仓库配置
   `SAFETY_API_KEY`（人工操作，agent 无法设置 secret）。
4. 更早遗留（#15/#16/#20 留白）：验证码、user.py String(100)/createTime、
   WS 刷新后取 token、nginx `/socket.io` 握手 101（需 Docker）——均见 git 历史。

## 坑与经验（重要，接力者必读）

1. **本仓库有两条状态检查，别混淆**：`CI`（backend-fast/frontend-fast/integration）
   与 `Security Scan`（bandit/safety/pip-audit）是**两个独立 workflow**。上一棒曾
   把后者误记为"连续六次转绿"，实为 20+ 次全红。核对 CI 时用
   `gh run list --workflow=security-scan.yml` 单独看。
2. **本地 pytest 必带 `-p no:launch_testing -p no:launch_ros`**（本机 ROS 插件
   collection 崩溃），详见 `.agent/ENV.md`；**勿写进 `pytest.ini`**。
3. **不要盲跑 `black`**：本地 black 会重排 122 个文件，CI 只跑 `ruff check`。
4. **bandit 多行 f-string 的 nosec 放闭合三引号那行**（写在起始行无效）。
5. `commit fix: #N` 自动关 issue；部分完成用 `refactor:`/`feat:`/`test:`/`chore:`。

## 下一步建议

- 无待办 issue。下一棒按协议第七节主动发现（先查重）。
- **首选候选**：清理/立项 `requirements/requirements.audit.txt` 冗余（见留白 1）——
  低风险、可本地闭环。
- 也可复核 Security Scan 首轮门禁稳定性（连续几次 push 是否稳定绿）。
- 功能类候选（更重）：user.py `String(100)`/`createTime` 统一、WS 刷新取 token。

## 环境备注

- 后端 `.venv` 齐全（Python 3.12）；fast gate 与 integration 本地均可跑。
- fast gate：`.venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -q --maxfail=1`
- **前端 node 必须走 mise 的 PATH**：`export PATH="$HOME/.local/share/mise/installs/node/22.23.2/bin:$PATH"`。
- 想看全部失败用例要 `-o addopts=""`；本地有真实 `.env`（含密钥，**勿提交**）。
- gh 可用（账号 zhangjszs）；bandit 已装在 `.venv`，safety/pip-audit 未装（勿污染 venv）。
- 本地分支 `wip/20260930T154700Z`（未推送）仍在，请人工确认去留。
