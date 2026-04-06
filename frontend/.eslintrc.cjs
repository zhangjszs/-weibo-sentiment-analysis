module.exports = {
  root: true,
  env: { browser: true, es2021: true, node: true },
  extends: ['plugin:vue/vue3-recommended'],
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  rules: {
    'vue/multi-word-component-names': 'off',  // 项目中使用单文件名组件（如HelloWorld.vue），符合项目规范
    'no-unused-vars': 'warn',  // 未使用变量设为警告，逐步清理
    'no-console': 'warn',  // console语句设为警告，生产环境应移除调试信息
  },
}
