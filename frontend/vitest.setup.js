// #49：刻意不在此安装完整 ElementPlus（config.global.plugins = [ElementPlus]）。
// <el-*> 必须经 vitest.config.js 里与生产共用的 Components 插件 + resolver
// 解析（见 config/components.mjs）——全局全量注册会掩盖 resolver 的回归，
// 让 tests/template-resolution.test.js 失去「resolver 被移除即变红」的能力。
// 字符串形式引用的图标 / v-loading 指令由 src/plugins/elementPlus.js 在应用
// 入口负责，单测不依赖它们。
export {}
