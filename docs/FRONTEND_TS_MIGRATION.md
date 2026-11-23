# 前端 TypeScript 迁移策略

> 产出 Issue：#58（已验收关闭）· 初稿：2026-10-09 · 作者：executor-20261009-r1
> 状态：策略基线 + 实际迁移进度记录。§2–§8 保留 #58 的 2026-10-09 历史策略快照（未随后续开发刷新处已就地标注，含作废的旧 Issue 编号建议）；#133（2026-10-25）在其之上交付**首个真实生产 TS 迁移切片**——远未完成全仓迁移，亦不承诺全仓类型安全；#135 / #136（2026-10-26）交付**第一批剩余图表工具**与**多标签工作区 store**；#139 / #140（2026-10-27）交付**会话缓存工具**与 **utils 桶文件**（`utils/authSession.ts`、`utils/index.ts`）；#142（2026-10-27）交付 **`.ts` 的 lint 工具链治理**（`no-redeclare` 误报，**不新增迁移模块**）；#141（2026-10-27）交付 **element-plus 插件注册模块**（`plugins/elementPlus.ts`）。

## 0. 实际迁移进度（#133 · 2026-10-25 · #135 / #136 · 2026-10-26 · #139 / #140 · 2026-10-27 · #141 · 2026-10-27 · #142 · 2026-10-27 lint 工具链治理）

真实生产模块迁移已由 #133、#135、#136、#139、#140 与 #141 交付，**仅覆盖七个模块**：

- **已迁移（#133）**：`src/stores/app.js` → `src/stores/app.ts`。`useAppStore` 名称、setup-store 结构、全部状态/动作与运行时语义不变；`setTheme` 参数显式标注 `string`，`theme`/`device` 仍为 `string`、`sidebarCollapsed` 为 `boolean`——未缩窄主题枚举、未新增存储值校验/回退（沿用 `localStorage` 任意字符串现状契约）。无 `.js` shim / re-export / 双实现。
- **已迁移（#135）**：`src/utils/echarts.js` → `src/utils/echarts.ts`、`src/utils/chinaMap.js` → `src/utils/chinaMap.ts`。运行时语义**逐字不变**：`echarts.use([...])` 注册清单、`ready ??=` 单例复用、`catch` 内 `ready = null` 允许重试、`!res.ok` 抛错文案 `地图资产加载失败：HTTP ${res.status}` 全部原样保留；无 `.js` shim / re-export / 双实现。类型侧：`echarts.ts` 保持 `import * as echarts from 'echarts/core'` + `export default echarts`（echarts 6.1.0 自带 `.d.ts`，**无需新增 `@types`**）；`chinaMap.ts` 的单例类型直接取自 echarts 自身签名 `type MapInput = Parameters<typeof echarts.registerMap>[1]`，**不自造 GeoJSON 结构**，`res.json()` 的 `any` 原样流入 `registerMap`（未新增任何断言链或调用形状改写）。接缝同步：`tests/china-map.test.js` 的动态 import 去掉 `.js` 扩展名（**仅此一行**，不改任何断言）。
- **已迁移（#136）**：`src/stores/tabs.js` → `src/stores/tabs.ts`（193 行）。`useTabsStore` 名称、setup-store 结构、state（`tabs`/`activeTab`/`cachedViews`）与全部动作（`addTab`/`closeTab`/`closeOtherTabs`/`closeAllTabs`/`setActiveTab`/`reorderTabs`/`updateTabPath`/`resetTabs`）**运行时语义逐字不变**（已用「tsc 转译后与原 `.js` 逐行 diff」自证：剥除空行与注释后**可执行语句差异为 0**）。类型侧：新增 `interface TabItem`（`name`/`title`/`path`/`icon: string | null`/`closable`）；`HOME_TAB: TabItem`；`tabs` 为 `ref<TabItem[]>`、`activeTab` 为 `ref<string>`；`addTab` 用**字段全可选**的最小结构类型（以匹配既有 `if (!route?.name || !route?.path) return` 守卫）、四个带导航的动作用 `router?: { push: (to: string) => unknown }` 最小结构类型——**均未引入 vue-router 类型依赖**。`JSON.parse` 结果以 `as TabItem[]` 断言恢复，**不新增任何字段校验 / 回退分支**，保持既有宽松恢复行为（#131 的 41 个用例锁定该语义）。接缝同步：`tests/tabbar-icons.test.js` 的 import 去掉 `.js` 扩展名（**仅此一行**）。本切片**未**给 `_persist` 新增 try/catch（D-034：无真实故障证据不加容错）。
- **已迁移（#139）**：`src/utils/authSession.js` → `src/utils/authSession.ts`（98 行）。运行时语义**逐字不变**——`AUTH_TOKEN_KEY` / `USER_CACHE_KEY` 常量、`currentUserCache` 的 `{ user, fetchedAt }` 结构与 TTL 判定、`resolveStorage` 的三级回退（传入 storage → `window.localStorage` → `null`）、`getCachedUser` 的 `JSON.parse` + `typeof === 'object'` 守卫 + 解析失败时 `removeItem` 并返回 `{}`、`setCachedUser` 的「非空对象才写盘」判定、`clearSessionState` 的清 token + 清内存缓存 + 双 `removeItem` 全部原样保留；无 `.js` shim / re-export / 双实现。类型侧：用户对象用**宽松记录类型** `type SessionUser = Record<string, unknown>`——api 层尚未类型化，**不自造** `id`/`username`/`is_admin` 等字段结构，待 api 层给出契约后再收紧；`JSON.parse` 结果以 `as SessionUser` 断言恢复，**不新增任何字段校验 / 回退分支**，保持既有宽松恢复行为（32 个既有用例锁定）。接缝同步：`tests/auth-session.test.js` 的 import 去掉 `.js` 扩展名（**仅此一行**）。
- **已迁移（#140）**：`src/utils/index.js` → `src/utils/index.ts`（265 → 290 行，**19 个导出**）——`@/utils` 桶入口。运行时语义**逐字不变**：`formatNumber` 的 `compact: 'wk'` 分支、`formatDate` 的 `pattern.replace` 链、`deepClone` 的 `instanceof Date`/`instanceof Array`/`instanceof Object` 判定与 `hasOwnProperty` 守卫、`downloadCsv` 的 `replaceAll('"', '""')` 转义与 BOM、`copyToClipboard` 的 Clipboard API → textarea + `execCommand` 回退、`debounce`/`throttle` 的 `this` 透传全部原样保留；无 `.js` shim / re-export / 双实现。**桶解析**（`@/utils` → `index.ts`）经 `build` + 全量 47/321 实测证明正常。类型侧：`type DateInput = Date | string | number`、`interface FormatNumberOptions { compact?: 'wk' }`；`deepClone<T>(obj: T): T` 保持泛型（实现内 5 处**编译期擦除**的类型断言，逐条见 Issue #140 执行报告）；`debounce`/`throttle` 用泛型 + 显式 `this` 形参**保留 `this` 透传**的运行时语义。**两处 TS 严格性冲突按「语义等价改写」处理**（未改运行时行为）：`d.getFullYear()` → `String(d.getFullYear())`（JS 的 `String.replace` 本就对 replaceValue 做 ToString，二者逐字相同）、`now - target` → `now.getTime() - target.getTime()`（JS 的 `-` 对 Date 走 ToPrimitive(hint number) → `valueOf()`，二者逐字等价）。接缝同步：`tests/format-utils.test.js` 与 `tests/utils-index-core.test.js` 的 import 各去掉 `.js` 扩展名（**各 1 行**）。
- **已迁移（#141）**：`src/plugins/elementPlus.js` → `src/plugins/elementPlus.ts`（87 行）——element-plus **最小全局注册**模块（`v-loading` 指令 + 字符串引用图标的全局组件注册）。运行时语义**逐字不变**：`ICON_COMPONENTS` 的**图标清单与顺序逐项保留**（**29 项**，与迁移前逐项逐序一致——增/删/改名/换序均无）、`installElementPlus` 的 `app.use(ElLoading)` + `for...of Object.entries(ICON_COMPONENTS)` 逐字保留；**无 `.js` shim / re-export / 双实现**。类型侧：图标项类型取自**第三方包自身**（`@element-plus/icons-vue` 的 `DefineComponent`），统一收敛为 **vue 自带的 `Component`**——`Record<string, Component>`，**不自造** `{ name: string }` 之类的假结构；`installElementPlus(app: App): void` 的 `App` 亦取自 **vue 自带类型**，**不另造** `{ use(...): void; component(...): void }` 最小结构。**类型断言 0 处**（`ElLoading` 自带 `install(app: App): void`，直接满足 vue 的 `Plugin`；`app.component(name, component)` 的 `Component` 重载直接可赋）。**零本地 `.js` 导入**——该模块只依赖 `element-plus/es/components/loading/index` 与 `@element-plus/icons-vue` 两个自带 `.d.ts` 的第三方包，故 `tsc --noEmit --listFiles` 实测 `frontend/src` 下**恰好 7 个 `.ts`、0 个 `.js`/`.vue`**，**类型门禁纯净度未被破坏**（对照：`stores/user.js` 若迁移会经 `@/api/*` + `@/router` 把 4 个 `.js` 拉进类型程序，故不在本批）。接缝同步：`tests/icon-registration.test.js` 与 `tests/tabbar-icons.test.js` 的 import 各去掉 `.js` 扩展名（**各 1 行**，不改任何断言、不增删用例）。
- **本地类型检查**：`frontend/tsconfig.json`（`strict` + `noEmit` + `allowJs`/`checkJs:false`）的 `include` 现为 `["src/stores/app.ts", "src/stores/tabs.ts", "src/utils/echarts.ts", "src/utils/chinaMap.ts", "src/utils/authSession.ts", "src/utils/index.ts", "src/plugins/elementPlus.ts"]`（**7 项**），配 `npm run typecheck`（`tsc --noEmit`）。**#140 起 `lib` 由 `ES2020` 提升为 `ES2021`**——`utils/index.ts` 的 `downloadCsv` 沿用既有实现中的 `String.prototype.replaceAll`（ES2021 运行时 API），`lib: ES2020` **不含**其类型声明（`tsc` 实测 TS2550）。**只提升 `lib`、不改 `target`**，故**仅影响类型声明、不影响 emit 与运行时**——运行时本就早已依赖 ES2021 的 `replaceAll`。**仅本地运行，不纳入 CI/pre-commit**；不把全仓未迁移 JS/SFC 拉进类型门禁，**不承诺全仓类型安全**。
- **devDependency**：当前提交的 `package-lock.json` 锁定 `typescript@5.9.3`、`@typescript-eslint/parser@8.46.2` 和 `@typescript-eslint/eslint-plugin@8.46.2`。parser 与插件在 `package.json` 中均为 `^8.46.2`；相同范围不保证重新解析时同版，更新锁文件时应核对两者实际解析版本。#142 的锁文件 diff 为 **97 插入 / 0 删除**：新增插件及 4 个传递锁项（`@typescript-eslint/type-utils`、`@typescript-eslint/utils`、`graphemer`、插件嵌套的 `ignore`），复用已有的 `@eslint-community/regexpp`、`natural-compare`、`ts-api-utils`，无既有包版本漂移。Vue 3 / Pinia 自带类型，未装重复 `@types/*` 或 `vue-tsc`。
- **工具链接**：`eslint.config.js` 仅对 `.ts` 换用 `@typescript-eslint/parser`（JS/Vue 规则不放宽；`.ts` 的 `no-undef`/`no-unused-vars` 交由 tsc 严格检查）；**#142 起 `.ts` 的 `no-redeclare` 改用 `@typescript-eslint/no-redeclare`**——基础规则按 JS 语义判定、**不识别 TS 重载签名**，会把 `function f<T>(x: T): T` + 实现签名误报为 `'f' is already defined`（#140 执行轮实测 exit 1，被迫绕行）；改用插件版而非直接 `off`，是为保留 ESLint 层的重复声明检测——**CI 的 `frontend-fast` 跑 `npm run lint` 但不跑 `typecheck`**，若直接 `off` 则重复声明在 CI 中无人拦截（实测：真实门禁内的重复声明被 tsc 以 `TS2451` / `TS2393` 拦截，插件版亦独立报出）。`vitest.config.js` 的 `coverage.include` 扩为 `src/**/*.{js,ts,vue}`；`package.json` 的 `lint` src glob 纳入 `.ts`。
- **尚未迁移**：其余 2 个 store（`stores/user.js`、`stores/analysis.js`）、api/（14）、composables/、router/、`main.js` 与 45 个 `.vue` 组件/视图仍为 JS/SFC，**不在当前类型门禁内**。§2 六批次顺序仍是后续参考。

## 1. 现状摘要

| 维度 | 数据 |
|------|------|
| .ts 文件 | 0 |
| .js 文件 | 32（api/ 14 · utils/ 5 · stores/ 4 · composables/ 6 · router/ 1 · plugins/ 1 · main.js） |
| .vue 文件 | 45（views/ 6305 行 · components/ 3322 行） |
| tsconfig.json | 无 |
| typescript 依赖 | 无 |
| @types/* | 无 |
| JSDoc 注释 | 仅 1 文件（api/user.js 2 处） |
| 总代码量 | ~13,700 行（JS + Vue） |

**结论**：前端完全无 TypeScript 基础，需从基础设施搭建开始，分层渐进迁移。

> 注：本表为 2026-10-09 历史快照。#133（2026-10-25）已引入 `typescript` devDep 与本地 `typecheck`，并迁移首个 `.ts`（`stores/app.ts`）；#135（2026-10-26）再迁 `utils/echarts.ts` + `utils/chinaMap.ts`；#136（2026-10-26）再迁 `stores/tabs.ts`；#139 / #140（2026-10-27）再迁 `utils/authSession.ts` 与 `utils/index.ts`；#141（2026-10-27）再迁 `plugins/elementPlus.ts`（**当前共 7 个 `.ts`**），见 §0；其余统计待全仓迁移后再刷新。

## 2. 迁移顺序建议

按「风险由低到高、依赖由底向上」原则分六批推进：

> 维护注记（2026-10-10，#61 / D-1 死代码清理）：6 个零消费者模块
> （`composables/useResponsive.js`、`composables/useTable.js`、
> `composables/index.js`、`api/analysis.js`、`components/Common/DataTable.vue`、
> `components/charts/SentimentPie.vue`，共 1,027 行）已删除，第四/六批
> 工作量相应下调。`utils/websocket.js` 其时归 T-4 决策；后续经 D-011/#82
> 已作为死管道**删除**，故已从下方第二批清单移除。

### 第一批：基础设施 + 低风险纯函数（本批目标）

- 新增 `tsconfig.json` + `tsconfig.node.json`
- 安装 `typescript` + 必要 `@types/*`（vue、pinia、vue-router、axios、element-plus）
- 迁移 `api/index.js`、`api/content.js`、`api/tasks.js`、`api/propagation.js`、`api/platform.js`
- 迁移 `utils/echarts.js` ✅（#135）、`utils/chinaMap.js` ✅（#135）
- 迁移 `plugins/elementPlus.js` ✅（#141）
- 迁移 `stores/app.js` ✅（#133）

**选择理由**：纯函数或配置式模块，输入输出明确，无组件耦合，类型化收益立竿见影。

### 第二批：api/ 剩余 + utils/ 剩余

- `api/alert.js`、`api/auth.js`、`api/favorites.js`、`api/predict.js`、`api/report.js`、`api/spider.js`、`api/stats.js`、`api/user.js`
- `api/request.js`（axios 封装，需定义拦截器类型）
- `utils/index.js` ✅（#140）、`utils/authSession.js` ✅（#139）

**选择理由**：api 层是数据边界，类型化后可为上游提供契约；utils 中 request.js 是基础设施，优先类型化。

### 第三批：stores/ 剩余

- `stores/analysis.js`、`stores/tabs.js` ✅（#136）、`stores/user.js`

**选择理由**：Pinia store 状态结构复杂，需先有 api 层类型作为输入。

### 第四批：composables/

- 6 个 composable 文件（~1900 行），逻辑密集但与组件解耦程度较高

**选择理由**：composables 是业务逻辑核心，类型化收益大但难度中高，需在 stores 之后。

### 第五批：router/ + 入口

- `router/index.js`（249 行，配置式）
- `main.js`、`App.vue`

**选择理由**：路由配置类型化收益明确；入口文件收尾。

### 第六批：components/ + views/（最高风险）

- 45 个 .vue 文件（~9,650 行），需逐组件迁移
- 建议按页面维度拆分，每个页面一个子任务

**选择理由**：Vue SFC 的 `<script setup lang="ts">` 迁移需处理 props/emits/slots 类型，工作量大且回归风险高，放最后。

## 3. tsconfig 配置方案

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**关键决策**：
- `strict: true`——渐进迁移期可先设 `strict: false`，首批稳定后逐步开启
- `noEmit: true`——Vite 负责构建，tsconfig 仅用于类型检查
- `allowImportingTsExtensions: true`——允许 `.ts` 扩展名导入
- paths 别名 `@/*` 与 vite.config.js 保持一致

> 注（#133 as-built）：实际落地的 `tsconfig.json` 是上述方案的**更小子集**——`include` 仅 `src/stores/app.ts`，未加 `tsconfig.node.json`/`references`/`allowImportingTsExtensions`/全仓 `*.vue` include（渐进门禁，避免把未迁移 JS/SFC 拉入类型检查）。本 §3 保留为全量迁移期的目标形态参考。

## 4. 类型定义策略

### 4.1 API 响应类型

```typescript
// src/types/api.d.ts
export interface ApiResponse<T = unknown> {
  code: number
  data: T
  message?: string
}

export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}
```

### 4.2 组件 Props/Emits

```typescript
// 示例：通用组件 Props
export interface ChartProps {
  title?: string
  height?: string | number
  data: unknown[]
}
```

### 4.3 Store 状态类型

```typescript
// 示例：User Store
export interface UserState {
  token: string
  userInfo: UserInfo | null
  permissions: string[]
}
```

### 4.4 类型存放

- 全局类型：`src/types/*.d.ts`
- 模块局部类型：就近放置于同目录 `.d.ts` 文件
- Vue SFC 类型：`<script setup lang="ts">` 内直接定义

## 5. 风险点与回滚方案

| 风险 | 影响 | 缓解措施 | 回滚方案 |
|------|------|----------|----------|
| Vite 构建失败 | 全流程阻塞 | 首批迁移后立即跑 `npm run build` 验证 | git revert 对应 commit |
| 类型错误导致运行时异常 | 线上故障 | 严格区分编译时类型检查与运行时行为 | 回退 `strict` 模式 |
| Vue SFC 迁移引入回归 | UI 异常 | 逐组件迁移 + 浏览器冒烟验证 | 单组件 revert |
| 依赖版本冲突 | 安装失败 | 安装前检查兼容性矩阵 | 锁定 package.json 版本 |
| 测试覆盖率下降 | 质量退化 | 迁移同时补充类型测试 | 暂停迁移补测试 |

**通用回滚方案**：每批迁移独立 commit，失败时 `git revert <commit>` 即可回退，不影响已迁移批次。

## 6. 第一批迁移文件清单

| # | 文件 | 行数 | 选择理由 |
|---|------|------|----------|
| 1 | `api/index.js` | 1 | 入口文件，迁移后其余 api 模块有统一出口 |
| 2 | `api/content.js` | 19 | 纯查询函数，输入输出明确 |
| 3 | `api/tasks.js` | 17 | 纯查询函数 |
| 4 | `api/propagation.js` | 19 | 纯查询函数 |
| 5 | `api/platform.js` | 39 | 纯查询函数 |
| 6 | `utils/echarts.js` ✅（#135） | 33 | 工具函数，无状态 |
| 7 | `utils/chinaMap.js` ✅（#135） | 28 | 工具函数，无状态 |
| 8 | `plugins/elementPlus.js` ✅（#141） | 87 | 配置式，无逻辑 |
| 9 | `stores/app.js` ✅（#133） | 45 | 简单 store，状态结构清晰 |
| 10 | `api/user.js` | 24 | 已有 JSDoc 注释，类型化成本最低 |

## 7. 验收标准对照

- [x] 产出迁移策略文档，包含迁移顺序、tsconfig 方案、类型定义策略、风险点
- [x] 文档中明确建议的第一批迁移文件清单（10 个）
- [x] 文档已提交到仓库 docs/ 目录

## 8. 后续阶段建议（无编号）

> #58 初稿曾把以下阶段映射为建议 Issue `#60–#66`；这些编号**实际已被其他任务占用**，不能冒充 TS 子任务，故作废编号、仅保留阶段名。TS 渐进化依已授权方向（D-009/D-018/D-019）由 Planner 逐批立项，不预设 Issue 号。

1. **基础设施**：✅ 已由 #133 交付——本地 `tsconfig.json` + `npm run typecheck` + eslint/vitest 的 `.ts` 支持。
2. **首批纯函数 / store**：`stores/app.ts` ✅（#133）、`utils/echarts.ts` + `utils/chinaMap.ts` ✅（#135）、`stores/tabs.ts` ✅（#136）、`plugins/elementPlus.ts` ✅（#141）；其余 store 与 api/、utils/ 中可类型化的纯函数按覆盖率与依赖顺序小步推进。
3. **api/ + utils/ 剩余**：数据边界类型化，为上游提供契约（`utils/index.ts` ✅ #140、`utils/authSession.ts` ✅ #139）。
4. **stores/ 剩余**：状态结构复杂，宜在 api 类型就绪后（`stores/tabs.ts` 已由 #136 提前完成——它不触碰 api，只读 `localStorage` + 接收路由对象）。
5. **composables/**：逻辑密集、与组件解耦程度较高。
6. **router/ + 入口**：`router/index.js`、`main.js`、`App.vue`。
7. **components/ + views/（最高风险）**：45 个 `.vue` 逐个迁移，建议按页面拆分。

## 9. 现有请求与会话契约（#145，只读盘点）

基线 `d423f3b`（干净的生产快照）。本节记录实际包络、失败语义和依赖，不沿用 §4.1 的通用示例作为接口承诺，不授权迁移。

### 9.1 `auth.js` 的六个调用

[`frontend/src/api/auth.js`](../frontend/src/api/auth.js) 的六个导出均经 [`frontend/src/api/index.js`](../frontend/src/api/index.js) 的默认重导出进入公共 [`frontend/src/api/request.js`](../frontend/src/api/request.js)。六个成功响应的 HTTP 状态和包络 `code` 均为 200。后端 [`ok` / `error`](../src/utils/api_response.py#L13-L30) 含 `code`、`msg`、`timestamp`，有请求标识时附 `request_id`；仅在数据非 `None` 时挂 `data`。不要把 `data` 视为必填，也不要把所有失败体都当成该结构：例如[`rate_limit`](../src/utils/rate_limiter.py#L211-L224) 的 HTTP 429 含 `code`、`msg`、`data.retry_after`，不通过该包络函数。

| 导出 / HTTP | 请求与前端消费 | 成功 `data` / 副作用 | 失败或未登录 | 基线凭据 |
|---|---|---|---|---|
| `login` · `POST /api/auth/login` | JSON `username`, `password`；[`Login.vue`](../frontend/src/views/auth/Login.vue#L89-L110) 调 `user.doLogin`，后者读 `data.token` / `data.user`，成功后页面跳到 `redirect` 或 `/home` | `{token, user: {id, username, create_time, is_admin}}`；设置认证 Cookie | 公开；校验失败 400、凭据被拒 401（公共拦截器处理 HTTP 错误），另有 429 / 503 / 500；`doLogin` 捕获拒绝并返回 `success:false` 与 `error.message`，不保证等于服务端 `msg` | [`api_login`](../src/views/api/auth_routes.py#L60-L102)、[`AuthService.login`](../src/services/auth_service.py#L28-L64)、[`doLogin`](../frontend/src/stores/user.js#L43-L55)、[`login-journey`](../frontend/tests/login-journey.test.js) |
| `register` · `POST /api/auth/register` | JSON `username`, `password`, `confirmPassword`；后端兼容旧拼写 `passwordCheked`，前端不发送；[`Register.vue`](../frontend/src/views/auth/Register.vue#L106-L133) 读 `code` / `msg`，成功跳 `/login` | 无 `data`、不签发 token | 公开；校验/重复名等注册失败 400，另有 429 / 503 / 500。HTTP 拒绝走页面 catch 并提示注册失败，不是 fulfilled 非 200 分支 | [`api_register`](../src/views/api/auth_routes.py#L105-L140)、[`login-journey`](../frontend/tests/login-journey.test.js) |
| `logout` · `POST /api/auth/logout` | 无业务 body/query；[`Header.vue`](../frontend/src/components/Layout/Header.vue#L231) 调 `user.doLogout`，不读响应字段 | 无 `data`；撤销当前 Bearer/Cookie token（如有）、清认证 Cookie | 公开；无登录态仍成功。请求拒绝时 store 记错，在 `finally` 仍清本地会话及工作区标签并跳 `/login` | [`api_logout`](../src/views/api/auth_routes.py#L176-L204)、[`doLogout`](../frontend/src/stores/user.js#L31-L66)、[`test_auth_jwt.py`](../tests/test_auth_jwt.py#L181-L188)、[`test_jwt_revocation.py`](../tests/test_jwt_revocation.py) |
| `checkSession` · `GET /api/session/check` | 无业务 body/query；[`App.vue`](../frontend/src/App.vue#L14-L20) 启动调用 `user.initAuth`，只据 `data.authenticated` 分流 | `{authenticated, user}`；有效凭据时 `user` 是校验后的 JWT 字段（`user_id`, `username`, `jti`, `exp`, `iat`），不是用户资料 | 公开；没有有效凭据返回 **HTTP 200**、`authenticated:false`、`user:null`，store 清态并返回 `false`；处理失败 500 | [`session_check`](../src/app.py#L471-L484)、[`verify_token`](../src/utils/jwt_handler.py#L98-L136)、[`test_api_contract.py`](../tests/test_api_contract.py#L26-L40)、[`initAuth`](../frontend/src/stores/user.js#L68-L102) |
| `extendSession` · `POST /api/session/extend` | 无业务 body/query；`initAuth` 仅在 check 认证后调用，仅消费 `data.token` | `{extended:true, user, token}`；`user` 为认证上下文字段，签发新 token、撤销旧 token，并刷新认证 Cookie | 未认证/过期 401；Cookie 写请求仍经 Origin 校验（拒绝 403）；处理失败 500。拒绝时 store 清内存 token，随后仍尝试 `getUserInfo` | [`session_extend` 和中间件](../src/app.py#L486-L566)、[`test_auth_jwt.py`](../tests/test_auth_jwt.py#L121-L152)、[`initAuth`](../frontend/src/stores/user.js#L68-L102) |
| `getUserInfo` · `GET /api/auth/me` | 无业务 body/query；`initAuth` 用 `data` 更新并缓存 `userInfo`；router 的同一路径查询走独立 `meClient`，不调用该导出 | `{id, username, nickname, email, bio, avatar_color, create_time, is_admin}`；接口给出字段，但不能从 `info.get` 推导永不为 `null` | 未认证 401、用户查不到 404；另有 400 / 503 / 500。拒绝时 store 清态并返回 `false`，仅 `redirectOnFailure` 为真时由 store 另行 replace | [`api_me`](../src/views/api/auth_routes.py#L143-L173)、[`initAuth`](../frontend/src/stores/user.js#L68-L102)、[`meClient`](../frontend/src/router/index.js#L173-L199)、[`user-store`](../frontend/tests/user-store.test.js) |

认证信息不是上述四个无参导出的业务参数：公共请求实例 `withCredentials:true`，内存中 token 非空时附 `Authorization: Bearer ...`。`/api/auth/*` 由 `/api` 蓝图提供；`/api/session/*` 是 Flask app 的会话检查/续期路由。历史 [`/user/login`、`/user/register`、`/user/logOut`](../src/views/user/user.py#L40-L178) 是另一组表单/页面路由，存在 HTML/跳转与 JSON 分支；`/user/info` 也不是 `/api/auth/me`。不要用旧表单路径的结果为六个导出补 DTO（见 [ADR 0002](adr/0002-api-prefix-and-auth-unification.md)）。

### 9.2 公共 `request` 的实际返回与 config

- **实例与成功路径**：`request` 为默认导出的 Axios 实例（相对站点 URL、30 秒、Cookie、JSON Content-Type）；同文件另导出 `http` 的 `get/post/put/delete/request` 薄封装，桶只导出默认值。Axios fulfilled 拦截器取 `response.data`，`code` 在 `[200,300)`（含 201/202）或等于 409 时返回**完整业务包络**，不是 AxiosResponse、也不是包络内部 `data`。业务码 409 静默透传只发生在 fulfilled 路径；被 Axios 拒绝的 HTTP 409 走 HTTP 错误分支，不自动转为成功。见 [`request-error-paths`](../frontend/tests/request-error-paths.test.js#L66-L86)。
- **二进制/非包络**：当前 `request.js` **没有** Blob、`responseType:'blob'`、原始响应直通或空响应特判。普通 Blob 无 `code`，会进入业务失败（`请求失败`），不能声明 Blob 成功重载；SPA CSV 的 Blob 在本地 [`downloadCsv`/`downloadBlob`](../frontend/src/utils/index.ts#L250-L299) 生成，并非该实例的响应类型。
- **错误路径**：fulfilled 的非成功业务码用包络 `msg`（否则 `请求失败`）构造 `new Error` 并拒绝，401/403/404/500 有特定提示；Axios rejected 分支始终拒绝**原始 error 对象**，按 HTTP 状态（401/403/404/408/500/502/503、其余取 `data?.msg` 或状态码）或无响应（`ECONNABORTED` 超时、有 request 无 response 为网络错误、两者均无为配置错误）提示。不要把 HTTP `data.msg` 和业务 Error 的 `message` 统一承诺给调用端。见 [`request.js` 两类响应拦截器](../frontend/src/api/request.js#L82-L167) 与 [`request-error-paths`](../frontend/tests/request-error-paths.test.js)。
- **401 三条路径不同**：公共拦截器在业务 401 或 HTTP 401 都警告、清 `authSession`（内存 token、用户缓存与 `/me` TTL 缓存），对当前 `fullPath` 编码后 `router.replace`，缺路径退 `/home`，只在导航进行时合并重复跳转；Promise 仍被拒绝。这不等于 `user.doLogout`（另清 Pinia 用户/标签并 `push('/login')`），也不等于 router 守卫的专用 `meClient`（8 秒，读取原始 Axios `response.data`，异常/非 200 业务码转 `null`，守卫按未登录处理；有效用户缓存 60 秒）。见 [`request.js`](../frontend/src/api/request.js#L41-L50)、[`authSession.ts`](../frontend/src/utils/authSession.ts#L101-L112)、[`router-guard`](../frontend/tests/router-guard.test.js)、[`user-store`](../frontend/tests/user-store.test.js)。

| 扩展 config 字段 | 写入方 | 读取/作用 |
|---|---|---|
| `loadingOptions` | 业务包装如 [`content.js`](../frontend/src/api/content.js)、[`spider.js`](../frontend/src/api/spider.js) 传选项（含 `text`）或 `false`；六个 auth 导出不传 | 请求拦截器读；缺省/`false` 静默，不要求 `fullscreen`，展示时选项传给 `ElLoading.service` |
| `hideLoading` | [`request-loading`](../frontend/tests/request-loading.test.js#L58-L66) 传 `true`；未发现生产显式写入 | 拦截器读，覆盖展示选项 |
| `_loadingShown` | 请求拦截器仅为实际展示的请求写 `true`，并非外部参数 | 请求失败、响应成功/失败处理读同一 config，释放该次计数；并发最后一个释放才 close。测试 adapter 保留原 config，不能视为新增私有字段（`adapter` 是 Axios 自带） |

### 9.3 依赖闭环与 D-043 下的切片

- **有延迟加载闭环、无 router 守卫直接回调公共实例的静态环**：`auth.js → api/index.js → request.js → router/index.js` 都是静态导入或重导出。返回边为 [`router/index.js` 登录路由的动态 import](../frontend/src/router/index.js#L13-L24) → `Login.vue` → [`stores/user.js`](../frontend/src/stores/user.js#L1-L12) → `api/auth.js`；注册路由的 `Register.vue` 直接导入 `api/auth.js`，也闭合这条路径。router 自己静态依赖的是 Axios、Element Plus、`tabs.ts` 与 `authSession.ts` 等，[`meClient`](../frontend/src/router/index.js#L173-L199) 专用实例刻意避开直接的 `router → request`。
- **当前三文件没有满足 D-043 的单文件机械迁移**：只迁 `auth` 会拉桶、公共请求与 router；只迁桶会拉 `request` 与 router；只迁 `request` 也会拉 router。在仓库外临时 tsconfig（继承现有选项，仅为探明闭包补解析现有 Vite `@/` 别名，并将三个原 JS 文件分别设为入口）跑 `tsc --noEmit --listFiles`，生产 JS 集分别为 `{auth,index,request,router}`、`{index,request,router}`、`{request,router}`。此探针不等于编译迁移后的 TS；现行 [`frontend/tsconfig.json`](../frontend/tsconfig.json) 未配置 `@/`，迁移不能用无法解析的 import、`exclude`、shim 或 suppress 达到零计数。
- **首个候选**：另立项只类型化公共 transport。生产改动下界是 `request.js → request.ts`（到 `authSession.ts` 用可解析的相对导入）与现有 [`frontend/src/main.js`](../frontend/src/main.js#L19-L38) 的组合点，由入口在安装 router 及挂载前提供读取当前路径与 `replace` 的导航能力；请求模块不再 import JS router。再更新 `frontend/tsconfig.json` 的单个 include 与必要的请求拦截器测试接线。保持调用方式、初始化时序、401 去重、拦截器拒绝身份、加载计数及默认实例不变，不新增无导航的静默回退。候选并非本轮实现；Planner 须先标定接线和生命周期，再另定 `index` + 六个 `auth` 包装的具体类型契约。不在首切片内迁 router/store/SFC、并入 `meClient` 或设计统一 DTO；不能用 §4.1 通用类型代替逐接口实证。
- **门禁与 `SessionUser`**：干净基线 `cd frontend && npm exec -- tsc --noEmit --listFiles` → 0，`frontend/src` 下 7 个 TS、0 个 JS/Vue；未来只纳入 `request.ts` 时预期 8 / 0，并确认无未解析模块诊断。现有 [`SessionUser`](../frontend/src/utils/authSession.ts#L1-L18) 仍应保留宽类型：登录资料、`/me` 资料和 check/extend 的 JWT 会话字段不同；`getCachedUser` 还从持久化 JSON 宽松恢复并可能返回 `{}`。后续先在各 API 响应边界区分 payload，再由单独规格为缓存与 store 兼容旧值/空态并证明消费点，不能只靠断言把存量缓存收窄成 `/me` DTO。

### 9.4 公共请求层候选的类型与入口验证（#151）

在主干 `34927c667fe65c9ce0ff505aebd4fe06eea26803` 的独立快照中，将原拦截器转成候选 `request.ts`，并临时接线验证。此次交付是规格和验证记录。

#### 模块求值、装配和请求发出顺序

| 时点 | 源码职责与可发出的请求 |
|---|---|
| 入口依赖求值 | [`main.js` 的入口导入](../frontend/src/main.js#L19-L24) 加载 App 与 router。App 的静态依赖经 [user store](../frontend/src/stores/user.js#L1-L20)、auth 包装及桶加载公共请求。原 [`request.js`](../frontend/src/api/request.js#L32-L84) 在顶层创建实例、注册拦截器，导航读取留在 401 回调。router 顶层创建 router 与 `meClient`、注册守卫，页面组件为懒加载。这里没有发送公共请求，也没有执行守卫。 |
| Pinia 安装之后、router 安装之前 | 在 [`main.js` 的组合点](../frontend/src/main.js#L24-L28) 同步配置一次导航能力。回调每次从 `router.currentRoute.value` 读取当前路径，`replace` 委托真实 router 并返回原 Promise。配置调用本身不读路径、不导航。 |
| 安装 router | 锁内 Vue Router 的 `install(app)` 在浏览器首次安装时调用 `push(routerHistory.location)` 发起初始导航。[`beforeEach`](../frontend/src/router/index.js#L205-L247) 放行公开路由，受保护路由先读 TTL 缓存，未命中才通过 [独立 `meClient`](../frontend/src/router/index.js#L173-L199) 调 `/api/auth/me`。认证失败由守卫处理，公共实例的 401 回调不参与。 |
| 挂载及组件生命周期 | [`main.js`](../frontend/src/main.js#L26-L38) 在安装 router 和 Element Plus 后调用 `mount`。[`App.vue`](../frontend/src/App.vue#L7-L20) 的 setup 创建 store，`onMounted` 才调用 [`initAuth`](../frontend/src/stores/user.js#L68-L102)。后者先用公共实例调用 `checkSession`，认证成功再尝试 `extendSession`，随后用公共实例调用 `getUserInfo`。登录、注册、登出和已挂载页面的请求也在入口装配之后。守卫的异步导航与挂载后的请求可以交错，无需等待 `router.isReady()` 再接线。 |

生产入口在两条路径之前同步接线。接线表达式在临时 `main.js` 中置于 `app.use(router)` 之前。

```js
configureRequestNavigation({
  getFullPath: () => router.currentRoute?.value?.fullPath,
  replace: (target) => router.replace(target),
})
app.use(router)
```

候选以 `{ getFullPath: () => string | undefined; replace: (target: string) => Promise<unknown> }` 描述导航能力。模块求值阶段只保存拦截器，401 开始跳转时才读取回调。直接绕过生产入口的消费者须显式装配，测试已这样接线。若无装配便发生第一次 401，候选调用未设置的导航对象时会抛错，此时已有清态副作用且可能留下去重标记。后续实现须用入口和测试装配证明这条路径不可达，若出现新的无入口消费者，须另外处理装配契约。

#### 公共类型和行为

| 表面 | 候选契约 |
|---|---|
| 默认实例的调用式 | `request(config)` 为 API 包装当前调用式，也保留 Axios 的 `request(url, config?)` 重载。回到同一个 Axios 实例，返回 `Promise<ResponseEnvelope>`。 |
| 默认实例的方法式 | 仓库已用 `get(url, config?)`、`delete(url, config?)`、`post(url, data?, config?)`、`put(url, data?, config?)`。候选同样建模 `request(config)`、`head/options` 和 `patch/postForm/putForm/patchForm/query` 的包络返回。保留 `defaults`、`interceptors`、`getUri` 和原始 `create` 行为，`create().get()` 仍为 Axios 响应。 |
| `http` 五个薄封装 | `get(url, config?)`、`post(url, data, config?)`、`put(url, data, config?)`、`delete(url, config?)`、`request(config)`。相同公共 config，直接透传完整包络。首页使用 `http.get`。 |
| Config | 基于 `AxiosRequestConfig<unknown, unknown>` 保留 `url/method/params/data/headers/timeout/adapter` 等标准选项。自定义 `loadingOptions?: LoadingOptions \| false` 从实际 `ElLoading.service` 取类型，`hideLoading?: boolean` 覆盖展示。只有拦截器内部的 `InternalAxiosRequestConfig` 扩展私有 `_loadingShown`，标记成功展示的请求并平衡三条收尾路径的计数。默认 30 秒、Cookie、JSON Content-Type、内存 Bearer 注入沿用。 |
| 完整成功包络 | `{ code: number; msg?: string; timestamp?: string; request_id?: string; data?: unknown }`。时间与请求标识沿用 §9.1 的服务端出处，适配器最小包络仍兼容。保留可选 `data` 与未证实的 payload 形状。2xx 业务码与 fulfilled 的业务 409 透传整个对象，Axios 拒绝的 HTTP 409 走错误提示并保持原 error。 |
| 两条错误分支 | fulfilled 的业务失败用 `msg \|\| '请求失败'` 构造新 `Error`。Axios rejected 按 HTTP 状态、无响应和配置错误分类提示，原样拒绝对象。候选在内部限定一次响应拦截器注册的类型边界，因为锁内 Axios 1.20.0 的声明要求 fulfilled 仍返回 AxiosResponse。对外只声明配置和包络，不借用该原始响应返回类型。 |

| 401 验收表 | 触发、提示与拒绝 | 导航和会话 |
|---|---|---|
| 业务 401 | Axios fulfilled 后读 `code === 401`，一次登录过期提示，拒绝新 `Error`，保留 `msg` 与默认回退文案。 | 第一次导航前清内存 token、持久化用户、遗留存储 token 和 `/me` TTL 缓存。读当时的路径，缺失或空值回退 `/home`，按原式编码后执行 `replace`。 |
| HTTP 401 | Axios rejected 后读 `response.status === 401`，一次同文案提示，拒绝的对象必须和 adapter error 严格相等。 | 与业务 401 共享窗口。同一窗口混合两次会各提示、只跳一次，等待同一个 router Promise 的 `finally` 释放窗口。完成后再次触发可以重新跳转。 |
| router 的 `meClient` | 专用实例仍接收 Axios 原始响应，8 秒超时。HTTP/网络异常或业务码非 200 归为 null。 | 由守卫按现行规则清态/重定向，继续使用 60 秒缓存；公共实例的过期提示及导航去重不参与。 |

#### 实测和后续文件边界

Node 26.13.1、npm 11.20.0、TypeScript 5.9.3、Axios 1.20.0、Vitest 3.2.7。临时快照的 `npm ci --offline --no-audit` 退出 0，安装 423 个包，锁 SHA-256 前后均为 `28c721d730dd57aee98d23112de1eda8fe0b3dfe0ab9e1ced295b90716837c4d`。

- 在原 `frontend/` 和临时候选 `frontend/` 分别运行 `npm exec -- tsc --noEmit --listFiles`，均退出 0。生产文件由 7 TS / 0 JS/Vue 变为 8 TS / 0 JS/Vue，集合差仅为 `src/api/request.ts`。保留原七个 include，候选唯一项目内 TS import 为 `../utils/authSession`，无未解析模块、新显式 `any`、抑制注释、JS shim。
- 独立临时 tsconfig 在现有 include 后加调用探针。`npm exec -- tsc --noEmit -p tsconfig.probe-151.json` 的正例退出 0，验证调用式、方法式、`http.request` 与独立创建的原始 Axios 实例。追加两个负例后退出 2，实际诊断分别为 TS2322（`data` 可缺席）与 TS2739（包络无 `status`、`statusText`、`headers`、`config`）。日常门禁不纳入探针。
- 用 `NODE_OPTIONS=--no-webstorage npm run test:run -- tests/request-error-paths.test.js tests/request-loading.test.js tests/router-guard.test.js tests/login-journey.test.js tests/response-envelope.test.js` 运行原实现和临时候选，两边均退出 0（5 文件 / 53 用例）。候选的三份直接请求测试使用显式导航回调，保留既有断言。候选全量测试 47 文件 / 323 用例、lint、typecheck、build、bundle 均退出 0。首次 format:check 仅报候选布局，运行 Prettier 后退出 0。
- Chromium 本地冒烟 `bash ../run-smoke151.sh` → 0。两份产物分别由 Vite preview 提供，在 `/login?seed=1` 和 `/home?seed=1` 验证入口。API 固定返回 401，将公共 session check 延迟到初始导航落地后再放行。两份产物公开页均只有 session check，受保护页均另有守卫 me 请求。两者的公共提示和解码后的跳转目标一致，浏览器无页面异常。初始守卫与挂载可以交错的结论来自源码。

```ts
import type { AxiosResponse } from 'axios'
import request, { http, type ResponseEnvelope } from './src/api/request'

export async function positive() {
  const result: ResponseEnvelope = await request({
    url: '/api/auth/register',
    method: 'post',
    data: { username: 'fixture' },
    loadingOptions: false,
  })
  const byUrl: ResponseEnvelope = await request('/api/session/check', { hideLoading: true })
  const direct: ResponseEnvelope = await request.get('/api/auth/me')
  const wrapped: ResponseEnvelope = await http.request({ url: '/api/auth/me' })
  const raw: AxiosResponse<unknown> = await request.create().get<unknown>('/api/auth/me')
  return [result.code, result.msg, result.timestamp, result.request_id, result.data,
    byUrl.code, direct.code, wrapped.code, raw.status]
}

export async function negative() {
  const result = await http.get('/api/auth/me')
  const required: ResponseEnvelope & { data: unknown } = result
  const raw: AxiosResponse<unknown> = result
  return [required, raw]
}
```

后续生产切片的文件边界为 `request.js` 改名为 `request.ts`、[`main.js`](../frontend/src/main.js)、[`tsconfig.json`](../frontend/tsconfig.json)，以及改用显式导航装配并更新 import 的 [request-error-paths](../frontend/tests/request-error-paths.test.js)、[request-loading](../frontend/tests/request-loading.test.js)、[response-envelope](../frontend/tests/response-envelope.test.js)。当前桶和首页均用省略后缀的路径。保持 auth/router/store/SFC、认证权限模型、包络来源、会话缓存、CI 和依赖在这次验证的范围之外。
