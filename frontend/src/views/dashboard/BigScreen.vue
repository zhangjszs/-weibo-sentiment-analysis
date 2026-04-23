<template>
  <div
    class="big-screen"
    :class="{ fullscreen: isFullscreen }"
  >
    <div class="screen-header">
      <div class="header-left">
        <span class="time">{{ currentTime }}</span>
        <span class="date">{{ currentDate }}</span>
      </div>
      <div class="header-center">
        <h1 class="title">
          微博舆情分析实时监控大屏
        </h1>
      </div>
      <div class="header-right">
        <el-button @click="showConfig = true">
          配置
        </el-button>
        <el-button
          type="primary"
          @click="toggleFullscreen"
        >
          {{ isFullscreen ? '退出全屏' : '全屏显示' }}
        </el-button>
      </div>
    </div>

    <div class="screen-body">
      <div class="left-panel">
        <div class="panel-item">
          <div class="panel-title">
            数据概览
          </div>
          <div class="stat-grid">
            <div class="stat-item">
              <div
                ref="articleCountRef"
                class="stat-value"
              >
                {{ animatedStats.articleCount }}
              </div>
              <div class="stat-label">
                文章总数
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-value">
                {{ animatedStats.commentCount }}
              </div>
              <div class="stat-label">
                评论总数
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-value positive">
                {{ animatedStats.positiveCount }}
              </div>
              <div class="stat-label">
                正面评价
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-value negative">
                {{ animatedStats.negativeCount }}
              </div>
              <div class="stat-label">
                负面评价
              </div>
            </div>
          </div>
        </div>

        <div class="panel-item">
          <div class="panel-title">
            情感分布
          </div>
          <BaseChart
            ref="sentimentChartRef"
            :options="sentimentChartOptions"
            height="220px"
          />
        </div>

        <div class="panel-item">
          <div class="panel-title">
            实时预警
          </div>
          <div class="alert-list">
            <div
              v-for="alert in recentAlerts"
              :key="alert.id"
              class="alert-item"
              :class="alert.level"
            >
              <span class="alert-time">{{ alert.time }}</span>
              <span class="alert-title">{{ alert.title }}</span>
            </div>
            <div
              v-if="recentAlerts.length === 0"
              class="no-alert"
            >
              暂无预警
            </div>
          </div>
        </div>
      </div>

      <div class="center-panel">
        <div class="map-container">
          <div class="panel-title">
            地域分布
          </div>
          <BaseChart
            ref="mapChartRef"
            :options="mapChartOptions"
            height="400px"
          />
        </div>

        <div class="trend-container">
          <div class="panel-title">
            舆情趋势
          </div>
          <BaseChart
            ref="trendChartRef"
            :options="trendChartOptions"
            height="200px"
          />
        </div>
      </div>

      <div class="right-panel">
        <div class="panel-item">
          <div class="panel-title">
            热门话题 Top 10
          </div>
          <div class="topic-list">
            <div
              v-for="(topic, index) in hotTopics"
              :key="index"
              class="topic-item"
            >
              <span
                class="topic-rank"
                :class="{ top: index < 3 }"
              >{{ index + 1 }}</span>
              <span class="topic-name">{{ topic.name }}</span>
              <div class="topic-bar">
                <div
                  class="topic-bar-inner"
                  :style="{ width: topic.percent + '%' }"
                />
              </div>
              <span class="topic-heat">{{ topic.heat }}</span>
            </div>
          </div>
        </div>

        <div class="panel-item">
          <div class="panel-title">
            词云
          </div>
          <div
            ref="wordCloudRef"
            class="word-cloud-container"
          />
        </div>

        <div class="panel-item">
          <div class="panel-title">
            传播速度
          </div>
          <BaseChart
            ref="speedChartRef"
            :options="speedChartOptions"
            height="180px"
          />
        </div>
      </div>

      <!-- 时间轴播放控制栏 -->
      <div
        v-if="showTimeline"
        class="timeline-bar"
      >
        <el-button
          :icon="isPlaying ? 'VideoPause' : 'VideoPlay'"
          circle
          @click="togglePlay"
        />
        <el-slider
          v-model="timelineIndex"
          :max="timelineData.length - 1"
          :step="1"
          :format-tooltip="(v) => timelineData[v]?.label || v"
          class="timeline-slider"
        />
        <span class="timeline-label">{{ timelineData[timelineIndex]?.label }}</span>
        <el-button
          size="small"
          @click="showTimeline = false"
        >
          关闭
        </el-button>
      </div>

      <!-- 大屏配置面板 -->
      <el-drawer
        v-model="showConfig"
        title="大屏配置"
        direction="rtl"
        size="320px"
      >
        <div class="config-panel">
          <div class="config-section">
            <div class="config-title">
              刷新间隔
            </div>
            <el-radio-group
              v-model="refreshInterval"
              @change="onRefreshIntervalChange"
            >
              <el-radio :value="3000">
                3秒
              </el-radio>
              <el-radio :value="5000">
                5秒
              </el-radio>
              <el-radio :value="10000">
                10秒
              </el-radio>
              <el-radio :value="30000">
                30秒
              </el-radio>
            </el-radio-group>
          </div>
          <div class="config-section">
            <div class="config-title">
              显示模块
            </div>
            <el-checkbox v-model="visiblePanels.sentiment">
              情感分布
            </el-checkbox>
            <el-checkbox v-model="visiblePanels.topics">
              热门话题
            </el-checkbox>
            <el-checkbox v-model="visiblePanels.alerts">
              实时预警
            </el-checkbox>
            <el-checkbox v-model="visiblePanels.trend">
              舆情趋势
            </el-checkbox>
            <el-checkbox v-model="visiblePanels.map">
              地域分布
            </el-checkbox>
          </div>
          <div class="config-section">
            <div class="config-title">
              时间轴播放
            </div>
            <el-button
              type="primary"
              @click="openTimeline"
            >
              开启时间轴
            </el-button>
          </div>
        </div>
      </el-drawer>
    </div>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted, onUnmounted } from 'vue'
  import BaseChart from '@/components/Charts/BaseChart.vue'
  import {
    getBigScreenStats,
    getBigScreenRegion,
    getBigScreenTrend,
    getBigScreenHotTopics,
    getBigScreenAlerts,
  } from '@/api/stats'
  import { ElMessage } from 'element-plus'

  const isFullscreen = ref(false)
  const currentTime = ref('')
  const currentDate = ref('')
  const loading = ref(false)

  // 统计数据 - 从 API 获取
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

  // 热门话题 - 从 API 获取
  const hotTopics = ref([])

  // 最近预警 - 从 API 获取
  const recentAlerts = ref([])

  // 地区数据 - 从 API 获取
  const regionData = ref([])

  // 趋势数据 - 从 API 获取
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
        label: {
          show: true,
          formatter: '{b}: {d}%',
          color: '#fff',
        },
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
    legend: {
      data: ['正面', '中性', '负面'],
      textStyle: { color: '#fff' },
      top: 0,
    },
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
      {
        name: '正面',
        type: 'line',
        smooth: true,
        data: trendData.value.positive.length > 0 ? trendData.value.positive : [120, 132, 201, 234, 290, 330, 410],
        itemStyle: { color: '#10B981' },
      },
      {
        name: '中性',
        type: 'line',
        smooth: true,
        data: trendData.value.neutral.length > 0 ? trendData.value.neutral : [80, 92, 141, 154, 190, 230, 280],
        itemStyle: { color: '#64748B' },
      },
      {
        name: '负面',
        type: 'line',
        smooth: true,
        data: trendData.value.negative.length > 0 ? trendData.value.negative : [30, 42, 61, 74, 90, 110, 130],
        itemStyle: { color: '#EF4444' },
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

      if (step >= steps) {
        clearInterval(timer)
      }
    }, interval)
  }

  // 从 API 加载统计数据
  const loadStats = async () => {
    try {
      const res = await getBigScreenStats()
      if (res.data) {
        stats.value = {
          articleCount: res.data.articleCount || 0,
          commentCount: res.data.commentCount || 0,
          positiveCount: res.data.positiveCount || 0,
          negativeCount: res.data.negativeCount || 0,
          neutralCount: res.data.neutralCount || 0,
        }
        animateStats()
      }
    } catch (error) {
      console.error('加载统计数据失败:', error)
    }
  }

  // 从 API 加载地区数据
  const loadRegionData = async () => {
    try {
      const res = await getBigScreenRegion()
      if (res.data && res.data.data) {
        regionData.value = res.data.data
      }
    } catch (error) {
      console.error('加载地区数据失败:', error)
    }
  }

  // 从 API 加载趋势数据
  const loadTrendData = async () => {
    try {
      const res = await getBigScreenTrend(24)
      if (res.data) {
        trendData.value = {
          times: res.data.times || [],
          positive: res.data.positive || [],
          neutral: res.data.neutral || [],
          negative: res.data.negative || [],
        }
      }
    } catch (error) {
      console.error('加载趋势数据失败:', error)
    }
  }

  // 从 API 加载热门话题
  const loadHotTopics = async () => {
    try {
      const res = await getBigScreenHotTopics(10)
      if (res.data && res.data.topics) {
        hotTopics.value = res.data.topics
      }
    } catch (error) {
      console.error('加载热门话题失败:', error)
    }
  }

  // 从 API 加载预警数据
  const loadAlerts = async () => {
    try {
      const res = await getBigScreenAlerts(5)
      if (res.data && res.data.alerts) {
        recentAlerts.value = res.data.alerts
      }
    } catch (error) {
      console.error('加载预警数据失败:', error)
    }
  }

  // 加载所有数据
  const loadAllData = async () => {
    loading.value = true
    await Promise.all([
      loadStats(),
      loadRegionData(),
      loadTrendData(),
      loadHotTopics(),
      loadAlerts(),
    ])
    loading.value = false
  }

  // 模拟数据更新（当 API 不可用时使用）
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

  onMounted(() => {
    updateTime()
    timeTimer = setInterval(updateTime, 1000)
    
    // 加载真实数据
    loadAllData()
    
    // 定时刷新数据
    dataTimer = setInterval(() => {
      loadStats()
      loadHotTopics()
      loadAlerts()
    }, refreshInterval.value)
  })

  onUnmounted(() => {
    if (timeTimer) clearInterval(timeTimer)
    if (dataTimer) clearInterval(dataTimer)
  })

  // 时间轴播放
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
        if (timelineIndex.value < timelineData.value.length - 1) {
          timelineIndex.value++
        } else {
          timelineIndex.value = 0
        }
      }, 1000)
    } else {
      clearInterval(playTimer)
    }
  }

  const openTimeline = () => {
    showConfig.value = false
    showTimeline.value = true
  }

  // 大屏配置
  const showConfig = ref(false)
  const refreshInterval = ref(5000)
  const visiblePanels = ref({
    sentiment: true,
    topics: true,
    alerts: true,
    trend: true,
    map: true,
  })

  const onRefreshIntervalChange = (val) => {
    if (dataTimer) clearInterval(dataTimer)
    dataTimer = setInterval(simulateDataUpdate, val)
  }
</script>

<style lang="scss" scoped>
  .big-screen {
    min-height: 100vh;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    color: #fff;
    padding: 20px;
    position: relative;
    overflow: hidden;

    // Artistic background elements
    &::before {
      content: '';
      position: absolute;
      top: 0;
      right: 0;
      width: 500px;
      height: 500px;
      background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, rgba(59, 130, 246, 0) 70%);
      border-radius: 50%;
      transform: translate(30%, -30%);
      z-index: 1;
    }

    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 0;
      width: 400px;
      height: 400px;
      background: radial-gradient(circle, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0) 70%);
      border-radius: 50%;
      transform: translate(-30%, 30%);
      z-index: 1;
    }

    &.fullscreen {
      padding: 12px;
    }

    .screen-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 20px 32px;
      background: linear-gradient(
        90deg,
        rgba(59, 130, 246, 0.2),
        rgba(59, 130, 246, 0.1),
        rgba(59, 130, 246, 0.2)
      );
      border: 1px solid rgba(59, 130, 246, 0.3);
      border-radius: 16px;
      margin-bottom: 24px;
      position: relative;
      z-index: 2;
      backdrop-filter: blur(10px);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);

      &::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #3b82f6, #10b981, #3b82f6);
        border-radius: 16px 16px 0 0;
      }

      .header-left {
        display: flex;
        align-items: center;
        gap: 20px;

        .time {
          font-size: 32px;
          font-weight: 700;
          color: #3b82f6;
          text-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
          font-variant-numeric: tabular-nums;
        }
        .date {
          font-size: 16px;
          color: #94a3b8;
          background: rgba(148, 163, 184, 0.1);
          padding: 6px 12px;
          border-radius: 12px;
        }
      }

      .header-center {
        .title {
          font-size: 32px;
          font-weight: 800;
          background: linear-gradient(90deg, #3b82f6, #10b981, #3b82f6);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          margin: 0;
          text-shadow: 0 0 30px rgba(59, 130, 246, 0.3);
          letter-spacing: 1px;
        }
      }

      .header-right {
        display: flex;
        gap: 12px;

        .el-button {
          border-radius: 12px;
          border: 1px solid rgba(59, 130, 246, 0.3);
          background: rgba(59, 130, 246, 0.1);
          color: #3b82f6;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

          &:hover {
            background: rgba(59, 130, 246, 0.2);
            box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
            transform: translateY(-2px);
          }

          &--primary {
            background: linear-gradient(90deg, #3b82f6, #1d4ed8);
            border: none;
            color: white;

            &:hover {
              background: linear-gradient(90deg, #2563eb, #1e40af);
              box-shadow: 0 4px 16px rgba(59, 130, 246, 0.4);
            }
          }
        }
      }
    }

    .screen-body {
      display: flex;
      gap: 20px;
      height: calc(100vh - 160px);
      position: relative;
      z-index: 2;

      .left-panel,
      .right-panel {
        width: 28%;
        display: flex;
        flex-direction: column;
        gap: 20px;
      }

      .center-panel {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 20px;
      }

      .panel-item {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 16px;
        padding: 20px;
        flex: 1;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;

        &::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          width: 4px;
          height: 100%;
          background: linear-gradient(180deg, #3b82f6, #10b981);
          border-radius: 16px 0 0 16px;
        }

        &:hover {
          box-shadow: 0 8px 32px rgba(59, 130, 246, 0.2);
          transform: translateY(-4px);
          border-color: rgba(59, 130, 246, 0.4);
        }

        .panel-title {
          font-size: 18px;
          font-weight: 600;
          color: #3b82f6;
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid rgba(59, 130, 246, 0.2);
          position: relative;

          &::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 80px;
            height: 2px;
            background: linear-gradient(90deg, #3b82f6, #10b981);
          }
        }
      }

      .stat-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;

        .stat-item {
          text-align: center;
          padding: 20px;
          background: rgba(59, 130, 246, 0.1);
          border-radius: 12px;
          border: 1px solid rgba(59, 130, 246, 0.2);
          transition: all 0.3s ease;
          position: relative;
          overflow: hidden;

          &::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, #3b82f6, transparent);
          }

          &:hover {
            background: rgba(59, 130, 246, 0.15);
            transform: scale(1.02);
            box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2);
          }

          .stat-value {
            font-size: 32px;
            font-weight: 700;
            color: #3b82f6;
            text-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
            font-variant-numeric: tabular-nums;
            margin-bottom: 8px;
            transition: all 0.3s ease;

            &.positive {
              color: #10b981;
              text-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
            }
            &.negative {
              color: #ef4444;
              text-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
            }

            &:hover {
              transform: scale(1.05);
            }
          }

          .stat-label {
            font-size: 14px;
            color: #94a3b8;
            font-weight: 500;
            letter-spacing: 0.5px;
          }
        }
      }

      .alert-list {
        max-height: 100%;
        overflow-y: auto;

        &::-webkit-scrollbar {
          width: 4px;
        }

        &::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 2px;
        }

        &::-webkit-scrollbar-thumb {
          background: rgba(59, 130, 246, 0.5);
          border-radius: 2px;
        }

        .alert-item {
          display: flex;
          align-items: center;
          padding: 12px 16px;
          margin-bottom: 12px;
          border-radius: 12px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.05);
          transition: all 0.3s ease;
          position: relative;

          &::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            border-radius: 12px 0 0 12px;
          }

          &.danger {
            &::before {
              background: linear-gradient(180deg, #ef4444, #dc2626);
            }
          }
          &.warning {
            &::before {
              background: linear-gradient(180deg, #f59e0b, #d97706);
            }
          }
          &.info {
            &::before {
              background: linear-gradient(180deg, #3b82f6, #2563eb);
            }
          }

          &:hover {
            background: rgba(255, 255, 255, 0.08);
            transform: translateX(8px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
          }

          .alert-time {
            font-size: 12px;
            color: #94a3b8;
            margin-right: 16px;
            background: rgba(148, 163, 184, 0.1);
            padding: 4px 8px;
            border-radius: 8px;
          }

          .alert-title {
            font-size: 14px;
            flex: 1;
            line-height: 1.4;
          }
        }

        .no-alert {
          text-align: center;
          color: #64748b;
          padding: 32px;
          background: rgba(100, 116, 139, 0.1);
          border-radius: 12px;
          border: 1px dashed rgba(100, 116, 139, 0.3);
        }
      }

      .topic-list {
        max-height: 100%;
        overflow-y: auto;

        &::-webkit-scrollbar {
          width: 4px;
        }

        &::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 2px;
        }

        &::-webkit-scrollbar-thumb {
          background: rgba(59, 130, 246, 0.5);
          border-radius: 2px;
        }

        .topic-item {
          display: flex;
          align-items: center;
          padding: 12px 0;
          transition: all 0.3s ease;

          &:hover {
            transform: translateX(4px);
          }

          .topic-rank {
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 600;
            background: #64748b;
            border-radius: 8px;
            margin-right: 16px;
            transition: all 0.3s ease;

            &.top {
              background: linear-gradient(135deg, #f59e0b, #ef4444);
              box-shadow: 0 2px 10px rgba(245, 158, 11, 0.4);
            }

            &:hover {
              transform: scale(1.1);
            }
          }

          .topic-name {
            flex: 1;
            font-size: 14px;
            line-height: 1.4;
            margin-right: 12px;
          }

          .topic-bar {
            width: 100px;
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            margin: 0 12px;
            overflow: hidden;
            position: relative;

            .topic-bar-inner {
              height: 100%;
              background: linear-gradient(90deg, #3b82f6, #10b981);
              border-radius: 4px;
              transition: width 1s ease-out;
              position: relative;

              &::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
                animation: shimmer 2s infinite;
              }
            }
          }

          .topic-heat {
            font-size: 13px;
            color: #94a3b8;
            width: 60px;
            text-align: right;
            font-weight: 500;
          }
        }
      }

      .word-cloud-container {
        height: 180px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #64748b;
        background: rgba(100, 116, 139, 0.1);
        border-radius: 12px;
        border: 1px dashed rgba(100, 116, 139, 0.3);
        transition: all 0.3s ease;

        &:hover {
          background: rgba(100, 116, 139, 0.15);
          border-color: rgba(100, 116, 139, 0.5);
        }
      }

      .map-container,
      .trend-container {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 16px;
        padding: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        position: relative;
        overflow: hidden;

        &::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          width: 4px;
          height: 100%;
          background: linear-gradient(180deg, #3b82f6, #10b981);
          border-radius: 16px 0 0 16px;
        }

        .panel-title {
          font-size: 18px;
          font-weight: 600;
          color: #3b82f6;
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid rgba(59, 130, 246, 0.2);
          position: relative;

          &::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 80px;
            height: 2px;
            background: linear-gradient(90deg, #3b82f6, #10b981);
          }
        }
      }

      .map-container {
        flex: 2;
      }
      .trend-container {
        flex: 1;
      }
    }

    .timeline-bar {
      position: absolute;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(30, 41, 59, 0.9);
      border: 1px solid rgba(59, 130, 246, 0.3);
      border-radius: 24px;
      padding: 16px 24px;
      display: flex;
      align-items: center;
      gap: 16px;
      backdrop-filter: blur(10px);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
      z-index: 10;

      .el-button {
        border-radius: 50%;
        background: rgba(59, 130, 246, 0.2);
        border: 1px solid rgba(59, 130, 246, 0.3);
        color: #3b82f6;

        &:hover {
          background: rgba(59, 130, 246, 0.3);
        }
      }

      .timeline-slider {
        flex: 1;
        max-width: 400px;

        :deep(.el-slider__runway) {
          background: rgba(255, 255, 255, 0.1);
        }

        :deep(.el-slider__bar) {
          background: linear-gradient(90deg, #3b82f6, #10b981);
        }

        :deep(.el-slider__button) {
          border-color: #3b82f6;
          background: #3b82f6;
          box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
        }
      }

      .timeline-label {
        color: #94a3b8;
        font-size: 14px;
        min-width: 80px;
        text-align: center;
      }
    }

    .config-panel {
      background: rgba(15, 23, 42, 0.95);
      border-radius: 16px;
      padding: 24px;
      backdrop-filter: blur(10px);

      .config-section {
        margin-bottom: 24px;

        .config-title {
          font-size: 16px;
          font-weight: 600;
          color: #3b82f6;
          margin-bottom: 16px;
          padding-bottom: 8px;
          border-bottom: 1px solid rgba(59, 130, 246, 0.2);
        }

        .el-radio-group {
          display: flex;
          flex-direction: column;
          gap: 12px;

          .el-radio {
            color: #94a3b8;

            &__input.is-checked .el-radio__inner {
              border-color: #3b82f6;
              background: #3b82f6;
            }

            &__label {
              transition: color 0.3s ease;

              &:hover {
                color: #3b82f6;
              }
            }
          }
        }

        .el-checkbox {
          display: block;
          margin-bottom: 12px;
          color: #94a3b8;

          &__input.is-checked .el-checkbox__inner {
            border-color: #3b82f6;
            background: #3b82f6;
          }

          &__label {
            transition: color 0.3s ease;

            &:hover {
              color: #3b82f6;
            }
          }
        }

        .el-button {
          width: 100%;
          border-radius: 12px;
          background: linear-gradient(90deg, #3b82f6, #1d4ed8);
          border: none;
          color: white;
          transition: all 0.3s ease;

          &:hover {
            background: linear-gradient(90deg, #2563eb, #1e40af);
            box-shadow: 0 4px 16px rgba(59, 130, 246, 0.4);
          }
        }
      }
    }
  }

  /* Animations */
  @keyframes shimmer {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }

  /* Responsive adjustments */
  @media screen and (max-width: 1440px) {
    .big-screen {
      .screen-body {
        .left-panel,
        .right-panel {
          width: 30%;
        }
      }
    }
  }

  @media screen and (max-width: 1200px) {
    .big-screen {
      .screen-header {
        .header-center {
          .title {
            font-size: 24px;
          }
        }

        .header-left {
          .time {
            font-size: 24px;
          }
        }
      }

      .screen-body {
        flex-direction: column;
        height: auto;
        min-height: calc(100vh - 160px);

        .left-panel,
        .right-panel {
          width: 100%;
          flex-direction: row;

          .panel-item {
            flex: 1;
          }
        }

        .center-panel {
          flex-direction: row;

          .map-container,
          .trend-container {
            flex: 1;
          }
        }
      }
    }
  }
</style>
