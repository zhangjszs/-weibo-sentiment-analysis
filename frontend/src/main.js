import { createApp } from 'vue'
import { createPinia } from 'pinia'
// #39：组件样式由 ElementPlusResolver 按模板标签按需注入，不再全量引入
// dist/index.css（360KB）。以下是以 JS API 形式使用、模板扫描不到的组件，
// 必须手工补样式；dark 变量保持全量（纯变量，体积可忽略）。
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'
import 'element-plus/es/components/loading/style/css'
import 'element-plus/theme-chalk/dark/css-vars.css'

// Inter 本地字体（#20）：替代 Google Fonts 外链，与 CSP 一致且离线可用
import '@fontsource/inter/300.css'
import '@fontsource/inter/400.css'
import '@fontsource/inter/500.css'
import '@fontsource/inter/600.css'
import '@fontsource/inter/700.css'
import '@fontsource/inter/800.css'

import App from './App.vue'
import router from './router'
import { installElementPlus } from './plugins/elementPlus'
import './styles/theme.scss'
import './styles/index.scss'
const app = createApp(App)

app.use(createPinia())
app.use(router)
installElementPlus(app)

if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((error) => {
      console.error('SW registration failed:', error)
    })
  })
}

app.mount('#app')
