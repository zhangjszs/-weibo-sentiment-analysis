# 前端 TypeScript 迁移策略

> 产出 Issue：#58 · 日期：2026-10-09 · 作者：executor-20261009-r1
> 状态：策略文档（待 Planner 验收）

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

## 2. 迁移顺序建议

按「风险由低到高、依赖由底向上」原则分六批推进：

> 维护注记（2026-10-10，#61 / D-1 死代码清理）：6 个零消费者模块
> （`composables/useResponsive.js`、`composables/useTable.js`、
> `composables/index.js`、`api/analysis.js`、`components/Common/DataTable.vue`、
> `components/charts/SentimentPie.vue`，共 1,027 行）已删除，第四/六批
> 工作量相应下调。`utils/websocket.js` **不在**删除范围（归 T-4 决策），
> 第二批清单维持原样。

### 第一批：基础设施 + 低风险纯函数（本批目标）

- 新增 `tsconfig.json` + `tsconfig.node.json`
- 安装 `typescript` + 必要 `@types/*`（vue、pinia、vue-router、axios、element-plus）
- 迁移 `api/index.js`、`api/content.js`、`api/tasks.js`、`api/propagation.js`、`api/platform.js`
- 迁移 `utils/echarts.js`、`utils/chinaMap.js`
- 迁移 `plugins/elementPlus.js`
- 迁移 `stores/app.js`

**选择理由**：纯函数或配置式模块，输入输出明确，无组件耦合，类型化收益立竿见影。

### 第二批：api/ 剩余 + utils/ 剩余

- `api/alert.js`、`api/auth.js`、`api/favorites.js`、`api/predict.js`、`api/report.js`、`api/spider.js`、`api/stats.js`、`api/user.js`
- `api/request.js`（axios 封装，需定义拦截器类型）
- `utils/index.js`、`utils/authSession.js`、`utils/websocket.js`

**选择理由**：api 层是数据边界，类型化后可为上游提供契约；utils 中 request.js 是基础设施，优先类型化。

### 第三批：stores/ 剩余

- `stores/analysis.js`、`stores/tabs.js`、`stores/user.js`

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
| 6 | `utils/echarts.js` | 33 | 工具函数，无状态 |
| 7 | `utils/chinaMap.js` | 28 | 工具函数，无状态 |
| 8 | `plugins/elementPlus.js` | 87 | 配置式，无逻辑 |
| 9 | `stores/app.js` | 45 | 简单 store，状态结构清晰 |
| 10 | `api/user.js` | 24 | 已有 JSDoc 注释，类型化成本最低 |

## 7. 验收标准对照

- [x] 产出迁移策略文档，包含迁移顺序、tsconfig 方案、类型定义策略、风险点
- [x] 文档中明确建议的第一批迁移文件清单（10 个）
- [x] 文档已提交到仓库 docs/ 目录

## 8. 后续 Issue 建议

1. **#60（建议）**：前端 TS 基础设施搭建（tsconfig + 依赖安装 + vite 配置确认）
2. **#61（建议）**：第一批文件迁移（10 个文件，按本文清单执行）
3. **#62（建议）**：第二批 api/utils 迁移
4. **#63（建议）**：stores 迁移
5. **#64（建议）**：composables 迁移
6. **#65（建议）**：router + 入口迁移
7. **#66（建议）**：Vue SFC 迁移（按页面拆分）
