<template>
  <div class="home-container">
    <div class="dashboard-toolbar">
      <el-button
        :icon="Setting"
        circle
        size="small"
        title="自定义布局"
        @click="showSettings = true"
      />
    </div>

    <template
      v-for="widget in widgetList"
      :key="widget.key"
    >
      <!-- 统计卡片 -->
      <el-row
        v-if="widget.key === 'stats' && widget.visible"
        :gutter="24"
        class="stat-row"
      >
        <el-col
          :xs="24"
          :sm="12"
          :md="6"
        >
          <StatCard
            :value="statsData.articleCount"
            label="总文章数"
            icon="Document"
            bg-color="#EFF6FF"
            icon-color="#2563EB"
          />
        </el-col>
        <el-col
          :xs="24"
          :sm="12"
          :md="6"
        >
          <StatCard
            :value="statsData.todayCount"
            label="今日新增"
            icon="TrendCharts"
            bg-color="#ECFDF5"
            icon-color="#059669"
          />
        </el-col>
        <el-col
          :xs="24"
          :sm="12"
          :md="6"
        >
          <StatCard
            :value="statsData.topAuthor"
            label="最火作者"
            icon="User"
            bg-color="#FFFBEB"
            icon-color="#D97706"
          />
        </el-col>
        <el-col
          :xs="24"
          :sm="12"
          :md="6"
        >
          <StatCard
            :value="statsData.topRegion"
            label="热门地区"
            icon="Location"
            bg-color="#FFF1F2"
            icon-color="#E11D48"
          />
        </el-col>
      </el-row>

      <!-- 时间线图表 -->
      <el-row
        v-if="widget.key === 'timeline' && widget.visible"
        :gutter="24"
        class="mb-4"
      >
        <el-col :span="24">
          <BaseCard class="chart-card">
            <template #header>
              <span class="header-title">文章发布时间分布</span>
              <el-button
                type="primary"
                plain
                size="small"
                :icon="Refresh"
                @click="refreshData"
              >
                刷新数据
              </el-button>
            </template>
            <BaseChart
              ref="lineChartRef"
              :options="lineChartOptions"
              height="350px"
            />
          </BaseCard>
        </el-col>
      </el-row>

      <!-- 图表区 -->
      <el-row
        v-if="widget.key === 'charts' && widget.visible"
        :gutter="24"
      >
        <el-col
          :xs="24"
          :lg="8"
        >
          <BaseCard
            class="chart-card"
            title="评论点赞量 Top 5"
          >
            <div class="top-comments">
              <div
                v-for="(comment, index) in topComments"
                :key="index"
                class="comment-item"
              >
                <div class="comment-avatar">
                  {{ comment.user.charAt(0) }}
                </div>
                <div class="comment-info">
                  <div class="comment-header">
                    <span class="comment-user">{{ comment.user }}</span>
                    <span class="comment-likes"><el-icon><StarFilled /></el-icon> {{ comment.likes }}</span>
                  </div>
                  <div
                    class="comment-content"
                    :title="comment.content"
                  >
                    {{ comment.content }}
                  </div>
                </div>
              </div>
            </div>
          </BaseCard>
        </el-col>
        <el-col
          :xs="24"
          :lg="8"
        >
          <BaseCard
            class="chart-card"
            title="文章类型占比"
          >
            <BaseChart
              ref="pieChartRef"
              :options="pieChartOptions"
              height="350px"
            />
          </BaseCard>
        </el-col>
        <el-col
          :xs="24"
          :lg="8"
        >
          <BaseCard
            class="chart-card"
            title="评论用户时间占比"
          >
            <BaseChart
              ref="timePieChartRef"
              :options="timePieChartOptions"
              height="350px"
            />
          </BaseCard>
        </el-col>
      </el-row>
    </template>

    <!-- 自定义布局抽屉 -->
    <el-drawer
      v-model="showSettings"
      title="仪表盘布局设置"
      size="320px"
      :append-to-body="true"
    >
      <div class="widget-settings">
        <p class="settings-tip">
          拖拽调整顺序，切换显示/隐藏，选择宽度
        </p>
        <VueDraggable
          v-model="widgetList"
          handle=".drag-handle"
          @end="saveWidgetList"
        >
          <div
            v-for="opt in widgetList"
            :key="opt.key"
            class="widget-item"
          >
            <el-icon class="drag-handle">
              <Rank />
            </el-icon>
            <el-switch
              v-model="opt.visible"
              @change="saveWidgetList"
            />
            <span class="widget-label">{{ opt.label }}</span>
            <el-tooltip
              :content="opt.span === 24 ? '切换为半宽' : '切换为全宽'"
              placement="top"
            >
              <el-button
                :icon="opt.span === 24 ? Grid : FullScreen"
                circle
                size="small"
                class="span-btn"
                @click="toggleSpan(opt)"
              />
            </el-tooltip>
          </div>
        </VueDraggable>
        <el-divider />
        <el-button
          type="primary"
          plain
          size="small"
          @click="resetWidgets"
        >
          恢复默认布局
        </el-button>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
  import { ref, onMounted, computed } from 'vue'
  import { VueDraggable } from 'vue-draggable-plus'
  import { Refresh, StarFilled, Setting, Rank, Grid, FullScreen } from '@element-plus/icons-vue'
  import { ElMessage } from 'element-plus'
  import StatCard from '@/components/Common/StatCard.vue'
  import BaseCard from '@/components/Common/BaseCard.vue'
  import BaseChart from '@/components/Charts/BaseChart.vue'
  import { getHomeStats, getTodayStats, refreshSpiderData } from '@/api/stats'

  const lineChartRef = ref(null)
  const pieChartRef = ref(null)
  const timePieChartRef = ref(null)

  const statsData = ref({
    articleCount: 0,
    todayCount: '0篇',
    topAuthor: '-',
    topRegion: '-',
  })

  const topComments = ref([])

  const xData = ref([])
  const yData = ref([])
  const articleTypeData = ref([])
  const commentTimeData = ref([])

  // Dashboard customization
  const showSettings = ref(false)

  const defaultWidgetList = [
    { key: 'stats', label: '统计卡片', visible: true, span: 24 },
    { key: 'timeline', label: '文章发布时间分布', visible: true, span: 24 },
    { key: 'charts', label: '图表区（评论/类型/时间）', visible: true, span: 24 },
  ]

  const loadWidgetList = () => {
    try {
      const saved = localStorage.getItem('dashboard_widget_list')
      if (saved) {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed) && parsed.length === defaultWidgetList.length) {
          return parsed
        }
      }
    } catch {
      /* ignore */
    }
    return defaultWidgetList.map((w) => ({ ...w }))
  }

  const widgetList = ref(loadWidgetList())
  const saveWidgetList = () =>
    localStorage.setItem('dashboard_widget_list', JSON.stringify(widgetList.value))
  const resetWidgets = () => {
    widgetList.value = defaultWidgetList.map((w) => ({ ...w }))
    saveWidgetList()
  }
  const toggleSpan = (widget) => {
    widget.span = widget.span === 24 ? 12 : 24
    saveWidgetList()
  }

  const lineChartOptions = computed(() => ({
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#ffffff',
      borderColor: '#eaeaea',
      textStyle: { color: '#171717' },
      extraCssText: 'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04); border-radius: 8px;',
    },
    grid: {
      top: '10%',
      left: '2%',
      right: '2%',
      bottom: '0%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: xData.value,
      axisLine: { lineStyle: { color: '#eaeaea' } },
      axisLabel: { color: '#666666' },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#f5f5f5', type: 'dashed' } },
      axisLabel: { color: '#666666' },
    },
    series: [
      {
        name: '文章数',
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: {
          width: 3,
          color: '#2563EB',
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              {
                offset: 0,
                color: 'rgba(37, 99, 235, 0.2)', // 0% 处的颜色
              },
              {
                offset: 1,
                color: 'rgba(37, 99, 235, 0)', // 100% 处的颜色
              },
            ],
            global: false, // 缺省为 false
          },
        },
        data: yData.value,
      },
    ],
  }))

  const pieChartOptions = computed(() => ({
    tooltip: {
      trigger: 'item',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      textStyle: {
        color: '#64748B',
      },
    },
    series: [
      {
        type: 'pie',
        radius: ['45%', '75%'],
        itemStyle: {
          borderRadius: 4,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: false,
          position: 'center',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold',
          },
        },
        data: articleTypeData.value,
      },
    ],
  }))

  const timePieChartOptions = computed(() => ({
    tooltip: {
      trigger: 'item',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      textStyle: {
        color: '#64748B',
      },
    },
    series: [
      {
        type: 'pie',
        radius: ['45%', '75%'],
        itemStyle: {
          borderRadius: 4,
          borderColor: '#fff',
          borderWidth: 2,
        },
        data: commentTimeData.value,
      },
    ],
  }))

  const loadData = async () => {
    try {
      const homeRes = await getHomeStats()
      if (homeRes.code === 200) {
        const data = homeRes.data
        statsData.value = {
          articleCount: data.articleLen || 0,
          todayCount: '0篇',
          topAuthor: data.maxLikeAuthorName || '-',
          topRegion: data.maxCity || '-',
        }
        xData.value = data.xData || []
        yData.value = data.yData || []
        topComments.value = (data.topFiveComments || []).map((comment) => ({
          user: comment[5] || '',
          content: comment[4] || '',
          likes: comment[2] || 0,
        }))
        articleTypeData.value = data.userCreatedDicData || []
        commentTimeData.value = data.commentUserCreatedDicData || []
      }

      const todayRes = await getTodayStats()
      if (todayRes.code === 200) {
        statsData.value.todayCount = (todayRes.data.today_articles || 0) + '篇'
      }
    } catch (error) {
      ElMessage.error('加载数据失败')
      console.error(error)
    }
  }

  const refreshData = async () => {
    try {
      ElMessage.info('开始刷新数据...')
      const res = await refreshSpiderData({ page_num: 3 })
      if (res.code === 200) {
        const taskId = res.data?.task_id
        if (taskId) {
          ElMessage.success(`刷新任务已提交，Task ID: ${taskId}`)
        } else {
          ElMessage.success(res.msg || '刷新成功')
        }
        await loadData()
      } else {
        ElMessage.error(res.msg || '刷新失败')
      }
    } catch (error) {
      ElMessage.error('刷新失败')
    }
  }

  onMounted(() => {
    loadData()
  })
</script>

<style lang="scss" scoped>
  .home-container {
    .dashboard-toolbar {
      display: flex;
      justify-content: flex-end;
      margin-bottom: 12px;
    }

    .widget-settings {
      .settings-tip {
        color: $text-secondary;
        font-size: 13px;
        margin: 0 0 16px;
      }

      .widget-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 0;
        border-bottom: 1px solid $border-color-light;
        cursor: default;

        .drag-handle {
          cursor: grab;
          color: $text-secondary;
          font-size: 16px;
          flex-shrink: 0;
          &:active {
            cursor: grabbing;
          }
        }

        .widget-label {
          font-size: 13px;
          color: $text-primary;
          flex: 1;
        }

        .span-btn {
          flex-shrink: 0;
        }
      }
    }

    .stat-row {
      margin-bottom: 24px;
    }

    .chart-card {
      height: 100%;
      // el-card styles transferred to BaseCard, keeping custom overrides
    }

    .top-comments {
      .comment-item {
        display: flex;
        align-items: flex-start;
        padding: 16px 0;
        border-bottom: 1px solid $border-color-light;

        &:last-child {
          border-bottom: none;
        }

        .comment-avatar {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background-color: $primary-light;
          color: $primary-color;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          margin-right: 12px;
          flex-shrink: 0;
          font-size: 14px;
        }

        .comment-info {
          flex: 1;
          min-width: 0;

          .comment-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;

            .comment-user {
              font-weight: 600;
              color: $text-primary;
              font-size: 14px;
            }

            .comment-likes {
              color: $warning-color;
              font-weight: 600;
              font-size: 12px;
              display: flex;
              align-items: center;
              gap: 2px;
            }
          }

          .comment-content {
            color: $text-secondary;
            font-size: 13px;
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
          }
        }
      }
    }
  }
</style>
