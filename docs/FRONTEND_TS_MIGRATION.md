# 前端 TypeScript 迁移策略

> 产出 Issue：#58（已验收关闭）· 初稿：2026-10-09 · 作者：executor-20261009-r1
> 状态：策略基线 + 实际迁移进度记录。§2–§8 保留 #58 的 2026-10-09 历史策略快照（未随后续开发刷新处已就地标注，含作废的旧 Issue 编号建议）；#133（2026-10-25）在其之上交付**首个真实生产 TS 迁移切片**——远未完成全仓迁移，亦不承诺全仓类型安全；#135 / #136（2026-10-26）交付**第一批剩余图表工具**与**多标签工作区 store**；#139 / #140（2026-10-27）交付**会话缓存工具**与 **utils 桶文件**（`utils/authSession.ts`、`utils/index.ts`）；#142（2026-10-27）交付 **`.ts` 的 lint 工具链治理**（`no-redeclare` 误报，**不新增迁移模块**）。

## 0. 实际迁移进度（#133 · 2026-10-25 · #135 / #136 · 2026-10-26 · #139 / #140 · 2026-10-27 · #142 · 2026-10-27 lint 工具链治理）

真实生产模块迁移已由 #133、#135、#136、#139 与 #140 交付，**仅覆盖六个模块**：

- **已迁移（#133）**：`src/stores/app.js` → `src/stores/app.ts`。`useAppStore` 名称、setup-store 结构、全部状态/动作与运行时语义不变；`setTheme` 参数显式标注 `string`，`theme`/`device` 仍为 `string`、`sidebarCollapsed` 为 `boolean`——未缩窄主题枚举、未新增存储值校验/回退（沿用 `localStorage` 任意字符串现状契约）。无 `.js` shim / re-export / 双实现。
- **已迁移（#135）**：`src/utils/echarts.js` → `src/utils/echarts.ts`、`src/utils/chinaMap.js` → `src/utils/chinaMap.ts`。运行时语义**逐字不变**：`echarts.use([...])` 注册清单、`ready ??=` 单例复用、`catch` 内 `ready = null` 允许重试、`!res.ok` 抛错文案 `地图资产加载失败：HTTP ${res.status}` 全部原样保留；无 `.js` shim / re-export / 双实现。类型侧：`echarts.ts` 保持 `import * as echarts from 'echarts/core'` + `export default echarts`（echarts 6.1.0 自带 `.d.ts`，**无需新增 `@types`**）；`chinaMap.ts` 的单例类型直接取自 echarts 自身签名 `type MapInput = Parameters<typeof echarts.registerMap>[1]`，**不自造 GeoJSON 结构**，`res.json()` 的 `any` 原样流入 `registerMap`（未新增任何断言链或调用形状改写）。接缝同步：`tests/china-map.test.js` 的动态 import 去掉 `.js` 扩展名（**仅此一行**，不改任何断言）。
- **已迁移（#136）**：`src/stores/tabs.js` → `src/stores/tabs.ts`（193 行）。`useTabsStore` 名称、setup-store 结构、state（`tabs`/`activeTab`/`cachedViews`）与全部动作（`addTab`/`closeTab`/`closeOtherTabs`/`closeAllTabs`/`setActiveTab`/`reorderTabs`/`updateTabPath`/`resetTabs`）**运行时语义逐字不变**（已用「tsc 转译后与原 `.js` 逐行 diff」自证：剥除空行与注释后**可执行语句差异为 0**）。类型侧：新增 `interface TabItem`（`name`/`title`/`path`/`icon: string | null`/`closable`）；`HOME_TAB: TabItem`；`tabs` 为 `ref<TabItem[]>`、`activeTab` 为 `ref<string>`；`addTab` 用**字段全可选**的最小结构类型（以匹配既有 `if (!route?.name || !route?.path) return` 守卫）、四个带导航的动作用 `router?: { push: (to: string) => unknown }` 最小结构类型——**均未引入 vue-router 类型依赖**。`JSON.parse` 结果以 `as TabItem[]` 断言恢复，**不新增任何字段校验 / 回退分支**，保持既有宽松恢复行为（#131 的 41 个用例锁定该语义）。接缝同步：`tests/tabbar-icons.test.js` 的 import 去掉 `.js` 扩展名（**仅此一行**）。本切片**未**给 `_persist` 新增 try/catch（D-034：无真实故障证据不加容错）。
- **已迁移（#139）**：`src/utils/authSession.js` → `src/utils/authSession.ts`（98 行）。运行时语义**逐字不变**——`AUTH_TOKEN_KEY` / `USER_CACHE_KEY` 常量、`currentUserCache` 的 `{ user, fetchedAt }` 结构与 TTL 判定、`resolveStorage` 的三级回退（传入 storage → `window.localStorage` → `null`）、`getCachedUser` 的 `JSON.parse` + `typeof === 'object'` 守卫 + 解析失败时 `removeItem` 并返回 `{}`、`setCachedUser` 的「非空对象才写盘」判定、`clearSessionState` 的清 token + 清内存缓存 + 双 `removeItem` 全部原样保留；无 `.js` shim / re-export / 双实现。类型侧：用户对象用**宽松记录类型** `type SessionUser = Record<string, unknown>`——api 层尚未类型化，**不自造** `id`/`username`/`is_admin` 等字段结构，待 api 层给出契约后再收紧；`JSON.parse` 结果以 `as SessionUser` 断言恢复，**不新增任何字段校验 / 回退分支**，保持既有宽松恢复行为（32 个既有用例锁定）。接缝同步：`tests/auth-session.test.js` 的 import 去掉 `.js` 扩展名（**仅此一行**）。
- **已迁移（#140）**：`src/utils/index.js` → `src/utils/index.ts`（265 → 290 行，**19 个导出**）——`@/utils` 桶入口。运行时语义**逐字不变**：`formatNumber` 的 `compact: 'wk'` 分支、`formatDate` 的 `pattern.replace` 链、`deepClone` 的 `instanceof Date`/`instanceof Array`/`instanceof Object` 判定与 `hasOwnProperty` 守卫、`downloadCsv` 的 `replaceAll('"', '""')` 转义与 BOM、`copyToClipboard` 的 Clipboard API → textarea + `execCommand` 回退、`debounce`/`throttle` 的 `this` 透传全部原样保留；无 `.js` shim / re-export / 双实现。**桶解析**（`@/utils` → `index.ts`）经 `build` + 全量 47/321 实测证明正常。类型侧：`type DateInput = Date | string | number`、`interface FormatNumberOptions { compact?: 'wk' }`；`deepClone<T>(obj: T): T` 保持泛型（实现内 5 处**编译期擦除**的类型断言，逐条见 Issue #140 执行报告）；`debounce`/`throttle` 用泛型 + 显式 `this` 形参**保留 `this` 透传**的运行时语义。**两处 TS 严格性冲突按「语义等价改写」处理**（未改运行时行为）：`d.getFullYear()` → `String(d.getFullYear())`（JS 的 `String.replace` 本就对 replaceValue 做 ToString，二者逐字相同）、`now - target` → `now.getTime() - target.getTime()`（JS 的 `-` 对 Date 走 ToPrimitive(hint number) → `valueOf()`，二者逐字等价）。接缝同步：`tests/format-utils.test.js` 与 `tests/utils-index-core.test.js` 的 import 各去掉 `.js` 扩展名（**各 1 行**）。
- **本地类型检查**：`frontend/tsconfig.json`（`strict` + `noEmit` + `allowJs`/`checkJs:false`）的 `include` 现为 `["src/stores/app.ts", "src/stores/tabs.ts", "src/utils/echarts.ts", "src/utils/chinaMap.ts", "src/utils/authSession.ts", "src/utils/index.ts"]`，配 `npm run typecheck`（`tsc --noEmit`）。**#140 起 `lib` 由 `ES2020` 提升为 `ES2021`**——`utils/index.ts` 的 `downloadCsv` 沿用既有实现中的 `String.prototype.replaceAll`（ES2021 运行时 API），`lib: ES2020` **不含**其类型声明（`tsc` 实测 TS2550）。**只提升 `lib`、不改 `target`**，故**仅影响类型声明、不影响 emit 与运行时**——运行时本就早已依赖 ES2021 的 `replaceAll`。**仅本地运行，不纳入 CI/pre-commit**；不把全仓未迁移 JS/SFC 拉进类型门禁，**不承诺全仓类型安全**。
- **devDependency**：固定 `typescript@5.9.3` + `@typescript-eslint/parser@8.46.2` + `@typescript-eslint/eslint-plugin@8.46.2`（**parser 与插件严格同版本**，两者同在 `^8.46.2` 区间故 lockfile 必然解析到同一版本；Vue 3 / Pinia 自带类型，未装重复 `@types/*` 或 `vue-tsc`）；既有直接依赖版本未变（#142 新增插件时 `package-lock.json` 为 **97 插入 / 0 删除**，无既有包版本漂移）。
- **工具链接**：`eslint.config.js` 仅对 `.ts` 换用 `@typescript-eslint/parser`（JS/Vue 规则不放宽；`.ts` 的 `no-undef`/`no-unused-vars` 交由 tsc 严格检查）；**#142 起 `.ts` 的 `no-redeclare` 改用 `@typescript-eslint/no-redeclare`**——基础规则按 JS 语义判定、**不识别 TS 重载签名**，会把 `function f<T>(x: T): T` + 实现签名误报为 `'f' is already defined`（#140 执行轮实测 exit 1，被迫绕行）；改用插件版而非直接 `off`，是为保留 ESLint 层的重复声明检测——**CI 的 `frontend-fast` 跑 `npm run lint` 但不跑 `typecheck`**，若直接 `off` 则重复声明在 CI 中无人拦截（实测：真实门禁内的重复声明被 tsc 以 `TS2451` / `TS2393` 拦截，插件版亦独立报出）。`vitest.config.js` 的 `coverage.include` 扩为 `src/**/*.{js,ts,vue}`；`package.json` 的 `lint` src glob 纳入 `.ts`。
- **尚未迁移**：其余 2 个 store（`stores/user.js`、`stores/analysis.js`）、api/（14）、`plugins/elementPlus.js`、composables/、router/、`main.js` 与 45 个 `.vue` 组件/视图仍为 JS/SFC，**不在当前类型门禁内**。§2 六批次顺序仍是后续参考。

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

> 注：本表为 2026-10-09 历史快照。#133（2026-10-25）已引入 `typescript` devDep 与本地 `typecheck`，并迁移首个 `.ts`（`stores/app.ts`）；#135（2026-10-26）再迁 `utils/echarts.ts` + `utils/chinaMap.ts`；#136（2026-10-26）再迁 `stores/tabs.ts`；#139 / #140（2026-10-27）再迁 `utils/authSession.ts` 与 `utils/index.ts`（当前共 6 个 `.ts`），见 §0；其余统计待全仓迁移后再刷新。

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
- 迁移 `plugins/elementPlus.js`
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
| 8 | `plugins/elementPlus.js` | 87 | 配置式，无逻辑 |
| 9 | `stores/app.js` ✅（#133） | 45 | 简单 store，状态结构清晰 |
| 10 | `api/user.js` | 24 | 已有 JSDoc 注释，类型化成本最低 |

## 7. 验收标准对照

- [x] 产出迁移策略文档，包含迁移顺序、tsconfig 方案、类型定义策略、风险点
- [x] 文档中明确建议的第一批迁移文件清单（10 个）
- [x] 文档已提交到仓库 docs/ 目录

## 8. 后续阶段建议（无编号）

> #58 初稿曾把以下阶段映射为建议 Issue `#60–#66`；这些编号**实际已被其他任务占用**，不能冒充 TS 子任务，故作废编号、仅保留阶段名。TS 渐进化依已授权方向（D-009/D-018/D-019）由 Planner 逐批立项，不预设 Issue 号。

1. **基础设施**：✅ 已由 #133 交付——本地 `tsconfig.json` + `npm run typecheck` + eslint/vitest 的 `.ts` 支持。
2. **首批纯函数 / store**：`stores/app.ts` ✅（#133）、`utils/echarts.ts` + `utils/chinaMap.ts` ✅（#135）、`stores/tabs.ts` ✅（#136）；其余 store 与 api/、utils/ 中可类型化的纯函数按覆盖率与依赖顺序小步推进。
3. **api/ + utils/ 剩余**：数据边界类型化，为上游提供契约（`utils/index.ts` ✅ #140、`utils/authSession.ts` ✅ #139）。
4. **stores/ 剩余**：状态结构复杂，宜在 api 类型就绪后（`stores/tabs.ts` 已由 #136 提前完成——它不触碰 api，只读 `localStorage` + 接收路由对象）。
5. **composables/**：逻辑密集、与组件解耦程度较高。
6. **router/ + 入口**：`router/index.js`、`main.js`、`App.vue`。
7. **components/ + views/（最高风险）**：45 个 `.vue` 逐个迁移，建议按页面拆分。
