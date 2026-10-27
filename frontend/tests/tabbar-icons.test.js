import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import TabBar from '../src/components/Layout/TabBar.vue'
import { useTabsStore } from '../src/stores/tabs'
import { ICON_COMPONENTS } from '../src/plugins/elementPlus'
import router from '../src/router/index.js'

// #55：TabBar 页签图标契约（console 告警清理的防回归锚点）。
//
// 路由 meta.icon 必须是「字符串名」（经 ICON_COMPONENTS 全局注册解析），
// 不能是组件对象：组件对象被 addTab 塞进 Pinia reactive store 会触发
// "Vue received a Component that was made a reactive object" 告警，且
// _persist() 的 JSON.stringify 会把组件对象破坏成垃圾结构，页签恢复后
// 触发 "missing template or render function"（#43 浏览器冒烟实录）。
// markRaw 只能修前者修不了后者，字符串方案两头都堵死。
//
// #79（T-5）：原第 1 个 describe 的静态源码扫描（读 router/index.js 文本 +
// 正则）改为真实挂载——读运行时路由记录（非源码文本），逐个建页签挂载
// TabBar，断言图标真实渲染。不再读源码文本。

const NOISE_PATTERNS = [
  /made a reactive object/,
  /Failed to resolve component/,
  /missing template or render function/,
]

describe('#55 路由 meta.icon 字符串契约（真实挂载版）', () => {
  let warnSpy
  let errorSpy

  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    warnSpy.mockRestore()
    errorSpy.mockRestore()
  })

  it('所有路由 meta.icon 均为字符串且挂载后真实渲染出 SVG', async () => {
    // 运行时路由记录（非源码文本）：meta.icon 仍须是字符串名
    const routes = router.getRoutes().filter((r) => r.meta?.icon !== undefined)
    // 防空转：路由图标数量级不断言空
    expect(routes.length).toBeGreaterThanOrEqual(15)

    const store = useTabsStore()
    for (const r of routes) {
      // 裸标识符（组件引用）视为违规——与原正则断言同契约
      expect(
        typeof r.meta.icon,
        `meta.icon 必须是字符串名，路由 ${r.path} 实际：${typeof r.meta.icon}`
      ).toBe('string')
      const name = r.name || r.path
      // store 缺省自带 Home 页签，同名跳过（不重复压栈）
      if (store.tabs.some((t) => t.name === name)) continue
      store.tabs.push({
        name,
        title: r.meta.title || r.path,
        path: r.path,
        icon: r.meta.icon,
        closable: true,
      })
    }
    // 去重后页签数与路由图标数一致（Home 缺省存在）
    expect(store.tabs).toHaveLength(routes.length)

    // global.components 复刻生产入口 installElementPlus 的全局图标注册
    const wrapper = mount(TabBar, {
      global: { components: ICON_COMPONENTS },
    })
    try {
      await flushPromises()

      // 每个页签图标都真实渲染出 SVG（缺注册即空白，计数对不上）
      expect(wrapper.findAll('.tab-icon svg')).toHaveLength(routes.length)

      const noise = [...warnSpy.mock.calls, ...errorSpy.mock.calls].flat().join('\n')
      for (const pattern of NOISE_PATTERNS) {
        expect(noise, `不应出现「${pattern}」类告警`).not.toMatch(pattern)
      }
    } finally {
      wrapper.unmount()
    }
  })
})

describe('#55 TabBar 字符串图标渲染', () => {
  let warnSpy
  let errorSpy

  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  it('字符串图标解析为真实图标组件且全程无 reactive/resolve 告警', () => {
    const store = useTabsStore()
    store.tabs.push({
      name: 'ArticleAnalysis',
      title: '文章分析',
      path: '/article-analysis',
      icon: 'Document',
      closable: true,
    })

    // global.components 复刻生产入口 installElementPlus 的全局图标注册
    const wrapper = mount(TabBar, {
      global: { components: ICON_COMPONENTS },
    })

    const icon = wrapper.find('.tab-icon')
    expect(icon.exists()).toBe(true)
    expect(icon.find('svg').exists()).toBe(true)

    const noise = [...warnSpy.mock.calls, ...errorSpy.mock.calls].flat().join('\n')
    for (const pattern of NOISE_PATTERNS) {
      expect(noise, `不应出现「${pattern}」类告警`).not.toMatch(pattern)
    }
  })
})

describe('#55 页签图标持久化往返', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('addTab 存入的字符串图标经 JSON 往返后原样恢复', () => {
    const store = useTabsStore()
    store.addTab({
      name: 'Predict',
      path: '/predict',
      meta: { title: '内容预测', icon: 'Cpu' },
    })

    const persisted = JSON.parse(localStorage.getItem('weibo_tabs'))
    const tab = persisted.find((t) => t.name === 'Predict')
    expect(tab.icon).toBe('Cpu')
    // 全量守卫：持久化里不允许出现任何非字符串图标（组件对象序列化即坏）
    for (const t of persisted) {
      expect(typeof t.icon === 'string' || t.icon === null).toBe(true)
    }
  })
})
