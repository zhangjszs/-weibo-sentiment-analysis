import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

/**
 * #75（T-2）：视图级挂载测试矩阵 —— system + user 目录（3 视图）。
 *
 * 每个用例真实 mount 一个视图（mock API 层），断言挂载无异常 +
 * 关键区域渲染。只加测试，不改源码。
 */

vi.mock('@/api/spider', () => ({
  getSpiderOverview: vi.fn(),
  getSpiderLogs: vi.fn(),
  startCrawl: vi.fn(),
  getSpiderStatus: vi.fn(),
  quickCrawl: vi.fn(),
  clearCache: vi.fn(),
}))

vi.mock('@/api/tasks', () => ({
  getStartupStatus: vi.fn(),
  getTaskStatus: vi.fn(),
  queryTaskResult: vi.fn(),
}))

vi.mock('@/api/favorites', () => ({
  getFavorites: vi.fn(),
  removeFavorite: vi.fn(),
  addFavorite: vi.fn(),
  batchCheckFavorites: vi.fn(),
}))

import { getSpiderOverview, getSpiderLogs } from '@/api/spider'
import { getStartupStatus } from '@/api/tasks'
import { getFavorites } from '@/api/favorites'
import Tasks from '../src/views/system/tasks.vue'
import Help from '../src/views/system/Help.vue'
import Favorites from '../src/views/user/Favorites.vue'
import router from '../src/router/index.js'

const mountWithRouter = (component) =>
  mount(component, {
    global: {
      plugins: [router],
    },
  })

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  getSpiderOverview.mockResolvedValue({
    code: 200,
    msg: 'ok',
    data: {
      articleCount: 0,
      commentCount: 0,
      userCount: 0,
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
  getSpiderLogs.mockResolvedValue({ code: 200, msg: 'ok', data: { logs: [] } })
  getStartupStatus.mockResolvedValue({ code: 200, msg: 'ok', data: {} })
  getFavorites.mockResolvedValue({
    code: 200,
    msg: 'ok',
    data: {
      items: [{ article_id: 'a1', content: '收藏内容', source: '微博', created_at: '2026-10-01' }],
      total: 1,
    },
  })
})

describe('视图挂载矩阵 system+user（#75 T-2）', () => {
  it('tasks.vue：挂载无异常，渲染任务进度与列表区', async () => {
    const wrapper = mount(Tasks)
    try {
      await flushPromises()
      expect(wrapper.find('.tasks-page').exists()).toBe(true)
      // useTasks 全链路到达：TaskProgress 与 TaskList 均渲染
      expect(wrapper.find('.task-progress-wrapper').exists()).toBe(true)
      expect(wrapper.find('.task-list-wrapper').exists()).toBe(true)
    } finally {
      wrapper.unmount()
    }
  })

  it('Help.vue：挂载无异常，渲染帮助页', async () => {
    const wrapper = mountWithRouter(Help)
    try {
      await flushPromises()
      expect(wrapper.find('.help-page').exists()).toBe(true)
    } finally {
      wrapper.unmount()
    }
  })

  it('Favorites.vue：挂载无异常，渲染收藏内容', async () => {
    const wrapper = mountWithRouter(Favorites)
    try {
      await flushPromises()
      expect(wrapper.find('.favorites-page').exists()).toBe(true)
      expect(wrapper.text()).toContain('收藏内容')
    } finally {
      wrapper.unmount()
    }
  })
})
