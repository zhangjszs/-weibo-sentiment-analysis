import { describe, it, expect, vi, beforeEach } from 'vitest'
import { readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import TabBar from '../src/components/Layout/TabBar.vue'
import { useTabsStore } from '../src/stores/tabs.js'
import { ICON_COMPONENTS } from '../src/plugins/elementPlus.js'

// #55：TabBar 页签图标契约（console 告警清理的防回归锚点）。
//
// 路由 meta.icon 必须是「字符串名」（经 ICON_COMPONENTS 全局注册解析），
// 不能是组件对象：组件对象被 addTab 塞进 Pinia reactive store 会触发
// "Vue received a Component that was made a reactive object" 告警，且
// _persist() 的 JSON.stringify 会把组件对象破坏成垃圾结构，页签恢复后
// 触发 "missing template or render function"（#43 浏览器冒烟实录）。
// markRaw 只能修前者修不了后者，字符串方案两头都堵死。

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const ROUTER_SOURCE = readFileSync(join(ROOT, 'src/router/index.js'), 'utf8')

const NOISE_PATTERNS = [
  /made a reactive object/,
  /Failed to resolve component/,
  /missing template or render function/,
]

describe('#55 路由 meta.icon 字符串契约', () => {
  it('router/index.js 中所有 meta.icon 都是带引号的字符串且已注册', () => {
    // 逐字面量匹配 meta 行里的 icon: 值——裸标识符（组件引用）视为违规
    const refs = [...ROUTER_SOURCE.matchAll(/icon:\s*([^\s,}]+)/g)].map((m) => m[1])

    // 扫描必须真的命中（防止正则失配让断言空转）
    expect(refs.length).toBeGreaterThanOrEqual(15)

    for (const raw of refs) {
      expect(raw, `meta.icon 必须是字符串字面量，实际：${raw}`).toMatch(/^'[A-Za-z]+'$/)
      const name = raw.slice(1, -1)
      expect(ICON_COMPONENTS, `${name} 未在 ICON_COMPONENTS 注册`).toHaveProperty(name)
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
