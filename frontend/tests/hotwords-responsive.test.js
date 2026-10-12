import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

/**
 * R-3（#73）：热词页 8/16 分栏在移动端（<768px）纵向堆叠。
 *
 * 真实 mount `hotWords.vue`：断言信息/趋势两列的 xs/sm prop 与渲染出的
 * 断点 class——模板改回固定 `:span="8"/":span="16"` 时本用例必须变红。
 */

vi.mock('@/api/stats', () => ({
  getHotWords: vi.fn(),
}))

import { getHotWords } from '@/api/stats'
import HotWords from '../src/views/analysis/hotWords.vue'

const mountView = () =>
  mount(HotWords, {
    global: {
      stubs: { BaseChart: true },
    },
  })

beforeEach(() => {
  vi.clearAllMocks()
  getHotWords.mockResolvedValue({ code: 200, msg: 'ok', data: { hotWordList: [] } })
})

describe('热词页分栏响应式（R-3 #73）', () => {
  it('信息/趋势两列带 xs=24 / sm=8·16，渲染出对应断点 class', async () => {
    const wrapper = mountView()
    try {
      await flushPromises()

      // 第二行（热词信息 + 趋势图）的两列
      const rows = wrapper.findAll('.el-row')
      expect(rows.length).toBeGreaterThanOrEqual(2)
      const cols = rows[1].findAllComponents({ name: 'ElCol' })
      expect(cols).toHaveLength(2)

      expect(cols[0].props('xs')).toBe(24) // 移动端整行
      expect(cols[0].props('sm')).toBe(8) // ≥768px 恢复 8 栏
      expect(cols[1].props('xs')).toBe(24)
      expect(cols[1].props('sm')).toBe(16) // ≥768px 恢复 16 栏

      // 断点 class 是布局真正生效的载体
      expect(rows[1].findAll('.el-col-xs-24').length).toBe(2)
      expect(rows[1].find('.el-col-sm-8').exists()).toBe(true)
      expect(rows[1].find('.el-col-sm-16').exists()).toBe(true)
    } finally {
      wrapper.unmount()
    }
  })
})
