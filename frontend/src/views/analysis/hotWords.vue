<template>
  <div class="hot-words-container">
    <el-row
      :gutter="20"
      class="stat-row"
    >
      <el-col :span="24">
        <el-card class="filter-card">
          <el-form
            :inline="true"
            :model="filterForm"
          >
            <el-form-item label="热词选择">
              <el-select
                v-model="filterForm.hotWord"
                placeholder="请选择热词"
                style="width: 240px"
                @change="handleHotWordChange"
              >
                <el-option
                  v-for="item in hotWordList"
                  :key="item[0]"
                  :label="item[0]"
                  :value="item[0]"
                />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                @click="handleSearch"
              >
                查询
              </el-button>
              <el-button @click="handleReset">
                重置
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-row
      :gutter="20"
      class="stat-row"
    >
      <el-col :span="8">
        <el-card class="info-card">
          <el-descriptions
            title="热词信息"
            :column="1"
            border
          >
            <el-descriptions-item label="热词名称">
              {{ currentHotWord }}
            </el-descriptions-item>
            <el-descriptions-item label="出现次数">
              {{ hotWordStats.count }}次
            </el-descriptions-item>
            <el-descriptions-item label="热词情感">
              <el-tag :type="getEmotionType(hotWordStats.emotion)">
                {{ hotWordStats.emotion }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <span>热词年份变化趋势</span>
          </template>
          <BaseChart
            ref="trendChartRef"
            :options="trendChartOptions"
            height="280px"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="table-card">
          <template #header>
            <div class="card-header">
              <span>热词查询表格</span>
              <el-button
                type="primary"
                :icon="Download"
                @click="handleExport"
              >
                导出数据
              </el-button>
            </div>
          </template>
          <el-table
            :data="tableData"
            :loading="loading"
            stripe
            border
            style="width: 100%"
          >
            <el-table-column
              prop="id"
              label="文章ID"
              width="100"
            />
            <el-table-column
              prop="user"
              label="评论用户"
              width="150"
            />
            <el-table-column
              prop="location"
              label="用户地址"
              width="150"
            />
            <el-table-column
              prop="content"
              label="内容"
              min-width="300"
              show-overflow-tooltip
            />
            <el-table-column
              prop="time"
              label="评论时间"
              width="180"
            />
            <el-table-column
              prop="likes"
              label="点赞数"
              width="100"
              align="center"
            >
              <template #default="{ row }">
                👍 {{ row.likes }}
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="total"
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
  import { Download } from '@element-plus/icons-vue'
  import { ElMessage } from 'element-plus'
  import BaseChart from '@/components/Charts/BaseChart.vue'
  import { getHotWords } from '@/api/stats'

  const trendChartRef = ref(null)
  const loading = ref(false)
  const hotWordList = ref([])
  const tableData = ref([])
  const currentHotWord = ref('')
  const hotWordStats = ref({
    count: 0,
    emotion: '',
  })
  const xData = ref([])
  const yData = ref([])

  const currentPage = ref(1)
  const pageSize = ref(10)
  const total = ref(0)

  const filterForm = ref({
    hotWord: '',
  })

  const trendChartOptions = computed(() => ({
    tooltip: {
      trigger: 'axis',
    },
    xAxis: {
      type: 'category',
      data: xData.value,
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        name: '分布个数',
        type: 'bar',
        data: yData.value,
      },
    ],
  }))

  const getEmotionType = (emotion) => {
    if (!emotion) return 'info'
    const lowerEmotion = emotion.toLowerCase()
    if (lowerEmotion.includes('正面') || lowerEmotion.includes('positive')) return 'success'
    if (lowerEmotion.includes('负面') || lowerEmotion.includes('negative')) return 'danger'
    if (lowerEmotion.includes('中性') || lowerEmotion.includes('neutral')) return 'warning'
    return 'info'
  }

  const loadHotWords = async () => {
    try {
      const res = await getHotWords('')
      if (res.code === 200) {
        hotWordList.value = res.data.hotWordList || []
        if (hotWordList.value.length > 0) {
          filterForm.value.hotWord = hotWordList.value[0][0]
          await handleHotWordChange(hotWordList.value[0][0])
        }
      }
    } catch (error) {
      ElMessage.error('加载热词列表失败')
    }
  }

  const handleHotWordChange = async (hotWord) => {
    currentHotWord.value = hotWord
    await loadData(hotWord)
  }

  const loadData = async (hotWord) => {
    loading.value = true
    try {
      const res = await getHotWords(hotWord)
      if (res.code === 200) {
        const data = res.data
        hotWordStats.value = {
          count: data.defaultHotWordNum || 0,
          emotion: data.emotionValue || '',
        }
        xData.value = data.xData || []
        yData.value = data.yData || []
        tableData.value = (data.tableList || []).map((item) => ({
          id: item[0],
          user: item[5],
          location: item[7],
          content: item[4],
          time: item[1],
          likes: item[2],
        }))
        total.value = tableData.value.length
      }
    } catch (error) {
      ElMessage.error('加载数据失败')
    } finally {
      loading.value = false
    }
  }

  const handleSearch = async () => {
    if (!filterForm.value.hotWord) {
      ElMessage.warning('请选择热词')
      return
    }
    currentPage.value = 1
    await loadData(filterForm.value.hotWord)
  }

  const handleReset = () => {
    filterForm.value.hotWord = ''
  }

  const handleSizeChange = (size) => {
    pageSize.value = size
    loadData(filterForm.value.hotWord)
  }

  const handlePageChange = (page) => {
    currentPage.value = page
    loadData(filterForm.value.hotWord)
  }

  const handleExport = () => {
    ElMessage.info('导出功能开发中')
  }

  onMounted(() => {
    loadHotWords()
  })
</script>

<style lang="scss" scoped>
  .hot-words-container {
    .stat-row {
      margin-bottom: 20px;
    }

    .filter-card {
      margin-bottom: 20px;
    }

    .info-card {
      height: 100%;
    }

    .chart-card {
      height: 100%;
    }

    .table-card {
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .pagination-wrapper {
        margin-top: 20px;
        display: flex;
        justify-content: flex-end;
      }
    }
  }
</style>
