import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

/**
 * #78（U-10）：BigScreen 热门话题补空态。
 *
 * 覆盖：
 * 1. topics 为空且无失败 → 可见空态（.no-topics / 暂无话题），不再是一块空白；
 * 2. topics 非空 → 空态不渲染，话题正常渲染；
 * 3. 加载失败 → 面板错误态代替空态（#19：失败不伪装成空态），且不清空旧话题。
 *
 * mock 层级：@/api/stats 五函数；@/utils/chinaMap；BaseChart stub。
 */

vi.mock('@/api/stats', () => ({
  getBigScreenStats: vi.fn(),
  getBigScreenRegion: vi.fn(),
  getBigScreenTrend: vi.fn(),
  getBigScreenHotTopics: vi.fn(),
  getBigScreenAlerts: vi.fn(),
}))

vi.mock('@/utils/chinaMap', () => ({
  ensureChinaMap: vi.fn(() => Promise.resolve({})),
}))

import {
  getBigScreenStats,
  getBigScreenRegion,
  getBigScreenTrend,
  getBigScreenHotTopics,
  getBigScreenAlerts,
} from '@/api/stats'
import BigScreen from '../src/views/dashboard/BigScreen.vue'

const envelope = (data) => ({ code: 200, msg: 'ok', data })
const TOPIC = { name: '话题A', percent: 50, heat: 100 }

const mockAllSuccess = (topics = [TOPIC]) => {
  getBigScreenStats.mockResolvedValue(envelope({ articleCount: 1 }))
  getBigScreenRegion.mockResolvedValue(envelope({ data: [] }))
  getBigScreenTrend.mockResolvedValue(envelope({ times: [], counts: [] }))
  getBigScreenHotTopics.mockResolvedValue(envelope({ topics }))
  getBigScreenAlerts.mockResolvedValue(envelope({ alerts: [] }))
}

const mountView = () =>
  mount(BigScreen, {
    global: { stubs: { BaseChart: true } },
  })

beforeEach(() => {
  vi.clearAllMocks()
  setActivePinia(createPinia())
  mockAllSuccess()
})

describe('BigScreen 热门话题空态（#78 U-10）', () => {
  it('topics 为空时渲染明确空态，不再是一块空白', async () => {
    mockAllSuccess([])
    const wrapper = mountView()
    try {
      await flushPromises()

      expect(wrapper.find('.no-topics').exists()).toBe(true)
      expect(wrapper.text()).toContain('暂无话题')
      expect(wrapper.findAll('.topic-item').length).toBe(0)
    } finally {
      wrapper.unmount()
    }
  })

  it('topics 非空时空态不渲染', async () => {
    const wrapper = mountView()
    try {
      await flushPromises()

      expect(wrapper.find('.no-topics').exists()).toBe(false)
      expect(wrapper.text()).toContain('话题A')
    } finally {
      wrapper.unmount()
    }
  })

  it('加载失败时错误态代替空态，且不清空旧话题（#19）', async () => {
    const wrapper = mountView()
    try {
      await flushPromises()
      expect(wrapper.text()).toContain('话题A')
      expect(wrapper.find('.no-topics').exists()).toBe(false)

      // 面板级刷新失败（新请求失败）
      getBigScreenHotTopics.mockRejectedValue(new Error('topics down'))
      await wrapper.vm.retryPanel('topics')
      await flushPromises()

      expect(wrapper.find('.panel-error').exists()).toBe(true)
      // 失败不伪装成空态
      expect(wrapper.find('.no-topics').exists()).toBe(false)
      expect(wrapper.text()).not.toContain('暂无话题')
      // 旧话题仍在
      expect(wrapper.text()).toContain('话题A')
    } finally {
      wrapper.unmount()
    }
  })
})
