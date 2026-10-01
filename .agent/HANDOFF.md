# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `DeepSeek-V4.1-Flash-20261001T120450Z`（DeepSeek-V4.1-Flash），
UTC 2026-10-01T12:04 ~ 12:2x。第三棒，本会话一轮：#31。

## 本会话做了什么（一个 issue 关闭）

| Issue | 内容 | 要点 |
|-------|------|------|
| #31 | Security Scan 工作流 20/20 全红 | 恢复 `|| true`、6 处 md5 加 usedforsecurity=False、B608/B615/B105 加 nosec、新增 `.bandit`；报告 111→0 |

**关键发现（纠正上一棒的错误记录）**：上一棒 HANDOFF/STATE 写"Security Scan
连续六次转绿"，与事实相反——`gh run list --workflow=security-scan.yml` 显示
main 上**连续 20+ 次全部 failure**，从未绿过。上一棒把 CI 与 Security Scan
两个 workflow 混淆了。根因是 `9536e2b`（traeagent "Review and Update Project
to SOAT"）删除了 `d36906b` 为三条扫描命令加的 `|| true`，导致任一发现即
step 以退出码 1 中止。本轮已修复。

数字基线：后端 fast gate **1261 passed, 3 skipped, 197 deselected**（绿）；
bandit `-c .bandit -r src/` **0 发现**；ruff 0。

## 本轮的改动（commit 0fd132f）

- `.github/workflows/security-scan.yml`：三条扫描命令恢复 `|| true`，bandit 加 `-c .bandit`。
- `.bandit`（新增）：跳过 B311/B110 两类噪音，附带理由注释。
- 6 个源文件：`hashlib.md5(...)` → `hashlib.md5(..., usedforsecurity=False)`
  （缓存键/去重哈希，非安全用途）。
- 4 处误报加 `# nosec` 并注明依据：B608×2（分桶 SQL 仅插值白名单列名+整数）、
  B615×1（本地模型目录 from_pretrained）、B105×1（脱敏正则）。

## 留白项（有意不做，供下一棒/人工决策）

1. **Security Scan 只报告不阻断**：这是 d36906b 的既定策略，本轮尊重之。
   若希望它成为真正的门禁（如仅 HIGH 阻断），需产品/安全侧决策后另行改造。
2. **safety scan 需要登录**：CI 无 `SAFETY_API_KEY`，该步在 `|| true` 下静默跳过，
   报告可能为空。若要在 CI 用 Safety 需配置 secret。
3. **bandit 的 B110 被整体跳过**：try/except/pass 属风格问题；若想收紧，
   逐处复核后再从 `.bandit` 移除 B110。
4. 上一棒遗留：验证码、user.py String(100)/createTime、WS 刷新后取 token、
   jti/锁定多 worker 语义、conftest 两套 SQLite 语义——均见 git 历史，未动。

## 坑与经验（重要，接力者必读）

1. **本地 pytest 必带 `-p no:launch_testing -p no:launch_ros`**：本机 shell 源过
   ROS 2 的 setup.bash，launch_testing 注册为 pytest11 插件，依赖 `osrf_pycommon`
   缺失，直接在 collection 阶段崩溃。**不要**把这个写进 `pytest.ini`（CI 无此问题，
   属机器相关污染）；写进 `.agent/ENV.md` 即可。
2. **不要在本仓库盲跑 `black`**：本地 black（26.5.1）会把 122 个文件全部重排
   （如 PROVINCE_MAP 逐行展开），与仓库现有风格不符。CI 只跑 `ruff check`，
   **不跑 black**。改动请手工贴合周围风格，勿用 black 批量格式化。
3. **bandit 多行 f-string 的 nosec 放"闭合三引号那行"**：bandit 把 B608 报在
   `sql = f"""` 起始行，但 nosec 需写在闭合 `"""` 行（已验证生效），写在起始行会
   被当成字符串内容或被忽略。
4. **commit `fix: #N` 自动关闭 issue**（GitHub closing keyword）；部分完成用
   `refactor:`/`feat:`/`test:`/`chore:` 开头。
5. 其余历史坑（conftest 勿回退、config 模块重导入、axios mock）见上一棒记录，
   仍有效。

## 下一步建议

- 无待办 issue。下一棒按协议第七节主动发现（先查重）。
- **优先核对**：本轮 push 后 Security Scan 是否**首次转绿**（此前 20+ 次全红）；
  若仍红，看具体是哪一步（safety/pip-audit 在 `|| true` 下不应失败）。
- 可继续核对 #20 留的 nginx `/socket.io` 上线握手 101（需 Docker，本机无）。
- 有意的候选议题（需先查重）：`safety` 步骤在无 secret 下的空报告、
  是否给 Security Scan 加真正的严重度门禁。

## 环境备注

- 后端 `.venv` 齐全（Python 3.12）；fast gate 与 integration 本地均可跑。
- fast gate 命令：`.venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -q --maxfail=1`
- **前端 node 必须走 mise 的 PATH**：`export PATH="$HOME/.local/share/mise/installs/node/22.23.2/bin:$PATH"`。
- 想看全部失败用例要 `-o addopts=""`（pytest.ini 的 addopts 自带 `--maxfail=1`）。
- 本地有真实 `.env`（含密钥，**勿提交**），会影响起子进程的用例。
- gh 可用（账号 zhangjszs）。
- 本地分支 `wip/20260930T154700Z`（73cd2a7，未推送，pytest.ini 屏蔽 ROS 的旧尝试）
  仍存在；本轮改走 ENV.md 记录，未采用该分支做法，请人工确认去留。
