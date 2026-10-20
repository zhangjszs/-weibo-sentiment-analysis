import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

/**
 * #65（U-2）：platform.vue 补齐加载态与错误态。
 *
 * 覆盖：
 * 1. 三路 fetch 期间对应区域显示加载指示（.content-loading），到达后消失；
 * 2. 内容失败 → 常驻错误态 + 重试入口，且不清空已渲染旧数据（#19）；
 * 3. 重试成功后错误态消失；
 * 4. 统计/对比两路失败各有区域错误态。
 *
 * mock 层级：@/api/platform 三个函数；BaseChart stub（echarts 重）。
 */

vi.mock('@/api/platform', () => ({
  getPlatformData: vi.fn(),
  getPlatformStats: vi.fn(),
  comparePlatforms: vi.fn(),
}))

import { getPlatformData, getPlatformStats, comparePlatforms } from '@/api/platform'
import Platform from '../src/views/analysis/platform.vue'

const ITEM = {
  content_id: 'c1',
  author_name: '作者A',
  author_verified: false,
  author_followers: 100,
  published_at: '2026-10-01T10:00:00',
  content: '测试内容一',
  view_count: 10,
  like_count: 2,
  comment_count: 1,
  repost_count: 0,
  sentiment: 'positive',
  keywords: ['kw'],
}

const dataOk = (items = [ITEM]) => ({
  code: 200,
  msg: 'ok',
  data: { data: items, pagination: { total: items.length } },
})
const statsOk = () => ({
  code: 200,
  msg: 'ok',
  data: { weibo: { total_content: 5, total_users: 3, total_likes: 9, total_comments: 1 } },
})
const compareOk = () => ({ code: 200, msg: 'ok', data: { comparison: {} } })

const mockAllSuccess = () => {
  getPlatformData.mockResolvedValue(dataOk())
  getPlatformStats.mockResolvedValue(statsOk())
  comparePlatforms.mockResolvedValue(compareOk())
}

const mountView = () =>
  mount(Platform, {
    global: { stubs: { BaseChart: true } },
  })

let consoleErrorSpy

beforeEach(() => {
  vi.clearAllMocks()
  mockAllSuccess()
  consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
})

afterEach(() => {
  consoleErrorSpy.mockRestore()
})

describe('platform 加载/错误态（#65 U-2）', () => {
  it('内容 fetch 期间显示加载指示，到达后消失并渲染列表', async () => {
    let resolveData
    getPlatformData.mockReturnValue(
      new Promise((resolve) => {
        resolveData = resolve
      })
    )
    const wrapper = mountView()
    try {
      await flushPromises()
      expect(wrapper.find('.content-loading').exists()).toBe(true)

      resolveData(dataOk())
      await flushPromises()

      expect(wrapper.find('.content-loading').exists()).toBe(false)
      expect(wrapper.text()).toContain('测试内容一')
    } finally {
      wrapper.unmount()
    }
  })

  it('内容失败时显示错误态与重试，且不清空旧数据（#19）', async () => {
    const wrapper = mountView()
    try {
      await flushPromises()
      expect(wrapper.text()).toContain('测试内容一')
      expect(wrapper.find('.content-error').exists()).toBe(false)

      // 切 tab 触发重载，新请求失败
      getPlatformData.mockRejectedValue(new Error('platform down'))
      await wrapper.findAll('.el-tabs__item')[1].trigger('click')
      await flushPromises()

      expect(wrapper.find('.content-error').exists()).toBe(true)
      expect(wrapper.find('.content-error').text()).toContain('数据加载失败，已保留旧数据')
      expect(wrapper.find('.content-error .el-button').exists()).toBe(true)
      // 旧数据仍在，未被清空或伪装成空态
      expect(wrapper.text()).toContain('测试内容一')
      expect(consoleErrorSpy).toHaveBeenCalled()
    } finally {
      wrapper.unmount()
    }
  })

  it('重试成功后错误态消失', async () => {
    getPlatformData.mockRejectedValueOnce(new Error('boom'))
    const wrapper = mountView()
    try {
      await flushPromises()
      expect(wrapper.find('.content-error').exists()).toBe(true)

      getPlatformData.mockResolvedValue(dataOk())
      await wrapper.find('.content-error .el-button').trigger('click')
      await flushPromises()

      expect(wrapper.find('.content-error').exists()).toBe(false)
      expect(wrapper.text()).toContain('测试内容一')
      expect(consoleErrorSpy).toHaveBeenCalled()
    } finally {
      wrapper.unmount()
    }
  })

  it('统计失败时显示区域错误态与重试', async () => {
    getPlatformStats.mockRejectedValue(new Error('stats down'))
    const wrapper = mountView()
    try {
      await flushPromises()
      expect(wrapper.find('.stats-error').exists()).toBe(true)
      expect(wrapper.find('.stats-error').text()).toContain('统计加载失败')
      expect(wrapper.find('.stats-error .el-button').exists()).toBe(true)
      expect(consoleErrorSpy).toHaveBeenCalled()
    } finally {
      wrapper.unmount()
    }
  })

  it('对比数据失败时显示区域错误态与重试', async () => {
    comparePlatforms.mockRejectedValue(new Error('compare down'))
    const wrapper = mountView()
    try {
      await flushPromises()
      expect(wrapper.find('.compare-error').exists()).toBe(true)
      expect(wrapper.find('.compare-error .el-button').exists()).toBe(true)
      expect(consoleErrorSpy).toHaveBeenCalled()
    } finally {
      wrapper.unmount()
    }
  })
})
