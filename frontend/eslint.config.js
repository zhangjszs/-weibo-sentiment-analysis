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
      // #51：以下 5 条是 vue/recommended 中的纯格式规则，与 Prettier
      // （.prettierrc.json，printWidth 100 的属性换行/单行元素内容策略）
      // 直接冲突——格式统一由 `npm run format:check` 门禁负责，eslint 不再
      // 双重规定。其余 vue 模板质量规则（v-if 配 key、属性命名等）全部保留。
      'vue/html-closing-bracket-newline': 'off',
      'vue/html-indent': 'off',
      'vue/html-self-closing': 'off',
      'vue/max-attributes-per-line': 'off',
      'vue/singleline-html-element-content-newline': 'off',
      // 未使用变量设为警告，逐步清理
      'no-unused-vars': 'warn',
      // 只放行 warn/error 诊断输出；log/debug/info 会被警告（#21 收紧）
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      // 禁止使用已废弃的 /getAllData 前缀（已收敛至 /api/*，见 ADR 0002）
      'no-restricted-syntax': [
        'error',
        {
          selector: 'Literal[value=/getAllData/]',
          message: 'Use /api/* instead of deprecated /getAllData/* (see ADR 0002).',
        },
        {
          selector: 'TemplateElement[value.raw=/getAllData/]',
          message: 'Use /api/* instead of deprecated /getAllData/* (see ADR 0002).',
        },
      ],
    },
  },
  { ignores: ['dist/**', 'node_modules/**'] },
]
