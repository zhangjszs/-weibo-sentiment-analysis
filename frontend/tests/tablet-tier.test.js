import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick, ref, inject } from 'vue'
import { createPinia, setActivePinia } from 'pinia'

/**
 * #81（R-4）：平板段（768–1024）布局差异化。
 *
 * 覆盖：
 * 1. 判定链：Layout 单源 resize 驱动 → provide('isTablet') → 深层消费方同步
 *    （500 非平板 / 800 平板 / 1200 非平板）；
 * 2. 样板消费：home R-2 两列在平板档取中间档（sm=24 纵向堆叠），桌面取并排；
 * 3. 不回退：移动端 xs=24 与桌面 sm=12 行为保持（另有 home-mobile-columns 回归）。
 */

vi.mock('@/api/request', () => ({
  http: { get: vi.fn() },
  default: {},
}))

import { http } from '@/api/request'
import router from '../src/router/index.js'
import Layout from '../src/components/Layout/index.vue'
import Home from '../src/views/home/index.vue'

const DESKTOP_WIDTH = 1200
const TABLET_WIDTH = 800
const MOBILE_WIDTH = 500

const setWidth = async (width) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  })
  window.dispatchEvent(new Event('resize'))
  await flushPromises()
  await nextTick()
}

// 透过 stub 的 RouterView 观测 Layout 下发的 isTablet（经过真实 provide 链）
const RouterViewProbe = {
  setup() {
    const t = inject('isTablet', ref(null))
    return { t }
  },
  template: '<div class="rv-probe">{{ t === null ? "none" : t ? "tablet" : "notablet" }}</div>',
}

const mountLayoutWithProbe = async (width) => {
  await setWidth(width)
  const pinia = createPinia()
  setActivePinia(pinia)
  const wrapper = mount(Layout, {
    global: {
      plugins: [pinia, router],
      stubs: {
        Sidebar: true,
        Header: true,
        TabBar: true,
        MobileNav: true,
        RouterView: RouterViewProbe,
      },
    },
  })
  await flushPromises()
  await nextTick()
  return wrapper
}

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

const mountHome = (tabletFlag) =>
  mount(Home, {
    global: {
      directives: { loading: {} },
      provide: { isTablet: ref(tabletFlag) },
      stubs: {
        AnalysisFilters: FiltersStub,
        AnalysisSummary: true,
        AnalysisSection: true,
        BaseCard: true,
      },
    },
  })

const searchAndGetCols = async (wrapper) => {
  await wrapper.find('.stub-search').trigger('click')
  await flushPromises()
  const rows = wrapper.findAll('.el-row')
  expect(rows).toHaveLength(2)
  return rows[1].findAllComponents({ name: 'ElCol' })
}

beforeEach(() => {
  vi.clearAllMocks()
  http.get.mockResolvedValue(okBody)
})

afterEach(async () => {
  await setWidth(DESKTOP_WIDTH)
})

describe('平板档判定与消费（#81 R-4）', () => {
  it('Layout 单源 resize 驱动 isTablet 下发（500/800/1200）', async () => {
    const wrapper = await mountLayoutWithProbe(MOBILE_WIDTH)
    try {
      expect(wrapper.find('.rv-probe').text()).toBe('notablet')

      await setWidth(TABLET_WIDTH)
      expect(wrapper.find('.rv-probe').text()).toBe('tablet')

      await setWidth(DESKTOP_WIDTH)
      expect(wrapper.find('.rv-probe').text()).toBe('notablet')

      // 临界值：768 进档，1024 出档
      await setWidth(768)
      expect(wrapper.find('.rv-probe').text()).toBe('tablet')
      await setWidth(1024)
      expect(wrapper.find('.rv-probe').text()).toBe('notablet')
    } finally {
      wrapper.unmount()
    }
  })

  it('平板档 home R-2 两列取中间档纵向堆叠（sm=24）', async () => {
    const wrapper = mountHome(true)
    try {
      const cols = await searchAndGetCols(wrapper)
      expect(cols).toHaveLength(2)
      for (const col of cols) {
        expect(col.props('xs')).toBe(24)
        expect(col.props('sm')).toBe(24)
      }
      expect(wrapper.findAll('.el-col-xs-24.el-col-sm-24')).toHaveLength(2)
    } finally {
      wrapper.unmount()
    }
  })

  it('非平板档 home R-2 两列保持并排（sm=12），移动端仍堆叠', async () => {
    const wrapper = mountHome(false)
    try {
      const cols = await searchAndGetCols(wrapper)
      expect(cols).toHaveLength(2)
      for (const col of cols) {
        expect(col.props('xs')).toBe(24)
        expect(col.props('sm')).toBe(12)
      }
      expect(wrapper.findAll('.el-col-xs-24.el-col-sm-12')).toHaveLength(2)
    } finally {
      wrapper.unmount()
    }
  })
})
