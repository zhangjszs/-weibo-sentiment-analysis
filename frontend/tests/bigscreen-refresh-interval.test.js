import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

/**
 * #83：大屏改刷新间隔后真实数据刷新被随机数模拟静默替换。
 *
 * 修复：onRefreshIntervalChange 重建真实刷新定时器
 *（setInterval(refreshPanels, val)，与首屏挂载一致）；simulateDataUpdate
 * 已删除（全仓零引用）。
 *
 * 用例设计：
 * - harness 包裹 useBigScreen，vi.useFakeTimers 推进 3 个新周期；
 * - Math.random 固定 0.999：修复前 simulate 每次必改写 stats（+9/+49/+19/+4），
 *   保证本用例在修复前为确定性 RED（已实证，见执行报告）；
 * - 真实路径断言落在 store 边界（fetchStats 被调用）：SWR TTL 30s 内复用
 *   缓存属正常语义，不要求每个周期都打到 API。
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
import { useAnalysisStore } from '@/stores/analysis'
import { useBigScreen } from '../src/composables/useBigScreen.js'

const envelope = (data) => ({ code: 200, msg: 'ok', data })

const harness = {
  template: '<div />',
  setup() {
    return useBigScreen()
  },
}

const mockAllSuccess = () => {
  getBigScreenStats.mockResolvedValue(
    envelope({
      articleCount: 12,
      commentCount: 34,
      positiveCount: 5,
      negativeCount: 6,
      neutralCount: 7,
    })
  )
  getBigScreenRegion.mockResolvedValue(envelope({ data: [{ name: '北京', value: 1 }] }))
  getBigScreenTrend.mockResolvedValue(envelope({ times: ['10:00'], counts: [3] }))
  getBigScreenHotTopics.mockResolvedValue(envelope({ topics: [{ name: '话题A' }] }))
  getBigScreenAlerts.mockResolvedValue(envelope({ alerts: [{ id: 1, title: '预警A' }] }))
}

beforeEach(() => {
  vi.clearAllMocks()
  setActivePinia(createPinia())
})

describe('大屏刷新间隔切换（#83）', () => {
  it('改间隔后重建真实刷新定时器，stats 不被随机数改写', async () => {
    mockAllSuccess()
    vi.useFakeTimers()
    const randomSpy = vi.spyOn(Math, 'random').mockReturnValue(0.999)
    const wrapper = mount(harness)
    try {
      await vi.advanceTimersByTimeAsync(0)
      // 首屏真实数据已就位
      expect(wrapper.vm.stats.articleCount).toBe(12)

      const store = useAnalysisStore()
      const fetchSpy = vi.spyOn(store, 'fetchStats')

      // 用户在配置抽屉把间隔改成 3s
      wrapper.vm.onRefreshIntervalChange(3000)
      await vi.advanceTimersByTimeAsync(9000)

      // 真实数据路径被触发（store 边界），而非静默停掉
      expect(fetchSpy).toHaveBeenCalled()
      // stats 保持后端返回值，未被随机数改写
      expect(wrapper.vm.stats.articleCount).toBe(12)
      expect(wrapper.vm.stats.commentCount).toBe(34)
      expect(wrapper.vm.stats.positiveCount).toBe(5)
      expect(wrapper.vm.stats.negativeCount).toBe(6)
    } finally {
      wrapper.unmount()
      randomSpy.mockRestore()
      vi.useRealTimers()
    }
  })
})
