import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'

import { useAppStore } from '@/stores/app'

/**
 * #130：stores/app.js 的主题持久化 / dark class 联动 / 侧栏开关行为锁定。
 * 使用真实 pinia + jsdom 真实 localStorage 与 document，不 mock 任何全局。
 */

const THEME_KEY = 'weibo_theme'
const root = () => document.documentElement

function resetEnvironment() {
  localStorage.clear()
  root().className = ''
}

beforeEach(() => {
  resetEnvironment()
  setActivePinia(createPinia())
})

afterEach(() => {
  resetEnvironment()
})

describe('初始化 (#130)', () => {
  it('无存储时默认 light/展开/desktop，且不添加 dark class', () => {
    const store = useAppStore()

    expect(store.theme).toBe('light')
    expect(store.sidebarCollapsed).toBe(false)
    expect(store.device).toBe('desktop')
    expect(root().classList.contains('dark')).toBe(false)
    // 初始化本身不写存储，持久化只发生在显式切换时
    expect(localStorage.getItem(THEME_KEY)).toBeNull()
  })

  it('存储为 dark 时恢复 dark，并由 immediate watch 立即加上 dark class', () => {
    localStorage.setItem(THEME_KEY, 'dark')

    const store = useAppStore()

    expect(store.theme).toBe('dark')
    expect(root().classList.contains('dark')).toBe(true)
  })

  it('存储为 light 时恢复 light，且清除根元素上残留的 dark class', () => {
    localStorage.setItem(THEME_KEY, 'light')
    root().classList.add('dark')

    const store = useAppStore()

    expect(store.theme).toBe('light')
    expect(root().classList.contains('dark')).toBe(false)
  })
})

describe('toggleTheme (#130)', () => {
  it('light → dark → light 双向切换，每步同步存储、className 与 dark class', async () => {
    const store = useAppStore()

    store.toggleTheme()
    await nextTick()
    expect(store.theme).toBe('dark')
    expect(localStorage.getItem(THEME_KEY)).toBe('dark')
    expect(root().className).toBe('dark')
    expect(root().classList.contains('dark')).toBe(true)

    store.toggleTheme()
    await nextTick()
    expect(store.theme).toBe('light')
    expect(localStorage.getItem(THEME_KEY)).toBe('light')
    expect(root().className).toBe('light')
    expect(root().classList.contains('dark')).toBe(false)
  })

  it('从存储恢复的 dark 下切换会回到 light 并移除 dark class', async () => {
    localStorage.setItem(THEME_KEY, 'dark')
    const store = useAppStore()

    store.toggleTheme()
    await nextTick()

    expect(store.theme).toBe('light')
    expect(localStorage.getItem(THEME_KEY)).toBe('light')
    expect(root().classList.contains('dark')).toBe(false)
  })
})

describe('setTheme (#130)', () => {
  it("setTheme('dark') 直接赋值、持久化并同步 dark class", async () => {
    const store = useAppStore()

    store.setTheme('dark')
    await nextTick()

    expect(store.theme).toBe('dark')
    expect(localStorage.getItem(THEME_KEY)).toBe('dark')
    expect(root().className).toBe('dark')
    expect(root().classList.contains('dark')).toBe(true)
  })

  it("setTheme('light') 覆盖 dark：存储改写且 dark class 移除", async () => {
    const store = useAppStore()
    store.setTheme('dark')
    await nextTick()

    store.setTheme('light')
    await nextTick()

    expect(store.theme).toBe('light')
    expect(localStorage.getItem(THEME_KEY)).toBe('light')
    expect(root().classList.contains('dark')).toBe(false)
  })

  it('持久化的主题能被新 pinia 实例恢复（往返）', () => {
    useAppStore().setTheme('dark')

    setActivePinia(createPinia())
    const restored = useAppStore()

    expect(restored.theme).toBe('dark')
  })
})

describe('toggleSidebar (#130)', () => {
  it('false → true → false 布尔翻转，且不影响主题与存储', () => {
    const store = useAppStore()

    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(true)

    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(false)

    expect(store.theme).toBe('light')
    expect(localStorage.getItem(THEME_KEY)).toBeNull()
  })
})
