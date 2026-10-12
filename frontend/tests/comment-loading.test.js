import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

/**
 * #71（U-8）：修复 comment.vue 死 loading 标志（选择绑定路径）。
 *
 * 覆盖：
 * 1. loadData pending 期间图表区（.charts-loading）与热门评论区
 *    （.hot-comments-loading）均显示加载指示；
 * 2. 加载完成后两处指示消失并渲染真实热门评论。
 *
 * mock 层级：@/api/stats 的 getCommentData、@/api/content 的 getComments、
 * @/utils 的 downloadCsv；BaseChart stub。
 */

vi.mock('@/api/stats', () => ({
  getCommentData: vi.fn(),
}))

vi.mock('@/api/content', () => ({
  getComments: vi.fn(),
}))

vi.mock('@/utils', () => ({
  downloadCsv: vi.fn(),
}))

import { getCommentData } from '@/api/stats'
import { getComments } from '@/api/content'
import Comment from '../src/views/analysis/comment.vue'

const commentDataOk = () => ({
  code: 200,
  msg: 'ok',
  data: {
    timeDistribution: { hours: ['10:00'], counts: [5] },
    userActivity: { users: ['用户A'], counts: [3] },
    sentimentData: [{ value: 5, name: '正面' }],
    hotComments: [
      { user: '用户A', time: '2026-10-01', content: '热门评论内容', likes: 10, replies: 2 },
    ],
  },
})

const listOk = () => ({ code: 200, msg: 'ok', data: { list: [], total: 0 } })

const mountView = () =>
  mount(Comment, {
    global: { stubs: { BaseChart: true } },
  })

beforeEach(() => {
  vi.clearAllMocks()
  getCommentData.mockResolvedValue(commentDataOk())
  getComments.mockResolvedValue(listOk())
})

describe('comment 死 loading 绑定（#71 U-8）', () => {
  it('loadData pending 期间图表区与热门评论区均显示加载指示', async () => {
    let resolveData
    getCommentData.mockReturnValue(
      new Promise((resolve) => {
        resolveData = resolve
      })
    )
    const wrapper = mountView()
    try {
      await flushPromises()

      // 三张图表卡均有指示，热门评论区有指示
      expect(wrapper.findAll('.charts-loading').length).toBe(3)
      expect(wrapper.find('.hot-comments-loading').exists()).toBe(true)

      resolveData(commentDataOk())
      await flushPromises()

      expect(wrapper.find('.charts-loading').exists()).toBe(false)
      expect(wrapper.find('.hot-comments-loading').exists()).toBe(false)
      expect(wrapper.text()).toContain('热门评论内容')
    } finally {
      wrapper.unmount()
    }
  })

  it('加载完成后渲染真实热门评论', async () => {
    const wrapper = mountView()
    try {
      await flushPromises()

      expect(wrapper.find('.charts-loading').exists()).toBe(false)
      expect(wrapper.find('.hot-comments-loading').exists()).toBe(false)
      expect(wrapper.text()).toContain('热门评论内容')
    } finally {
      wrapper.unmount()
    }
  })
})
