import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import globals from 'globals'

// ESLint 9 flat config（替代 .eslintrc.cjs）
export default [
  js.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  {
    languageOptions: {
      globals: { ...globals.browser, ...globals.node },
      ecmaVersion: 2022,
      sourceType: 'module',
    },
    rules: {
      // 项目中使用单文件名组件（如 HelloWorld.vue），符合项目规范
      'vue/multi-word-component-names': 'off',
      // 未使用变量设为警告，逐步清理
      'no-unused-vars': 'warn',
      // console 语句设为警告，生产环境应移除调试信息
      'no-console': 'warn',
    },
  },
  { ignores: ['dist/**', 'node_modules/**'] },
]
