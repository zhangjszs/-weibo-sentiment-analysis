import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

/**
 * #87（U-13）：comment.vue 热门评论补空态。
 *
 * 覆盖：
 * 1. hotComments 为空且非加载中 → 可见空态（.hot-comments-empty）；
 * 2. pending 期 → 加载指示而非空态（与 #71 共存）；
 * 3. 非空 → 空态不渲染，评论正常渲染。
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

const commentDataOk = (hotComments = []) => ({
  code: 200,
  msg: 'ok',
  data: {
    timeDistribution: { hours: [], counts: [] },
    userActivity: { users: [], counts: [] },
    sentimentData: [],
    hotComments,
  },
})

const listOk = () => ({ code: 200, msg: 'ok', data: { list: [], total: 0 } })

const mountView = () =>
  mount(Comment, {
    global: { stubs: { BaseChart: true } },
  })

beforeEach(() => {
  vi.clearAllMocks()
  getComments.mockResolvedValue(listOk())
})

describe('comment 热门评论空态（#87 U-13）', () => {
  it('空数组且非加载中 → 渲染明确空态', async () => {
    getCommentData.mockResolvedValue(commentDataOk([]))
    const wrapper = mountView()
    try {
      await flushPromises()

      expect(wrapper.find('.hot-comments-empty').exists()).toBe(true)
      expect(wrapper.text()).toContain('暂无热门评论')
      expect(wrapper.findAll('.comment-item').length).toBe(0)
    } finally {
      wrapper.unmount()
    }
  })

  it('pending 期 → 加载指示而非空态', async () => {
    let resolveData
    getCommentData.mockReturnValue(
      new Promise((resolve) => {
        resolveData = resolve
      })
    )
    const wrapper = mountView()
    try {
      await flushPromises()

      expect(wrapper.find('.hot-comments-loading').exists()).toBe(true)
      expect(wrapper.find('.hot-comments-empty').exists()).toBe(false)

      resolveData(commentDataOk([]))
      await flushPromises()

      expect(wrapper.find('.hot-comments-loading').exists()).toBe(false)
      expect(wrapper.find('.hot-comments-empty').exists()).toBe(true)
    } finally {
      wrapper.unmount()
    }
  })

  it('非空 → 空态不渲染', async () => {
    getCommentData.mockResolvedValue(
      commentDataOk([{ user: '用户A', time: '2026-10-01', content: '热门', likes: 1, replies: 0 }])
    )
    const wrapper = mountView()
    try {
      await flushPromises()

      expect(wrapper.find('.hot-comments-empty').exists()).toBe(false)
      expect(wrapper.text()).toContain('热门')
    } finally {
      wrapper.unmount()
    }
  })
})
