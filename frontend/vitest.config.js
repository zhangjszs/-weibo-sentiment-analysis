import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['tests/**/*.test.js', 'tests/**/*.spec.js'],
    exclude: ['node_modules', 'dist', 'tests/auth-session.test.js'],
    // Frontend unit tests must not depend on the backend.
    // Mock any API calls in tests using vi.mock or msw.
    setupFiles: ['vitest.setup.js'],
  },
})
