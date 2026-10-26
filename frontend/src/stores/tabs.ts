import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// #136：多标签工作区页签的运行时结构（字段与迁移前 JS 版逐字一致）。
export interface TabItem {
  name: string
  title: string
  path: string
  icon: string | null
  closable: boolean
}

const HOME_TAB: TabItem = {
  name: 'Home',
  title: '首页',
  path: '/home',
  icon: 'HomeFilled',
  closable: false,
}

const STORAGE_TABS_KEY = 'weibo_tabs'
const STORAGE_ACTIVE_KEY = 'weibo_active_tab'

// #136：localStorage 中的页签快照按 TabItem[] 断言恢复。
// 断言而非校验：保持迁移前的宽松恢复行为——不对持久化内容做字段校验、
// 不过滤脏数据、不新增回退分支（#131 的 41 个用例锁定该宽松语义）。
function loadTabsFromStorage(): TabItem[] {
  try {
    const saved = localStorage.getItem(STORAGE_TABS_KEY)
    if (saved) {
      const parsed = JSON.parse(saved) as TabItem[]
      if (Array.isArray(parsed) && parsed.length > 0) {
        // Ensure home tab is always first
        const hasHome = parsed.some((t) => t.name === HOME_TAB.name)
        if (!hasHome) parsed.unshift(HOME_TAB)
        return parsed
      }
    }
  } catch {
    // ignore
  }
  return [{ ...HOME_TAB }]
}

function loadActiveFromStorage(tabs: TabItem[]): string {
  try {
    const saved = localStorage.getItem(STORAGE_ACTIVE_KEY)
    if (saved && tabs.some((t) => t.name === saved)) {
      return saved
    }
  } catch {
    // ignore
  }
  return HOME_TAB.name
}

export const useTabsStore = defineStore('tabs', () => {
  const tabs = ref<TabItem[]>(loadTabsFromStorage())
  const activeTab = ref<string>(loadActiveFromStorage(tabs.value))

  // Component names to keep alive
  const cachedViews = computed(() => tabs.value.map((t) => t.name))

  function _persist() {
    localStorage.setItem(STORAGE_TABS_KEY, JSON.stringify(tabs.value))
    localStorage.setItem(STORAGE_ACTIVE_KEY, activeTab.value)
  }

  /**
   * Add a tab from a route meta. If it already exists, just activate it.
   * @param route 路由对象；字段全部可选（缺 name/path 即 no-op，与迁移前守卫一致）
   */
  function addTab(route: {
    name?: string
    path?: string
    query?: Record<string, string>
    meta?: { title?: string; icon?: string }
  }) {
    if (!route?.name || !route?.path) return

    const existing = tabs.value.find((t) => t.name === route.name)
    if (existing) {
      activeTab.value = route.name
      _persist()
      return
    }

    const newTab: TabItem = {
      name: route.name,
      title: route.meta?.title || route.name,
      path:
        route.path +
        (route.query && Object.keys(route.query).length
          ? '?' + new URLSearchParams(route.query).toString()
          : ''),
      icon: route.meta?.icon || null,
      closable: true,
    }
    tabs.value.push(newTab)
    activeTab.value = newTab.name
    _persist()
  }

  /**
   * Close/remove a tab by its name. Automatically activates adjacent tab.
   */
  function closeTab(name: string, router?: { push: (to: string) => unknown }) {
    if (name === HOME_TAB.name) return // home is unclosable

    const idx = tabs.value.findIndex((t) => t.name === name)
    if (idx === -1) return

    tabs.value.splice(idx, 1)

    // If we closed the active tab, determine next active tab
    if (activeTab.value === name) {
      const nextTab = tabs.value[idx] || tabs.value[idx - 1] || tabs.value[0]
      activeTab.value = nextTab.name
      if (router) router.push(nextTab.path)
    }
    _persist()
  }

  /**
   * Close all tabs except the given one (default: keep home)
   */
  function closeOtherTabs(keepName: string, router?: { push: (to: string) => unknown }) {
    tabs.value = tabs.value.filter((t) => !t.closable || t.name === keepName)
    if (!tabs.value.find((t) => t.name === activeTab.value)) {
      const target = tabs.value.find((t) => t.name === keepName) || tabs.value[0]
      activeTab.value = target.name
      if (router) router.push(target.path)
    }
    _persist()
  }

  /**
   * Close all closable tabs, go back to home
   */
  function closeAllTabs(router?: { push: (to: string) => unknown }) {
    tabs.value = tabs.value.filter((t) => !t.closable)
    activeTab.value = HOME_TAB.name
    if (router) router.push(HOME_TAB.path)
    _persist()
  }

  /**
   * Set active tab and navigate
   */
  function setActiveTab(name: string, router?: { push: (to: string) => unknown }) {
    const tab = tabs.value.find((t) => t.name === name)
    if (!tab) return
    activeTab.value = name
    if (router) router.push(tab.path)
    _persist()
  }

  /**
   * Reorder tabs by drag (swap indices)
   */
  function reorderTabs(fromIdx: number, toIdx: number) {
    // Don't move home tab (index 0)
    if (fromIdx === 0 || toIdx === 0) return
    if (fromIdx === toIdx) return
    const moved = tabs.value.splice(fromIdx, 1)[0]
    tabs.value.splice(toIdx, 0, moved)
    _persist()
  }

  /**
   * Update route path on a tab (when query changes etc.)
   */
  function updateTabPath(name: string, path: string) {
    const tab = tabs.value.find((t) => t.name === name)
    if (tab) {
      tab.path = path
      _persist()
    }
  }

  return {
    tabs,
    activeTab,
    cachedViews,
    addTab,
    closeTab,
    closeOtherTabs,
    closeAllTabs,
    setActiveTab,
    reorderTabs,
    updateTabPath,
    resetTabs,
  }

  /**
   * 登出时调用：清空工作区 tab（内存 + localStorage 持久化）。
   * tab 记录含有用户浏览过的路由与查询串（可能带敏感参数），多用户共机
   * 时不能让下一个账号看到上一个账号的工作区（#20 敏感缓存清理）。
   */
  function resetTabs() {
    tabs.value = [{ ...HOME_TAB }]
    activeTab.value = HOME_TAB.name
    try {
      localStorage.removeItem(STORAGE_TABS_KEY)
      localStorage.removeItem(STORAGE_ACTIVE_KEY)
    } catch {
      // ignore
    }
  }
})
