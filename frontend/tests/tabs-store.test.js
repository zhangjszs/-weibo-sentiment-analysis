import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { useTabsStore } from '@/stores/tabs'

/**
 * #131：stores/tabs.js 多标签工作区状态机锁定。
 * 真实 pinia + jsdom 真实 localStorage；router 仅用可断言 stub `{ push: vi.fn() }`。
 */

const TABS_KEY = 'weibo_tabs'
const ACTIVE_KEY = 'weibo_active_tab'

const HOME = {
  name: 'Home',
  title: '首页',
  path: '/home',
  icon: 'HomeFilled',
  closable: false,
}

const tabOf = (name, extra = {}) => ({
  name,
  title: name,
  path: `/${name.toLowerCase()}`,
  icon: null,
  closable: true,
  ...extra,
})

const route = (name, extra = {}) => ({
  name,
  path: `/${name.toLowerCase()}`,
  meta: { title: `${name}标题`, icon: 'Icon' },
  ...extra,
})

const names = (store) => store.tabs.map((t) => t.name)
const storedTabs = () => JSON.parse(localStorage.getItem(TABS_KEY))
const storedActive = () => localStorage.getItem(ACTIVE_KEY)

function seedStorage(tabs, active) {
  if (tabs !== undefined) {
    localStorage.setItem(TABS_KEY, typeof tabs === 'string' ? tabs : JSON.stringify(tabs))
  }
  if (active !== undefined) localStorage.setItem(ACTIVE_KEY, active)
}

/** 建立 [Home, A, B, C] 且 activeTab 为指定值的 store（经存储恢复，不依赖 addTab）。 */
function storeWithTabs(active = 'Home') {
  seedStorage([HOME, tabOf('A'), tabOf('B'), tabOf('C')], active)
  setActivePinia(createPinia())
  return useTabsStore()
}

let router

beforeEach(() => {
  localStorage.removeItem(TABS_KEY)
  localStorage.removeItem(ACTIVE_KEY)
  setActivePinia(createPinia())
  router = { push: vi.fn() }
})

afterEach(() => {
  localStorage.removeItem(TABS_KEY)
  localStorage.removeItem(ACTIVE_KEY)
})

describe('存储恢复与损坏回退 (#131)', () => {
  it('无存储时初始化为仅含 Home 且激活 Home，cachedViews 同步', () => {
    const store = useTabsStore()

    expect(store.tabs).toEqual([HOME])
    expect(store.activeTab).toBe('Home')
    expect(store.cachedViews).toEqual(['Home'])
  })

  it('存储合法时恢复 tabs 与 activeTab', () => {
    seedStorage([HOME, tabOf('A'), tabOf('B')], 'B')

    const store = useTabsStore()

    expect(names(store)).toEqual(['Home', 'A', 'B'])
    expect(store.activeTab).toBe('B')
    expect(store.cachedViews).toEqual(['Home', 'A', 'B'])
  })

  it('存储缺少 Home 时在首位补入 Home', () => {
    seedStorage([tabOf('A'), tabOf('B')], 'A')

    const store = useTabsStore()

    expect(names(store)).toEqual(['Home', 'A', 'B'])
    expect(store.tabs[0]).toEqual(HOME)
    expect(store.activeTab).toBe('A')
  })

  it.each([
    ['非法 JSON', '{not json'],
    ['空数组', '[]'],
    ['空串', ''],
    ['非数组 JSON', '{"name":"A"}'],
  ])('weibo_tabs 为%s 时回退为 [Home]', (_label, raw) => {
    seedStorage(raw, 'A')

    const store = useTabsStore()

    expect(store.tabs).toEqual([HOME])
    expect(store.activeTab).toBe('Home')
  })

  it('weibo_active_tab 不在 tabs 中时回退为 Home', () => {
    seedStorage([HOME, tabOf('A')], 'Ghost')

    const store = useTabsStore()

    expect(store.activeTab).toBe('Home')
  })

  it('仅有 tabs 而无 weibo_active_tab 时激活 Home', () => {
    seedStorage([HOME, tabOf('A')])

    expect(useTabsStore().activeTab).toBe('Home')
  })
})

describe('addTab (#131)', () => {
  it.each([
    ['route 为空', undefined],
    ['缺 name', { path: '/x' }],
    ['缺 path', { name: 'X' }],
  ])('%s 时为 no-op，不写存储', (_label, input) => {
    const store = useTabsStore()

    store.addTab(input)

    expect(store.tabs).toEqual([HOME])
    expect(store.activeTab).toBe('Home')
    expect(localStorage.getItem(TABS_KEY)).toBeNull()
    expect(localStorage.getItem(ACTIVE_KEY)).toBeNull()
  })

  it('已存在同名 tab 时只激活并持久化，不重复新增', () => {
    const store = storeWithTabs('Home')

    store.addTab(route('B'))

    expect(names(store)).toEqual(['Home', 'A', 'B', 'C'])
    expect(store.activeTab).toBe('B')
    expect(storedActive()).toBe('B')
    expect(storedTabs().map((t) => t.name)).toEqual(['Home', 'A', 'B', 'C'])
  })

  it('新增 tab：title 取 meta.title、icon 取 meta.icon、closable=true 并激活', () => {
    const store = useTabsStore()

    store.addTab(route('Hot'))

    expect(store.tabs[1]).toEqual({
      name: 'Hot',
      title: 'Hot标题',
      path: '/hot',
      icon: 'Icon',
      closable: true,
    })
    expect(store.activeTab).toBe('Hot')
    expect(store.cachedViews).toEqual(['Home', 'Hot'])
  })

  it('缺 meta 时 title 回退为 name、icon 为 null', () => {
    const store = useTabsStore()

    store.addTab({ name: 'Bare', path: '/bare' })

    expect(store.tabs[1]).toEqual({
      name: 'Bare',
      title: 'Bare',
      path: '/bare',
      icon: null,
      closable: true,
    })
  })

  it('query 序列化进 path（?a=1&b=2），空 query 不追加问号', () => {
    const store = useTabsStore()

    store.addTab(route('Q', { query: { a: '1', b: '2' } }))
    store.addTab(route('E', { query: {} }))

    expect(store.tabs.find((t) => t.name === 'Q').path).toBe('/q?a=1&b=2')
    expect(store.tabs.find((t) => t.name === 'E').path).toBe('/e')
  })

  it('新增后 weibo_tabs / weibo_active_tab 与内存状态 JSON 往返一致', () => {
    const store = useTabsStore()

    store.addTab(route('Hot', { query: { k: 'v' } }))

    expect(storedTabs()).toEqual(JSON.parse(JSON.stringify(store.tabs)))
    expect(storedTabs()[1].path).toBe('/hot?k=v')
    expect(storedActive()).toBe(store.activeTab)
  })
})

describe('closeTab (#131)', () => {
  it('关闭 Home 被拒绝：tabs/active/存储/路由均不变', () => {
    const store = storeWithTabs('A')

    store.closeTab('Home', router)

    expect(names(store)).toEqual(['Home', 'A', 'B', 'C'])
    expect(store.activeTab).toBe('A')
    expect(router.push).not.toHaveBeenCalled()
  })

  it('关闭不存在的 name 为 no-op，不写存储', () => {
    const store = storeWithTabs('A')
    localStorage.removeItem(TABS_KEY)

    store.closeTab('Ghost', router)

    expect(names(store)).toEqual(['Home', 'A', 'B', 'C'])
    expect(router.push).not.toHaveBeenCalled()
    expect(localStorage.getItem(TABS_KEY)).toBeNull()
  })

  it('关闭非激活 tab：activeTab 不变、不跳转、持久化更新', () => {
    const store = storeWithTabs('A')

    store.closeTab('C', router)

    expect(names(store)).toEqual(['Home', 'A', 'B'])
    expect(store.activeTab).toBe('A')
    expect(router.push).not.toHaveBeenCalled()
    expect(storedTabs().map((t) => t.name)).toEqual(['Home', 'A', 'B'])
    expect(storedActive()).toBe('A')
  })

  it('关闭激活的中间 tab：优先激活右侧邻居并 push 其 path', () => {
    const store = storeWithTabs('B')

    store.closeTab('B', router)

    expect(names(store)).toEqual(['Home', 'A', 'C'])
    expect(store.activeTab).toBe('C')
    expect(router.push).toHaveBeenCalledTimes(1)
    expect(router.push).toHaveBeenCalledWith('/c')
    expect(storedActive()).toBe('C')
  })

  it('关闭激活的末尾 tab：回退激活左侧邻居', () => {
    const store = storeWithTabs('C')

    store.closeTab('C', router)

    expect(names(store)).toEqual(['Home', 'A', 'B'])
    expect(store.activeTab).toBe('B')
    expect(router.push).toHaveBeenCalledWith('/b')
  })

  it('关闭激活 tab 且未传 router 时只切换 activeTab，不抛错', () => {
    const store = storeWithTabs('B')

    store.closeTab('B')

    expect(store.activeTab).toBe('C')
    expect(storedActive()).toBe('C')
  })
})

describe('closeOtherTabs (#131)', () => {
  it('只保留非 closable 与 keepName；激活 tab 被清时切到 keep 并 push', () => {
    const store = storeWithTabs('C')

    store.closeOtherTabs('A', router)

    expect(names(store)).toEqual(['Home', 'A'])
    expect(store.activeTab).toBe('A')
    expect(router.push).toHaveBeenCalledTimes(1)
    expect(router.push).toHaveBeenCalledWith('/a')
    expect(storedTabs().map((t) => t.name)).toEqual(['Home', 'A'])
    expect(storedActive()).toBe('A')
  })

  it('激活 tab 恰为 keepName 时不跳转', () => {
    const store = storeWithTabs('B')

    store.closeOtherTabs('B', router)

    expect(names(store)).toEqual(['Home', 'B'])
    expect(store.activeTab).toBe('B')
    expect(router.push).not.toHaveBeenCalled()
  })

  it('激活 Home 时保留 Home 与 keep，不跳转', () => {
    const store = storeWithTabs('Home')

    store.closeOtherTabs('A', router)

    expect(names(store)).toEqual(['Home', 'A'])
    expect(store.activeTab).toBe('Home')
    expect(router.push).not.toHaveBeenCalled()
  })

  it('keepName 缺省且激活 tab 被清时回到首位 Home 并 push /home', () => {
    const store = storeWithTabs('B')

    store.closeOtherTabs(undefined, router)

    expect(names(store)).toEqual(['Home'])
    expect(store.activeTab).toBe('Home')
    expect(router.push).toHaveBeenCalledWith('/home')
  })
})

describe('closeAllTabs / setActiveTab (#131)', () => {
  it('closeAllTabs：只剩 Home、激活 Home、push /home 并持久化', () => {
    const store = storeWithTabs('B')

    store.closeAllTabs(router)

    expect(names(store)).toEqual(['Home'])
    expect(store.activeTab).toBe('Home')
    expect(router.push).toHaveBeenCalledWith('/home')
    expect(storedTabs().map((t) => t.name)).toEqual(['Home'])
    expect(storedActive()).toBe('Home')
  })

  it('closeAllTabs 未传 router 时不抛错', () => {
    const store = storeWithTabs('B')

    store.closeAllTabs()

    expect(names(store)).toEqual(['Home'])
    expect(store.activeTab).toBe('Home')
  })

  it('setActiveTab 未知 name：no-op，不跳转、不写存储', () => {
    const store = storeWithTabs('A')
    localStorage.removeItem(ACTIVE_KEY)

    store.setActiveTab('Ghost', router)

    expect(store.activeTab).toBe('A')
    expect(router.push).not.toHaveBeenCalled()
    expect(localStorage.getItem(ACTIVE_KEY)).toBeNull()
  })

  it('setActiveTab 已知 name：激活、push tab.path 并持久化', () => {
    const store = storeWithTabs('Home')

    store.setActiveTab('C', router)

    expect(store.activeTab).toBe('C')
    expect(router.push).toHaveBeenCalledTimes(1)
    expect(router.push).toHaveBeenCalledWith('/c')
    expect(storedActive()).toBe('C')
  })

  it('setActiveTab 未传 router 时仅激活', () => {
    const store = storeWithTabs('Home')

    store.setActiveTab('B')

    expect(store.activeTab).toBe('B')
    expect(storedActive()).toBe('B')
  })
})

describe('reorderTabs (#131)', () => {
  it.each([
    ['from 为 0', 0, 2],
    ['to 为 0', 2, 0],
    ['from === to', 2, 2],
  ])('%s 时拒绝移动，不写存储', (_label, from, to) => {
    const store = storeWithTabs('A')
    localStorage.removeItem(TABS_KEY)

    store.reorderTabs(from, to)

    expect(names(store)).toEqual(['Home', 'A', 'B', 'C'])
    expect(localStorage.getItem(TABS_KEY)).toBeNull()
  })

  it('正常移动：后移与前移顺序正确，Home 始终首位，并持久化', () => {
    const store = storeWithTabs('A')

    store.reorderTabs(1, 3)
    expect(names(store)).toEqual(['Home', 'B', 'C', 'A'])

    store.reorderTabs(3, 1)
    expect(names(store)).toEqual(['Home', 'A', 'B', 'C'])

    store.reorderTabs(2, 3)
    expect(names(store)).toEqual(['Home', 'A', 'C', 'B'])
    expect(storedTabs().map((t) => t.name)).toEqual(['Home', 'A', 'C', 'B'])
  })
})

describe('updateTabPath (#131)', () => {
  it('已知 name：更新 path 并持久化，其余字段不变', () => {
    const store = storeWithTabs('A')

    store.updateTabPath('B', '/b?page=2')

    const b = store.tabs.find((t) => t.name === 'B')
    expect(b).toEqual({ ...tabOf('B'), path: '/b?page=2' })
    expect(storedTabs().find((t) => t.name === 'B').path).toBe('/b?page=2')
  })

  it('未知 name：no-op，不写存储', () => {
    const store = storeWithTabs('A')
    localStorage.removeItem(TABS_KEY)

    store.updateTabPath('Ghost', '/ghost')

    expect(store.tabs.map((t) => t.path)).toEqual(['/home', '/a', '/b', '/c'])
    expect(localStorage.getItem(TABS_KEY)).toBeNull()
  })
})

describe('resetTabs (#131，#20 敏感缓存清理)', () => {
  it('重置为 [Home]、激活 Home，并移除 localStorage 两个键', () => {
    const store = storeWithTabs('B')
    store.addTab(route('Secret', { query: { token: 'abc' } }))
    expect(localStorage.getItem(TABS_KEY)).toContain('token=abc')

    store.resetTabs()

    expect(store.tabs).toEqual([HOME])
    expect(store.activeTab).toBe('Home')
    expect(localStorage.getItem(TABS_KEY)).toBeNull()
    expect(localStorage.getItem(ACTIVE_KEY)).toBeNull()
  })

  it('重置后新建 store 不会恢复上一账号的工作区', () => {
    const store = storeWithTabs('B')
    store.resetTabs()

    setActivePinia(createPinia())
    const fresh = useTabsStore()

    expect(fresh.tabs).toEqual([HOME])
    expect(fresh.activeTab).toBe('Home')
  })
})

describe('持久化往返 (#131)', () => {
  it('混合操作后存储内容与内存状态一致，且可被新 store 原样恢复', () => {
    const store = useTabsStore()

    store.addTab(route('A'))
    store.addTab(route('B', { query: { x: '1' } }))
    store.addTab(route('C'))
    store.reorderTabs(1, 3)
    store.updateTabPath('A', '/a?y=2')
    store.closeTab('B', router)
    store.setActiveTab('A', router)

    expect(storedTabs()).toEqual(JSON.parse(JSON.stringify(store.tabs)))
    expect(storedActive()).toBe(store.activeTab)

    setActivePinia(createPinia())
    const restored = useTabsStore()

    expect(restored.tabs).toEqual(store.tabs)
    expect(restored.activeTab).toBe('A')
    expect(names(restored)).toEqual(['Home', 'C', 'A'])
  })
})
