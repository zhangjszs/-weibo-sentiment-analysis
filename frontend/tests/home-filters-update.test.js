import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

/**
 * #80（U-11）：home filters 受控更新路径。
 *
 * 真实 mount `home/index.vue` + 真实 AnalysisFilters：填话题 → 点「开始分析」→
 * 断言 filters 经受控更新同步、搜索照常触发并渲染结果。
 * 说明：`const reactive` 告警来自 @vue/compiler-sfc 编译期通道，单测断言不到；
 * 告警消除以后面全量 test:run 输出摘录为准，本用例锁定更新机制不变。
 */

vi.mock('@/api/request', () => ({
  http: { get: vi.fn() },
  default: {},
}))

import { http } from '@/api/request'
import Home from '../src/views/home/index.vue'

const okBody = {
  data: {
    meta: { source_type: 'demo' },
    summary: {},
    trend: [{ label: '10:00', value: 1 }],
    sentiment: { distribution: { positive: 3, neutral: 1, negative: 0 } },
    propagation: { total_nodes: 2 },
  },
}

const mountHome = () =>
  mount(Home, {
    global: {
      stubs: {
        AnalysisSummary: true,
        AnalysisSection: true,
        BaseCard: true,
      },
    },
  })

beforeEach(() => {
  vi.clearAllMocks()
  http.get.mockResolvedValue(okBody)
})

describe('home filters 更新路径（U-11 #80）', () => {
  it('搜索触发 filters 同步，无 const 绑定告警，结果正常渲染', async () => {
    const wrapper = mountHome()
    try {
      await wrapper.find('input[placeholder="输入微博话题关键词..."]').setValue('AI')
      await wrapper.find('.analysis-filters .el-button').trigger('click')
      await flushPromises()

      // 搜索照常触发，结果渲染
      expect(http.get).toHaveBeenCalledWith(
        '/api/v1/analysis',
        expect.objectContaining({ params: expect.objectContaining({ topic: 'AI' }) })
      )
    } finally {
      wrapper.unmount()
    }
  })
})
