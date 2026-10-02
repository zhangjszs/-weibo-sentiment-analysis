import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import * as elementPlusIcons from '@element-plus/icons-vue'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// #39：模板里以标签形式直接使用的 element-plus 图标（<Star /> 等）按需自动
// 引入，替代曾经的「全量注册 290 个图标」。字符串形式的引用（路由 meta、
// icon="X" prop、<component :is="'X'">）仍走 plugins/elementPlus.js 的
// 最小全局注册，两套机制互不重叠。
const ICON_NAMES = new Set(Object.keys(elementPlusIcons))
const iconResolver = (name) => {
  if (ICON_NAMES.has(name)) {
    return { name, from: '@element-plus/icons-vue' }
  }
}

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd())

  return {
    plugins: [
      vue(),
      Components({
        resolvers: [ElementPlusResolver(), iconResolver],
        dts: false,
      }),
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
