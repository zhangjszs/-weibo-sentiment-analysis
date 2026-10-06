# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `glm-20261002T000100Z`（GLM 执行棒），UTC 2026-10-02T00:01 开始、
2026-10-06T08:2x 收尾（会话跨 4 天——中途其他接力棒在同一工作目录完成了
M2/M3 与 D-006~D-008，本棒在重新同步后抢救遗留并取队列任务）。

## 本会话做了什么

### 1. 抢救 #39 后续（commit 7c6a3f8）
本棒原以 #39 开工，实施被并行接力棒先行落地后，本棒的两项增量仍有价值并已提交：
- **predict 页 BaseChart 缺 import 修复**：模板用 `<BaseChart>` 但从未 import
  也无全局注册——仪表盘在该页一直渲染为空（既有缺陷，模板标签审计发现）
- **图标注册完整性守护测试**：静态扫描全部字符串图标引用，断言都在
  `ICON_COMPONENTS` 注册表且为 icons-vue 真实导出

### 2. #52 修复关闭（commit d968188）
**根因**：`Math.max(...([] || [1000]))` 因空数组真值短路得 -Infinity，
visualMap 连续渐变抛 addColorStop(undefined)；首屏 + watch 各一次 = 2 pageerror。
**修复**：抽 `resolveVisualMapMax()` 纯函数（空→1000 同演示尺度、非空取最大、
下限 1 防退化）。
**验证**：重建 #43 式空库冒烟（Playwright + SQLite 后端，脚本已入库
`scripts/smoke_bigscreen_empty_db.py`）：RED 2 pageerror → 硬编码实验定位 →
GREEN 0 错误；五门禁全绿（前端 14 文件 82 测试）；CI run 37437439077 绿。

## 留白 / 新发现（下一棒参考）

1. **AUTO_CREATE_DEMO_ADMIN 在 SQLite 上失效**：demo admin 引导 SQL 用
   `NOW()`（MySQL 方言），SQLite 报 `no such function: NOW`（#52 冒烟实测）。
   小修复（改数据库无关时间函数），可立项。
2. **dist 缺 favicon.ico**：SW precache 清单含 `/favicon.ico` 但 public/ 无
   此文件 → SW install 可能失败（#55 已含 favicon 404 项，顺带核对 precache）。
3. in-review 9 项（#43~#47、#48~#51）仍待 Planner 验收。
4. 剩余队列：#54/#55（P4）、#53（needs-info，等用户/Planner）。

## 环境备注

- 后端 `.venv`（Python 3.12）+ playwright 1.63 + chromium 可用，空库冒烟
  三步：`TEST_DATABASE_URL=sqlite://... python -c "database.init_db()"` →
  种 admin（bcrypt）→ 起 run.py + vite dev → 跑冒烟脚本。
- **前端 node 必须走 mise 的 PATH**：`export PATH="$HOME/.local/share/mise/installs/node/22.23.2/bin:$PATH"`。
- 本地有真实 `.env`（勿提交）；导出环境变量优先级高于 .env（load_dotenv 不覆盖）。
- gh 可用（账号 zhangjszs）。
