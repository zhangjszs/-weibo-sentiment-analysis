import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

/**
 * #19：大屏数据仓库的缓存保护。
 * - 单个接口失败不拖垮其余数据（Promise.allSettled）
 * - 异常/空响应不得把已有缓存覆盖为空
 */

vi.mock('@/api/stats', () => ({
  getBigScreenStats: vi.fn(),
  getBigScreenRegion: vi.fn(),
  getBigScreenTrend: vi.fn(),
  getBigScreenHotTopics: vi.fn(),
  getBigScreenAlerts: vi.fn(),
}))

import {
  getBigScreenStats,
  getBigScreenRegion,
  getBigScreenTrend,
  getBigScreenHotTopics,
  getBigScreenAlerts,
} from '@/api/stats'
import { useAnalysisStore } from '@/stores/analysis.js'

const envelope = (data) => ({ code: 200, msg: 'ok', data })

beforeEach(() => {
  vi.clearAllMocks()
  setActivePinia(createPinia())
})

describe('analysis store 缓存保护 (#19)', () => {
  it('单个接口失败：其余数据照常缓存，error 记录失败项', async () => {
    getBigScreenStats.mockResolvedValue(envelope({ articleCount: 7 }))
    getBigScreenRegion.mockRejectedValue(new Error('region down'))
    getBigScreenTrend.mockResolvedValue(envelope({ times: ['10:00'] }))
    getBigScreenHotTopics.mockResolvedValue(envelope({ topics: ['AI'] }))
    getBigScreenAlerts.mockResolvedValue(envelope({ alerts: [] }))

    const store = useAnalysisStore()
    await store.fetchAll()

    expect(store.error).toBeTruthy()
    expect(store.stats).toEqual({ articleCount: 7 })
    expect(store.trend).toEqual({ times: ['10:00'] })
    expect(store.hotTopics).toEqual({ topics: ['AI'] })
    expect(store.alerts).toEqual({ alerts: [] })
    expect(store.loading).toBe(false)
  })

  it('空响应不覆盖已有缓存', async () => {
    getBigScreenStats.mockResolvedValue(envelope({ articleCount: 7 }))
    const store = useAnalysisStore()
    await store.fetchStats()

    // 接口异常 / 包络缺 data：旧缓存保留，fetch 不抛错
    getBigScreenStats.mockRejectedValue(new Error('down'))
    await expect(store.fetchStats({ force: true })).rejects.toThrow('down')
    expect(store.stats).toEqual({ articleCount: 7 })

    getBigScreenStats.mockResolvedValue({ code: 200, msg: 'ok' })
    const returned = await store.fetchStats({ force: true })
    expect(returned).toEqual({ articleCount: 7 })
    expect(store.stats).toEqual({ articleCount: 7 })
  })

  it('TTL 内复用缓存，不重复请求', async () => {
    getBigScreenStats.mockResolvedValue(envelope({ articleCount: 1 }))
    const store = useAnalysisStore()
    await store.fetchStats()
    await store.fetchStats()
    expect(getBigScreenStats).toHaveBeenCalledTimes(1)
  })
})
