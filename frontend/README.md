# 微博舆情分析系统 - 启动指南

## 环境要求

- Node.js >= 16.0
- Python >= 3.8
- MySQL >= 5.7

## 安装依赖

### 1. 安装前端依赖
```bash
cd frontend
npm install
```

### 2. 安装后端依赖
```bash
pip install -r requirements.txt
```

## 启动项目

### 1. 启动后端服务
```bash
python run.py
```
后端服务将在 `http://127.0.0.1:5000` 启动

### 2. 启动前端开发服务器
```bash
cd frontend
pnpm install
pnpm dev
```
前端服务将在 `http://localhost:3000` 启动，并自动代理 `/api` 请求到后端

## 认证说明

- 登录后后端会写入 `HttpOnly` 认证 Cookie。
- 前端不会再把 JWT 持久化到 `localStorage`；刷新后会通过 Cookie 会话恢复登录态。
- 当前页内存 Bearer Token 仅用于需要显式令牌的场景，例如 WebSocket 认证。

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API 接口层
│   ├── components/       # 公共组件
│   │   ├── Layout/       # 布局组件
│   │   ├── Charts/       # 图表组件
│   │   └── Common/       # 通用组件
│   ├── router/           # 路由配置
│   ├── stores/           # 状态管理
│   ├── views/            # 页面组件
│   │   ├── auth/         # 登录/注册
│   │   ├── home/         # 首页
│   │   └── analysis/      # 分析页面
│   └── styles/           # 全局样式
└── vite.config.js        # Vite 配置
```

## 主要功能

- ✅ 现代化 UI 界面（Element Plus）
- ✅ 响应式布局设计
- ✅ 暗黑模式支持
- ✅ 用户认证系统
- ✅ 数据可视化展示
- ✅ 表格数据管理
- ✅ 热词统计分析
- ✅ 舆情分析图表
- ✅ 词云图展示
- ✅ IP 地理位置分析
- ✅ 评论情感分析

## 技术栈

- **前端**: Vue 3 + Element Plus + ECharts + Pinia + Vue Router
- **后端**: Flask + SQLAlchemy + MySQL
- **构建工具**: Vite 5

## 开发规范

1. 遵循组件化开发原则
2. 使用 Composition API
3. 组件命名使用 PascalCase
4. 样式使用 SCSS
5. 保持代码简洁和可维护性

## 下一步计划

- [ ] 添加单元测试
- [ ] 性能优化
- [ ] 添加骨架屏加载
- [ ] 完善错误处理
- [ ] 移动端适配优化
