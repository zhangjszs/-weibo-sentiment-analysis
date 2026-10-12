import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

/**
 * #76（T-3）：useSpider 失败可回归底线。
 *
 * 经 harness 真实执行 useSpider（mock @/api/spider）：
 * 1. 成功：概览/日志落位，loading 复位，无错误态；
 * 2. 失败：错误态可被观测（overviewError/logsError），旧数据保留（#19）；
 * 3. 空数据：零值概览/空日志落位，无错误态。
 *
 * 说明：harness 无 trendChartRef，renderTrendChart 提前返回，不触达 echarts；
 * 概览 isRunning 为 false，不启动轮询；监听器随 unmount 清理。
 */

vi.mock('@/api/spider', () => ({
  getSpiderOverview: vi.fn(),
  startCrawl: vi.fn(),
  getSpiderStatus: vi.fn(),
  getSpiderLogs: vi.fn(),
  clearCache: vi.fn(),
}))

import { getSpiderOverview, getSpiderLogs } from '@/api/spider'
import { useSpider } from '../src/composables/useSpider.js'

const harness = {
  template: '<div />',
  setup() {
    return useSpider()
  },
}

const overviewOk = (data = {}) => ({
  code: 200,
  msg: 'ok',
  data: {
    articleCount: 42,
    commentCount: 7,
    userCount: 3,
    latestArticleTime: '',
    latestCommentTime: '',
    isRunning: false,
    currentTask: null,
    progress: 0,
    message: '',
    dailyTrend: [],
    commentTrend: [],
    history: [],
    ...data,
  },
})

const mockAllSuccess = () => {
  getSpiderOverview.mockResolvedValue(overviewOk())
  getSpiderLogs.mockResolvedValue({ code: 200, msg: 'ok', data: { logs: ['INFO ok'] } })
}

beforeEach(() => {
  vi.clearAllMocks()
  mockAllSuccess()
})

describe('useSpider 底线（#76 T-3）', () => {
  it('成功：概览/日志落位，无错误态', async () => {
    const wrapper = mount(harness)
    try {
      await flushPromises()
      expect(wrapper.vm.overview.articleCount).toBe(42)
      expect(wrapper.vm.logs).toEqual(['INFO ok'])
      expect(wrapper.vm.overviewLoading).toBe(false)
      expect(wrapper.vm.logsLoading).toBe(false)
      expect(wrapper.vm.overviewError).toBe('')
      expect(wrapper.vm.logsError).toBe('')
    } finally {
      wrapper.unmount()
    }
  })

  it('失败：错误态可被观测，旧数据保留（#19）', async () => {
    const wrapper = mount(harness)
    try {
      await flushPromises()
      expect(wrapper.vm.overview.articleCount).toBe(42)

      getSpiderOverview.mockRejectedValue(new Error('overview down'))
      getSpiderLogs.mockRejectedValue(new Error('logs down'))
      await wrapper.vm.loadOverview()
      await wrapper.vm.loadLogs()
      await flushPromises()

      expect(wrapper.vm.overviewError).toContain('概览加载失败')
      expect(wrapper.vm.logsError).toContain('日志加载失败')
      expect(wrapper.vm.overview.articleCount).toBe(42)
      expect(wrapper.vm.logs).toEqual(['INFO ok'])
      expect(wrapper.vm.overviewLoading).toBe(false)
      expect(wrapper.vm.logsLoading).toBe(false)
    } finally {
      wrapper.unmount()
    }
  })

  it('空数据：零值概览/空日志落位，无错误态', async () => {
    getSpiderOverview.mockResolvedValue(overviewOk({ articleCount: 0, commentCount: 0 }))
    getSpiderLogs.mockResolvedValue({ code: 200, msg: 'ok', data: { logs: [] } })
    const wrapper = mount(harness)
    try {
      await flushPromises()
      expect(wrapper.vm.overview.articleCount).toBe(0)
      expect(wrapper.vm.logs).toEqual([])
      expect(wrapper.vm.overviewError).toBe('')
      expect(wrapper.vm.logsError).toBe('')
    } finally {
      wrapper.unmount()
    }
  })
})
