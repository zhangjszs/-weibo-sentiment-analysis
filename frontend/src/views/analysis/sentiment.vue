<template>
  <div class="sentiment-analysis-container">
    <el-row
      :gutter="24"
      class="stat-row"
    >
      <el-col
        :xs="24"
        :sm="8"
      >
        <StatCard
          :value="sentimentStats.positive"
          label="正面评价"
          icon="CircleCheck"
          bg-color="#ECFDF5"
          icon-color="#059669"
        />
      </el-col>
      <el-col
        :xs="24"
        :sm="8"
      >
        <StatCard
          :value="sentimentStats.neutral"
          label="中性评价"
          icon="Remove"
          bg-color="#F1F5F9"
          icon-color="#64748B"
        />
      </el-col>
      <el-col
        :xs="24"
        :sm="8"
      >
        <StatCard
          :value="sentimentStats.negative"
          label="负面评价"
          icon="CircleClose"
          bg-color="#FEF2F2"
          icon-color="#DC2626"
        />
      </el-col>
    </el-row>

    <el-row
      :gutter="24"
      class="mb-4"
    >
      <el-col
        :xs="24"
        :lg="8"
      >
        <el-card class="chart-card">
          <template #header>
            <span class="header-title">舆情情感分布</span>
          </template>
          <BaseChart
            ref="sentimentPieRef"
            :options="sentimentPieOptions"
            height="300px"
            @click="handlePieClick"
          />
        </el-card>
      </el-col>

      <el-col
        :xs="24"
        :lg="8"
      >
        <el-card class="chart-card">
          <template #header>
            <span class="header-title">情感类型分布</span>
          </template>
          <BaseChart
            ref="emotionBarRef"
            :options="emotionBarOptions"
            height="300px"
          />
        </el-card>
      </el-col>

      <el-col
        :xs="24"
        :lg="8"
      >
        <el-card class="chart-card">
          <template #header>
            <span class="header-title">情感得分分布</span>
          </template>
          <BaseChart
            ref="scoreDistRef"
            :options="scoreDistOptions"
            height="300px"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-row
      :gutter="24"
      class="mb-4"
    >
      <el-col :span="24">
        <el-card class="chart-card">
          <template #header>
            <span class="header-title">舆情趋势变化</span>
          </template>
          <BaseChart
            ref="trendChartRef"
            :options="trendChartOptions"
            height="350px"
            @click="handleTrendClick"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-row
      :gutter="24"
      class="mb-4"
    >
      <el-col :span="24">
        <el-card class="chart-card">
          <template #header>
            <span class="header-title">关键词云</span>
          </template>
          <div class="keywords-cloud">
            <div
              v-for="(keyword, index) in keywords"
              :key="index"
              class="keyword-item"
              :style="{
                fontSize: Math.min(Math.max(12 + keyword.weight, 12), 32) + 'px',
                color: keyword.color,
                opacity: 0.8 + keyword.weight / 200,
              }"
            >
              {{ keyword.text }}
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="24">
      <el-col :span="24">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span class="header-title">舆情详情列表</span>
              <div class="header-actions">
                <el-select
                  v-model="filters.sentiment"
                  placeholder="情感"
                  clearable
                  size="small"
                  style="width: 120px"
                >
                  <el-option
                    label="正面"
                    value="正面"
                  />
                  <el-option
                    label="中性"
                    value="中性"
                  />
                  <el-option
                    label="负面"
                    value="负面"
                  />
                </el-select>
                <el-input
                  v-model="filters.keyword"
                  placeholder="内容关键词"
                  clearable
                  size="small"
                  style="width: 220px"
                />
                <el-date-picker
                  v-model="filters.dateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  value-format="YYYY-MM-DD"
                  size="small"
                />
                <el-button
                  plain
                  size="small"
                  @click="resetFilters"
                >
                  重置
                </el-button>
                <el-button
                  type="primary"
                  plain
                  size="small"
                  :icon="Refresh"
                  @click="loadData"
                >
                  刷新数据
                </el-button>
              </div>
            </div>
          </template>
          <el-table
            :data="pagedList"
            :loading="loading"
            style="width: 100%"
          >
            <el-table-column
              prop="id"
              label="ID"
              width="80"
              align="center"
            />
            <el-table-column
              prop="content"
              label="内容"
              min-width="300"
              show-overflow-tooltip
            />
            <el-table-column
              prop="sentiment"
              label="情感倾向"
              width="120"
              align="center"
            >
              <template #default="{ row }">
                <el-tag
                  :type="getSentimentType(row.sentiment)"
                  effect="plain"
                  round
                >
                  {{ row.sentiment }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              prop="score"
              label="情感分数"
              width="120"
              align="center"
            >
              <template #default="{ row }">
                <span :class="getScoreClass(row.score)">{{ row.score }}</span>
              </template>
            </el-table-column>
            <el-table-column
              prop="emotion"
              label="情感类型"
              width="120"
              align="center"
            >
              <template #default="{ row }">
                <el-tag
                  :type="getEmotionType(row.emotion)"
                  effect="plain"
                  round
                  size="small"
                >
                  {{ row.emotion || '无感' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              prop="keywords"
              label="关键词"
              width="180"
              align="center"
            >
              <template #default="{ row }">
                <div class="keywords-list">
                  <el-tag
                    v-for="(keyword, index) in row.keywords.slice(0, 3)"
                    :key="index"
                    size="small"
                    effect="light"
                    class="keyword-tag"
                  >
                    {{ keyword }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column
              prop="reasoning"
              label="分析理由"
              min-width="300"
            >
              <template #default="{ row }">
                <el-tooltip
                  :content="row.reasoning"
                  placement="top"
                  :disabled="!row.reasoning"
                >
                  <div class="reasoning-text">
                    {{ row.reasoning ? row.reasoning.substring(0, 50) + (row.reasoning.length > 50 ? '...' : '') : '无' }}
                  </div>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column
              prop="analysis_source"
              label="分析来源"
              width="120"
              align="center"
            >
              <template #default="{ row }">
                <el-tag
                  type="info"
                  size="small"
                >
                  {{ row.analysis_source || 'unknown' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              prop="source"
              label="数据来源"
              width="100"
              align="center"
            >
              <template #default="{ row }">
                <el-tag
                  type="success"
                  size="small"
                >
                  {{ row.source }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              prop="time"
              label="时间"
              width="180"
              align="center"
            />
          </el-table>

          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="filteredTotal"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handlePageChange"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
  import { ref, onMounted, computed } from 'vue'
  import { CircleCheck, Remove, CircleClose, Refresh } from '@element-plus/icons-vue'
  import { ElMessage } from 'element-plus'
  import StatCard from '@/components/Common/StatCard.vue'
  import BaseChart from '@/components/Charts/BaseChart.vue'
  import { getYuqingData } from '@/api/stats'

  const loading = ref(false)
  const rawList = ref([])
  const sentimentStats = ref({
    positive: 0,
    neutral: 0,
    negative: 0,
  })
  const sentimentData = ref([])
  const trendData = ref([])
  const keywords = ref([])

  const currentPage = ref(1)
  const pageSize = ref(10)
  const total = ref(0)
  const filters = ref({ sentiment: '', keyword: '', dateRange: [] })

  const sentimentPieRef = ref(null)
  const trendChartRef = ref(null)
  const emotionBarRef = ref(null)
  const scoreDistRef = ref(null)

  const sentimentPieOptions = computed(() => ({
    tooltip: { trigger: 'item' },
    legend: {
      orient: 'vertical',
      right: 10,
      textStyle: { color: '#64748B' },
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        itemStyle: {
          borderRadius: 4,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: { show: false },
        data: [
          { value: sentimentStats.value.positive, name: '正面', itemStyle: { color: '#10B981' } }, // Emerald 500
          { value: sentimentStats.value.neutral, name: '中性', itemStyle: { color: '#64748B' } }, // Slate 500
          { value: sentimentStats.value.negative, name: '负面', itemStyle: { color: '#EF4444' } }, // Red 500
        ],
      },
    ],
  }))

  const trendChartOptions = computed(() => ({
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
      data: trendData.value.dates || [],
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
        name: '正面',
        type: 'line',
        smooth: true,
        symbol: 'none',
        data: trendData.value.positive || [],
        itemStyle: { color: '#10B981' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(16, 185, 129, 0.2)' },
              { offset: 1, color: 'rgba(16, 185, 129, 0)' },
            ],
          },
        },
      },
      {
        name: '中性',
        type: 'line',
        smooth: true,
        symbol: 'none',
        data: trendData.value.neutral || [],
        itemStyle: { color: '#64748B' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(100, 116, 139, 0.2)' },
              { offset: 1, color: 'rgba(100, 116, 139, 0)' },
            ],
          },
        },
      },
      {
        name: '负面',
        type: 'line',
        smooth: true,
        symbol: 'none',
        data: trendData.value.negative || [],
        itemStyle: { color: '#EF4444' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(239, 68, 68, 0.2)' },
              { offset: 1, color: 'rgba(239, 68, 68, 0)' },
            ],
          },
        },
      },
    ],
  }))

  const emotionBarOptions = computed(() => {
    // 计算情感类型分布
    const emotionCounts = {}
    rawList.value.forEach(item => {
      const emotion = item.emotion || '无感'
      emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1
    })
    
    const emotions = Object.keys(emotionCounts)
    const counts = Object.values(emotionCounts)
    
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: emotions,
        axisLabel: {
          rotate: 45,
          color: '#666666'
        },
        axisLine: {
          lineStyle: {
            color: '#eaeaea'
          }
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          color: '#666666'
        },
        splitLine: {
          lineStyle: {
            color: '#f5f5f5',
            type: 'dashed'
          }
        }
      },
      series: [
        {
          name: '情感类型',
          type: 'bar',
          data: counts,
          itemStyle: {
            color: function(params) {
              const colorMap = {
                '喜悦': '#10B981',
                '感动': '#34D399',
                '兴奋': '#6EE7B7',
                '期待': '#A7F3D0',
                '愤怒': '#EF4444',
                '悲伤': '#FCA5A5',
                '失望': '#F87171',
                '厌恶': '#DC2626',
                '焦虑': '#F59E0B',
                '恐惧': '#FBBF24',
                '惊讶': '#FCD34D',
                '无奈': '#60A5FA',
                '讽刺': '#93C5FD',
                '平静': '#BFDBFE',
                '无感': '#9CA3AF'
              }
              return colorMap[params.name] || '#9CA3AF'
            }
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }
  })

  const scoreDistOptions = computed(() => {
    // 计算情感得分分布
    const scoreRanges = {
      '0.0-0.2': 0,
      '0.2-0.4': 0,
      '0.4-0.6': 0,
      '0.6-0.8': 0,
      '0.8-1.0': 0
    }
    
    rawList.value.forEach(item => {
      const score = item.score || 0.5
      if (score < 0.2) {
        scoreRanges['0.0-0.2']++
      } else if (score < 0.4) {
        scoreRanges['0.2-0.4']++
      } else if (score < 0.6) {
        scoreRanges['0.4-0.6']++
      } else if (score < 0.8) {
        scoreRanges['0.6-0.8']++
      } else {
        scoreRanges['0.8-1.0']++
      }
    })
    
    const ranges = Object.keys(scoreRanges)
    const counts = Object.values(scoreRanges)
    
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: ranges,
        axisLabel: {
          color: '#666666'
        },
        axisLine: {
          lineStyle: {
            color: '#eaeaea'
          }
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          color: '#666666'
        },
        splitLine: {
          lineStyle: {
            color: '#f5f5f5',
            type: 'dashed'
          }
        }
      },
      series: [
        {
          name: '得分分布',
          type: 'bar',
          data: counts,
          itemStyle: {
            color: function(params) {
              const colorMap = {
                '0.0-0.2': '#EF4444',
                '0.2-0.4': '#F87171',
                '0.4-0.6': '#64748B',
                '0.6-0.8': '#34D399',
                '0.8-1.0': '#10B981'
              }
              return colorMap[params.name] || '#64748B'
            }
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }
  })

  const getSentimentType = (sentiment) => {
    if (!sentiment) return 'info'
    const lower = sentiment.toLowerCase()
    if (lower.includes('正面') || lower.includes('positive')) return 'success'
    if (lower.includes('负面') || lower.includes('negative')) return 'danger'
    return 'info'
  }

  const getScoreClass = (score) => {
    if (score > 0.6) return 'text-success'
    if (score < 0.4) return 'text-danger'
    return 'text-muted'
  }

  const getEmotionType = (emotion) => {
    const emotionMap = {
      '喜悦': 'success',
      '感动': 'success',
      '兴奋': 'success',
      '期待': 'success',
      '愤怒': 'danger',
      '悲伤': 'danger',
      '失望': 'danger',
      '厌恶': 'danger',
      '焦虑': 'warning',
      '恐惧': 'warning',
      '惊讶': 'warning',
      '无奈': 'info',
      '讽刺': 'info',
      '平静': 'info',
      '无感': 'info'
    }
    return emotionMap[emotion] || 'info'
  }

  const filteredList = computed(() => {
    const keyword = (filters.value.keyword || '').trim()
    const sentiment = filters.value.sentiment || ''
    const [start, end] = filters.value.dateRange || []

    const matchDate = (val) => {
      if (!start && !end) return true
      if (!val) return false
      const dateStr = String(val).slice(0, 10)
      if (start && dateStr < start) return false
      if (end && dateStr > end) return false
      return true
    }

    return (rawList.value || []).filter((x) => {
      if (sentiment && x.sentiment !== sentiment) return false
      if (keyword && !String(x.content || '').includes(keyword)) return false
      if (!matchDate(x.time)) return false
      return true
    })
  })

  const filteredTotal = computed(() => filteredList.value.length)

  const pagedList = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return filteredList.value.slice(start, end)
  })

  const loadData = async () => {
    loading.value = true
    try {
      const res = await getYuqingData()

      if (res.code === 200) {
        const data = res.data
        sentimentStats.value = data.stats || { positive: 0, neutral: 0, negative: 0 }
        rawList.value = data.list || []
        trendData.value = data.trend || { dates: [], positive: [], neutral: [], negative: [] }
        keywords.value = data.keywords || []
        total.value = data.total || 0
        currentPage.value = 1
      }
    } catch (error) {
      ElMessage.error('加载数据失败')
    } finally {
      loading.value = false
    }
  }

  const handleSizeChange = (size) => {
    pageSize.value = size
    currentPage.value = 1
  }

  const handlePageChange = (page) => {
    currentPage.value = page
  }

  const resetFilters = () => {
    filters.value.sentiment = ''
    filters.value.keyword = ''
    filters.value.dateRange = []
    currentPage.value = 1
  }

  const handlePieClick = (params) => {
    const name = params?.name
    if (!name || typeof name !== 'string') return
    filters.value.sentiment = name
    currentPage.value = 1
  }

  const handleTrendClick = (params) => {
    const date = params?.name
    if (!date || typeof date !== 'string') return
    filters.value.dateRange = [date, date]
    currentPage.value = 1
  }

  onMounted(() => {
    loadData()
  })
</script>

<style lang="scss" scoped>
  .sentiment-analysis-container {
    .stat-row {
      margin-bottom: 24px;
    }

    .chart-card {
      height: 100%;
      display: flex;
      flex-direction: column;

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .header-actions {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
        justify-content: flex-end;
      }

      .header-title {
        font-size: 16px;
        font-weight: 600;
        color: $text-primary;
      }
    }

    .keywords-cloud {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      align-items: center;
      gap: 16px;
      padding: 32px;
      min-height: 200px;

      .keyword-item {
        padding: 6px 16px;
        border-radius: 20px;
        background: rgba(241, 245, 249, 0.5); // Slate 100
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: 500;

        &:hover {
          transform: scale(1.1) translateY(-2px);
          background: #fff;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
      }
    }

    .text-success {
      color: $success-color;
      font-weight: bold;
    }
    .text-danger {
      color: $danger-color;
      font-weight: bold;
    }
    .text-muted {
      color: $text-secondary;
    }

    .keywords-list {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      justify-content: center;
    }

    .keyword-tag {
      margin: 2px 0;
    }

    .reasoning-text {
      font-size: 13px;
      line-height: 1.4;
      color: $text-secondary;
      cursor: help;
      transition: color 0.3s;

      &:hover {
        color: $primary-color;
      }
    }

    .pagination-wrapper {
      margin-top: 24px;
      display: flex;
      justify-content: flex-end;
    }
  }
</style>
