import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

/**
 * #75（T-2）：视图级挂载测试矩阵 —— analysis 目录（7 视图）。
 *
 * 每个用例真实 mount 一个视图（mock API 层），断言挂载无异常 +
 * 关键区域渲染。只加测试，不改源码。
 */

vi.mock('@/api/stats', () => ({
  getArticleData: vi.fn(),
  getIPData: vi.fn(),
  getTableData: vi.fn(),
  getContentCloudData: vi.fn(),
  getYuqingData: vi.fn(),
  getHotWords: vi.fn(),
  getCommentData: vi.fn(),
  getBigScreenStats: vi.fn(),
  getBigScreenRegion: vi.fn(),
  getBigScreenTrend: vi.fn(),
  getBigScreenHotTopics: vi.fn(),
  getBigScreenAlerts: vi.fn(),
}))

vi.mock('@/api/content', () => ({
  getArticles: vi.fn(),
  getComments: vi.fn(),
}))

vi.mock('@/api/favorites', () => ({
  addFavorite: vi.fn(),
  removeFavorite: vi.fn(),
  batchCheckFavorites: vi.fn(),
}))

vi.mock('@/api/predict', () => ({
  predictSentiment: vi.fn(),
  predictBatch: vi.fn(),
  getModelInfo: vi.fn(),
}))

vi.mock('@/api/propagation', () => ({
  analyzePropagation: vi.fn(),
  getPropagationGraph: vi.fn(),
}))

vi.mock('@/utils', async (importOriginal) => ({
  ...(await importOriginal()),
  downloadCsv: vi.fn(),
}))

vi.mock('@/utils/chinaMap', () => ({
  ensureChinaMap: vi.fn(() => Promise.resolve({})),
}))

vi.mock('@/utils/echarts', () => ({
  default: {
    init: vi.fn(() => ({
      setOption: vi.fn(),
      resize: vi.fn(),
      dispose: vi.fn(),
      on: vi.fn(),
    })),
    graphic: { LinearGradient: vi.fn() },
  },
}))

import {
  getArticleData,
  getIPData,
  getTableData,
  getContentCloudData,
  getYuqingData,
} from '@/api/stats'
import { getArticles } from '@/api/content'
import { batchCheckFavorites } from '@/api/favorites'
import { getModelInfo } from '@/api/predict'
import Article from '../src/views/analysis/article.vue'
import Ip from '../src/views/analysis/ip.vue'
import Predict from '../src/views/analysis/predict.vue'
import Propagation from '../src/views/analysis/propagation.vue'
import Sentiment from '../src/views/analysis/sentiment.vue'
import WeiboStats from '../src/views/analysis/weiboStats.vue'
import WordCloud from '../src/views/analysis/wordCloud.vue'

const mountView = (component, stubs = { BaseChart: true }) =>
  mount(component, { global: { stubs } })

beforeEach(() => {
  vi.clearAllMocks()
  getArticleData.mockResolvedValue({
    code: 200,
    msg: 'ok',
    data: {
      xData: ['2026-10-01'],
      yData: [5],
      typeData: [{ value: 5, name: '原创' }],
      sentimentData: [3, 1, 1],
      typeList: [['原创']],
      articleList: [],
    },
  })
  getArticles.mockResolvedValue({ code: 200, msg: 'ok', data: { list: [], total: 0 } })
  batchCheckFavorites.mockResolvedValue({ code: 200, msg: 'ok', data: {} })
  getIPData.mockResolvedValue({
    code: 200,
    msg: 'ok',
    data: { ipList: [], mapData: [], regionData: [] },
  })
  getModelInfo.mockResolvedValue({
    code: 200,
    msg: 'ok',
    data: { model_type: 'TF-IDF', best_model: 'NaiveBayes', accuracy: 0.9 },
  })
  getYuqingData.mockResolvedValue({
    code: 200,
    msg: 'ok',
    data: {
      stats: { positive: 1, neutral: 0, negative: 0 },
      list: [],
      trend: { dates: [], positive: [], neutral: [], negative: [] },
      keywords: [],
    },
  })
  getTableData.mockResolvedValue({
    code: 200,
    msg: 'ok',
    data: { hotWordList: [], tableList: [] },
  })
  getContentCloudData.mockResolvedValue({
    code: 200,
    msg: 'ok',
    data: { contentCloud: '', authorCloud: '', wordStats: [] },
  })
})

describe('视图挂载矩阵 analysis（#75 T-2）', () => {
  it('article.vue：挂载无异常，渲染发布时间分布面板', async () => {
    const wrapper = mountView(Article)
    try {
      await flushPromises()
      expect(wrapper.find('.article-analysis-container').exists()).toBe(true)
      expect(wrapper.text()).toContain('文章发布时间分布')
    } finally {
      wrapper.unmount()
    }
  })

  it('ip.vue：挂载无异常，渲染地理分布面板', async () => {
    const wrapper = mountView(Ip)
    try {
      await flushPromises()
      expect(wrapper.find('.ip-analysis-container').exists()).toBe(true)
      expect(wrapper.text()).toContain('IP地理位置分布')
    } finally {
      wrapper.unmount()
    }
  })

  it('predict.vue：挂载无异常，渲染模型信息面板', async () => {
    const wrapper = mountView(Predict, {
      BaseChart: true,
      PredictInput: true,
      PredictResult: true,
    })
    try {
      await flushPromises()
      expect(wrapper.find('.predict-container').exists()).toBe(true)
      expect(wrapper.text()).toContain('模型信息')
      expect(wrapper.text()).toContain('TF-IDF')
    } finally {
      wrapper.unmount()
    }
  })

  it('propagation.vue：挂载无异常，渲染传播路径面板', async () => {
    const wrapper = mountView(Propagation)
    try {
      await flushPromises()
      expect(wrapper.find('.propagation-container').exists()).toBe(true)
      expect(wrapper.text()).toContain('传播路径图')
    } finally {
      wrapper.unmount()
    }
  })

  it('sentiment.vue：挂载无异常，渲染情感分布面板', async () => {
    const wrapper = mountView(Sentiment)
    try {
      await flushPromises()
      expect(wrapper.find('.sentiment-analysis-container').exists()).toBe(true)
      expect(wrapper.text()).toContain('舆情情感分布')
    } finally {
      wrapper.unmount()
    }
  })

  it('weiboStats.vue：挂载无异常，渲染统计面板', async () => {
    const wrapper = mountView(WeiboStats)
    try {
      await flushPromises()
      expect(wrapper.find('.weibo-stats-container').exists()).toBe(true)
      expect(wrapper.text()).toContain('微博舆情统计')
    } finally {
      wrapper.unmount()
    }
  })

  it('wordCloud.vue：挂载无异常，渲染词云面板', async () => {
    const wrapper = mountView(WordCloud)
    try {
      await flushPromises()
      expect(wrapper.find('.word-cloud-container').exists()).toBe(true)
      expect(wrapper.text()).toContain('文章内容词云')
    } finally {
      wrapper.unmount()
    }
  })
})
