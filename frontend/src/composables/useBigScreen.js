import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAnalysisStore } from '@/stores/analysis'
import { ensureChinaMap } from '@/utils/chinaMap'

// 空数据兜底（#52）：regionData 为空时 `Math.max()` 返回 -Infinity，
// visualMap 连续渐变对 -Infinity 求色会抛
// "Failed to execute 'addColorStop' ... could not be parsed as a color"。
// 空时回落 1000，与 map 序列的演示数据同尺度；非空取真实最大值，
// 且下限 1 避免「全 0 行」造成的 min=max 退化。
export function resolveVisualMapMax(regionData) {
  if (!regionData || regionData.length === 0) {
    return 1000
  }
  return Math.max(...regionData.map((d) => d.value), 1)
}

// 面板中文名（#62）：失败提示按面板归属，便于用户定位是哪一块没数据
const PANEL_LABELS = {
  stats: '统计数据',
  region: '地域分布',
  trend: '舆情趋势',
  topics: '热门话题',
  alerts: '预警数据',
}

export function useBigScreen() {
  const analysisStore = useAnalysisStore()

  const isFullscreen = ref(false)
  const currentTime = ref('')
  const currentDate = ref('')
  const loading = ref(false)

  // #62（U-1）：区域级失败态。api/request.js 的拦截器已对每个失败请求弹 ElMessage，
  // 挂墙大屏不应依赖转瞬即逝的 toast，故这里改为常驻可见状态：
  // - loadError：首屏/全量加载失败；partial=true 表示已有数据可展示，不遮挡面板
  // - panelErrors：自动刷新中单个面板的失败（#19：失败不清空已渲染数据）
  const loadError = ref(null)
  const panelErrors = ref({ stats: null, topics: null, alerts: null })
  const retryingPanel = ref(null)

  // #40：地图数据运行时拉取并注册（原先依赖「先访问 IP 页」的全局 registerMap
  // 状态，直接进大屏时地图系列渲染不出）。就绪后再挂载地图图表。
  const mapReady = ref(false)
  ensureChinaMap()
    .then(() => {
      mapReady.value = true
    })
    .catch((error) => {
      console.error('Failed to load China map data:', error)
    })

  const stats = ref({
    articleCount: 0,
    commentCount: 0,
    positiveCount: 0,
    negativeCount: 0,
    neutralCount: 0,
  })

  const animatedStats = ref({
    articleCount: 0,
    commentCount: 0,
    positiveCount: 0,
    negativeCount: 0,
  })

  const hotTopics = ref([])
  const recentAlerts = ref([])
  const regionData = ref([])
  const trendData = ref({ times: [], counts: [] })

  let timeTimer = null
  let dataTimer = null

  const sentimentChartOptions = computed(() => ({
    tooltip: { trigger: 'item' },
    series: [
      {
        type: 'pie',
        radius: ['50%', '70%'],
        center: ['50%', '50%'],
        data: [
          { value: stats.value.positiveCount, name: '正面', itemStyle: { color: '#10B981' } },
          { value: stats.value.neutralCount, name: '中性', itemStyle: { color: '#64748B' } },
          { value: stats.value.negativeCount, name: '负面', itemStyle: { color: '#EF4444' } },
        ],
        label: { show: true, formatter: '{b}: {d}%', color: '#fff' },
      },
    ],
  }))

  const mapChartOptions = computed(() => ({
    tooltip: { trigger: 'item' },
    visualMap: {
      min: 0,
      // 空数据兜底（#52）：见 resolveVisualMapMax
      max: resolveVisualMapMax(regionData.value),
      left: 'left',
      top: 'bottom',
      text: ['高', '低'],
      inRange: { color: ['#3B82F6', '#1D4ED8', '#1E3A8A'] },
      textStyle: { color: '#fff' },
    },
    series: [
      {
        type: 'map',
        map: 'china',
        roam: true,
        data:
          regionData.value.length > 0
            ? regionData.value
            : [
                { name: '北京', value: 985 },
                { name: '上海', value: 876 },
                { name: '广东', value: 765 },
                { name: '浙江', value: 654 },
                { name: '江苏', value: 543 },
                { name: '四川', value: 432 },
                { name: '湖北', value: 321 },
                { name: '山东', value: 234 },
              ],
        label: { show: false },
        itemStyle: { areaColor: '#1E3A8A', borderColor: '#3B82F6' },
        emphasis: { label: { show: true } },
      },
    ],
  }))

  // #53（方案 2）：趋势面板只画后端真实 counts（单系列「讨论量」）。
  // 后端两条路径都只返 {times, counts}，三情感系列无数据源——此前三条曲线
  // 全走硬编码假数据回退，现已删除；空数据时 series 直接为空数组（不崩，
  // 见 #52 空数据兜底），xAxis 的 times 回退保留以维持坐标轴结构。
  const trendChartOptions = computed(() => ({
    tooltip: { trigger: 'axis' },
    legend: { data: ['讨论量'], textStyle: { color: '#fff' }, top: 0 },
    xAxis: {
      type: 'category',
      data:
        trendData.value.times.length > 0
          ? trendData.value.times
          : ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'],
      axisLine: { lineStyle: { color: '#3B82F6' } },
      axisLabel: { color: '#94A3B8' },
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#3B82F6' } },
      axisLabel: { color: '#94A3B8' },
      splitLine: { lineStyle: { color: '#1E3A8A' } },
    },
    series: [
      {
        name: '讨论量',
        type: 'line',
        smooth: true,
        data: trendData.value.counts,
        itemStyle: { color: '#3B82F6' },
      },
    ],
  }))

  const speedChartOptions = computed(() => ({
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: Array.from({ length: 12 }, (_, i) => `${i * 5}分`),
      axisLine: { lineStyle: { color: '#3B82F6' } },
      axisLabel: { color: '#94A3B8', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#94A3B8', fontSize: 10 },
      splitLine: { lineStyle: { color: '#1E3A8A' } },
    },
    series: [
      {
        type: 'bar',
        data: [120, 200, 150, 80, 70, 110, 130, 180, 220, 190, 160, 140],
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#3B82F6' },
              { offset: 1, color: '#1E3A8A' },
            ],
          },
        },
      },
    ],
  }))

  const updateTime = () => {
    const now = new Date()
    currentTime.value = now.toLocaleTimeString()
    currentDate.value = now.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long',
    })
  }

  const animateStats = () => {
    const duration = 2000
    const steps = 60
    const interval = duration / steps
    const targets = {
      articleCount: stats.value.articleCount,
      commentCount: stats.value.commentCount,
      positiveCount: stats.value.positiveCount,
      negativeCount: stats.value.negativeCount,
    }
    let step = 0
    const timer = setInterval(() => {
      step++
      const progress = step / steps
      const easeProgress = 1 - Math.pow(1 - progress, 3)
      animatedStats.value = {
        articleCount: Math.floor(targets.articleCount * easeProgress),
        commentCount: Math.floor(targets.commentCount * easeProgress),
        positiveCount: Math.floor(targets.positiveCount * easeProgress),
        negativeCount: Math.floor(targets.negativeCount * easeProgress),
      }
      if (step >= steps) clearInterval(timer)
    }, interval)
  }

  // SWR 接线：经由 Pinia store，TTL 30s 内复用缓存
  const loadStats = async ({ force = false } = {}) => {
    try {
      const data = await analysisStore.fetchStats({ force })
      if (!data) {
        // HTTP 200 但载荷缺失：与「真无数据」区分开，不再静默（#19 / #62）
        panelErrors.value.stats = '统计数据返回为空，已保留上一次数据'
        return
      }
      stats.value = {
        articleCount: data.articleCount || 0,
        commentCount: data.commentCount || 0,
        positiveCount: data.positiveCount || 0,
        negativeCount: data.negativeCount || 0,
        neutralCount: data.neutralCount || 0,
      }
      animateStats()
      panelErrors.value.stats = null
    } catch (error) {
      console.error('加载统计数据失败:', error)
      panelErrors.value.stats = '统计数据加载失败，已保留上一次数据'
    }
  }

  const loadHotTopics = async ({ force = false } = {}) => {
    try {
      const data = await analysisStore.fetchHotTopics({ force })
      if (!data) {
        panelErrors.value.topics = '热门话题返回为空，已保留上一次数据'
        return
      }
      if (data.topics) hotTopics.value = data.topics
      else if (Array.isArray(data)) hotTopics.value = data
      panelErrors.value.topics = null
    } catch (error) {
      console.error('加载热门话题失败:', error)
      panelErrors.value.topics = '热门话题加载失败，已保留上一次数据'
    }
  }

  const loadAlerts = async ({ force = false } = {}) => {
    try {
      const data = await analysisStore.fetchAlerts({ force })
      if (!data) {
        panelErrors.value.alerts = '预警数据返回为空，已保留上一次数据'
        return
      }
      if (data.alerts) recentAlerts.value = data.alerts
      else if (Array.isArray(data)) recentAlerts.value = data
      panelErrors.value.alerts = null
    } catch (error) {
      console.error('加载预警数据失败:', error)
      panelErrors.value.alerts = '预警数据加载失败，已保留上一次数据'
    }
  }

  const loadAllData = async ({ force = false } = {}) => {
    loading.value = true
    loadError.value = null
    try {
      await analysisStore.fetchAll({ force })
      // fetchAll 内部 allSettled：部分失败不抛出，失败信息落在 store.error。
      // 是否已有可用数据用 lastFetched 判定（只有成功返回才更新），
      // 从而区分「全量失败」与「部分失败但旧数据仍在」两种降级形态。
      const hasData = Object.values(analysisStore.lastFetched).some((t) => t > 0)
      if (analysisStore.error) {
        loadError.value = {
          message: hasData ? '部分数据加载失败，已保留旧数据' : '数据加载失败，请重试',
          partial: hasData,
        }
      } else {
        // 无异常也没拿到数据（HTTP 200 载荷缺失）：与「真无数据」区分开，不静默显示零值（#19）
        const missing = Object.keys(analysisStore.lastFetched)
          .filter((key) => analysisStore.lastFetched[key] === 0)
          .map((key) => PANEL_LABELS[key] || key)
        if (missing.length > 0) {
          loadError.value = {
            message: `以下数据未返回：${missing.join('、')}`,
            partial: hasData,
          }
        }
      }
    } catch (e) {
      console.error('加载数据失败:', e)
      loadError.value = { message: '数据加载失败，请重试', partial: false }
    }
    // 回填本地 refs 以保持图表 computed 响应
    try {
      if (analysisStore.stats) {
        const d = analysisStore.stats
        stats.value = {
          articleCount: d.articleCount || 0,
          commentCount: d.commentCount || 0,
          positiveCount: d.positiveCount || 0,
          negativeCount: d.negativeCount || 0,
          neutralCount: d.neutralCount || 0,
        }
        animateStats()
      }
      if (analysisStore.region) {
        const d = analysisStore.region
        regionData.value = d.data || d || []
      }
      if (analysisStore.trend) {
        const d = analysisStore.trend
        trendData.value = {
          times: d.times || [],
          counts: d.counts || [],
        }
      }
      if (analysisStore.hotTopics) {
        const d = analysisStore.hotTopics
        hotTopics.value = d.topics || d || []
      }
      if (analysisStore.alerts) {
        const d = analysisStore.alerts
        recentAlerts.value = d.alerts || d || []
      }
      // 全量加载成功即视为三个刷新面板已就绪
      panelErrors.value = { stats: null, topics: null, alerts: null }
    } catch (e) {
      console.error('回填失败:', e)
      loadError.value = { message: '数据解析失败，请重试', partial: false }
    } finally {
      loading.value = false
    }
  }

  // 全量重试：重新进入 loading 并绕过 SWR 缓存（#62 U-1 重试入口）
  const retryLoad = () => loadAllData({ force: true })

  // 自动刷新：三个面板各自记录失败态并保留旧数据（#19），互不拖累
  const refreshPanels = () => Promise.all([loadStats(), loadHotTopics(), loadAlerts()])

  // 面板级重试：仅重新触发对应 fetch，成功后清除该面板的错误态
  const retryPanel = async (key) => {
    if (!(key in panelErrors.value)) return
    retryingPanel.value = key
    try {
      if (key === 'stats') await loadStats({ force: true })
      else if (key === 'topics') await loadHotTopics({ force: true })
      else if (key === 'alerts') await loadAlerts({ force: true })
    } finally {
      retryingPanel.value = null
    }
  }

  const simulateDataUpdate = () => {
    stats.value.articleCount += Math.floor(Math.random() * 10)
    stats.value.commentCount += Math.floor(Math.random() * 50)
    stats.value.positiveCount += Math.floor(Math.random() * 20)
    stats.value.negativeCount += Math.floor(Math.random() * 5)
    animatedStats.value = {
      articleCount: stats.value.articleCount,
      commentCount: stats.value.commentCount,
      positiveCount: stats.value.positiveCount,
      negativeCount: stats.value.negativeCount,
    }
  }

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen()
      isFullscreen.value = true
    } else {
      document.exitFullscreen()
      isFullscreen.value = false
    }
  }

  const showTimeline = ref(false)
  const isPlaying = ref(false)
  const timelineIndex = ref(0)
  let playTimer = null

  const timelineData = ref([
    { label: '00:00', positive: 120, neutral: 80, negative: 30 },
    { label: '04:00', positive: 132, neutral: 92, negative: 42 },
    { label: '08:00', positive: 201, neutral: 141, negative: 61 },
    { label: '12:00', positive: 234, neutral: 154, negative: 74 },
    { label: '16:00', positive: 290, neutral: 190, negative: 90 },
    { label: '20:00', positive: 330, neutral: 230, negative: 110 },
    { label: '24:00', positive: 410, neutral: 280, negative: 130 },
  ])

  const togglePlay = () => {
    isPlaying.value = !isPlaying.value
    if (isPlaying.value) {
      playTimer = setInterval(() => {
        if (timelineIndex.value < timelineData.value.length - 1) timelineIndex.value++
        else timelineIndex.value = 0
      }, 1000)
    } else clearInterval(playTimer)
  }

  const openTimeline = () => {
    showConfig.value = false
    showTimeline.value = true
  }

  const showConfig = ref(false)
  const refreshInterval = ref(5000)
  const visiblePanels = ref({ sentiment: true, topics: true, alerts: true, trend: true, map: true })

  const onRefreshIntervalChange = (val) => {
    if (dataTimer) clearInterval(dataTimer)
    dataTimer = setInterval(simulateDataUpdate, val)
  }

  onMounted(() => {
    updateTime()
    timeTimer = setInterval(updateTime, 1000)
    loadAllData()
    dataTimer = setInterval(refreshPanels, refreshInterval.value)
  })

  onUnmounted(() => {
    if (timeTimer) clearInterval(timeTimer)
    if (dataTimer) clearInterval(dataTimer)
  })

  return {
    isFullscreen,
    currentTime,
    currentDate,
    loading,
    loadError,
    panelErrors,
    retryingPanel,
    retryLoad,
    retryPanel,
    refreshPanels,
    stats,
    animatedStats,
    hotTopics,
    recentAlerts,
    regionData,
    trendData,
    mapReady,
    sentimentChartOptions,
    mapChartOptions,
    trendChartOptions,
    speedChartOptions,
    toggleFullscreen,
    showTimeline,
    isPlaying,
    timelineIndex,
    timelineData,
    togglePlay,
    openTimeline,
    showConfig,
    refreshInterval,
    visiblePanels,
    onRefreshIntervalChange,
  }
}
