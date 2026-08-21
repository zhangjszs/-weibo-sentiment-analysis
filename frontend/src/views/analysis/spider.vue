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

    <SpiderStats :overview="overview" />

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

            <!-- 清空缓存 -->
            <div class="action-card">
              <div class="action-header">
                <el-icon
                  :size="20"
                  color="#EF4444"
                >
                  <Delete />
                </el-icon>
                <span>清空系统缓存</span>
              </div>
              <p class="action-desc">
                清除内存与文件缓存，强制刷新数据
              </p>
              <div class="action-controls">
                <el-button
                  type="danger"
                  :icon="Delete"
                  size="small"
                  :loading="clearingCache"
                  @click="handleClearCache"
                >
                  清空缓存
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
            <div class="header-actions">
              <el-radio-group
                v-model="logFilter"
                size="small"
              >
                <el-radio-button label="all">
                  全部
                </el-radio-button>
                <el-radio-button label="error">
                  错误
                </el-radio-button>
                <el-radio-button label="warn">
                  警告
                </el-radio-button>
                <el-radio-button label="info">
                  信息
                </el-radio-button>
              </el-radio-group>
              <el-button
                size="small"
                text
                :loading="logsLoading"
                @click="loadLogs"
              >
                <el-icon><Refresh /></el-icon> 刷新
              </el-button>
            </div>
          </div>
          <div class="panel-body">
            <div
              ref="logContainerRef"
              class="log-container"
            >
              <div
                v-if="filteredLogs.length === 0"
                class="empty-state"
              >
                <el-empty
                  description="暂无日志"
                  :image-size="60"
                />
              </div>
              <div v-else>
                <div
                  v-for="(line, idx) in filteredLogs"
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
import { Monitor, Refresh, Download, Search, Loading, Sunny, ChatLineRound, Clock, CircleCheck, CircleClose, TrendCharts, Notebook, Opportunity, Delete } from '@element-plus/icons-vue'
import SpiderStats from '@/components/analysis/SpiderStats.vue'
import { useSpider } from '@/composables/useSpider'

const {
  overview, hotPageNum, searchKeyword, searchPageNum, refreshing, clearingCache,
  logs, logsLoading, logFilter, logContainerRef, trendChartRef,
  filteredLogs, refreshAll, handleClearCache, startCrawlAction, getLogLevel,
} = useSpider()
</script>

<style lang="scss" scoped src="./spider.scss"></style>
