import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { createComponentsPlugin } from './config/components.mjs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [
    vue(),
    // #49：与 vite.config.js 共用同一份 Components + resolver 配置，
    // 让单测中的 <el-*> 与生产构建走同一条解析链，消除模板级组件解析盲区。
    // importStyle: false 仅关样式注入（jsdom 无视觉断言），见 config/components.mjs
    createComponentsPlugin({ importStyle: false }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['tests/**/*.test.js', 'tests/**/*.spec.js'],
    exclude: ['node_modules', 'dist'],
    // Frontend unit tests must not depend on the backend.
    // Mock any API calls in tests using vi.mock or msw.
    setupFiles: ['vitest.setup.js'],
  },
})
