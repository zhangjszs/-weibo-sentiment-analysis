<template>
  <div class="spider-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-info">
        <h2>
          <el-icon><Monitor /></el-icon>
          爬虫管理中心
        </h2>
        <p class="subtitle">
          管理微博数据爬取任务，查看运行状态与日志
        </p>
      </div>
      <div class="header-actions">
        <el-button
          :icon="Refresh"
          circle
          :loading="refreshing"
          @click="refreshAll"
        />
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row
      :gutter="20"
      class="stats-row"
    >
      <el-col
        :xs="24"
        :sm="12"
        :md="6"
      >
        <div class="stat-card card-articles">
          <div class="stat-icon">
            <el-icon :size="28">
              <Document />
            </el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">
              {{ overview.articleCount || 0 }}
            </div>
            <div class="stat-label">
              文章总数
            </div>
          </div>
        </div>
      </el-col>
      <el-col
        :xs="24"
        :sm="12"
        :md="6"
      >
        <div class="stat-card card-comments">
          <div class="stat-icon">
            <el-icon :size="28">
              <ChatDotRound />
            </el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">
              {{ overview.commentCount || 0 }}
            </div>
            <div class="stat-label">
              评论总数
            </div>
          </div>
        </div>
      </el-col>
      <el-col
        :xs="24"
        :sm="12"
        :md="6"
      >
        <div class="stat-card card-users">
          <div class="stat-icon">
            <el-icon :size="28">
              <User />
            </el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">
              {{ overview.userCount || 0 }}
            </div>
            <div class="stat-label">
              用户总数
            </div>
          </div>
        </div>
      </el-col>
      <el-col
        :xs="24"
        :sm="12"
        :md="6"
      >
        <div class="stat-card card-time">
          <div class="stat-icon">
            <el-icon :size="28">
              <Timer />
            </el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value stat-time-value">
              {{ overview.latestArticleTime || '暂无' }}
            </div>
            <div class="stat-label">
              最近采集
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 运行状态栏 -->
    <transition name="slide-fade">
      <div
        v-if="overview.isRunning"
        class="running-bar"
      >
        <div class="running-info">
          <el-icon class="is-loading">
            <Loading />
          </el-icon>
          <span class="running-task">{{ overview.currentTask || '运行中' }}</span>
          <span class="running-msg">{{ overview.message }}</span>
        </div>
        <el-progress
          :percentage="overview.progress || 0"
          :stroke-width="8"
          color="#6366F1"
          class="running-progress"
        />
      </div>
    </transition>

    <!-- 操作面板 + 日志 -->
    <el-row
      :gutter="20"
      class="main-row"
    >
      <!-- 左侧：操作面板 -->
      <el-col
        :xs="24"
        :lg="10"
      >
        <div class="panel operation-panel">
          <div class="panel-header">
            <h3>
              <el-icon><Opportunity /></el-icon> 爬取操作
            </h3>
          </div>
          <div class="panel-body">
            <!-- 刷新热门 -->
            <div class="action-card">
              <div class="action-header">
                <el-icon
                  :size="20"
                  color="#F59E0B"
                >
                  <Sunny />
                </el-icon>
                <span>刷新热门微博</span>
              </div>
              <p class="action-desc">
                获取微博热门时间线最新内容
              </p>
              <div class="action-controls">
                <el-input-number
                  v-model="hotPageNum"
                  :min="1"
                  :max="10"
                  size="small"
                  style="width: 100px"
                />
                <span class="control-label">页</span>
                <el-button
                  type="warning"
                  :loading="overview.isRunning"
                  :icon="Download"
                  size="small"
                  @click="startCrawlAction('hot')"
                >
                  开始爬取
                </el-button>
              </div>
            </div>

            <!-- 关键词搜索 -->
            <div class="action-card">
              <div class="action-header">
                <el-icon
                  :size="20"
                  color="#6366F1"
                >
                  <Search />
                </el-icon>
                <span>关键词搜索爬取</span>
              </div>
              <p class="action-desc">
                按关键词搜索并爬取微博内容
              </p>
              <div class="action-controls">
                <el-input
                  v-model="searchKeyword"
                  placeholder="输入关键词"
                  size="small"
                  style="width: 160px"
                  clearable
                />
                <el-input-number
                  v-model="searchPageNum"
                  :min="1"
                  :max="10"
                  size="small"
                  style="width: 80px"
                />
                <el-button
                  type="primary"
                  :loading="overview.isRunning"
                  :disabled="!searchKeyword.trim()"
                  :icon="Search"
                  size="small"
                  @click="startCrawlAction('search')"
                >
                  搜索
                </el-button>
              </div>
            </div>

            <!-- 评论爬取 -->
            <div class="action-card">
              <div class="action-header">
                <el-icon
                  :size="20"
                  color="#10B981"
                >
                  <ChatLineRound />
                </el-icon>
                <span>爬取评论数据</span>
              </div>
              <p class="action-desc">
                获取最近文章的评论内容
              </p>
              <div class="action-controls">
                <el-button
                  type="success"
                  :loading="overview.isRunning"
                  :icon="Download"
                  size="small"
                  @click="startCrawlAction('comments')"
                >
                  开始爬取
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 爬取历史 -->
        <div class="panel history-panel">
          <div class="panel-header">
            <h3>
              <el-icon><Clock /></el-icon> 爬取历史
            </h3>
          </div>
          <div class="panel-body">
            <div
              v-if="!overview.history || overview.history.length === 0"
              class="empty-state"
            >
              <el-empty
                description="暂无爬取记录"
                :image-size="60"
              />
            </div>
            <div
              v-else
              class="history-list"
            >
              <div
                v-for="(item, index) in overview.history"
                :key="index"
                class="history-item"
                :class="'history-' + item.status"
              >
                <div class="history-badge">
                  <el-icon
                    v-if="item.status === 'success'"
                    color="#10B981"
                  >
                    <CircleCheck />
                  </el-icon>
                  <el-icon
                    v-else
                    color="#EF4444"
                  >
                    <CircleClose />
                  </el-icon>
                </div>
                <div class="history-content">
                  <div class="history-action">
                    {{ item.action }}
                  </div>
                  <div class="history-meta">
                    <span>{{ item.time }}</span>
                    <span v-if="item.count"> · {{ item.count }} 条数据</span>
                    <span v-if="item.detail"> · {{ item.detail }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 右侧：数据趋势 + 日志 -->
      <el-col
        :xs="24"
        :lg="14"
      >
        <!-- 数据趋势图 -->
        <div class="panel chart-panel">
          <div class="panel-header">
            <h3>
              <el-icon><TrendCharts /></el-icon> 数据趋势 (近7天)
            </h3>
          </div>
          <div class="panel-body">
            <div
              ref="trendChartRef"
              class="trend-chart"
            />
          </div>
        </div>

        <!-- 日志面板 -->
        <div class="panel log-panel">
          <div class="panel-header">
            <h3>
              <el-icon><Notebook /></el-icon> 运行日志
            </h3>
            <el-button
              size="small"
              text
              :loading="logsLoading"
              @click="loadLogs"
            >
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>
          <div class="panel-body">
            <div
              ref="logContainerRef"
              class="log-container"
            >
              <div
                v-if="logs.length === 0"
                class="empty-state"
              >
                <el-empty
                  description="暂无日志"
                  :image-size="60"
                />
              </div>
              <div v-else>
                <div
                  v-for="(line, idx) in logs"
                  :key="idx"
                  class="log-line"
                  :class="getLogLevel(line)"
                >
                  {{ line }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
  import { ref, reactive, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
  import { ElMessage } from 'element-plus'
  import {
    Document,
    ChatDotRound,
    User,
    Timer,
    Monitor,
    Refresh,
    Download,
    Search,
    Loading,
    Sunny,
    ChatLineRound,
    Clock,
    CircleCheck,
    CircleClose,
    TrendCharts,
    Notebook,
    Opportunity,
  } from '@element-plus/icons-vue'
  import { getSpiderOverview, startCrawl, getSpiderStatus, getSpiderLogs } from '@/api/spider'
  import echarts from '@/utils/echarts'

  // 概览 data
  const overview = reactive({
    articleCount: 0,
    commentCount: 0,
    userCount: 0,
    latestArticleTime: '',
    latestCommentTime: '',
    isRunning: false,
    currentTask: null,
    progress: 0,
    message: '',
    dailyTrend: [],
    commentTrend: [],
    history: [],
  })

  // 操作表单
  const hotPageNum = ref(3)
  const searchKeyword = ref('')
  const searchPageNum = ref(3)
  const refreshing = ref(false)

  // 日志
  const logs = ref([])
  const logsLoading = ref(false)
  const logContainerRef = ref(null)

  // 图表
  const trendChartRef = ref(null)
  let trendChart = null

  const handleResize = () => {
    trendChart?.resize()
  }

  const handleVisibilityChange = () => {
    if (document.hidden) {
      stopStatusPolling()
      return
    }
    if (overview.isRunning) {
      startStatusPolling()
    }
  }

  // 轮询定时器
  let statusTimer = null
  let pollErrorCount = 0

  // ===== 数据加载 =====
  async function loadOverview() {
    try {
      const res = await getSpiderOverview()
      if (res.code === 200 && res.data) {
        Object.assign(overview, res.data)
        renderTrendChart()
      }
    } catch (e) {
      console.error('加载概览失败:', e)
    }
  }

  async function loadLogs() {
    logsLoading.value = true
    try {
      const res = await getSpiderLogs(200)
      if (res.code === 200 && res.data) {
        logs.value = res.data.logs || []
      }
    } catch (e) {
      console.error('加载日志失败:', e)
    } finally {
      logsLoading.value = false
    }
  }

  async function refreshAll() {
    refreshing.value = true
    await Promise.all([loadOverview(), loadLogs()])
    refreshing.value = false
  }

  // ===== 爬取操作 =====
  async function startCrawlAction(type) {
    const params = { type }
    if (type === 'hot') {
      params.pageNum = hotPageNum.value
    } else if (type === 'search') {
      params.keyword = searchKeyword.value
      params.pageNum = searchPageNum.value
    }

    try {
      const res = await startCrawl(params)
      if (res.code === 200) {
        ElMessage.success(res.msg || '爬虫任务已启动')
        overview.isRunning = true
        startStatusPolling()
      } else {
        ElMessage.warning(res.msg || '启动失败')
      }
    } catch (e) {
      ElMessage.error('请求失败: ' + (e.message || e))
    }
  }

  // ===== 状态轮询 =====
  function startStatusPolling() {
    stopStatusPolling()
    pollErrorCount = 0
    statusTimer = setInterval(async () => {
      try {
        const res = await getSpiderStatus()
        if (res.code === 200 && res.data) {
          overview.isRunning = res.data.isRunning
          overview.currentTask = res.data.currentTask
          overview.progress = res.data.progress
          overview.message = res.data.message

          if (!res.data.isRunning) {
            stopStatusPolling()
            // 任务完成后自动刷新概览
            await loadOverview()
            ElMessage.success('爬取任务已完成')
          }
        }
        pollErrorCount = 0
      } catch (e) {
        console.error('轮询状态失败:', e)
        pollErrorCount += 1
        if (pollErrorCount >= 3) {
          stopStatusPolling()
          overview.isRunning = false
          overview.message = '状态获取失败，已停止轮询，请稍后刷新重试'
          ElMessage.error('状态获取失败，请检查网络或稍后重试')
        }
      }
    }, 2000)
  }

  function stopStatusPolling() {
    if (statusTimer) {
      clearInterval(statusTimer)
      statusTimer = null
    }
  }

  // ===== 图表渲染 =====
  function renderTrendChart() {
    if (!trendChartRef.value) return

    if (!trendChart) {
      trendChart = echarts.init(trendChartRef.value)
    }

    const articleDates = overview.dailyTrend.map((d) => d.date)
    const articleCounts = overview.dailyTrend.map((d) => d.count)
    const commentDates = overview.commentTrend.map((d) => d.date)
    const commentCounts = overview.commentTrend.map((d) => d.count)

    // 合并日期轴
    const allDates = [...new Set([...articleDates, ...commentDates])].sort()

    const articleMap = Object.fromEntries(overview.dailyTrend.map((d) => [d.date, d.count]))
    const commentMap = Object.fromEntries(overview.commentTrend.map((d) => [d.date, d.count]))

    const option = {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        borderColor: '#334155',
        textStyle: { color: '#E2E8F0', fontSize: 12 },
      },
      legend: {
        data: ['文章', '评论'],
        textStyle: { color: '#94A3B8' },
        top: 0,
      },
      grid: { top: 40, right: 20, bottom: 30, left: 50 },
      xAxis: {
        type: 'category',
        data: allDates.map((d) => d.slice(5)), // MM-DD
        axisLine: { lineStyle: { color: '#334155' } },
        axisLabel: { color: '#94A3B8', fontSize: 11 },
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: '#1E293B' } },
        axisLabel: { color: '#94A3B8', fontSize: 11 },
      },
      series: [
        {
          name: '文章',
          type: 'line',
          smooth: true,
          data: allDates.map((d) => articleMap[d] || 0),
          lineStyle: { color: '#6366F1', width: 2 },
          itemStyle: { color: '#6366F1' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(99, 102, 241, 0.3)' },
              { offset: 1, color: 'rgba(99, 102, 241, 0.02)' },
            ]),
          },
        },
        {
          name: '评论',
          type: 'line',
          smooth: true,
          data: allDates.map((d) => commentMap[d] || 0),
          lineStyle: { color: '#10B981', width: 2 },
          itemStyle: { color: '#10B981' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
              { offset: 1, color: 'rgba(16, 185, 129, 0.02)' },
            ]),
          },
        },
      ],
    }

    trendChart.setOption(option)
  }

  // ===== 日志高亮 =====
  function getLogLevel(line) {
    if (line.includes('ERROR') || line.includes('CRITICAL')) return 'log-error'
    if (line.includes('WARNING')) return 'log-warn'
    if (line.includes('INFO')) return 'log-info'
    return 'log-debug'
  }

  // ===== 生命周期 =====
  onMounted(async () => {
    await Promise.all([loadOverview(), loadLogs()])
    if (overview.isRunning) {
      startStatusPolling()
    }

    // 窗口 resize 时重绘图表
    window.addEventListener('resize', handleResize)
    document.addEventListener('visibilitychange', handleVisibilityChange)
  })

  onBeforeUnmount(() => {
    stopStatusPolling()
    trendChart?.dispose()
    window.removeEventListener('resize', handleResize)
    document.removeEventListener('visibilitychange', handleVisibilityChange)
  })
</script>

<style lang="scss" scoped>
  .spider-page {
    max-width: 1400px;
    margin: 0 auto;
  }

  /* 页面头部 */
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
  }

  .page-header h2 {
    font-size: 22px;
    font-weight: 700;
    color: $text-primary;
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0;
  }

  .subtitle {
    color: $text-secondary;
    font-size: 13px;
    margin: 4px 0 0 0;
  }

  /* 统计卡片 */
  .stats-row {
    margin-bottom: 20px;
  }

  .stat-card {
    background: $surface-color;
    border-radius: 12px;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
    border: 1px solid $border-color;
    transition:
      transform 0.2s,
      box-shadow 0.2s;
  }

  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .stat-icon {
    width: 52px;
    height: 52px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .card-articles .stat-icon {
    background: rgba(99, 102, 241, 0.1);
    color: #6366f1;
  }
  .card-comments .stat-icon {
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;
  }
  .card-users .stat-icon {
    background: rgba(245, 158, 11, 0.1);
    color: #f59e0b;
  }
  .card-time .stat-icon {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }

  .stat-value {
    font-size: 26px;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.2;
  }

  .stat-time-value {
    font-size: 14px;
    font-weight: 600;
  }

  .stat-label {
    font-size: 13px;
    color: #94a3b8;
    margin-top: 2px;
  }

  /* 运行状态栏 */
  .running-bar {
    background: linear-gradient(135deg, #eef2ff, #e0e7ff);
    border: 1px solid #c7d2fe;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 20px;
  }

  .running-info {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .running-task {
    font-weight: 600;
    color: #4338ca;
  }

  .running-msg {
    color: #6366f1;
    font-size: 13px;
  }

  .running-progress {
    flex: 1;
    min-width: 200px;
  }

  .slide-fade-enter-active {
    transition: all 0.3s ease;
  }
  .slide-fade-leave-active {
    transition: all 0.2s ease;
  }
  .slide-fade-enter-from,
  .slide-fade-leave-to {
    transform: translateY(-10px);
    opacity: 0;
  }

  /* 面板通用 */
  .panel {
    background: #fff;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
    margin-bottom: 20px;
    overflow: hidden;
  }

  .panel-header {
    padding: 16px 20px;
    border-bottom: 1px solid #f1f5f9;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .panel-header h3 {
    font-size: 15px;
    font-weight: 600;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 0;
  }

  .panel-body {
    padding: 16px 20px;
  }

  /* 操作卡片 */
  .action-card {
    padding: 16px;
    border-radius: 10px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    margin-bottom: 12px;
    transition: border-color 0.2s;
  }

  .action-card:hover {
    border-color: #cbd5e1;
  }

  .action-card:last-child {
    margin-bottom: 0;
  }

  .action-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 4px;
  }

  .action-desc {
    font-size: 12px;
    color: #94a3b8;
    margin: 0 0 12px 0;
  }

  .action-controls {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .control-label {
    color: #64748b;
    font-size: 13px;
  }

  /* 历史记录 */
  .history-list {
    max-height: 300px;
    overflow-y: auto;
  }

  .history-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 0;
    border-bottom: 1px solid #f1f5f9;
  }

  .history-item:last-child {
    border-bottom: none;
  }

  .history-badge {
    flex-shrink: 0;
    margin-top: 2px;
  }

  .history-action {
    font-size: 13px;
    font-weight: 500;
    color: #1e293b;
  }

  .history-meta {
    font-size: 12px;
    color: #94a3b8;
    margin-top: 2px;
  }

  /* 趋势图 */
  .trend-chart {
    width: 100%;
    height: 280px;
  }

  /* 日志面板 */
  .log-container {
    max-height: 400px;
    overflow-y: auto;
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
    font-size: 11.5px;
    line-height: 1.6;
    background: #0f172a;
    border-radius: 8px;
    padding: 12px 16px;
  }

  .log-line {
    color: #cbd5e1;
    word-break: break-all;
    padding: 1px 0;
  }

  .log-error {
    color: #f87171;
  }

  .log-warn {
    color: #fbbf24;
  }

  .log-info {
    color: #60a5fa;
  }

  .log-debug {
    color: #64748b;
  }

  .empty-state {
    padding: 20px 0;
    text-align: center;
  }

  /* 响应式 */
  @media (max-width: 768px) {
    .stats-row .el-col {
      margin-bottom: 12px;
    }

    .running-bar {
      flex-direction: column;
      align-items: flex-start;
    }

    .running-progress {
      width: 100%;
    }

    .action-controls {
      flex-direction: column;
      align-items: flex-start;
    }
  }
</style>
