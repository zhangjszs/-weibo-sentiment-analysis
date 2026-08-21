import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAnalysisStore } from '@/stores/analysis'

export function useBigScreen() {
  const analysisStore = useAnalysisStore()

  const isFullscreen = ref(false)
  const currentTime = ref('')
  const currentDate = ref('')
  const loading = ref(false)

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
  const trendData = ref({ times: [], positive: [], neutral: [], negative: [] })

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
      max: Math.max(...(regionData.value.map(d => d.value) || [1000])),
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
        data: regionData.value.length > 0 ? regionData.value : [
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

  const trendChartOptions = computed(() => ({
    tooltip: { trigger: 'axis' },
    legend: { data: ['正面', '中性', '负面'], textStyle: { color: '#fff' }, top: 0 },
    xAxis: {
      type: 'category',
      data: trendData.value.times.length > 0 ? trendData.value.times : ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'],
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
      { name: '正面', type: 'line', smooth: true, data: trendData.value.positive.length > 0 ? trendData.value.positive : [120, 132, 201, 234, 290, 330, 410], itemStyle: { color: '#10B981' } },
      { name: '中性', type: 'line', smooth: true, data: trendData.value.neutral.length > 0 ? trendData.value.neutral : [80, 92, 141, 154, 190, 230, 280], itemStyle: { color: '#64748B' } },
      { name: '负面', type: 'line', smooth: true, data: trendData.value.negative.length > 0 ? trendData.value.negative : [30, 42, 61, 74, 90, 110, 130], itemStyle: { color: '#EF4444' } },
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
          color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#3B82F6' }, { offset: 1, color: '#1E3A8A' }] },
        },
      },
    ],
  }))

  const updateTime = () => {
    const now = new Date()
    currentTime.value = now.toLocaleTimeString()
    currentDate.value = now.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
  }

  const animateStats = () => {
    const duration = 2000
    const steps = 60
    const interval = duration / steps
    const targets = { articleCount: stats.value.articleCount, commentCount: stats.value.commentCount, positiveCount: stats.value.positiveCount, negativeCount: stats.value.negativeCount }
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
  const loadStats = async () => {
    try {
      const data = await analysisStore.fetchStats()
      if (data) {
        stats.value = {
          articleCount: data.articleCount || 0,
          commentCount: data.commentCount || 0,
          positiveCount: data.positiveCount || 0,
          negativeCount: data.negativeCount || 0,
          neutralCount: data.neutralCount || 0,
        }
        animateStats()
      }
    } catch (error) { console.error('加载统计数据失败:', error) }
  }

  const loadRegionData = async () => {
    try {
      const data = await analysisStore.fetchRegion()
      if (data && data.data) regionData.value = data.data
      else if (data && Array.isArray(data)) regionData.value = data
    } catch (error) { console.error('加载地区数据失败:', error) }
  }

  const loadTrendData = async () => {
    try {
      const data = await analysisStore.fetchTrend()
      if (data) trendData.value = { times: data.times || [], positive: data.positive || [], neutral: data.negative ? data.negative : [], negative: data.negative || [] }
      // 兼容 store 返回结构：trend 含 times/positive/neutral/negative
      if (data && data.times) trendData.value = { times: data.times || [], positive: data.positive || [], neutral: data.neutral || [], negative: data.negative || [] }
    } catch (error) { console.error('加载趋势数据失败:', error) }
  }

  const loadHotTopics = async () => {
    try {
      const data = await analysisStore.fetchHotTopics()
      if (data && data.topics) hotTopics.value = data.topics
      else if (Array.isArray(data)) hotTopics.value = data
    } catch (error) { console.error('加载热门话题失败:', error) }
  }

  const loadAlerts = async () => {
    try {
      const data = await analysisStore.fetchAlerts()
      if (data && data.alerts) recentAlerts.value = data.alerts
      else if (Array.isArray(data)) recentAlerts.value = data
    } catch (error) { console.error('加载预警数据失败:', error) }
  }

  const loadAllData = async () => {
    loading.value = true
    try { await analysisStore.fetchAll() } catch (e) { console.error('加载数据失败:', e) }
    // 回填本地 refs 以保持图表 computed 响应
    try {
      if (analysisStore.stats) {
        const d = analysisStore.stats
        stats.value = { articleCount: d.articleCount || 0, commentCount: d.commentCount || 0, positiveCount: d.positiveCount || 0, negativeCount: d.negativeCount || 0, neutralCount: d.neutralCount || 0 }
        animateStats()
      }
      if (analysisStore.region) {
        const d = analysisStore.region
        regionData.value = d.data || d || []
      }
      if (analysisStore.trend) {
        const d = analysisStore.trend
        trendData.value = { times: d.times || [], positive: d.positive || [], neutral: d.neutral || [], negative: d.negative || [] }
      }
      if (analysisStore.hotTopics) {
        const d = analysisStore.hotTopics
        hotTopics.value = d.topics || d || []
      }
      if (analysisStore.alerts) {
        const d = analysisStore.alerts
        recentAlerts.value = d.alerts || d || []
      }
    } catch (e) { console.error('回填失败:', e) }
    loading.value = false
  }

  const simulateDataUpdate = () => {
    stats.value.articleCount += Math.floor(Math.random() * 10)
    stats.value.commentCount += Math.floor(Math.random() * 50)
    stats.value.positiveCount += Math.floor(Math.random() * 20)
    stats.value.negativeCount += Math.floor(Math.random() * 5)
    animatedStats.value = { articleCount: stats.value.articleCount, commentCount: stats.value.commentCount, positiveCount: stats.value.positiveCount, negativeCount: stats.value.negativeCount }
  }

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) { document.documentElement.requestFullscreen(); isFullscreen.value = true }
    else { document.exitFullscreen(); isFullscreen.value = false }
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

  const openTimeline = () => { showConfig.value = false; showTimeline.value = true }

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
    dataTimer = setInterval(() => { loadStats(); loadHotTopics(); loadAlerts() }, refreshInterval.value)
  })

  onUnmounted(() => {
    if (timeTimer) clearInterval(timeTimer)
    if (dataTimer) clearInterval(dataTimer)
  })

  return {
    isFullscreen, currentTime, currentDate, loading,
    stats, animatedStats, hotTopics, recentAlerts, regionData, trendData,
    sentimentChartOptions, mapChartOptions, trendChartOptions, speedChartOptions,
    toggleFullscreen, showTimeline, isPlaying, timelineIndex, timelineData, togglePlay, openTimeline,
    showConfig, refreshInterval, visiblePanels, onRefreshIntervalChange,
  }
}
