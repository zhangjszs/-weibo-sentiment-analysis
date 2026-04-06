<template>
  <div class="article-analysis-container">
    <el-row
      :gutter="24"
      class="mb-4"
    >
      <el-col :span="24">
        <el-card class="chart-card">
          <template #header>
            <span class="header-title">文章发布时间分布</span>
          </template>
          <BaseChart
            ref="timeChartRef"
            :options="timeChartOptions"
            height="400px"
            @click="handleTimeChartClick"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-row
      :gutter="24"
      class="mb-4"
    >
      <el-col
        :xs="24"
        :lg="12"
      >
        <el-card class="chart-card">
          <template #header>
            <span class="header-title">文章类型分布</span>
          </template>
          <BaseChart
            ref="typeChartRef"
            :options="typeChartOptions"
            height="350px"
            @click="handleTypeChartClick"
          />
        </el-card>
      </el-col>

      <el-col
        :xs="24"
        :lg="12"
      >
        <el-card class="chart-card">
          <template #header>
            <span class="header-title">文章情感分布</span>
          </template>
          <BaseChart
            ref="sentimentChartRef"
            :options="sentimentChartOptions"
            height="350px"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="24">
      <el-col :span="24">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span class="header-title">热门文章排行</span>
              <el-button
                type="primary"
                plain
                size="small"
                @click="loadData"
              >
                刷新数据
              </el-button>
            </div>
          </template>
          <el-table
            :data="articleList"
            :loading="loading"
            style="width: 100%"
          >
            <el-table-column
              prop="id"
              label="文章ID"
              width="100"
              align="center"
            />
            <el-table-column
              prop="user"
              label="发布用户"
              width="150"
            >
              <template #default="{ row }">
                <div class="user-cell">
                  <el-avatar
                    :size="24"
                    :style="{ backgroundColor: '#2563EB', color: '#fff' }"
                  >
                    {{
                      row.user.charAt(0)
                    }}
                  </el-avatar>
                  <span>{{ row.user }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column
              prop="content"
              label="文章内容"
              min-width="400"
              show-overflow-tooltip
            />
            <el-table-column
              prop="time"
              label="发布时间"
              width="180"
              align="center"
            />
            <el-table-column
              prop="likes"
              label="点赞数"
              width="120"
              align="center"
            >
              <template #default="{ row }">
                <span class="stat-text likes">👍 {{ row.likes }}</span>
              </template>
            </el-table-column>
            <el-table-column
              prop="reposts"
              label="转发数"
              width="120"
              align="center"
            >
              <template #default="{ row }">
                <span class="stat-text reposts">🔁 {{ row.reposts }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            文章列表
          </div>
          <div class="header-actions">
            <el-button
              type="default"
              plain
              size="small"
              :icon="Download"
              :disabled="listData.length === 0"
              @click="exportList"
            >
              导出 CSV
            </el-button>
            <el-button
              type="default"
              plain
              size="small"
              :icon="Refresh"
              @click="loadList"
            >
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-form
        :inline="true"
        class="filter-form"
        @submit.prevent
      >
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            placeholder="内容关键词"
            clearable
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select
            v-model="filters.type"
            placeholder="全部"
            clearable
            style="width: 180px"
          >
            <el-option
              v-for="t in typeOptions"
              :key="t"
              :label="t"
              :value="t"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :icon="Search"
            @click="applyFilters"
          >
            查询
          </el-button>
          <el-button @click="resetFilters">
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <el-table
        :data="listData"
        :loading="listLoading"
        style="width: 100%"
      >
        <el-table-column
          prop="id"
          label="ID"
          width="120"
          align="center"
        />
        <el-table-column
          prop="authorName"
          label="作者"
          width="160"
          show-overflow-tooltip
        />
        <el-table-column
          prop="region"
          label="地区"
          width="120"
          align="center"
        />
        <el-table-column
          prop="type"
          label="类型"
          width="110"
          align="center"
        />
        <el-table-column
          prop="created_at"
          label="时间"
          width="180"
          align="center"
        />
        <el-table-column
          prop="content"
          label="内容"
          min-width="360"
          show-overflow-tooltip
        />
        <el-table-column
          prop="likeNum"
          label="赞"
          width="90"
          align="center"
        />
        <el-table-column
          prop="commentsLen"
          label="评"
          width="90"
          align="center"
        />
        <el-table-column
          prop="reposts_count"
          label="转"
          width="90"
          align="center"
        />
        <el-table-column
          label="操作"
          width="160"
          fixed="right"
          align="center"
        >
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              :icon="View"
              @click="openDetail(row)"
            >
              查看
            </el-button>
            <el-button
              :type="favoriteMap[row.id] ? 'warning' : 'default'"
              link
              :icon="favoriteMap[row.id] ? StarFilled : Star"
              @click="toggleFavorite(row)"
            >
              {{ favoriteMap[row.id] ? '已收藏' : '收藏' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.limit"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="detailVisible"
      title="文章详情"
      width="760px"
    >
      <div
        v-if="detailRow"
        class="detail"
      >
        <div class="detail-row">
          <div class="detail-label">
            作者
          </div>
          <div class="detail-value">
            {{ detailRow.authorName || '-' }}
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">
            时间
          </div>
          <div class="detail-value">
            {{ detailRow.created_at || '-' }}
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">
            地区
          </div>
          <div class="detail-value">
            {{ detailRow.region || '-' }}
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">
            指标
          </div>
          <div class="detail-value">
            赞 {{ detailRow.likeNum || 0 }} · 评 {{ detailRow.commentsLen || 0 }} · 转
            {{ detailRow.reposts_count || 0 }}
          </div>
        </div>
        <div class="detail-content">
          {{ detailRow.content || '' }}
        </div>
        <div
          v-if="detailRow.detailUrl"
          class="detail-link"
        >
          <el-link
            :href="detailRow.detailUrl"
            target="_blank"
            type="primary"
          >
            打开微博链接
          </el-link>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
  import { ref, onMounted, computed } from 'vue'
  import { ElMessage } from 'element-plus'
  import { Search, Refresh, Download, View, Star, StarFilled } from '@element-plus/icons-vue'
  import BaseChart from '@/components/Charts/BaseChart.vue'
  import { getArticleData } from '@/api/stats'
  import { getArticles } from '@/api/content'
  import { addFavorite, removeFavorite, batchCheckFavorites } from '@/api/favorites'
  import { downloadCsv } from '@/utils'

  const loading = ref(false)
  const articleList = ref([])
  const timeData = ref({ x: [], y: [] })
  const typeData = ref([])
  const sentimentData = ref([])

  const timeChartRef = ref(null)
  const typeChartRef = ref(null)
  const sentimentChartRef = ref(null)
  const typeOptions = ref([])

  const timeChartOptions = computed(() => ({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: '#E2E8F0',
      textStyle: { color: '#1E293B' },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: timeData.value.x,
      axisLine: { lineStyle: { color: '#E2E8F0' } },
      axisLabel: { color: '#64748B' },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#F1F5F9' } },
      axisLabel: { color: '#64748B' },
    },
    series: [
      {
        name: '发布数量',
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 3, color: '#2563EB' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(37, 99, 235, 0.2)' },
              { offset: 1, color: 'rgba(37, 99, 235, 0)' },
            ],
          },
        },
        data: timeData.value.y,
      },
    ],
  }))

  const typeChartOptions = computed(() => ({
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
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: { show: false },
        data: typeData.value,
      },
    ],
  }))

  const sentimentChartOptions = computed(() => ({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: ['正面', '中性', '负面'],
      axisLine: { lineStyle: { color: '#E2E8F0' } },
      axisLabel: { color: '#64748B' },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#F1F5F9' } },
      axisLabel: { color: '#64748B' },
    },
    series: [
      {
        type: 'bar',
        barWidth: '40%',
        data: sentimentData.value,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: (params) => {
            const colors = ['#10B981', '#64748B', '#EF4444'] // Emerald, Slate, Red
            return colors[params.dataIndex] || '#2563EB'
          },
        },
      },
    ],
  }))

  const loadData = async () => {
    loading.value = true
    try {
      const res = await getArticleData()
      if (res.code === 200) {
        const data = res.data
        timeData.value = { x: data.xData || [], y: data.yData || [] }
        typeData.value = data.typeData || []
        sentimentData.value = data.sentimentData || [0, 0, 0]
        typeOptions.value = (data.typeList || [])
          .map((x) => (Array.isArray(x) ? x[0] : x))
          .filter(Boolean)
        articleList.value = (data.articleList || []).map((item) => ({
          id: item[0],
          user: item[5],
          content: item[4],
          time: item[1],
          likes: item[2],
          reposts: item[3] || 0,
        }))
      }
    } catch (error) {
      ElMessage.error('加载数据失败')
    } finally {
      loading.value = false
    }
  }

  const listLoading = ref(false)
  const listData = ref([])
  const pagination = ref({ page: 1, limit: 10, total: 0 })
  const filters = ref({ keyword: '', type: '', dateRange: [] })

  const detailVisible = ref(false)
  const detailRow = ref(null)
  const favoriteMap = ref({})

  const normalizeDates = () => {
    const [start, end] = filters.value.dateRange || []
    return {
      start_time: start || '',
      end_time: end || '',
    }
  }

  const loadList = async () => {
    listLoading.value = true
    try {
      const { start_time, end_time } = normalizeDates()
      const res = await getArticles({
        page: pagination.value.page,
        limit: pagination.value.limit,
        keyword: filters.value.keyword || '',
        type: filters.value.type || '',
        start_time,
        end_time,
      })
      if (res.code === 200) {
        const data = res.data || {}
        listData.value = data.list || []
        pagination.value.total = data.total || 0
      }
    } catch (e) {
      ElMessage.error('加载文章列表失败')
    } finally {
      listLoading.value = false
    }

    // Batch check favorites for loaded articles
    const ids = listData.value.map((a) => String(a.id)).filter(Boolean)
    if (ids.length) {
      try {
        const favRes = await batchCheckFavorites(ids)
        if (favRes.code === 200) {
          favoriteMap.value = { ...favoriteMap.value, ...favRes.data.favorites }
        }
      } catch {
        /* ignore */
      }
    }
  }

  const applyFilters = () => {
    pagination.value.page = 1
    loadList()
  }

  const resetFilters = () => {
    filters.value.keyword = ''
    filters.value.type = ''
    filters.value.dateRange = []
    pagination.value.page = 1
    loadList()
  }

  const handlePageChange = (page) => {
    pagination.value.page = page
    loadList()
  }

  const handleSizeChange = (size) => {
    pagination.value.limit = size
    pagination.value.page = 1
    loadList()
  }

  const openDetail = (row) => {
    detailRow.value = row
    detailVisible.value = true
  }

  const exportList = () => {
    const headers = ['ID', '作者', '地区', '类型', '时间', '内容', '赞', '评', '转', '链接']
    const rows = listData.value.map((a) => [
      a.id,
      a.authorName,
      a.region,
      a.type,
      a.created_at,
      a.content,
      a.likeNum,
      a.commentsLen,
      a.reposts_count,
      a.detailUrl,
    ])
    downloadCsv(`articles_${Date.now()}.csv`, headers, rows)
  }

  const handleTimeChartClick = (params) => {
    const date = params?.name
    if (!date || typeof date !== 'string') return
    filters.value.dateRange = [date, date]
    applyFilters()
  }

  const handleTypeChartClick = (params) => {
    const t = params?.name
    if (!t || typeof t !== 'string') return
    filters.value.type = t
    applyFilters()
  }

  onMounted(() => {
    loadData()
    loadList()
  })

  const toggleFavorite = async (row) => {
    const id = String(row.id)
    const isFav = favoriteMap.value[id]
    try {
      const res = isFav ? await removeFavorite(id) : await addFavorite(id)
      if (res.code === 200) {
        favoriteMap.value = { ...favoriteMap.value, [id]: !isFav }
        ElMessage.success(isFav ? '已取消收藏' : '收藏成功')
      }
    } catch {
      ElMessage.error('操作失败')
    }
  }
</script>

<style lang="scss" scoped>
  .article-analysis-container {
    .chart-card {
      height: 100%;
      display: flex;
      flex-direction: column;

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .header-title {
        font-size: 16px;
        font-weight: 600;
        color: $text-primary;
      }
    }

    .user-cell {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 500;
    }

    .stat-text {
      font-weight: 600;

      &.likes {
        color: #f59e0b;
      } // Amber
      &.reposts {
        color: #3b82f6;
      } // Blue
    }

    .list-card {
      margin-top: 24px;

      .filter-form {
        margin-bottom: 12px;
      }

      .pagination-wrapper {
        margin-top: 16px;
        display: flex;
        justify-content: flex-end;
      }
    }

    .detail {
      .detail-row {
        display: flex;
        align-items: center;
        padding: 6px 0;
        gap: 12px;
      }

      .detail-label {
        width: 56px;
        color: $text-secondary;
      }

      .detail-value {
        color: $text-primary;
        flex: 1;
        min-width: 0;
      }

      .detail-content {
        margin-top: 12px;
        padding: 12px;
        border: 1px solid $border-color-light;
        border-radius: $border-radius-base;
        background: $background-color;
        color: $text-primary;
        line-height: 1.6;
        white-space: pre-wrap;
        word-break: break-word;
      }

      .detail-link {
        margin-top: 12px;
      }
    }
  }
</style>
