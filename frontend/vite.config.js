import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { createComponentsPlugin } from './config/components.mjs'
import { visualizer } from 'rollup-plugin-visualizer'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd())

  return {
    plugins: [
      vue(),
      // 组件/图标按需解析配置在 build/components.mjs（#49），与 vitest 共用
      createComponentsPlugin(),
      // 一次性诊断（#40）：VISUALIZER=1 npm run build 生成模块级体积报告
      // （dist/stats.json，raw-data 模板）；日常构建零开销。
      ...(process.env.VISUALIZER
        ? [
            visualizer({
              template: 'raw-data',
              filename: 'dist/stats.json',
              gzipSize: true,
              brotliSize: false,
            }),
          ]
        : []),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      }
    },
    server: {
      port: 3000,
      host: true,
      open: true,
      proxy: {
        '/api': {
          target: env.VITE_APP_API_BASE_URL || 'http://127.0.0.1:5000',
          changeOrigin: true,
          secure: false,
          ws: true
          // 不再 rewrite，保留 /api 前缀
        },
        '/user': {
          target: env.VITE_APP_API_BASE_URL || 'http://127.0.0.1:5000',
          changeOrigin: true,
          secure: false
        },
        // deprecated: /getAllData proxy removed — frontend now uses /api/* (ADR 0002).
        // Backend retains 307 /getAllData/* → /api/* alias for one version; will be removed in next major.
        '/static': {
          target: env.VITE_APP_API_BASE_URL || 'http://127.0.0.1:5000',
          changeOrigin: true,
          secure: false
        },
        // Socket.IO（Flask-SocketIO 服务端在 /socket.io 路径）：无此代理时
        // dev 环境的 WS 握手会打到 vite 自身，必然失败（#20）
        '/socket.io': {
          target: env.VITE_APP_API_BASE_URL || 'http://127.0.0.1:5000',
          changeOrigin: true,
          secure: false,
          ws: true
        }
      }
    },
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: `@use "@/styles/variables.scss" as *;`
        }
      }
    },
    build: {
      target: 'es2020',
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: false,
      chunkSizeWarningLimit: 2000,
      rollupOptions: {
        output: {
          chunkFileNames: 'js/[name]-[hash].js',
          entryFileNames: 'js/[name]-[hash].js',
          assetFileNames: '[ext]/[name]-[hash].[ext]',
          manualChunks(id) {
            // element-plus 不再聚合为单一 chunk（#39）：聚合会把所有路由用到
            // 的组件全量塞进首屏强依赖（实测 981KB raw / 321KB gzip）。改由
            // rollup 按真实依赖拆分——首屏只携带壳层真正用到的组件，路由级
            // 组件跟随各自的路由 chunk。element-plus 的 sideEffects 声明保证
            // 组件 JS 可 tree-shake、样式不丢失。
            if (
              id.includes('node_modules/echarts/') ||
              id.includes('node_modules/zrender/')
            ) {
              return 'echarts'
            }
          }
        }
      }
    }
  }
})
