# 前端用户体验与技术债务现状调研

> Issue #60 产出。纯调研，**未修改任何源码**。
> 调研时间：2026-10-09（UTC）。分支 `agent/issue-60-ux-tech-debt-audit`。
> 基线验证：`npm run test:run` → 16 files / 88 tests 全过（退出码 0）；
> `npm run lint` → 退出码 0（`--max-warnings 0`）。
>
> **路径约定**：本文所有 `src/...` / `tests/...` 路径均相对于 `frontend/`，
> 即 `src/views/alert/center.vue` 指 `frontend/src/views/alert/center.vue`。
> 不带 `src/` 前缀的路径（如 `scripts/`、`docs/`）相对于仓库根。

## 0. 调研方法与证据来源

所有结论均来自以下可复现手段，无主观推测：

| 手段 | 命令 / 对象 |
|---|---|
| 全量文件枚举 | `find src/views -name "*.vue"` → 24 个视图；`find src/views src/components -name "*.vue"` → 46 个；`src/` 合计 17,296 行 |
| 三件套扫描 | `grep -rn "v-loading\|el-skeleton\|:loading=\|el-empty\|ElMessage\.error\|catch"` |
| 跨层追查 | 视图的 loading/error 常在 `src/composables/` 中，逐个读取 9 个 composable 与 22 个组件确认是否透出到用户 |
| 响应式扫描 | `grep -rn ':xs=\|:sm=\|:md=\|:lg=\|:xl=\|:span=\|@media'` |
| 死代码扫描 | 对每个 `src/**/*.{js,vue}` 按「无任何 importer」判定（extension-aware，排除相对导入误报后人工复核） |
| 测试覆盖 | 逐个读取 `frontend/tests/` 16 个文件，区分真实 mount / 真实模块执行 / 纯逻辑 / 静态 grep |
| TODO 扫描 | `grep -rn "TODO\|FIXME\|HACK\|XXX"` → **零命中**，与 #60 背景描述一致；债务只能靠本调研发现 |

范围说明：`src/views/error/{403,404,500}.vue` 与 `src/views/system/Help.vue` 为**静态页**（无异步数据），三件套不适用，下文标记 N/A，不计入缺口。

---

## 1. 维度一：UX 反馈完整性（loading / 错误提示 / 空状态）

### 1.1 两个全局兜底（先声明，避免误判）

这两层机制让「无视图级错误处理」不至于完全无声，但**不能替代**视图级反馈：

1. **中文空态兜底**：`src/App.vue:2` `<el-config-provider :locale="zhCn">` + `src/App.vue:9` 引入 `element-plus/dist/locale/zh-cn.mjs`。因此所有 `el-table` 数据为空时**自带中文「暂无数据」占位**——下表「built-in」即指此，是真实可见的空态，不是英文 "No Data"。
2. **全局错误 toast 兜底**：`src/api/request.js` 响应拦截器对信封错误码（401/403/404/500/default）与网络错误均弹出 `ElMessage` 后 `reject`（`request.js:98-163`）。因此标 ❌ 的页面在请求真失败时**仍有一条通用 toast**。

❌ 的真实含义是：**无视图/区域级错误态、无重试入口，且 HTTP 200 但载荷缺失时完全静默**——即 `if (res.code === 200)` 之后的赋值路径（如 `useAlert.js:104` 的 `alerts.value = res.data.alerts`，`res.data` 缺失时抛 TypeError 被空 catch 吞掉）。

### 1.2 24 视图覆盖矩阵

| 视图 | loading 态 | 错误提示 | 空状态 |
|---|---|---|---|
| `views/alert/center.vue` | ✅ `:9` → `components/alert/AlertList.vue:33` `v-loading` | ❌ `useAlert.js:108/121/132` 仅 `console.error` | ⚠️ built-in 表格；规则子面板 `center.vue:40-53` 无空态 |
| `views/analysis/article.vue` | ✅ `:53`、`:139` | ✅ `:372`、`:413` | ✅ built-in（两表） |
| `views/analysis/comment.vue` | ⚠️ 仅列表 `:111 :loading="listLoading"`；`loading`（声明 `:184`，置位 `:239/:252`）**从未在模板绑定** | ✅ `:250`、`:291` | ⚠️ built-in 表格；热门评论 `:44-56` 无空态 |
| `views/analysis/hotWords.vue` | ✅ `:71` | ✅ `:166`、`:198` | ✅ built-in |
| `views/analysis/ip.vue` | ✅ `:49`（+ 地图占位 `:16`「地图数据加载中…」） | ✅ `:157`（+ 地图 `:92` warning） | ✅ built-in |
| `views/analysis/platform.vue` | ❌ **全文 0 处 loading 绑定** | ❌ `:305/:316/:327` 仅 `console.error` | ✅ `:129` `el-empty 暂无数据` |
| `views/analysis/predict.vue` | ✅ `:33 v-loading="loadingModelInfo"` | ⚠️ 预测动作有 toast（`usePredict.js:157/160/233/236`），但挂载取模型信息仅 `console.error`（`usePredict.js:189`） | ✅ `:54`、`:107` |
| `views/analysis/propagation.vue` | ✅ `:85 v-loading` 主区域 | ✅ `:293` | ✅ `:87`、`:115` |
| `views/analysis/sentiment.vue` | ✅ `:148 :loading="loading"` | ✅ `useSentiment.js:409` | ⚠️ built-in 表格；关键词云 `:89-102` 无空态 |
| `views/analysis/spider.vue` | ❌ 仅动作按钮 `:13/:152/:231` 与运行条 `:21-36`；**首屏加载无任何指示** | ❌ `useSpider.js:56/:65` 仅 `console.error` | ✅ `:171`、`:239` |
| `views/analysis/weiboStats.vue` | ✅ `:41` | ✅ `:122` | ✅ built-in |
| `views/analysis/wordCloud.vue` | ✅ `:50`（+ 按钮 `:13/:32`） | ✅ `:121`、`:140`、`:192` | ✅ built-in |
| `views/auth/Login.vue` | ✅ `:45` 提交按钮（表单充分） | ✅ `:107` | N/A（表单） |
| `views/auth/Register.vue` | ✅ `:52` 提交按钮 | ✅ `:127`、`:130` | N/A（表单） |
| `views/dashboard/BigScreen.vue` | ❌ composable 维护 `loading`（`useBigScreen.js:23/257/298`）但视图 `:159-182` **未解构、未绑定**；仅地图占位 `:77` | ❌ `useBigScreen.js:232/242/252/261` 仅 `console.error` | ⚠️ 预警面板 `:68`「暂无预警」；热门话题 Top10 `:90-97` 无空态 |
| `views/error/403.vue` | N/A（静态页） | N/A | N/A |
| `views/error/404.vue` | N/A（静态页） | N/A | N/A |
| `views/error/500.vue` | N/A（静态页） | N/A | N/A |
| `views/home/index.vue` | ✅ `:2 v-loading="searching"`（页级） | ✅ `:91` + 拦截器 toast（注释 `:109-110`） | ✅ `:46 el-empty` + `AnalysisSection.vue:34-42` 渲染 `AnalysisEmptyState` |
| `views/system/Help.vue` | N/A（静态页） | N/A | N/A |
| `views/system/report.vue` | ✅ `:81 v-loading="loadingDemo"` | ❌ `fetchTemplates :227` / `fetchReportData :239` 仅 `console.error` | ✅ `:163 el-empty` |
| `views/system/tasks.vue` | ❌ 仅按钮（`TaskProgress.vue:10/:45`、`TaskList.vue:45/:127`）；爬虫历史表 `TaskList.vue:11` 与预热表 `:77` 无 loading | ✅ `useTasks.js:76/90/127/192` 四处 fetch 均有 `ElMessage.error` | ✅ `TaskList.vue:54 el-empty` + built-in |
| `views/user/Favorites.vue` | ✅ `:11-13` `v-if="loading"` + `el-skeleton` | ✅ `:105` | ✅ `:17 el-empty` |
| `views/user/Profile.vue` | ❌ 仅保存按钮 `:86/:129`；`loadProfile :236-249` 无指示 | ✅ `:247`（+ `:282/:285/:314/:317`） | N/A（表单/详情） |

统计：**loading 缺失 5 页**（platform / spider / BigScreen / tasks / Profile）+ **部分缺失 1 页**（comment）；**视图级错误态缺失 5 页**（platform / spider / BigScreen / report / alert-center）+ **部分缺失 1 页**（predict）；**空态缺失 3 处子区域**（alert 规则面板 / BigScreen 热门话题 / comment 热门评论）。

### 1.3 缺口清单（按用户影响排序）

| # | 页面 | 缺哪件 | 证据 | 用户可感知后果 |
|---|---|---|---|---|
| 1 | `analysis/platform.vue` | loading + 错误态 | `:292-307` 无 loading 标志；`:305/:316/:327` 仅 `console.error`；全文 0 处 loading 绑定 | 多平台页切换 tab、翻页时旧内容原样重绘，无在途反馈；失败时统计卡与列表停在旧值/零值，无解释 |
| 2 | `dashboard/BigScreen.vue` | loading + 错误态 | `useBigScreen.js:23` 维护 loading 但 `BigScreen.vue:159-182` 未解构；`:232/242/252/261` 仅 `console.error`；5s 自动刷新 `useBigScreen.js:367-371` 静默重绘 | 大屏挂墙场景下用户无法区分「首屏加载中」与「已加载」；API 故障时面板静默显示零值/旧值 |
| 3 | `analysis/spider.vue` | loading + 错误态 | `useSpider.js:48-69` 首屏 `loadOverview`/`loadLogs` 无指示；`:56/:65` 仅 `console.error` | 首屏渲染零值统计 + 空白日志窗，与「确实无数据」无法区分 |
| 4 | `alert/center.vue` | 错误态 + 规则空态 | `useAlert.js:108/121/132` 仅 `console.error`；规则 `v-for` `center.vue:40-53` 无空态兜底 | 预警中心失败时表格空、统计卡旧值；规则列表为空时是一块空白，无「暂无规则」 |
| 5 | `system/tasks.vue` | loading | `TaskList.vue:11`（爬虫历史表）、`:77`（预热结果表）无 loading | 挂载时空表与「加载完但真空」长得一样 |
| 6 | `system/report.vue` | 错误态 | `:227`、`:239` 仅 `console.error` | 预览区停在零值、模板单选为空且无解释；`:249` 的守卫只提示「请先等待数据加载成功」，不暴露根因 |
| 7 | `user/Profile.vue` | loading | `loadProfile :236-249` 无指示，仅保存按钮 `:86/:129` 有 | 资料卡短暂渲染默认值「用户 / 未知」，无加载提示 |
| 8 | `analysis/comment.vue` | loading（部分） | `loading` 声明 `:184`、置位 `:239/:252`，**模板中从未绑定**；仅列表 `:111` 绑定 `listLoading` | 图表与热门评论面板在拉数期间显示旧/空内容，无反馈。**这是一个死状态变量** |
| 9 | `analysis/predict.vue` | 错误态（部分） | `usePredict.js:189` 仅 `console.error` | 模型信息卡只显示 `el-empty 暂无模型信息`（`:54`），把「加载失败」伪装成「没有模型」 |
| 10 | `dashboard/BigScreen.vue` | 空态（子区域） | 热门话题 `:90-97` 无空态 | 空话题面板渲染为一块空白 |

---

## 2. 维度二：响应式一致性

### 2.1 移动端判定有三份独立实现

| # | 位置 | 实现 | 消费者 |
|---|---|---|---|
| 1 | `src/composables/useResponsive.js` | `MOBILE_BREAKPOINT = 768`、`TABLET_BREAKPOINT = 1024`（`:3-4`），导出 `useResponsive` / `useTouch` / `usePullRefresh` / `useGesture` / `useMobileChart`，共 271 行 | **零**（`grep -rn "useResponsive\|useTouch\|usePullRefresh\|useGesture\|useMobileChart" src/` 无任何文件引用） |
| 2 | `src/components/Layout/index.vue` | 本地 `isMobile` ref `:42` + `checkMobile() :53-55`，硬编码 `window.innerWidth < 768` | 自身（`:2/:4/:12/:16/:26`） |
| 3 | `src/components/Layout/MobileNav.vue` | 本地 `isMobile` ref `:30` + `checkMobile() :40-42`，硬编码 `window.innerWidth < 768` | 自身 |

**结论：不可收敛为现状——因为 #1 整份是死代码，#2 与 #3 是两份各自独立的重复实现。**

- `Layout/index.vue:26` 渲染 `<MobileNav v-if="isMobile" />`，两个组件同时挂载、各自监听 `resize`、各自维护同一 768px 阈值。功能上一致，但**阈值有两份字面量**：改一处不改另一处即产生「侧边栏已切移动布局而底部导航未出现」的分裂状态。
- `useResponsive.js` 的 `isTablet`（768–1024）、`isDesktop`、`colSpan`、`breakpoints` **无人消费**，因此**平板段（768–1024px）在全仓没有任何差异化处理**——Layout 只区分 mobile/desktop 两档。
- 该 composable 已在 #58 第四批（composables）迁移清单内，**类型化一份零消费者代码没有收益**。

### 2.2 固定 `:span` 导致的移动端挤压（真实缺陷）

Element Plus `el-col` 未指定 `:xs` 时默认 span=24（整行），因此缺 `:xs` 本身不造成挤压；**造成挤压的是固定 `:span="N"`**：

| 位置 | 写法 | 移动端后果 |
|---|---|---|
| `src/views/home/index.vue:26`、`:34` | `<el-col :span="12">` × 2 | **首页**（应用落地页）在 <768px 下两张图表卡各占 50% 宽度并排，手机上半屏被压成两条窄卡 |
| `src/views/analysis/hotWords.vue:32`、`:50` | `<el-col :span="8">` / `<el-col :span="16">` | 热词统计页 8/16 分栏在手机上把左栏压到 1/3 屏宽 |

其余 `:span="24"`（`home:12`、`article:4/:45`、`platform:4`、`wordCloud:42`、`predict:61`、`ip:36`、`sentiment:68/:84/:108`、`hotWords:4/:61`）为整行，无问题。

### 2.3 响应式覆盖总览

24 个视图中：11 个使用响应式 `el-col` 断点 props；13 个无 `el-col` 断点（其中 `weiboStats.vue`、`tasks.vue`、`Login/Register.vue`、`error/*.vue` 为单栏或表单，天然不需；`Favorites.vue`/`Profile.vue` 用 `@media (max-width: 640px)`（`:239`/`:471`），`Help.vue` 用 `@media (max-width: 640px)`（`:318`），`BigScreen` 用 `@media (max-width: 1440px/1200px)`（`BigScreen.scss:679/:690`）——大屏为定宽挂墙场景，移动端不属其目标，本调研不将其计入缺口）。

---

## 3. 维度三：测试覆盖盲区

### 3.1 现有前端测试资产（16 文件 / 88 测试，全绿）

按「是否真实执行被测代码」分类——这是判断覆盖含金量的关键：

| 类型 | 文件 | 说明 |
|---|---|---|
| **真实 mount 组件**（5 个叶子组件） | `navigation-and-empty-state.test.js`、`provenance.test.js`、`template-resolution.test.js`、`tabbar-icons.test.js`、`bigscreen-trend.test.js`（以 harness 包裹 `useBigScreen`） | 仅覆盖 `AnalysisEmptyState.vue`、`AnalysisSection.vue`、`AnalysisFilters.vue`、`ProvenanceBadge.vue`、`Layout/TabBar.vue` |
| **真实执行模块（不 mount）** | `router-guard.test.js`（真跑 `router.push` 与 `beforeEach`）、`auth-session.test.js`、`analysis-store.test.js`、`request-loading.test.js`、`response-envelope.test.js`、`websocket-client.test.js`、`visual-map-max.test.js`、`use-table.test.js` | 基础设施层覆盖扎实 |
| **静态 grep 测试**（读源码文本断言正则/字符串） | `icon-registration.test.js`（整文件）、`element-plus-icons.test.js`（第 2 个 `it`）、`tabbar-icons.test.js`（第 1 个 `describe`） | **扫到的组件渲染空白也能通过**；代码移动即静默失效 |
| **纯夹具、零 src 依赖** | `analysis-contract.test.js` | 只断言一个硬编码 `demoSnapshot` 字面量的键存在，不执行任何 src 模块 |

**`src/views/` 下 24 个视图，零个被任何测试 mount。**

### 3.2 核心用户旅程覆盖

| 旅程 | 覆盖 | 证据 |
|---|---|---|
| a. 登录（提交→token→跳转） | **未覆盖**（单测）/ 冒烟前置 | 无测试 mount `Login.vue` 或调 `stores/user.js` 的 `doLogin`；`auth-session.test.js` 只测 token 存储工具；`response-envelope.test.js` 测的是 401 过期跳转而非登录提交。真实浏览器仅作为冒烟脚本前置步骤 |
| b. 注册 | **未覆盖** | 无测试引用 `Register.vue`；冒烟脚本不访问 `/register` |
| c. 路由守卫 | **已覆盖** | `router-guard.test.js` 真跑守卫：未登录→`/login`、public/404 放行、`/api/auth/me` 60s TTL 缓存、adminOnly→`/403`、管理员放行 |
| d. 首页→关键词→触发分析 | **部分** | `AnalysisFilters.vue` 真实 mount（空关键词禁用、`search` emit 载荷）；`AnalysisSection` 状态机已测。但 `home/index.vue` 的 `onSearch`→`http`→`snapshot` 渲染链从未执行 |
| e. 任一分析页加载 | **未覆盖** | 11 个分析视图无一被 mount；`usePredict.js`/`useSentiment.js` 无测试 |
| f. 数据大屏 | **部分** | `bigscreen-trend.test.js` + `visual-map-max.test.js` 真实执行 composable；视图本身未 mount。冒烟脚本只断言「零 pageerror」 |
| g. 预警中心 | **未覆盖** | `useAlert.js`、`api/alert.js`、`center.vue` 无任何测试 |
| h. 任务中心 | **未覆盖** | 仅作为 adminOnly 守卫跳转目标出现；`useTasks.js`/`api/tasks.js` 无测试 |
| i. 个人中心 / 我的收藏 | **未覆盖** | `Profile.vue`、`Favorites.vue`、`api/favorites.js` 无测试 |
| j. 报告导出 | **未覆盖** | `report.vue`、`api/report.js` 无测试 |
| k. 爬虫管理 | **未覆盖** | `spider.vue`、`useSpider.js`、`api/spider.js` 无测试 |
| l. WebSocket 实时推送 | **未覆盖（管道本身是死的）** | `websocket-client.test.js` 测了包装器，但 `grep -rn "WebSocketClient\|websocket" src/` 显示**零消费者**——没有任何 view/composable 引入它 |
| m. 错误页 403/404/500 | **未覆盖（作为视图）** | 只测了路由可达性 |

### 3.3 浏览器冒烟现状

`scripts/smoke_bigscreen_empty_db.py` 与 `scripts/smoke_console_noise.py` 覆盖登录 + 5 个页面（big-screen / home / article / sentiment / ip），但**两者都只断言「零 pageerror + 控制台清洁」**，无任何数据断言。它们能抓住渲染崩溃，抓不到「loading 不显示」「错误被静默吞掉」这类本调研维度一/二描述的缺陷。

**盲区排序（按用户影响）**

1. **登录/注册——应用入口零单测覆盖。** token 存储与跳转正确性只靠冒烟脚本当前提步骤存在，无断言。
2. **24 个视图零 mount 测试。** 任何视图级模板错误、生命周期崩溃对 vitest 不可见。
3. **六个功能区在任何层面零覆盖**：预警中心、任务中心、爬虫管理、报告导出、个人中心/收藏、内容预测——含其专属 composables。
4. **WebSocket 推送是死管道**：包装器有测试、无消费者，"实时推送"作为旅程按构造即不可覆盖。
5. **3 个静态 grep 测试**可能绿着而组件实际渲染空白。

---

## 4. 维度四：与 #58（TS 迁移）的协同

#58 的六批计划（`docs/FRONTEND_TS_MIGRATION.md` §2）与本调研发现的**文件级重叠**如下——这正是"顺风车"的判定依据：

| #58 批次 | 涉及文件 | 本调研在此批文件中的发现 | 顺风车判定 |
|---|---|---|---|
| 第一批 | `api/{index,content,tasks,propagation,platform}.js`、`utils/{echarts,chinaMap}.js`、`plugins/elementPlus.js`、`stores/app.js` | 无 UX 缺口 | 无协同 |
| 第二批 | `api/*.js`（8 个）+ `api/request.js` + `utils/{index,authSession,websocket}.js` | **`utils/websocket.js`（198 行）是死代码**（零消费者，见 §5）；`api/request.js` 是全局错误兜底所在 | ⚠️ **冲突**：会给死代码加类型；同时是统一错误信封类型的最佳时机 |
| 第三批 | `stores/{analysis,tabs,user}.js` | `stores/user.js` 的 `doLogin` 是登录旅程核心，目前零测试 | ✅ 迁移时补登录/登出测试最顺 |
| 第四批 | 8 个 composable（~2250 行） | **`useResponsive.js`（271 行）+ `useTable.js`（171 行）+ `index.js`（145 行）合计 587 行是死代码**，约占本批 26%；`useBigScreen.js`/`useSpider.js`/`useAlert.js`/`usePredict.js` 正是维度一错误态缺口所在 | ⚠️ **冲突 + 强协同**：删死代码应在迁移前；迁移 `useBigScreen`/`useSpider`/`useAlert`/`usePredict` 时补 loading/error 是天然顺风车 |
| 第五批 | `router/index.js`、`main.js`、`App.vue` | `router/index.js` 守卫已有测试；`App.vue` 是中文 locale 挂载点 | ✅ 路由 meta 类型化收益明确 |
| 第六批 | 47 个 `.vue`（~10,000 行） | 维度一 5 个 loading 缺失页 + 5 个错误态缺失页、维度二 2 个固定 span 缺陷，**全部落在本批** | ✅ **最强协同**：每迁移一个 SFC 同时补三件套与响应式 |

**关键结论：#58 的第二批与第四批计划中，共约 785 行死代码（`utils/websocket.js` 198 + `useResponsive.js` 271 + `useTable.js` 171 + `composables/index.js` 145）会被类型化。这些工作不产生任何用户可见收益。建议在启动 #58 第二/四批之前先完成死代码清理。**

---

## 5. 附带发现：死代码与重复实现

### 5.1 死模块（零 importer，共 1,225 行）

| 模块 | 行数 | 有测试？ | 在 #58 批次中？ |
|---|---|---|---|
| `src/composables/useResponsive.js` | 271 | 否 | 第四批 |
| `src/components/Common/DataTable.vue` | 401 | 否 | 第六批 |
| `src/utils/websocket.js` | 198 | **是**（`websocket-client.test.js`，3 测试） | 第二批 |
| `src/composables/useTable.js` | 171 | **是**（`use-table.test.js`，4 测试，含 #19 失败态与竞态防护） | 第四批 |
| `src/composables/index.js` | 145 | 否 | 第四批 |
| `src/api/analysis.js` | 28 | 否 | 不在任何批次 |
| `src/components/charts/SentimentPie.vue` | 11 | 否 | 第六批 |

其中 `useTable.js` 的 `loadError` 失败态设计（`useTable.js:22/59/63`，注释明确为 #19 设计「区分真无数据与加载失败，供视图提示重试」）**从未被任何视图消费**——即维度一所有 ❌ 错误态页面，本可以复用一个已存在、已测试的失败态机制。

### 5.2 日期/数字格式化有 4 份本地重复实现

`src/utils/index.js` 已导出 `formatNumber`（`:1`）、`formatDate`（`:22`）等，但以下位置各自写了本地版本：

| 位置 | 本地实现 |
|---|---|
| `src/components/Analysis/AnalysisSummary.vue:78` | `formatDate` → `toLocaleDateString('zh-CN')` |
| `src/views/analysis/platform.vue:265` | `formatNumber` → `w`/`k` 缩写 |
| `src/composables/useTasks.js:133` | `formatDateTime` → `toLocaleString` |
| `src/components/system/TaskProgress.vue:157` | `formatDateTime` → `toLocaleString` |

语义已实际分裂：`platform.vue` 的 `formatNumber` 做万/千缩写，`utils` 的不做。数字口径不一致会直接影响用户对统计卡的解读。

### 5.3 一处 `v-model` 绑定 `const` reactive

`src/views/home/index.vue:61` `const filters = reactive({...})`，模板 `:4` `<AnalysisFilters v-model="filters">`。运行 `npm run test:run` 时 vitest 持续输出编译器警告：
`[@vue/compiler-sfc] v-model cannot update a const reactive binding filters. The compiler has transformed it to let to make the update work.`
编译器自动兜底，当前无功能问题，但属于应修正的隐患（`const` 语义与可变绑定矛盾）。

---

## 6. 候选改进清单

每项均可直接转为独立 Issue。「可搭 #58 顺风车」列标注该 Issue 适合与哪一批 TS 迁移合并做，以避免同一文件被改两遍。

| 编号 | 建议 Issue 标题 | 一句话目标 | 影响面 | 预估工作量（文件数） | 建议优先级 | 可搭 #58 顺风车 |
|---|---|---|---|---|---|---|
| **D-1** | 清理前端死代码（7 个零消费者模块，1,225 行） | 删除零 importer 的模块并同步处置其测试，使 #58 第二/四批不再为死代码付出类型化成本 | 前端全仓；解除 #58 批次冲突 | 7 删 + 2 测试文件调整 + 1 文档（#58 批次清单） | **P1** | ❌ **须先于 #58 第二/四批** |
| **U-1** | BigScreen 补齐加载态与错误态 | 让 `BigScreen.vue` 解构并绑定 `useBigScreen` 已维护的 `loading`，并把 4 处 `console.error` 提升为区域级错误提示 + 重试 | 数据大屏（挂墙主场景） | 2（`BigScreen.vue` + `useBigScreen.js`） | **P1** | ✅ 第四批 |
| **U-2** | platform.vue 补齐加载态与错误态 | 为多平台监测的三个 fetch 增加 loading 标志与用户可见错误提示 | 多平台监测页 | 1 | **P1** | ✅ 第六批 |
| **U-3** | spider.vue 补齐首屏加载态与错误态 | `useSpider` 的首屏 `loadOverview`/`loadLogs` 增加 loading 指示与错误提示 | 爬虫管理（adminOnly） | 2（`spider.vue` + `useSpider.js`） | **P1** | ✅ 第四批 + 第六批 |
| **U-4** | alert 中心补齐错误态与规则空态 | `useAlert` 三个 fetch 的 `console.error` 提升为用户可见提示；规则列表面板补空态 | 预警中心 | 2（`center.vue` + `useAlert.js`） | **P1** | ✅ 第四批 + 第六批 |
| **T-1** | 登录与注册旅程补 vitest 覆盖 | mount `Login.vue`/`Register.vue` 并驱动 `stores/user.js` 的 `doLogin`，断言 token 落库与跳转 | 应用入口；当前零覆盖 | 3 新增测试文件（或 2）+ 0 源码 | **P1** | ✅ 第三批 |
| **T-2** | 建立视图级挂载测试矩阵 | 为 24 个视图建立「挂载 + mock API + 无异常 + 三件套渲染」的最小测试骨架 | 全前端；当前 24/24 未 mount | 3–4 新增测试文件（按目录分批） | **P1** | ✅ 第六批（每迁移一个 SFC 补一个挂载测试） |
| **R-1** | 移动端判定收敛为单源 | 删除 `Layout/index.vue` 与 `MobileNav.vue` 两份重复的 `checkMobile`，统一改消费 `useResponsive`（顺带删除其死代码部分） | 全局布局；消除阈值双份字面量 | 3（`useResponsive.js` + `Layout/index.vue` + `MobileNav.vue`） | **P1** | ✅ 第四批 |
| **R-2** | 修复首页固定分栏在移动端的挤压 | `home/index.vue:26/:34` 的 `:span="12"` 改为响应式断点，使手机端纵向堆叠 | 首页（落地页） | 1 | **P1** | ✅ 第六批 |
| **U-5** | tasks.vue 两张表格补加载态 | 爬虫历史表与预热结果表挂载时显示 loading | 任务中心（adminOnly） | 2（`tasks.vue` + `TaskList.vue`） | P2 | ✅ 第六批 |
| **U-6** | report.vue 补齐错误态 | `fetchTemplates`/`fetchReportData` 失败时给用户可见提示，替换只进 console 的静默路径 | 报告导出 | 1 | P2 | ✅ 第六批 |
| **U-7** | Profile.vue 补资料加载态 | `loadProfile` 期间显示 skeleton/loading，避免渲染默认值「用户/未知」 | 个人中心 | 1 | P2 | ✅ 第六批 |
| **U-8** | 修复 comment.vue 死 loading 标志 | 把声明后从未绑定的 `loading`（`:184/:239/:252`）绑到图表与热门评论区域，或删除该死变量 | 评论分析 | 1 | P2 | ✅ 第六批 |
| **R-3** | 修复热词页固定分栏在移动端的挤压 | `hotWords.vue:32/:50` 的 `:span="8"/"16"` 改响应式 | 热词统计 | 1 | P2 | ✅ 第六批 |
| **T-3** | 六个零覆盖功能区补最小测试 | 为 `useAlert`/`useTasks`/`useSpider`/`usePredict` 等 composable 补最小单测，先建立失败可回归的底线 | 预警/任务/爬虫/预测 | 4–6 新增测试文件 | P2 | ✅ 第四批 |
| **T-4** | 处置 WebSocket 死管道 | 决定「删除 `utils/websocket.js`」或「接入实时推送」——当前包装器有测试、无消费者，属半成品 | 实时推送功能 | 1–2 | P2 | ⚠️ 与 #58 第二批冲突，须先决策 |
| **D-2** | 统一日期数字格式化实现 | 收敛 `AnalysisSummary`/`platform`/`useTasks`/`TaskProgress` 四处本地实现到 `utils/index.js`，统一数字口径 | 统计卡数字口径一致性 | 4–5 | P2 | ✅ 第二批 |
| **U-9** | predict.vue 模型信息加载失败可见化 | `usePredict.js:189` 的 `console.error` 改为错误提示，使「加载失败」不与「暂无模型」混淆 | 内容预测 | 2（`predict.vue` + `usePredict.js`） | P3 | ✅ 第四批 + 第六批 |
| **U-10** | BigScreen 热门话题补空态 | 热门话题 Top10 区域补空状态 | 数据大屏 | 1 | P3 | ✅ 第六批 |
| **R-4** | 平板段（768–1024）布局差异化 | 消费 `useResponsive` 已有的 `isTablet`/`colSpan`，为平板提供中间档布局 | 平板设备 | 1–2 | P4 | ✅ 第四批 |
| **T-5** | 静态 grep 测试替换为真实执行 | 将 `icon-registration`/`element-plus-icons`/`tabbar-icons` 中读源码断言的用例改为真实 mount 断言 | 测试含金量 | 3 | P3 | ❌ 独立 |
| **U-11** | 修正 home v-model 绑定 const reactive | `home/index.vue:61` 的 `const filters = reactive(...)` 配 `v-model` 触发编译器警告，改为 `let` 或受控更新 | 首页；消除编译器警告 | 1 | P3 | ✅ 第六批 |

> **给 Planner 的排序建议**：`D-1` 是 `U-*` 中顺风车判定与 #58 批次计划的前置，宜最先立项；`T-4` 需要产品决策（删还是接），宜转 needs-info；其余按 P1 → P2 顺序推进即可，`R-4` 与 `T-5` 可长期挂起。

---

## 7. 边界与未决事项

- **本调研未修改任何源码**，仅新增本文档。因此未跑前端五门禁中与本次改动相关的部分（无改动对象）；基线 `npm run test:run`（88 passed）与 `npm run lint`（退出码 0）为调研前后状态一致性的证据。
- 视觉设计评审**未做**（Issue 明确排除，无设计稿不做主观判断）。
- #58 已覆盖的 TS 类型安全分析**未重做**，本文只在 §4 做批次级协同标注。
- 性能（包体、渲染耗时）**未测**，不在 #60 范围内。
- `src/views/page/templates/` 服务端模板未纳入前端消费方调查（#54 教训提示该目录在 SPA 扫描之外）；本调研的死代码判定仅针对 `frontend/src/` 内部 importer，若后端模板引用了前端构建产物属另一层问题，未在本次范围内核实。
