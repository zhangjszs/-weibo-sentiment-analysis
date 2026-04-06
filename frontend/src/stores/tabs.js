import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const HOME_TAB = {
  name: 'Home',
  title: '首页',
  path: '/home',
  icon: 'HomeFilled',
  closable: false,
}

const STORAGE_TABS_KEY = 'weibo_tabs'
const STORAGE_ACTIVE_KEY = 'weibo_active_tab'

function loadTabsFromStorage() {
  try {
    const saved = localStorage.getItem(STORAGE_TABS_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      if (Array.isArray(parsed) && parsed.length > 0) {
        // Ensure home tab is always first
        const hasHome = parsed.some((t) => t.name === HOME_TAB.name)
        if (!hasHome) parsed.unshift(HOME_TAB)
        return parsed
      }
    }
  } catch (e) {
    // ignore
  }
  return [{ ...HOME_TAB }]
}

function loadActiveFromStorage(tabs) {
  try {
    const saved = localStorage.getItem(STORAGE_ACTIVE_KEY)
    if (saved && tabs.some((t) => t.name === saved)) {
      return saved
    }
  } catch (e) {
    // ignore
  }
  return HOME_TAB.name
}

export const useTabsStore = defineStore('tabs', () => {
  const tabs = ref(loadTabsFromStorage())
  const activeTab = ref(loadActiveFromStorage(tabs.value))

  // Component names to keep alive
  const cachedViews = computed(() => tabs.value.map((t) => t.name))

  function _persist() {
    localStorage.setItem(STORAGE_TABS_KEY, JSON.stringify(tabs.value))
    localStorage.setItem(STORAGE_ACTIVE_KEY, activeTab.value)
  }

  /**
   * Add a tab from a route meta. If it already exists, just activate it.
   * @param {{ name: string, path: string, meta: { title: string, icon: string } }} route
   */
  function addTab(route) {
    if (!route?.name || !route?.path) return

    const existing = tabs.value.find((t) => t.name === route.name)
    if (existing) {
      activeTab.value = route.name
      _persist()
      return
    }

    const newTab = {
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
  function closeTab(name, router) {
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
  function closeOtherTabs(keepName, router) {
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
  function closeAllTabs(router) {
    tabs.value = tabs.value.filter((t) => !t.closable)
    activeTab.value = HOME_TAB.name
    if (router) router.push(HOME_TAB.path)
    _persist()
  }

  /**
   * Set active tab and navigate
   */
  function setActiveTab(name, router) {
    const tab = tabs.value.find((t) => t.name === name)
    if (!tab) return
    activeTab.value = name
    if (router) router.push(tab.path)
    _persist()
  }

  /**
   * Reorder tabs by drag (swap indices)
   */
  function reorderTabs(fromIdx, toIdx) {
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
  function updateTabPath(name, path) {
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
  }
})
