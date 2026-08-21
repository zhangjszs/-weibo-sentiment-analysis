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
import BaseChart from '@/components/Charts/BaseChart.vue'
import { useBigScreen } from '@/composables/useBigScreen'

const {
  isFullscreen,
  currentTime,
  currentDate,
  loading,
  stats,
  animatedStats,
  hotTopics,
  recentAlerts,
  regionData,
  trendData,
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
} = useBigScreen()
</script>

<style lang="scss" scoped src="./BigScreen.scss"></style>
