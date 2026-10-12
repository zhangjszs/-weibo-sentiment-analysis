import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ElMessage } from 'element-plus'

/**
 * #76（T-3）：useTasks 失败可回归底线。
 *
 * 经 harness 真实执行 useTasks（mock @/api/spider + @/api/tasks）：
 * 1. 成功：概览/日志/启动状态落位，loading 全复位；
 * 2. 失败：ElMessage 报错，各 loading 复位，旧数据不变；
 * 3. 空数据：空对象/空日志落位，无报错。
 */

vi.mock('@/api/spider', () => ({
  getSpiderLogs: vi.fn(),
  getSpiderOverview: vi.fn(),
}))

vi.mock('@/api/tasks', () => ({
  getStartupStatus: vi.fn(),
  getTaskStatus: vi.fn(),
}))

import { getSpiderLogs, getSpiderOverview } from '@/api/spider'
import { getStartupStatus } from '@/api/tasks'
import { useTasks } from '../src/composables/useTasks.js'

const harness = {
  template: '<div />',
  setup() {
    return useTasks()
  },
}

const overviewOk = (data = {}) => ({
  code: 200,
  msg: 'ok',
  data: {
    articleCount: 42,
    commentCount: 7,
    history: [{ id: 't1' }],
    ...data,
  },
})

const mockAllSuccess = () => {
  getSpiderOverview.mockResolvedValue(overviewOk())
  getSpiderLogs.mockResolvedValue({ code: 200, msg: 'ok', data: { logs: ['INFO ok'] } })
  getStartupStatus.mockResolvedValue({ code: 200, msg: 'ok', data: { warmup: {} } })
}

let errorSpy

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  mockAllSuccess()
  errorSpy = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
})

afterEach(() => {
  errorSpy.mockRestore()
})

describe('useTasks 底线（#76 T-3）', () => {
  it('成功：三路数据落位，loading 全复位', async () => {
    const wrapper = mount(harness)
    try {
      await flushPromises()
      expect(wrapper.vm.spiderOverview.articleCount).toBe(42)
      expect(wrapper.vm.logs).toEqual(['INFO ok'])
      expect(wrapper.vm.startupStatus).toEqual({ warmup: {} })
      expect(wrapper.vm.spiderLoading).toBe(false)
      expect(wrapper.vm.logsLoading).toBe(false)
      expect(wrapper.vm.startupLoading).toBe(false)
      expect(errorSpy).not.toHaveBeenCalled()
    } finally {
      wrapper.unmount()
    }
  })

  it('失败：报错且 loading 复位，旧数据不变', async () => {
    const wrapper = mount(harness)
    try {
      await flushPromises()
      expect(wrapper.vm.spiderOverview.articleCount).toBe(42)

      getSpiderOverview.mockRejectedValue(new Error('overview down'))
      getSpiderLogs.mockRejectedValue(new Error('logs down'))
      getStartupStatus.mockRejectedValue(new Error('startup down'))
      await wrapper.vm.refreshSpider()
      await wrapper.vm.refreshLogs()
      await wrapper.vm.refreshStartup()
      await flushPromises()

      expect(errorSpy).toHaveBeenCalledTimes(3)
      expect(wrapper.vm.spiderLoading).toBe(false)
      expect(wrapper.vm.logsLoading).toBe(false)
      expect(wrapper.vm.startupLoading).toBe(false)
      // 旧数据不变
      expect(wrapper.vm.spiderOverview.articleCount).toBe(42)
      expect(wrapper.vm.logs).toEqual(['INFO ok'])
    } finally {
      wrapper.unmount()
    }
  })

  it('空数据：空对象/空日志落位，无报错', async () => {
    getSpiderOverview.mockResolvedValue(overviewOk({ articleCount: 0, history: [] }))
    getSpiderLogs.mockResolvedValue({ code: 200, msg: 'ok', data: { logs: [] } })
    getStartupStatus.mockResolvedValue({ code: 200, msg: 'ok', data: {} })
    const wrapper = mount(harness)
    try {
      await flushPromises()
      expect(wrapper.vm.spiderOverview.articleCount).toBe(0)
      expect(wrapper.vm.spiderHistory).toEqual([])
      expect(wrapper.vm.logs).toEqual([])
      expect(errorSpy).not.toHaveBeenCalled()
    } finally {
      wrapper.unmount()
    }
  })
})
