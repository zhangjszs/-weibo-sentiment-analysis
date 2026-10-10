import { describe, it, expect, vi, beforeEach } from 'vitest'
import { nextTick } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

/**
 * #62（U-1）：大屏加载态与区域级错误态。
 *
 * 覆盖：
 * 1. 首屏数据未就绪时视图渲染可见加载指示，加载完成后消失；
 * 2. 全量失败 → 区域级错误态 + 重试入口，重试重新进入 loading 并可恢复；
 * 3. 部分失败 → 降级提示但不遮挡已加载数据；
 * 4. 自动刷新失败 → 面板级可见错误态，且不清空已渲染旧数据（#19），可面板级重试；
 * 5. HTTP 200 但载荷缺失 → 不静默伪装成零值/空态（#19）。
 *
 * 注：api/request.js 的拦截器已对每个失败请求弹 ElMessage，大屏挂墙场景不应
 * 依赖转瞬即逝的 toast，故本 Issue 不再重复弹窗，改为常驻可见的区域级状态。
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
import { useBigScreen } from '../src/composables/useBigScreen.js'

const envelope = (data) => ({ code: 200, msg: 'ok', data })

const TOPIC = { name: '话题A', percent: 50, heat: 100 }
const ALERT = { id: 1, time: '10:00', title: '预警A', level: 'danger' }

const mockAllSuccess = () => {
  getBigScreenStats.mockResolvedValue(
    envelope({
      articleCount: 12,
      commentCount: 34,
      positiveCount: 5,
      negativeCount: 6,
      neutralCount: 7,
    })
  )
  getBigScreenRegion.mockResolvedValue(envelope({ data: [{ name: '北京', value: 1 }] }))
  getBigScreenTrend.mockResolvedValue(envelope({ times: ['10:00'], counts: [3] }))
  getBigScreenHotTopics.mockResolvedValue(envelope({ topics: [TOPIC] }))
  getBigScreenAlerts.mockResolvedValue(envelope({ alerts: [ALERT] }))
}

const mockAllReject = () => {
  getBigScreenStats.mockRejectedValue(new Error('network down'))
  getBigScreenRegion.mockRejectedValue(new Error('network down'))
  getBigScreenTrend.mockRejectedValue(new Error('network down'))
  getBigScreenHotTopics.mockRejectedValue(new Error('network down'))
  getBigScreenAlerts.mockRejectedValue(new Error('network down'))
}

// 五个接口全部保持 pending，用于观察 loading 态
const deferAll = () => {
  const mk = () => {
    let resolve
    const promise = new Promise((r) => {
      resolve = r
    })
    return { promise, resolve }
  }
  const d = { stats: mk(), region: mk(), trend: mk(), topics: mk(), alerts: mk() }
  getBigScreenStats.mockReturnValue(d.stats.promise)
  getBigScreenRegion.mockReturnValue(d.region.promise)
  getBigScreenTrend.mockReturnValue(d.trend.promise)
  getBigScreenHotTopics.mockReturnValue(d.topics.promise)
  getBigScreenAlerts.mockReturnValue(d.alerts.promise)
  return {
    resolveAll() {
      d.stats.resolve(envelope({ articleCount: 12 }))
      d.region.resolve(envelope({ data: [] }))
      d.trend.resolve(envelope({ times: [], counts: [] }))
      d.topics.resolve(envelope({ topics: [TOPIC] }))
      d.alerts.resolve(envelope({ alerts: [ALERT] }))
    },
  }
}

const mountView = () =>
  mount(BigScreen, {
    global: { stubs: { BaseChart: true } },
  })

const harness = {
  template: '<div />',
  setup() {
    return useBigScreen()
  },
}

beforeEach(() => {
  vi.clearAllMocks()
  setActivePinia(createPinia())
})

describe('BigScreen 视图加载/错误态（#62 U-1）', () => {
  it('首屏数据未就绪时渲染加载指示，数据到达后消失', async () => {
    const { resolveAll } = deferAll()
    const wrapper = mountView()
    try {
      await nextTick()
      expect(wrapper.find('.screen-loading').exists()).toBe(true)
      expect(wrapper.find('.screen-error').exists()).toBe(false)

      resolveAll()
      await flushPromises()

      expect(wrapper.find('.screen-loading').exists()).toBe(false)
      expect(wrapper.text()).toContain('预警A')
    } finally {
      wrapper.unmount()
    }
  })

  it('全量失败时渲染区域级错误态与重试入口，重试重新进入 loading 并恢复', async () => {
    mockAllReject()
    const wrapper = mountView()
    try {
      await flushPromises()
      expect(wrapper.find('.screen-loading').exists()).toBe(false)
      expect(wrapper.find('.screen-error').exists()).toBe(true)
      expect(wrapper.find('.screen-error').text()).toContain('数据加载失败，请重试')

      mockAllSuccess()
      await wrapper.find('.screen-error .el-button').trigger('click')

      // 重试后 loading 正确翻转
      expect(wrapper.find('.screen-loading').exists()).toBe(true)

      await flushPromises()
      expect(wrapper.find('.screen-loading').exists()).toBe(false)
      expect(wrapper.find('.screen-error').exists()).toBe(false)
      expect(wrapper.text()).toContain('预警A')
    } finally {
      wrapper.unmount()
    }
  })

  it('部分失败时显示降级提示但不遮挡已加载数据', async () => {
    mockAllSuccess()
    getBigScreenHotTopics.mockRejectedValue(new Error('topics down'))
    const wrapper = mountView()
    try {
      await flushPromises()
      expect(wrapper.find('.screen-degraded').exists()).toBe(true)
      expect(wrapper.find('.screen-error').exists()).toBe(false)
      expect(wrapper.text()).toContain('部分数据加载失败，已保留旧数据')
      expect(wrapper.text()).toContain('预警A')
    } finally {
      wrapper.unmount()
    }
  })

  it('自动刷新失败时在对应面板显示错误态与重试按钮', async () => {
    mockAllSuccess()
    getBigScreenHotTopics.mockRejectedValue(new Error('boom'))
    vi.useFakeTimers()
    const wrapper = mountView()
    try {
      await vi.advanceTimersByTimeAsync(0)
      expect(wrapper.find('.panel-error').exists()).toBe(false)

      // 5s 自动刷新周期触发；topics 从未成功 → 无 SWR 缓存 → 真正发起请求并失败
      await vi.advanceTimersByTimeAsync(5000)
      await nextTick()

      expect(wrapper.find('.panel-error').text()).toContain('热门话题加载失败')
      expect(wrapper.find('.panel-error .el-button').exists()).toBe(true)
    } finally {
      wrapper.unmount()
      vi.useRealTimers()
    }
  })
})

describe('useBigScreen 失败态（#62 U-1）', () => {
  it('全量失败时暴露 loadError，且不把失败伪装成空数据', async () => {
    mockAllReject()
    const wrapper = mount(harness)
    try {
      await flushPromises()
      expect(wrapper.vm.loadError).toEqual({ message: '数据加载失败，请重试', partial: false })
      expect(wrapper.vm.loading).toBe(false)
    } finally {
      wrapper.unmount()
    }
  })

  it('retryLoad 调用后重新进入 loading，成功后清除错误态', async () => {
    mockAllReject()
    const wrapper = mount(harness)
    try {
      await flushPromises()
      expect(wrapper.vm.loadError).toBeTruthy()

      mockAllSuccess()
      const pending = wrapper.vm.retryLoad()
      expect(wrapper.vm.loading).toBe(true)

      await pending
      expect(wrapper.vm.loading).toBe(false)
      expect(wrapper.vm.loadError).toBe(null)
      expect(wrapper.vm.stats.articleCount).toBe(12)
      expect(wrapper.vm.hotTopics).toEqual([TOPIC])
    } finally {
      wrapper.unmount()
    }
  })

  it('自动刷新失败时暴露面板错误态（refreshPanels 路径）', async () => {
    mockAllSuccess()
    getBigScreenHotTopics.mockRejectedValue(new Error('boom'))
    const wrapper = mount(harness)
    try {
      await flushPromises()
      // 首屏的失败由 loadAllData 汇总成降级态
      expect(wrapper.vm.loadError).toEqual({
        message: '部分数据加载失败，已保留旧数据',
        partial: true,
      })
      expect(wrapper.vm.panelErrors.topics).toBe(null)

      await wrapper.vm.refreshPanels()
      expect(wrapper.vm.panelErrors.topics).toBeTruthy()
    } finally {
      wrapper.unmount()
    }
  })

  it('面板重试失败保留旧数据（#19），成功则清除错误态', async () => {
    mockAllSuccess()
    const wrapper = mount(harness)
    try {
      await flushPromises()
      expect(wrapper.vm.hotTopics).toEqual([TOPIC])

      // force 绕过 30s TTL，走真实 fetch 失败路径
      getBigScreenHotTopics.mockRejectedValue(new Error('boom'))
      const failing = wrapper.vm.retryPanel('topics')
      expect(wrapper.vm.retryingPanel).toBe('topics')
      await failing

      expect(wrapper.vm.retryingPanel).toBe(null)
      expect(wrapper.vm.panelErrors.topics).toBeTruthy()
      expect(wrapper.vm.hotTopics).toEqual([TOPIC]) // #19：旧数据未被清空
      expect(wrapper.vm.recentAlerts).toEqual([ALERT]) // 其余面板不受拖累

      getBigScreenHotTopics.mockResolvedValue(
        envelope({ topics: [{ name: '话题B', percent: 60, heat: 200 }] })
      )
      await wrapper.vm.retryPanel('topics')

      expect(wrapper.vm.panelErrors.topics).toBe(null)
      expect(wrapper.vm.hotTopics).toEqual([{ name: '话题B', percent: 60, heat: 200 }])
    } finally {
      wrapper.unmount()
    }
  })

  it('HTTP 200 但载荷缺失：首屏暴露降级态，刷新时记面板错误，不伪装成空数据', async () => {
    mockAllSuccess()
    getBigScreenStats.mockResolvedValue(envelope(null))
    const wrapper = mount(harness)
    try {
      await flushPromises()
      expect(wrapper.vm.loadError).toEqual({
        message: '以下数据未返回：统计数据',
        partial: true,
      })
      expect(wrapper.vm.panelErrors.stats).toBe(null)

      await wrapper.vm.refreshPanels()
      expect(wrapper.vm.panelErrors.stats).toBeTruthy()
    } finally {
      wrapper.unmount()
    }
  })
})
