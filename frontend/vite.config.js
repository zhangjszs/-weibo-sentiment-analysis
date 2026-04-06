import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd())

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
        '#': path.resolve(__dirname, 'types')
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
        '/getAllData': {
          target: env.VITE_APP_API_BASE_URL || 'http://127.0.0.1:5000',
          changeOrigin: true,
          secure: false
        },
        '/static': {
          target: env.VITE_APP_API_BASE_URL || 'http://127.0.0.1:5000',
          changeOrigin: true,
          secure: false
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
      target: 'es2015',
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
            if (
              id.includes('node_modules/element-plus/') ||
              id.includes('node_modules/@element-plus/icons-vue/')
            ) {
              return 'element-plus'
            }
            if (
              id.includes('node_modules/echarts/') ||
              id.includes('node_modules/zrender/') ||
              id.includes('node_modules/vue-echarts/')
            ) {
              return 'echarts'
            }
          }
        }
      }
    }
  }
})
