import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const theme = ref(localStorage.getItem('weibo_theme') || 'light')
  const device = ref('desktop')

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    localStorage.setItem('weibo_theme', theme.value)
    document.documentElement.className = theme.value
  }

  function setTheme(themeName) {
    theme.value = themeName
    localStorage.setItem('weibo_theme', themeName)
    document.documentElement.className = themeName
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  watch(
    theme,
    (newTheme) => {
      if (newTheme === 'dark') {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
    },
    { immediate: true }
  )

  return {
    sidebarCollapsed,
    theme,
    device,
    toggleTheme,
    setTheme,
    toggleSidebar,
  }
})
