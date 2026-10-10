import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

/**
 * R-2（#63）：首页两张图表卡在移动端（<768px）纵向堆叠。
 *
 * 真实 mount `home/index.vue`：经 stub 的 AnalysisFilters 触发一次搜索，
 * 让 snapshot 就绪渲染出 el-row/el-col，再断言两个 el-col 的 xs/sm prop
 * 与渲染出的断点 class——模板改回固定 `:span="12"` 时本用例必须变红。
 */

vi.mock('@/api/request', () => ({
  http: { get: vi.fn() },
  default: {},
}))

import { http } from '@/api/request'
import Home from '../src/views/home/index.vue'

const FiltersStub = {
  name: 'AnalysisFilters',
  emits: ['search'],
  template:
    '<button class="stub-search" @click="$emit(\'search\', { topic: \'AI\' })">搜索</button>',
}

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
      // 视图用 v-loading；单测不装载 element-plus 全局插件（见 vitest.setup.js）
      directives: { loading: {} },
      stubs: {
        AnalysisFilters: FiltersStub,
        AnalysisSummary: true,
        AnalysisSection: true,
        BaseCard: true,
      },
    },
  })

beforeEach(() => {
  vi.clearAllMocks()
})

describe('首页分栏响应式（R-2 #63）', () => {
  it('两张图表卡的 el-col 带 xs=24 / sm=12，渲染出对应断点 class', async () => {
    http.get.mockResolvedValue(okBody)
    const wrapper = mountHome()
    try {
      await wrapper.find('.stub-search').trigger('click')
      await flushPromises()

      // 第二行（情感分布 + 传播摘要）的两列
      const rows = wrapper.findAll('.el-row')
      expect(rows).toHaveLength(2)
      const cols = rows[1].findAllComponents({ name: 'ElCol' })
      expect(cols).toHaveLength(2)

      for (const col of cols) {
        expect(col.props('xs')).toBe(24) // 移动端整行
        expect(col.props('sm')).toBe(12) // ≥768px 并排
      }

      // 断点 class 是布局真正生效的载体
      expect(rows[1].findAll('.el-col-xs-24.el-col-sm-12')).toHaveLength(2)
    } finally {
      wrapper.unmount()
    }
  })
})
