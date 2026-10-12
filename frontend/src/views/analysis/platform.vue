<template>
  <div class="platform-monitor-container">
    <el-row :gutter="24" class="mb-4">
      <el-col :span="24">
        <el-card class="platform-tabs-card">
          <el-tabs v-model="activePlatform" @tab-change="handlePlatformChange">
            <el-tab-pane
              v-for="platform in platforms"
              :key="platform.id"
              :name="platform.id"
              :label="platform.label"
            >
              <template #label>
                <span class="platform-tab">
                  <span class="platform-icon">{{ platform.icon }}</span>
                  <span>{{ platform.name }}</span>
                  <el-tag v-if="platform.enabled" type="success" size="small">启用</el-tag>
                </span>
              </template>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="24" class="mb-4">
      <el-col v-for="stat in currentStats" :key="stat.label" :xs="12" :sm="6" :md="4">
        <el-card class="stat-card">
          <div v-if="statsLoading" class="region-loading stats-loading">数据加载中...</div>
          <div v-if="statsError" class="region-error stats-error">
            <span>{{ statsError }}</span>
            <el-button link type="primary" size="small" :loading="statsLoading" @click="retryStats">
              重试
            </el-button>
          </div>
          <div class="stat-content">
            <div class="stat-value">
              {{ stat.value }}
            </div>
            <div class="stat-label">
              {{ stat.label }}
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="24">
      <el-col :xs="24" :lg="16">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>{{ currentPlatformName }}内容列表</span>
              <div class="header-actions">
                <el-input
                  v-model="searchKeyword"
                  placeholder="搜索内容..."
                  :prefix-icon="Search"
                  style="width: 200px"
                  size="small"
                  clearable
                />
                <el-select
                  v-model="sentimentFilter"
                  placeholder="情感筛选"
                  size="small"
                  style="width: 100px"
                  clearable
                >
                  <el-option label="正面" value="positive" />
                  <el-option label="中性" value="neutral" />
                  <el-option label="负面" value="negative" />
                </el-select>
              </div>
            </div>
          </template>

          <div v-if="contentLoading" class="region-loading content-loading">数据加载中...</div>
          <div v-if="contentError" class="region-error content-error">
            <span>{{ contentError }}</span>
            <el-button
              link
              type="primary"
              size="small"
              :loading="contentLoading"
              @click="retryContent"
            >
              重试
            </el-button>
          </div>
          <div class="content-list">
            <div v-for="item in filteredContent" :key="item.content_id" class="content-item">
              <div class="content-header">
                <div class="author-info">
                  <el-avatar :size="36" :icon="User" />
                  <div class="author-detail">
                    <span class="author-name">
                      {{ item.author_name }}
                      <el-icon v-if="item.author_verified" class="verified-icon"
                        ><CircleCheckFilled
                      /></el-icon>
                    </span>
                    <span class="author-followers">{{ item.author_followers }} 粉丝</span>
                  </div>
                </div>
                <div class="content-meta">
                  <span class="publish-time">{{ formatTime(item.published_at) }}</span>
                </div>
              </div>

              <div class="content-body">
                <p>{{ item.content }}</p>
              </div>

              <div class="content-stats">
                <span class="stat-item">
                  <el-icon><View /></el-icon>
                  {{ formatNumber(item.view_count) }}
                </span>
                <span class="stat-item">
                  <el-icon><Star /></el-icon>
                  {{ formatNumber(item.like_count) }}
                </span>
                <span class="stat-item">
                  <el-icon><ChatDotRound /></el-icon>
                  {{ formatNumber(item.comment_count) }}
                </span>
                <span class="stat-item">
                  <el-icon><Share /></el-icon>
                  {{ formatNumber(item.repost_count) }}
                </span>
                <el-tag :type="getSentimentType(item.sentiment)" size="small" class="sentiment-tag">
                  {{ getSentimentLabel(item.sentiment) }}
                </el-tag>
              </div>

              <div v-if="item.keywords?.length" class="content-tags">
                <el-tag
                  v-for="kw in item.keywords.slice(0, 3)"
                  :key="kw"
                  size="small"
                  effect="plain"
                >
                  {{ kw }}
                </el-tag>
              </div>
            </div>

            <el-empty v-if="filteredContent.length === 0" description="暂无数据" />
          </div>

          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="pageSize"
              :total="total"
              layout="total, prev, pager, next"
              @current-change="loadData"
            />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <div v-if="compareLoading" class="region-loading compare-loading">数据加载中...</div>
        <div v-if="compareError" class="region-error compare-error">
          <span>{{ compareError }}</span>
          <el-button
            link
            type="primary"
            size="small"
            :loading="compareLoading"
            @click="retryComparison"
          >
            重试
          </el-button>
        </div>
        <el-card class="chart-card">
          <template #header>
            <span>各平台数据对比</span>
          </template>
          <BaseChart ref="compareChartRef" :options="compareChartOptions" height="300px" />
          <el-empty
            v-if="!compareLoading && !compareError && !hasCompareData"
            description="暂无对比数据"
            :image-size="60"
            class="chart-empty compare-empty"
          />
        </el-card>

        <el-card class="trend-card mt-4">
          <template #header>
            <span>情感分布</span>
          </template>
          <BaseChart ref="sentimentChartRef" :options="sentimentChartOptions" height="250px" />
          <el-empty
            v-if="!compareLoading && !compareError && !hasSentimentData"
            description="暂无情感分布数据"
            :image-size="60"
            class="chart-empty sentiment-empty"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted } from 'vue'
  import {
    Search,
    User,
    View,
    Star,
    ChatDotRound,
    Share,
    CircleCheckFilled,
  } from '@element-plus/icons-vue'
  import BaseChart from '@/components/Charts/BaseChart.vue'
  import { getPlatformData, getPlatformStats, comparePlatforms } from '@/api/platform'

  const activePlatform = ref('weibo')
  const demoMode = import.meta.env.VITE_DEMO_MODE === 'true'
  const platforms = ref([
    { id: 'weibo', name: '微博', icon: '📱', enabled: true, label: '微博' },
    { id: 'wechat', name: '微信公众号', icon: '💬', enabled: true, label: '微信公众号' },
    { id: 'douyin', name: '抖音', icon: '🎵', enabled: true, label: '抖音' },
    { id: 'zhihu', name: '知乎', icon: '💡', enabled: true, label: '知乎' },
  ])

  const currentPlatformName = computed(() => {
    const p = platforms.value.find((p) => p.id === activePlatform.value)
    return p?.name || '未知平台'
  })

  const contentList = ref([])
  const currentPage = ref(1)
  const pageSize = ref(10)
  const total = ref(0)
  const searchKeyword = ref('')
  const sentimentFilter = ref('')

  const platformStats = ref({})
  const comparisonData = ref({})

  // U-2（#65）：三路 fetch 各自的 loading / 错误态（#62 同款语义）。
  // #19：失败只写错误态，从不清空已渲染旧数据、不伪装空态。
  const contentLoading = ref(false)
  const statsLoading = ref(false)
  const compareLoading = ref(false)
  const contentError = ref('')
  const statsError = ref('')
  const compareError = ref('')

  const currentStats = computed(() => {
    const stats = platformStats.value[activePlatform.value] || {}
    return [
      { label: '内容总数', value: formatNumber(stats.total_content || 0) },
      { label: '用户总数', value: formatNumber(stats.total_users || 0) },
      {
        label: '互动总量',
        value: formatNumber((stats.total_likes || 0) + (stats.total_comments || 0)),
      },
      { label: '增长率', value: `${((stats.growth_rate || 0) * 100).toFixed(1)}%` },
    ]
  })

  const filteredContent = computed(() => {
    let list = contentList.value

    if (searchKeyword.value) {
      const kw = searchKeyword.value.toLowerCase()
      list = list.filter(
        (item) =>
          item.content.toLowerCase().includes(kw) || item.author_name.toLowerCase().includes(kw)
      )
    }

    if (sentimentFilter.value) {
      list = list.filter((item) => item.sentiment === sentimentFilter.value)
    }

    return list
  })

  // U-12（#85）：对比/情感图改读 comparisonData 真实口径。
  // 后端 POST /api/platform/compare 返回 data.comparison[platform] =
  // {total_content, total_likes, total_comments, total_views, avg_*,
  //  sentiment_distribution{positive,neutral,negative}, ...}。
  // 缺失平台按 0 兜底；空 comparison 时图表画零值 + 模板显式空态
  // （#52 教训：空数据不断言崩溃；此前写死的假常量已删除）。
  const COMPARE_PLATFORMS = [
    { id: 'weibo', name: '微博' },
    { id: 'wechat', name: '微信' },
    { id: 'douyin', name: '抖音' },
    { id: 'zhihu', name: '知乎' },
  ]
  const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : 0)

  const compareChartOptions = computed(() => {
    const pick = (id, key) => num(comparisonData.value?.[id]?.[key])
    return {
      tooltip: { trigger: 'axis' },
      legend: { data: ['内容数', '点赞数', '评论数'], textStyle: { fontSize: 10 } },
      xAxis: {
        type: 'category',
        data: COMPARE_PLATFORMS.map((p) => p.name),
        axisLabel: { fontSize: 10 },
      },
      yAxis: { type: 'value' },
      series: [
        {
          name: '内容数',
          type: 'bar',
          data: COMPARE_PLATFORMS.map((p) => pick(p.id, 'total_content')),
        },
        {
          name: '点赞数',
          type: 'bar',
          data: COMPARE_PLATFORMS.map((p) => pick(p.id, 'total_likes')),
        },
        {
          name: '评论数',
          type: 'bar',
          data: COMPARE_PLATFORMS.map((p) => pick(p.id, 'total_comments')),
        },
      ],
    }
  })

  const sentimentTotals = computed(() => {
    const totals = { positive: 0, neutral: 0, negative: 0 }
    for (const p of COMPARE_PLATFORMS) {
      const dist = comparisonData.value?.[p.id]?.sentiment_distribution
      if (!dist) continue
      for (const key of Object.keys(totals)) {
        totals[key] += num(dist[key])
      }
    }
    return totals
  })

  const hasCompareData = computed(() =>
    COMPARE_PLATFORMS.some((p) => {
      const c = comparisonData.value?.[p.id]
      return c && num(c.total_content) + num(c.total_likes) + num(c.total_comments) > 0
    })
  )

  const hasSentimentData = computed(() => Object.values(sentimentTotals.value).some((v) => v > 0))

  const sentimentChartOptions = computed(() => ({
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'left' },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        data: [
          {
            value: sentimentTotals.value.positive,
            name: '正面',
            itemStyle: { color: '#10B981' },
          },
          {
            value: sentimentTotals.value.neutral,
            name: '中性',
            itemStyle: { color: '#64748B' },
          },
          {
            value: sentimentTotals.value.negative,
            name: '负面',
            itemStyle: { color: '#EF4444' },
          },
        ],
        label: { fontSize: 10 },
      },
    ],
  }))

  const formatNumber = (num) => {
    if (num >= 10000) return (num / 10000).toFixed(1) + 'w'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
    return num.toString()
  }

  const formatTime = (timeStr) => {
    if (!timeStr) return ''
    const date = new Date(timeStr)
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getSentimentType = (sentiment) => {
    const types = { positive: 'success', neutral: 'info', negative: 'danger' }
    return types[sentiment] || 'info'
  }

  const getSentimentLabel = (sentiment) => {
    const labels = { positive: '正面', neutral: '中性', negative: '负面' }
    return labels[sentiment] || '未知'
  }

  const loadData = async () => {
    contentLoading.value = true
    contentError.value = ''
    try {
      const res = await getPlatformData(activePlatform.value, {
        page: currentPage.value,
        page_size: pageSize.value,
        demo: demoMode,
      })

      if (res.code === 200) {
        contentList.value = res.data.data
        total.value = res.data.pagination.total
      } else {
        contentError.value = res.msg || '数据加载失败，已保留旧数据'
      }
    } catch (error) {
      console.error('加载数据失败:', error)
      contentError.value = '数据加载失败，已保留旧数据'
    } finally {
      contentLoading.value = false
    }
  }

  const loadStats = async () => {
    statsLoading.value = true
    statsError.value = ''
    try {
      const res = await getPlatformStats('all')
      if (res.code === 200) {
        platformStats.value = res.data
      } else {
        statsError.value = res.msg || '统计加载失败，已保留旧数据'
      }
    } catch (error) {
      console.error('加载统计失败:', error)
      statsError.value = '统计加载失败，已保留旧数据'
    } finally {
      statsLoading.value = false
    }
  }

  const loadComparison = async () => {
    compareLoading.value = true
    compareError.value = ''
    try {
      const res = await comparePlatforms(['weibo', 'wechat', 'douyin', 'zhihu'])
      if (res.code === 200) {
        comparisonData.value = res.data.comparison
      } else {
        compareError.value = res.msg || '对比数据加载失败'
      }
    } catch (error) {
      console.error('加载对比数据失败:', error)
      compareError.value = '对比数据加载失败'
    } finally {
      compareLoading.value = false
    }
  }

  const retryContent = () => loadData()
  const retryStats = () => loadStats()
  const retryComparison = () => loadComparison()

  const handlePlatformChange = () => {
    currentPage.value = 1
    loadData()
  }

  onMounted(() => {
    loadData()
    loadStats()
    loadComparison()
  })
</script>

<style lang="scss" scoped>
  .platform-monitor-container {
    .region-loading {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      margin-bottom: 12px;
      font-size: 13px;
      color: var(--el-text-color-secondary);
    }

    .region-error {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 12px;
      padding: 8px 12px;
      border-radius: 8px;
      background: rgba(239, 68, 68, 0.08);
      border: 1px dashed rgba(239, 68, 68, 0.4);
      color: var(--el-color-danger);
      font-size: 13px;
      line-height: 1.4;
    }

    .platform-tabs-card {
      .platform-tab {
        display: flex;
        align-items: center;
        gap: 6px;

        .platform-icon {
          font-size: 16px;
        }
      }
    }

    .stat-card {
      margin-bottom: 16px;

      .stat-content {
        text-align: center;

        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: var(--el-color-primary);
        }

        .stat-label {
          font-size: 13px;
          color: var(--el-text-color-secondary);
          margin-top: 4px;
        }
      }
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-actions {
        display: flex;
        gap: 12px;
      }
    }

    .content-list {
      .content-item {
        padding: 16px;
        border-bottom: 1px solid var(--el-border-color-lighter);

        &:last-child {
          border-bottom: none;
        }

        .content-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;

          .author-info {
            display: flex;
            align-items: center;
            gap: 12px;

            .author-detail {
              display: flex;
              flex-direction: column;

              .author-name {
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 4px;

                .verified-icon {
                  color: var(--el-color-primary);
                }
              }

              .author-followers {
                font-size: 12px;
                color: var(--el-text-color-secondary);
              }
            }
          }

          .content-meta {
            .publish-time {
              font-size: 12px;
              color: var(--el-text-color-secondary);
            }
          }
        }

        .content-body {
          margin-bottom: 12px;

          p {
            margin: 0;
            line-height: 1.6;
          }
        }

        .content-stats {
          display: flex;
          align-items: center;
          gap: 16px;
          margin-bottom: 8px;

          .stat-item {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 13px;
            color: var(--el-text-color-secondary);
          }

          .sentiment-tag {
            margin-left: auto;
          }
        }

        .content-tags {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }
      }
    }

    .pagination-container {
      margin-top: 16px;
      display: flex;
      justify-content: flex-end;
    }

    .mt-4 {
      margin-top: 16px;
    }
    .mb-4 {
      margin-bottom: 16px;
    }

    .chart-empty {
      margin-top: 8px;
    }
  }
</style>
