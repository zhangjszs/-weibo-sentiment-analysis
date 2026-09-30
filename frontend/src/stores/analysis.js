import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getBigScreenStats, getBigScreenRegion, getBigScreenTrend, getBigScreenHotTopics, getBigScreenAlerts } from '@/api/stats'

const TTL_MS = 30 * 1000

export const useAnalysisStore = defineStore('analysis', () => {
  const stats = ref(null)
  const region = ref(null)
  const trend = ref(null)
  const hotTopics = ref(null)
  const alerts = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const lastFetched = ref({ stats: 0, region: 0, trend: 0, topics: 0, alerts: 0 })

  const isStale = (key) => Date.now() - (lastFetched.value[key] || 0) > TTL_MS

  // 拉取封装：只在拿到有效 data 时更新缓存与时间戳。异常/空响应都不得把
  // 已有缓存覆盖为空（大屏一帧数据全丢比旧 30s 的数据更糟，#19）。
  async function fetchStats({ force = false } = {}) {
    if (!force && !isStale('stats') && stats.value) return stats.value
    const res = await getBigScreenStats()
    if (res?.data) {
      stats.value = res.data
      lastFetched.value.stats = Date.now()
    }
    return stats.value
  }

  async function fetchRegion({ force = false } = {}) {
    if (!force && !isStale('region') && region.value) return region.value
    const res = await getBigScreenRegion()
    if (res?.data) {
      region.value = res.data
      lastFetched.value.region = Date.now()
    }
    return region.value
  }

  async function fetchTrend({ force = false } = {}) {
    if (!force && !isStale('trend') && trend.value) return trend.value
    const res = await getBigScreenTrend(24)
    if (res?.data) {
      trend.value = res.data
      lastFetched.value.trend = Date.now()
    }
    return trend.value
  }

  async function fetchHotTopicsFn({ force = false } = {}) {
    if (!force && !isStale('topics') && hotTopics.value) return hotTopics.value
    const res = await getBigScreenHotTopics(10)
    if (res?.data) {
      hotTopics.value = res.data
      lastFetched.value.topics = Date.now()
    }
    return hotTopics.value
  }

  async function fetchAlertsFn({ force = false } = {}) {
    if (!force && !isStale('alerts') && alerts.value) return alerts.value
    const res = await getBigScreenAlerts(5)
    if (res?.data) {
      alerts.value = res.data
      lastFetched.value.alerts = Date.now()
    }
    return alerts.value
  }

  async function fetchAll({ force = false } = {}) {
    loading.value = true
    error.value = null
    try {
      // allSettled：单个接口失败不拖垮其余四块；error 只记第一失败项，
      // 调用方（useBigScreen）按各自 ref 是否有值回填，成功部分照常展示。
      const results = await Promise.allSettled([
        fetchStats({ force }),
        fetchRegion({ force }),
        fetchTrend({ force }),
        fetchHotTopicsFn({ force }),
        fetchAlertsFn({ force }),
      ])
      const failed = results.filter((r) => r.status === 'rejected')
      if (failed.length > 0) {
        error.value = failed[0].reason
        console.error('大屏部分数据加载失败:', ...failed.map((f) => f.reason))
      }
    } finally {
      loading.value = false
    }
  }

  return { stats, region, trend, hotTopics, alerts, loading, error, lastFetched, fetchStats, fetchRegion, fetchTrend, fetchHotTopics: fetchHotTopicsFn, fetchAlerts: fetchAlertsFn, fetchAll, isStale }
})
