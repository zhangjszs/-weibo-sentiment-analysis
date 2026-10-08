import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

/**
 * #53（D-007 方案 2）：大屏趋势面板改单系列画后端真实 counts。
 * - 后端真实/demo 两条路径都只返 {times, counts}，三情感系列无数据源；
 *   此前前端读 positive/neutral/negative 并静默回退到三组硬编码假数据。
 * - 本测试经 mount 驱动 useBigScreen 的 onMounted→loadAllData 全链路，
 *   断言 counts 从 store 到达 trendData 再到达 trendChartOptions.series。
 */

vi.mock('@/api/stats', () => ({
  getBigScreenStats: vi.fn(),
  getBigScreenRegion: vi.fn(),
  getBigScreenTrend: vi.fn(),
  getBigScreenHotTopics: vi.fn(),
  getBigScreenAlerts: vi.fn(),
}))

vi.mock('@/utils/chinaMap', () => ({
  ensureChinaMap: vi.fn(() => Promise.resolve({})),
}))

import {
  getBigScreenStats,
  getBigScreenRegion,
  getBigScreenTrend,
  getBigScreenHotTopics,
  getBigScreenAlerts,
} from '@/api/stats'
import { useBigScreen } from '../src/composables/useBigScreen.js'

const envelope = (data) => ({ code: 200, msg: 'ok', data })

const harness = {
  template: '<div />',
  setup() {
    return useBigScreen()
  },
}

const mockAll = (trendPayload) => {
  getBigScreenStats.mockResolvedValue(envelope({ articleCount: 1 }))
  getBigScreenRegion.mockResolvedValue(envelope({ data: [] }))
  getBigScreenTrend.mockResolvedValue(envelope(trendPayload))
  getBigScreenHotTopics.mockResolvedValue(envelope({ topics: [] }))
  getBigScreenAlerts.mockResolvedValue(envelope({ alerts: [] }))
}

beforeEach(() => {
  vi.clearAllMocks()
  setActivePinia(createPinia())
})

describe('大屏趋势单系列（#53 方案 2）', () => {
  it('后端 counts 到达 trendData，且无情感字段残留', async () => {
    mockAll({ times: ['10:00', '11:00'], counts: [5, 9] })
    const wrapper = mount(harness)
    try {
      await flushPromises()
      expect(wrapper.vm.trendData).toEqual({
        times: ['10:00', '11:00'],
        counts: [5, 9],
      })
      expect(wrapper.vm.trendData).not.toHaveProperty('positive')
      expect(wrapper.vm.trendData).not.toHaveProperty('neutral')
      expect(wrapper.vm.trendData).not.toHaveProperty('negative')
    } finally {
      wrapper.unmount()
    }
  })

  it('趋势图为单系列「讨论量」，data 即后端 counts', async () => {
    mockAll({ times: ['10:00', '11:00'], counts: [5, 9] })
    const wrapper = mount(harness)
    try {
      await flushPromises()
      const options = wrapper.vm.trendChartOptions
      expect(options.legend.data).toEqual(['讨论量'])
      expect(options.series).toHaveLength(1)
      expect(options.series[0].name).toBe('讨论量')
      expect(options.series[0].data).toEqual([5, 9])
    } finally {
      wrapper.unmount()
    }
  })

  it('空数据时 series 为空数组，不回退硬编码假数据', async () => {
    mockAll({ times: [], counts: [] })
    const wrapper = mount(harness)
    try {
      await flushPromises()
      const options = wrapper.vm.trendChartOptions
      expect(options.series).toHaveLength(1)
      expect(options.series[0].data).toEqual([])
      expect(JSON.stringify(options)).not.toContain('正面')
    } finally {
      wrapper.unmount()
    }
  })
})
