import { describe, it, expect, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

/**
 * #72（R-1）：移动端判定收敛为单源。
 *
 * 覆盖：
 * 1. 源码级：MobileNav.vue 无自有 isMobile ref/resize listener/768 字面量；
 *    全仓 JS 判定阈值仅 Layout/index.vue 一处；
 * 2. 行为级（真实 mount Layout + resize 事件驱动）：桌面宽 → 侧边栏在、
 *    底部导航缺席；移动宽 → 侧边栏消失、底部导航出现；
 * 3. 跨 768px 反复 resize → 两处同步切换（永不分裂）。
 *
 * 注意：
 * - 不做 router.push：Layout 挂载本身不导航，useRoute/router-link 在初始
 *   路由下即可工作；push 受保护路由会触发守卫的 /api/auth/me 真实请求
 *   （8s 超时），徒增耗时（实测教训）。
 * - 测试间清理 innerWidth 与组件卸载，避免污染其他文件。
 */

import router from '../src/router/index.js'
import Layout from '../src/components/Layout/index.vue'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const MOBILE_NAV_SOURCE = readFileSync(join(ROOT, 'src/components/Layout/MobileNav.vue'), 'utf8')
const LAYOUT_SOURCE = readFileSync(join(ROOT, 'src/components/Layout/index.vue'), 'utf8')

const DESKTOP_WIDTH = 1200
const MOBILE_WIDTH = 500

const setWidth = async (width) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  })
  window.dispatchEvent(new Event('resize'))
  await flushPromises()
  await nextTick()
}

const mountLayout = async (width) => {
  await setWidth(width)
  const pinia = createPinia()
  setActivePinia(pinia)
  const wrapper = mount(Layout, {
    global: {
      plugins: [pinia, router],
      stubs: {
        Sidebar: true,
        Header: true,
        TabBar: true,
        RouterView: true,
      },
    },
  })
  await flushPromises()
  await nextTick()
  return wrapper
}

afterEach(async () => {
  await setWidth(DESKTOP_WIDTH)
})

describe('移动端判定单源（#72 R-1）', () => {
  it('MobileNav 无自有判定逻辑，阈值全仓仅 Layout 一处', () => {
    // MobileNav 仅剩 prop 声明/使用
    expect(MOBILE_NAV_SOURCE).not.toMatch(/window\.innerWidth/)
    expect(MOBILE_NAV_SOURCE).not.toMatch(/addEventListener.*resize/)
    expect(MOBILE_NAV_SOURCE).not.toMatch(/removeEventListener.*resize/)
    expect(MOBILE_NAV_SOURCE).not.toMatch(/<\s*768/)
    expect(MOBILE_NAV_SOURCE).toMatch(/defineProps/)
    // 模板仍消费 isMobile（受控渲染）
    expect(MOBILE_NAV_SOURCE).toMatch(/v-if="isMobile"/)

    // Layout 为唯一判定点
    expect(LAYOUT_SOURCE).toMatch(/window\.innerWidth < 768/)
    expect(LAYOUT_SOURCE).toMatch(/:is-mobile="isMobile"/)

    // 全仓 JS 阈值断言锚点：所有 innerWidth 判定收敛于 checkMobile 单源函数
    // （#81 起含平板档，共 3 处），resize 监听仍唯一。
    // Mobile 端阈值语义不变（<768），#81 只在其旁扩展平板档。
    const block = (LAYOUT_SOURCE.match(/const checkMobile[\s\S]*?\n  \}/) || [''])[0]
    const inside = (block.match(/window\.innerWidth/g) || []).length
    const total = (LAYOUT_SOURCE.match(/window\.innerWidth/g) || []).length
    expect(inside).toBe(3)
    expect(total).toBe(3)
    const listeners = (LAYOUT_SOURCE.match(/addEventListener\('resize'/g) || []).length
    expect(listeners).toBe(1)
  })

  it('桌面宽：侧边栏在、底部导航缺席', async () => {
    const wrapper = await mountLayout(DESKTOP_WIDTH)
    try {
      expect(wrapper.find('.sidebar').exists()).toBe(true)
      expect(wrapper.find('.mobile-nav').exists()).toBe(false)
      expect(wrapper.find('.layout-container.mobile-mode').exists()).toBe(false)
      expect(wrapper.find('tab-bar-stub').exists()).toBe(true)
    } finally {
      wrapper.unmount()
    }
  })

  it('移动宽：侧边栏消失、底部导航出现', async () => {
    const wrapper = await mountLayout(MOBILE_WIDTH)
    try {
      expect(wrapper.find('.sidebar').exists()).toBe(false)
      expect(wrapper.find('.mobile-nav').exists()).toBe(true)
      expect(wrapper.findAll('.mobile-nav .nav-item').length).toBe(5)
      expect(wrapper.find('.layout-container.mobile-mode').exists()).toBe(true)
      expect(wrapper.find('tab-bar-stub').exists()).toBe(false)
    } finally {
      wrapper.unmount()
    }
  })

  it('跨 768px 反复 resize：侧边栏与底部导航同步切换', async () => {
    const wrapper = await mountLayout(DESKTOP_WIDTH)
    try {
      // 桌面 → 移动
      await setWidth(MOBILE_WIDTH)
      expect(wrapper.find('.sidebar').exists()).toBe(false)
      expect(wrapper.find('.mobile-nav').exists()).toBe(true)

      // 移动 → 桌面
      await setWidth(DESKTOP_WIDTH)
      expect(wrapper.find('.sidebar').exists()).toBe(true)
      expect(wrapper.find('.mobile-nav').exists()).toBe(false)

      // 临界值：768 为桌面侧（判定为 < 768）
      await setWidth(768)
      expect(wrapper.find('.sidebar').exists()).toBe(true)
      expect(wrapper.find('.mobile-nav').exists()).toBe(false)

      await setWidth(767)
      expect(wrapper.find('.sidebar').exists()).toBe(false)
      expect(wrapper.find('.mobile-nav').exists()).toBe(true)
    } finally {
      wrapper.unmount()
    }
  })
})
