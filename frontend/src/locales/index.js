import zhCN from './zh-CN.js'
import enUS from './en-US.js'

export const messages = {
  'zh-CN': zhCN,
  'en-US': enUS,
}

export const defaultLocale = 'zh-CN'
export const supportedLocales = ['zh-CN', 'en-US']

/**
 * 轻量级 i18n composable（不依赖 vue-i18n 包）
 * 使用 localStorage 持久化语言设置
 */
import { ref, computed } from 'vue'

const currentLocale = ref(
  typeof localStorage !== 'undefined'
    ? localStorage.getItem('weibo_locale') || defaultLocale
    : defaultLocale
)

export function useI18n() {
  const locale = currentLocale

  const setLocale = (lang) => {
    if (!supportedLocales.includes(lang)) return
    currentLocale.value = lang
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('weibo_locale', lang)
    }
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('lang', lang)
    }
  }

  const t = (key, params = {}) => {
    const keys = key.split('.')
    let value = messages[currentLocale.value]
    for (const k of keys) {
      value = value?.[k]
      if (value === undefined) break
    }
    if (value === undefined) {
      // fallback to zh-CN
      value = messages[defaultLocale]
      for (const k of keys) {
        value = value?.[k]
        if (value === undefined) break
      }
    }
    if (typeof value !== 'string') return key
    return value.replace(/\{(\w+)\}/g, (_, k) => params[k] ?? '')
  }

  return { locale, setLocale, t, supportedLocales }
}

export default { messages, defaultLocale, supportedLocales, useI18n }
