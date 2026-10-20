import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

/**
 * #66（U-3）：spider.vue 首屏加载态与错误态。
 *
 * 覆盖：
 * 1. 首屏概览 fetch 期间显示加载指示，到达后消失；
 * 2. 概览失败 → 常驻错误态 + 重试入口，旧数据（零值初始态）不崩；
 * 3. 日志失败 → 错误态代替「暂无日志」空态（#19：失败不伪装成空态），
 *    且不清空已有日志；
 * 4. 重试成功后错误态消失。
 *
 * mock 层级：@/api/spider 全函数；@/utils/echarts（jsdom 无 canvas，
 * 趋势图只断 chart 容器存在，不测绘制）。
 */

vi.mock('@/api/spider', () => ({
  getSpiderOverview: vi.fn(),
  startCrawl: vi.fn(),
  getSpiderStatus: vi.fn(),
  getSpiderLogs: vi.fn(),
  quickCrawl: vi.fn(),
  clearCache: vi.fn(),
}))

vi.mock('@/utils/echarts', () => ({
  default: {
    init: vi.fn(() => ({
      setOption: vi.fn(),
      resize: vi.fn(),
      dispose: vi.fn(),
    })),
    graphic: { LinearGradient: vi.fn() },
  },
}))

import { getSpiderOverview, getSpiderLogs } from '@/api/spider'
import Spider from '../src/views/analysis/spider.vue'

const overviewOk = () => ({
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
  },
})
const logsOk = (lines = ['2026-10-01 INFO 启动成功']) => ({
  code: 200,
  msg: 'ok',
  data: { logs: lines },
})

const mountView = () => mount(Spider)

let consoleErrorSpy

beforeEach(() => {
  vi.clearAllMocks()
  getSpiderOverview.mockResolvedValue(overviewOk())
  getSpiderLogs.mockResolvedValue(logsOk())
  consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
})

afterEach(() => {
  consoleErrorSpy.mockRestore()
})

describe('spider 首屏加载/错误态（#66 U-3）', () => {
  it('首屏概览 fetch 期间显示加载指示，到达后消失', async () => {
    let resolveOverview
    getSpiderOverview.mockReturnValue(
      new Promise((resolve) => {
        resolveOverview = resolve
      })
    )
    const wrapper = mountView()
    try {
      await flushPromises()
      expect(wrapper.find('.overview-loading').exists()).toBe(true)

      resolveOverview(overviewOk())
      await flushPromises()

      expect(wrapper.find('.overview-loading').exists()).toBe(false)
      expect(wrapper.text()).toContain('42')
    } finally {
      wrapper.unmount()
    }
  })

  it('概览失败时显示错误态与重试', async () => {
    getSpiderOverview.mockRejectedValue(new Error('overview down'))
    const wrapper = mountView()
    try {
      await flushPromises()
      expect(wrapper.find('.overview-error').exists()).toBe(true)
      expect(wrapper.find('.overview-error').text()).toContain('概览加载失败')
      expect(wrapper.find('.overview-error .el-button').exists()).toBe(true)
      expect(consoleErrorSpy).toHaveBeenCalled()
    } finally {
      wrapper.unmount()
    }
  })

  it('日志失败时错误态代替空态，且不清空已有日志（#19）', async () => {
    const wrapper = mountView()
    try {
      await flushPromises()
      expect(wrapper.text()).toContain('INFO 启动成功')
      expect(wrapper.find('.logs-error').exists()).toBe(false)

      // 手动刷新触发重载，新请求失败（第二个 panel-header 属于日志面板）
      getSpiderLogs.mockRejectedValue(new Error('logs down'))
      const headers = wrapper.findAll('.panel-header')
      await headers[headers.length - 1].find('.el-button').trigger('click')
      await flushPromises()

      expect(wrapper.find('.logs-error').exists()).toBe(true)
      expect(wrapper.find('.logs-error').text()).toContain('日志加载失败')
      // 失败不伪装成空态：无「暂无日志」，旧日志仍在
      expect(wrapper.text()).not.toContain('暂无日志')
      expect(wrapper.text()).toContain('INFO 启动成功')
      expect(consoleErrorSpy).toHaveBeenCalled()
    } finally {
      wrapper.unmount()
    }
  })

  it('重试成功后错误态消失', async () => {
    getSpiderOverview.mockRejectedValueOnce(new Error('boom'))
    const wrapper = mountView()
    try {
      await flushPromises()
      expect(wrapper.find('.overview-error').exists()).toBe(true)

      getSpiderOverview.mockResolvedValue(overviewOk())
      await wrapper.find('.overview-error .el-button').trigger('click')
      await flushPromises()

      expect(wrapper.find('.overview-error').exists()).toBe(false)
      expect(wrapper.text()).toContain('42')
      expect(consoleErrorSpy).toHaveBeenCalled()
    } finally {
      wrapper.unmount()
    }
  })
})
