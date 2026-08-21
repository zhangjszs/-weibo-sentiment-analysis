import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getSpiderOverview, startCrawl, getSpiderStatus, getSpiderLogs, clearCache } from '@/api/spider'
import echarts from '@/utils/echarts'

export function useSpider() {
  const overview = reactive({
    articleCount: 0, commentCount: 0, userCount: 0, latestArticleTime: '', latestCommentTime: '',
    isRunning: false, currentTask: null, progress: 0, message: '', dailyTrend: [], commentTrend: [], history: [],
  })
  const hotPageNum = ref(3)
  const searchKeyword = ref('')
  const searchPageNum = ref(3)
  const refreshing = ref(false)
  const clearingCache = ref(false)
  const logs = ref([])
  const logsLoading = ref(false)
  const logFilter = ref('all')
  const logContainerRef = ref(null)
  const trendChartRef = ref(null)
  let trendChart = null
  const handleResize = () => trendChart?.resize()
  const handleVisibilityChange = () => {
    if (document.hidden) { stopStatusPolling(); return }
    if (overview.isRunning) startStatusPolling()
  }
  let statusTimer = null
  let pollErrorCount = 0
  async function loadOverview() {
    try {
      const res = await getSpiderOverview()
      if (res.code === 200 && res.data) { Object.assign(overview, res.data); renderTrendChart() }
    } catch (e) { console.error('加载概览失败:', e) }
  }
  async function loadLogs() {
    logsLoading.value = true
    try {
      const res = await getSpiderLogs(200)
      if (res.code === 200 && res.data) logs.value = res.data.logs || []
    } catch (e) { console.error('加载日志失败:', e) } finally { logsLoading.value = false }
  }
  async function refreshAll() {
    refreshing.value = true
    await Promise.all([loadOverview(), loadLogs()])
    refreshing.value = false
  }
  const filteredLogs = computed(() => {
    if (logFilter.value === 'all') return logs.value
    return logs.value.filter(line => {
      const level = getLogLevel(line)
      if (logFilter.value === 'error') return level === 'log-error'
      if (logFilter.value === 'warn') return level === 'log-warn'
      if (logFilter.value === 'info') return level === 'log-info'
      return true
    })
  })
  async function handleClearCache() {
    clearingCache.value = true
    try {
      const res = await clearCache()
      if (res.code === 200) ElMessage.success('缓存已清空')
      else ElMessage.warning(res.msg || '清空失败')
    } catch (e) { ElMessage.error('请求失败: ' + (e.message || e)) } finally { clearingCache.value = false }
  }
  async function startCrawlAction(type) {
    const params = { type }
    if (type === 'hot') params.pageNum = hotPageNum.value
    else if (type === 'search') { params.keyword = searchKeyword.value; params.pageNum = searchPageNum.value }
    try {
      const res = await startCrawl(params)
      if (res.code === 200) { ElMessage.success(res.msg || '爬虫任务已启动'); overview.isRunning = true; startStatusPolling() }
      else ElMessage.warning(res.msg || '启动失败')
    } catch (e) { ElMessage.error('请求失败: ' + (e.message || e)) }
  }
  function startStatusPolling() {
    stopStatusPolling(); pollErrorCount = 0
    statusTimer = setInterval(async () => {
      try {
        const res = await getSpiderStatus()
        if (res.code === 200 && res.data) {
          overview.isRunning = res.data.isRunning; overview.currentTask = res.data.currentTask; overview.progress = res.data.progress; overview.message = res.data.message
          if (!res.data.isRunning) { stopStatusPolling(); await loadOverview(); ElMessage.success('爬取任务已完成') }
        }
        pollErrorCount = 0
      } catch (e) {
        console.error('轮询状态失败:', e); pollErrorCount += 1
        if (pollErrorCount >= 3) { stopStatusPolling(); overview.isRunning = false; overview.message = '状态获取失败，已停止轮询，请稍后刷新重试'; ElMessage.error('状态获取失败，请检查网络或稍后重试') }
      }
    }, 2000)
  }
  function stopStatusPolling() { if (statusTimer) { clearInterval(statusTimer); statusTimer = null } }
  function renderTrendChart() {
    if (!trendChartRef.value) return
    if (!trendChart) trendChart = echarts.init(trendChartRef.value)
    const articleDates = overview.dailyTrend.map((d) => d.date)
    const articleCounts = overview.dailyTrend.map((d) => d.count)
    const commentDates = overview.commentTrend.map((d) => d.date)
    const commentCounts = overview.commentTrend.map((d) => d.count)
    const allDates = [...new Set([...articleDates, ...commentDates])].sort()
    const articleMap = Object.fromEntries(overview.dailyTrend.map((d) => [d.date, d.count]))
    const commentMap = Object.fromEntries(overview.commentTrend.map((d) => [d.date, d.count]))
    const option = {
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(15, 23, 42, 0.9)', borderColor: '#334155', textStyle: { color: '#E2E8F0', fontSize: 12 } },
      legend: { data: ['文章', '评论'], textStyle: { color: '#94A3B8' }, top: 0 },
      grid: { top: 40, right: 20, bottom: 30, left: 50 },
      xAxis: { type: 'category', data: allDates.map((d) => d.slice(5)), axisLine: { lineStyle: { color: '#334155' } }, axisLabel: { color: '#94A3B8', fontSize: 11 } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: '#1E293B' } }, axisLabel: { color: '#94A3B8', fontSize: 11 } },
      series: [
        { name: '文章', type: 'line', smooth: true, data: allDates.map((d) => articleMap[d] || 0), lineStyle: { color: '#6366F1', width: 2 }, itemStyle: { color: '#6366F1' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(99, 102, 241, 0.3)' }, { offset: 1, color: 'rgba(99, 102, 241, 0.02)' }]) } },
        { name: '评论', type: 'line', smooth: true, data: allDates.map((d) => commentMap[d] || 0), lineStyle: { color: '#10B981', width: 2 }, itemStyle: { color: '#10B981' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(16, 185, 129, 0.3)' }, { offset: 1, color: 'rgba(16, 185, 129, 0.02)' }]) } },
      ],
    }
    trendChart.setOption(option)
  }
  function getLogLevel(line) {
    if (line.includes('ERROR') || line.includes('CRITICAL')) return 'log-error'
    if (line.includes('WARNING')) return 'log-warn'
    if (line.includes('INFO')) return 'log-info'
    return 'log-debug'
  }
  onMounted(async () => {
    await Promise.all([loadOverview(), loadLogs()])
    if (overview.isRunning) startStatusPolling()
    window.addEventListener('resize', handleResize)
    document.addEventListener('visibilitychange', handleVisibilityChange)
  })
  onBeforeUnmount(() => {
    stopStatusPolling(); trendChart?.dispose()
    window.removeEventListener('resize', handleResize)
    document.removeEventListener('visibilitychange', handleVisibilityChange)
  })
  return {
    overview, hotPageNum, searchKeyword, searchPageNum, refreshing, clearingCache,
    logs, logsLoading, logFilter, logContainerRef, trendChartRef,
    filteredLogs, loadOverview, loadLogs, refreshAll, handleClearCache, startCrawlAction,
    getLogLevel, renderTrendChart,
  }
}
