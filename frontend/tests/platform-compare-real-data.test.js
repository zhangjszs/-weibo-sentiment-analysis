import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

/**
 * #85（U-12）：platform.vue 对比与情感图接入后端真实口径及空态兜底。
 *
 * 覆盖：
 * 1. 对比图消费 comparisonData 真实字段（内容数/点赞数/评论数取自后端
 *    comparison[platform]），写死假常量不再出现；
 * 2. 情感分布图聚合各平台 sentiment_distribution，不再是写死的 45/30/25；
 * 3. comparison 为空时图表兜底零值不崩溃、控制台零报错，且模板显式空态。
 *
 * mock 层级：@/api/platform 三个函数；BaseChart stub（只断传入的 options）。
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

const platformSummary = (overrides = {}) => ({
  total_content: 0,
  total_likes: 0,
  total_comments: 0,
  total_views: 0,
  avg_likes: 0,
  avg_comments: 0,
  avg_views: 0,
  sentiment_distribution: { positive: 0, neutral: 0, negative: 0 },
  top_keywords: [],
  ...overrides,
})

const compareOk = (comparison) => ({
  code: 200,
  msg: 'ok',
  data: { comparison, metrics: ['total_content', 'avg_likes', 'avg_comments', 'avg_views'] },
})

const mockAllSuccess = (comparison = {}) => {
  getPlatformData.mockResolvedValue({
    code: 200,
    msg: 'ok',
    data: { data: [ITEM], pagination: { total: 1 } },
  })
  getPlatformStats.mockResolvedValue({
    code: 200,
    msg: 'ok',
    data: { weibo: { total_content: 5, total_users: 3, total_likes: 9, total_comments: 1 } },
  })
  comparePlatforms.mockResolvedValue(compareOk(comparison))
}

const mountView = () =>
  mount(Platform, {
    global: { stubs: { BaseChart: true } },
  })

const chartOptions = (wrapper) =>
  wrapper.findAllComponents({ name: 'BaseChart' }).map((c) => c.props('options'))

beforeEach(() => {
  vi.clearAllMocks()
  mockAllSuccess()
})

describe('platform 对比图真实数据接入（#85 U-12）', () => {
  it('对比图 series 取自 comparison 真实字段，写死假常量消失', async () => {
    mockAllSuccess({
      weibo: platformSummary({ total_content: 10, total_likes: 100, total_comments: 30 }),
      wechat: platformSummary({ total_content: 20, total_likes: 200, total_comments: 40 }),
      douyin: platformSummary({ total_content: 30, total_likes: 300, total_comments: 50 }),
      zhihu: platformSummary({ total_content: 40, total_likes: 400, total_comments: 60 }),
    })
    const wrapper = mountView()
    try {
      await flushPromises()

      const [compareOptions] = chartOptions(wrapper)
      const byName = Object.fromEntries(compareOptions.series.map((s) => [s.name, s.data]))
      expect(byName['内容数']).toEqual([10, 20, 30, 40])
      expect(byName['点赞数']).toEqual([100, 200, 300, 400])
      expect(byName['评论数']).toEqual([30, 40, 50, 60])
      // x 轴仍为四平台中文名
      expect(compareOptions.xAxis.data).toEqual(['微博', '微信', '抖音', '知乎'])

      // 写死假常量不再出现
      const raw = JSON.stringify(compareOptions)
      expect(raw).not.toContain('[50,30,45,25]')
      expect(raw).not.toContain('1200')

      // 有真实数据时无空态
      expect(wrapper.find('.compare-empty').exists()).toBe(false)
    } finally {
      wrapper.unmount()
    }
  })

  it('情感分布图聚合各平台 sentiment_distribution，不再写死 45/30/25', async () => {
    mockAllSuccess({
      weibo: platformSummary({
        sentiment_distribution: { positive: 5, neutral: 3, negative: 2 },
      }),
      wechat: platformSummary({
        sentiment_distribution: { positive: 1, neutral: 1, negative: 1 },
      }),
      douyin: platformSummary({}),
      zhihu: platformSummary({}),
    })
    const wrapper = mountView()
    try {
      await flushPromises()

      const [, sentimentOptions] = chartOptions(wrapper)
      const byName = Object.fromEntries(
        sentimentOptions.series[0].data.map((d) => [d.name, d.value])
      )
      expect(byName).toEqual({ 正面: 6, 中性: 4, 负面: 3 })

      // 有情感数据时无空态
      expect(wrapper.find('.sentiment-empty').exists()).toBe(false)
    } finally {
      wrapper.unmount()
    }
  })

  it('comparison 为空时图表兜底零值不崩溃、零报错，且模板显式空态', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    mockAllSuccess({})
    const wrapper = mountView()
    try {
      await flushPromises()

      const [compareOptions, sentimentOptions] = chartOptions(wrapper)
      // 零值兜底：三系列全 0，饼图三项全 0
      for (const s of compareOptions.series) {
        expect(s.data).toEqual([0, 0, 0, 0])
      }
      expect(sentimentOptions.series[0].data.map((d) => d.value)).toEqual([0, 0, 0])

      // 模板显式空态，而非假图
      expect(wrapper.find('.compare-empty').exists()).toBe(true)
      expect(wrapper.text()).toContain('暂无对比数据')
      expect(wrapper.find('.sentiment-empty').exists()).toBe(true)
      expect(wrapper.text()).toContain('暂无情感分布数据')

      // 控制台零报错
      expect(consoleError).not.toHaveBeenCalled()
    } finally {
      wrapper.unmount()
      consoleError.mockRestore()
    }
  })
})
