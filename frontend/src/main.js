import { createApp } from 'vue'
import { createPinia } from 'pinia'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'

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
