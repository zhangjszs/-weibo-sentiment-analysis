/**
 * 主题相关组合式函数
 * 提供暗黑模式切换和主题管理
 */

import { ref, computed, onMounted, watch } from 'vue'
import { useAppStore } from '@/stores/app'

/**
 * 使用主题
 */
export function useTheme() {
  const appStore = useAppStore()

  const isDark = computed(() => appStore.theme === 'dark')

  // 初始化主题
  const initTheme = () => {
    const savedTheme = localStorage.getItem('weibo_theme') || 'light'
    applyTheme(savedTheme)
  }

  // 应用主题
  const applyTheme = (themeName) => {
    const html = document.documentElement

    if (themeName === 'dark') {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }

    html.setAttribute('data-theme', themeName)
  }

  // 切换主题
  const toggleTheme = () => {
    const newTheme = isDark.value ? 'light' : 'dark'
    appStore.setTheme(newTheme)
    applyTheme(newTheme)
  }

  // 设置主题
  const setTheme = (themeName) => {
    appStore.setTheme(themeName)
    applyTheme(themeName)
  }

  // 监听主题变化
  watch(
    () => appStore.theme,
    (newTheme) => {
      applyTheme(newTheme)
    }
  )

  // 初始化
  onMounted(() => {
    initTheme()
  })

  return {
    isDark,
    toggleTheme,
    setTheme,
    initTheme,
  }
}

/**
 * 主题色配置
 */
export const themeColors = {
  light: {
    primary: '#0078D4',
    success: '#28a745',
    warning: '#ffc107',
    danger: '#dc3545',
    info: '#6c757d',
    background: '#f0f2f5',
    cardBg: '#ffffff',
    textPrimary: '#333333',
    textSecondary: '#666666',
    border: '#e8e8e8',
  },
  dark: {
    primary: '#3794ff',
    success: '#34d058',
    warning: '#ffcc00',
    danger: '#ea4a5a',
    info: '#8b949e',
    background: '#0d1117',
    cardBg: '#161b22',
    textPrimary: '#c9d1d9',
    textSecondary: '#8b949e',
    border: '#30363d',
  },
}

/**
 * 获取当前主题色
 */
export function getThemeColor(colorName) {
  const theme = localStorage.getItem('weibo_theme') || 'light'
  return themeColors[theme]?.[colorName] || themeColors.light[colorName]
}

/**
 * 高对比度主题
 */
export function useHighContrast() {
  const isHighContrast = ref(
    typeof localStorage !== 'undefined'
      ? localStorage.getItem('weibo_high_contrast') === 'true'
      : false
  )

  const applyHighContrast = (enabled) => {
    const html = document.documentElement
    if (enabled) {
      html.classList.add('high-contrast')
      html.setAttribute('data-contrast', 'high')
    } else {
      html.classList.remove('high-contrast')
      html.removeAttribute('data-contrast')
    }
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('weibo_high_contrast', String(enabled))
    }
  }

  const toggleHighContrast = () => {
    isHighContrast.value = !isHighContrast.value
    applyHighContrast(isHighContrast.value)
  }

  onMounted(() => {
    applyHighContrast(isHighContrast.value)
  })

  return { isHighContrast, toggleHighContrast, applyHighContrast }
}

/**
 * 字体大小调节
 */
const FONT_SIZES = { small: 12, medium: 14, large: 16, xlarge: 18 }
const DEFAULT_FONT_SIZE = 'medium'

export function useFontSize() {
  const fontSize = ref(
    typeof localStorage !== 'undefined'
      ? localStorage.getItem('weibo_font_size') || DEFAULT_FONT_SIZE
      : DEFAULT_FONT_SIZE
  )

  const applyFontSize = (size) => {
    const px = FONT_SIZES[size] || FONT_SIZES[DEFAULT_FONT_SIZE]
    document.documentElement.style.setProperty('--base-font-size', px + 'px')
    document.documentElement.setAttribute('data-font-size', size)
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('weibo_font_size', size)
    }
  }

  const setFontSize = (size) => {
    if (!FONT_SIZES[size]) return
    fontSize.value = size
    applyFontSize(size)
  }

  const increaseFontSize = () => {
    const keys = Object.keys(FONT_SIZES)
    const idx = keys.indexOf(fontSize.value)
    if (idx < keys.length - 1) setFontSize(keys[idx + 1])
  }

  const decreaseFontSize = () => {
    const keys = Object.keys(FONT_SIZES)
    const idx = keys.indexOf(fontSize.value)
    if (idx > 0) setFontSize(keys[idx - 1])
  }

  onMounted(() => {
    applyFontSize(fontSize.value)
  })

  return { fontSize, fontSizes: FONT_SIZES, setFontSize, increaseFontSize, decreaseFontSize }
}

/**
 * ARIA 无障碍辅助
 */
export function useAccessibility() {
  const announceMessage = ref('')
  let announceTimer = null

  const announce = (message, politeness = 'polite') => {
    announceMessage.value = ''
    if (announceTimer) clearTimeout(announceTimer)
    announceTimer = setTimeout(() => {
      announceMessage.value = message
    }, 50)
  }

  const setAriaLabel = (el, label) => {
    if (el) el.setAttribute('aria-label', label)
  }

  const setAriaExpanded = (el, expanded) => {
    if (el) el.setAttribute('aria-expanded', String(expanded))
  }

  const setAriaLive = (el, politeness = 'polite') => {
    if (el) el.setAttribute('aria-live', politeness)
  }

  const trapFocus = (containerEl) => {
    if (!containerEl) return () => {}
    const focusable = containerEl.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex=-1])'
    )
    if (!focusable.length) return () => {}
    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    const handler = (e) => {
      if (e.key !== 'Tab') return
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault()
          last.focus()
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }
    containerEl.addEventListener('keydown', handler)
    first.focus()
    return () => containerEl.removeEventListener('keydown', handler)
  }

  return { announceMessage, announce, setAriaLabel, setAriaExpanded, setAriaLive, trapFocus }
}
