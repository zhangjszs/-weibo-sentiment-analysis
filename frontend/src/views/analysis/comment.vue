<template>
  <div class="comment-analysis-container">
    <el-row :gutter="20">
      <el-col
        :xs="24"
        :lg="12"
      >
        <el-card class="chart-card">
          <template #header>
            <span>评论时间分布</span>
          </template>
          <BaseChart
            ref="timeChartRef"
            :options="timeChartOptions"
            height="350px"
          />
        </el-card>
      </el-col>

      <el-col
        :xs="24"
        :lg="12"
      >
        <el-card class="chart-card">
          <template #header>
            <span>评论用户活跃度</span>
          </template>
          <BaseChart
            ref="userActivityChartRef"
            :options="userActivityChartOptions"
            height="350px"
            @click="handleUserChartClick"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col
        :xs="24"
        :lg="8"
      >
        <el-card class="chart-card">
          <template #header>
            <span>评论情感分布</span>
          </template>
          <BaseChart
            ref="sentimentPieRef"
            :options="sentimentPieOptions"
            height="300px"
          />
        </el-card>
      </el-col>

      <el-col
        :xs="24"
        :lg="16"
      >
        <el-card class="chart-card">
          <template #header>
            <span>热门评论</span>
          </template>
          <div class="hot-comments">
            <div
              v-for="(comment, index) in hotComments"
              :key="index"
              class="comment-item"
            >
              <div class="comment-header">
                <span class="comment-user">🧑‍{{ comment.user }}</span>
                <span class="comment-time">{{ comment.time }}</span>
              </div>
              <div class="comment-content">
                {{ comment.content }}
              </div>
              <div class="comment-footer">
                <span>👍 {{ comment.likes }}</span>
                <span>💬 {{ comment.replies }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            评论列表
          </div>
          <div class="header-actions">
            <el-button
              :icon="Download"
              :disabled="listData.length === 0"
              @click="exportList"
            >
              导出 CSV
            </el-button>
            <el-button
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
            placeholder="评论内容关键词"
            clearable
            style="width: 220px"
          />
        </el-form-item>
        <el-form-item label="文章ID">
          <el-input
            v-model="filters.article_id"
            placeholder="rootId"
            clearable
            style="width: 220px"
          />
        </el-form-item>
        <el-form-item label="用户">
          <el-input
            v-model="filters.user"
            placeholder="评论用户"
            clearable
            style="width: 180px"
          />
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
          width="160"
          show-overflow-tooltip
        />
        <el-table-column
          prop="rootId"
          label="文章ID"
          width="160"
          show-overflow-tooltip
        />
        <el-table-column
          prop="user"
          label="用户"
          width="160"
          show-overflow-tooltip
        />
        <el-table-column
          prop="created_at"
          label="时间"
          width="180"
          align="center"
        />
        <el-table-column
          prop="likeNum"
          label="赞"
          width="90"
          align="center"
        />
        <el-table-column
          prop="content"
          label="内容"
          min-width="360"
          show-overflow-tooltip
        />
        <el-table-column
          label="操作"
          width="110"
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
      title="评论详情"
      width="760px"
    >
      <div
        v-if="detailRow"
        class="detail"
      >
        <div class="detail-row">
          <div class="detail-label">
            用户
          </div>
          <div class="detail-value">
            {{ detailRow.user || '-' }}
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">
            文章ID
          </div>
          <div class="detail-value">
            {{ detailRow.rootId || '-' }}
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
            点赞
          </div>
          <div class="detail-value">
            {{ detailRow.likeNum || 0 }}
          </div>
        </div>
        <div class="detail-content">
          {{ detailRow.content || '' }}
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
  import { Search, Refresh, Download, View } from '@element-plus/icons-vue'
  import BaseChart from '@/components/Charts/BaseChart.vue'
  import { getCommentData } from '@/api/stats'
  import { getComments } from '@/api/content'
  import { downloadCsv } from '@/utils'

  const loading = ref(false)
  const hotComments = ref([])
  const timeData = ref([])
  const userActivityData = ref([])
  const sentimentData = ref([])

  const timeChartRef = ref(null)
  const userActivityChartRef = ref(null)
  const sentimentPieRef = ref(null)

  const timeChartOptions = computed(() => ({
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: timeData.value.hours || [],
    },
    yAxis: { type: 'value' },
    series: [
      {
        type: 'line',
        smooth: true,
        areaStyle: { color: 'rgba(0, 128, 255, 0.2)' },
        data: timeData.value.counts || [],
      },
    ],
  }))

  const userActivityChartOptions = computed(() => ({
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: userActivityData.value.users || [],
    },
    yAxis: { type: 'value' },
    series: [
      {
        type: 'bar',
        data: userActivityData.value.counts || [],
        itemStyle: { color: '#005AA0' },
      },
    ],
  }))

  const sentimentPieOptions = computed(() => ({
    tooltip: { trigger: 'item' },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        data: sentimentData.value,
      },
    ],
  }))

  const loadData = async () => {
    loading.value = true
    try {
      const res = await getCommentData()
      if (res.code === 200) {
        const data = res.data
        timeData.value = data.timeDistribution || { hours: [], counts: [] }
        userActivityData.value = data.userActivity || { users: [], counts: [] }
        sentimentData.value = data.sentimentData || []
        hotComments.value = data.hotComments || []
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
  const filters = ref({ keyword: '', article_id: '', user: '', dateRange: [] })

  const detailVisible = ref(false)
  const detailRow = ref(null)

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
      const res = await getComments({
        page: pagination.value.page,
        limit: pagination.value.limit,
        keyword: filters.value.keyword || '',
        article_id: filters.value.article_id || '',
        user: filters.value.user || '',
        start_time,
        end_time,
      })
      if (res.code === 200) {
        const data = res.data || {}
        listData.value = data.list || []
        pagination.value.total = data.total || 0
      }
    } catch (e) {
      ElMessage.error('加载评论列表失败')
    } finally {
      listLoading.value = false
    }
  }

  const applyFilters = () => {
    pagination.value.page = 1
    loadList()
  }

  const resetFilters = () => {
    filters.value.keyword = ''
    filters.value.article_id = ''
    filters.value.user = ''
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
    const headers = ['ID', '文章ID', '用户', '时间', '赞', '内容']
    const rows = listData.value.map((c) => [
      c.id,
      c.rootId,
      c.user,
      c.created_at,
      c.likeNum,
      c.content,
    ])
    downloadCsv(`comments_${Date.now()}.csv`, headers, rows)
  }

  const handleUserChartClick = (params) => {
    const user = params?.name
    if (!user || typeof user !== 'string') return
    filters.value.user = user
    applyFilters()
  }

  onMounted(() => {
    loadData()
    loadList()
  })
</script>

<style lang="scss" scoped>
  .comment-analysis-container {
    .chart-card {
      margin-bottom: 20px;
    }

    .hot-comments {
      .comment-item {
        padding: 16px;
        border-bottom: 1px solid #f0f0f0;

        &:last-child {
          border-bottom: none;
        }

        .comment-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;

          .comment-user {
            font-weight: bold;
          }

          .comment-time {
            color: #999;
            font-size: 12px;
          }
        }

        .comment-content {
          color: #333;
          margin-bottom: 8px;
          line-height: 1.5;
        }

        .comment-footer {
          display: flex;
          gap: 16px;
          color: #999;
          font-size: 12px;
        }
      }
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
    }
  }
</style>
