import { createApp } from 'vue'
import { createPinia } from 'pinia'
import 'element-plus/dist/index.css'
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
import { lazyLoad } from './directives/lazyLoad'

const app = createApp(App)

app.directive('lazy', lazyLoad)

app.use(createPinia())
app.use(router)
installElementPlus(app)

if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js')
      .then((registration) => {
        console.log('SW registered:', registration.scope)
      })
      .catch((error) => {
        console.log('SW registration failed:', error)
      })
  })
}

app.mount('#app')
