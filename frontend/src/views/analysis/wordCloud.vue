<template>
  <div class="word-cloud-container">
    <el-row :gutter="20">
      <el-col
        :xs="24"
        :lg="12"
      >
        <el-card class="chart-card">
          <template #header>
            <span>文章内容词云</span>
          </template>
          <div class="word-cloud-image">
            <img
              :src="contentCloudUrl"
              alt="内容词云"
              @error="handleImageError"
            >
          </div>
          <div class="cloud-actions">
            <el-button
              type="primary"
              :loading="loading"
              @click="regenerateContentCloud"
            >
              重新生成
            </el-button>
            <el-button @click="downloadImage(contentCloudUrl, 'content-cloud')">
              下载图片
            </el-button>
          </div>
        </el-card>
      </el-col>

      <el-col
        :xs="24"
        :lg="12"
      >
        <el-card class="chart-card">
          <template #header>
            <span>评论用户名词云</span>
          </template>
          <div class="word-cloud-image">
            <img
              :src="authorCloudUrl"
              alt="用户名词云"
              @error="handleImageError"
            >
          </div>
          <div class="cloud-actions">
            <el-button
              type="primary"
              :loading="loading"
              @click="regenerateAuthorCloud"
            >
              重新生成
            </el-button>
            <el-button @click="downloadImage(authorCloudUrl, 'author-cloud')">
              下载图片
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>词频统计 Top 50</span>
              <el-button
                type="primary"
                @click="exportWordStats"
              >
                导出数据
              </el-button>
            </div>
          </template>
          <el-table
            :data="wordStats"
            :loading="loading"
            stripe
            border
            style="width: 100%"
          >
            <el-table-column
              prop="rank"
              label="排名"
              width="80"
              align="center"
            >
              <template #default="{ $index }">
                <el-tag :type="getRankTagType($index + 1)">
                  {{ $index + 1 }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              prop="word"
              label="词语"
              width="200"
            />
            <el-table-column
              prop="count"
              label="出现次数"
              width="150"
              align="center"
              sortable
            />
            <el-table-column
              prop="frequency"
              label="频率"
              width="100"
              align="center"
            />
            <el-table-column
              prop="sentiment"
              label="情感倾向"
              width="120"
              align="center"
            >
              <template #default="{ row }">
                <el-tag :type="getSentimentType(row.sentiment)">
                  {{ row.sentiment }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
  import { ref, onMounted } from 'vue'
  import { ElMessage } from 'element-plus'
  import { getContentCloudData } from '@/api/stats'

  const loading = ref(false)
  const contentCloudUrl = ref('')
  const authorCloudUrl = ref('')
  const wordStats = ref([])
  const defaultContentCloud = '/static/contentCloud.jpg'
  const defaultAuthorCloud = '/static/authorNameCloud.jpg'

  const handleImageError = (e) => {
    e.target.src = defaultContentCloud
  }

  const downloadImage = (url, filename) => {
    try {
      const link = document.createElement('a')
      link.href = url
      link.download = `${filename}.jpg`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      ElMessage.success('图片下载成功')
    } catch (error) {
      ElMessage.error('下载失败')
    }
  }

  const regenerateContentCloud = async () => {
    loading.value = true
    try {
      const res = await getContentCloudData({ type: 'content' })
      if (res.code === 200) {
        if (res.data.contentCloud) {
          contentCloudUrl.value = res.data.contentCloud + '?t=' + Date.now()
          ElMessage.success('内容词云已重新生成')
        } else {
          ElMessage.warning('未能获取到图片URL')
        }
        if (res.data.wordStats) {
          wordStats.value = res.data.wordStats
        }
      }
    } catch (error) {
      ElMessage.error('生成失败')
    } finally {
      loading.value = false
    }
  }

  const regenerateAuthorCloud = async () => {
    loading.value = true
    try {
      const res = await getContentCloudData({ type: 'author' })
      if (res.code === 200) {
        if (res.data.authorCloud) {
          authorCloudUrl.value = res.data.authorCloud + '?t=' + Date.now()
          ElMessage.success('用户名词云已重新生成')
        } else {
          ElMessage.warning('未能获取到图片URL')
        }
      }
    } catch (error) {
      ElMessage.error('生成失败')
    } finally {
      loading.value = false
    }
  }

  const getRankTagType = (rank) => {
    if (rank === 1) return 'danger'
    if (rank <= 3) return 'warning'
    if (rank <= 10) return 'success'
    return 'info'
  }

  const getSentimentType = (sentiment) => {
    if (!sentiment) return 'info'
    const lower = sentiment.toLowerCase()
    if (lower.includes('正面') || lower.includes('positive')) return 'success'
    if (lower.includes('负面') || lower.includes('negative')) return 'danger'
    return 'info'
  }

  const exportWordStats = () => {
    try {
      const csvContent = [
        ['排名', '词语', '出现次数', '频率', '情感倾向'].join(','),
        ...wordStats.value.map((item, index) =>
          [index + 1, item.word, item.count, item.frequency, item.sentiment].join(',')
        ),
      ].join('\n')

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = 'word-stats.csv'
      link.click()
      ElMessage.success('数据导出成功')
    } catch (error) {
      ElMessage.error('导出失败')
    }
  }

  const loadData = async () => {
    loading.value = true
    try {
      const res = await getContentCloudData()
      if (res.code === 200) {
        const data = res.data
        contentCloudUrl.value = data.contentCloud || defaultContentCloud
        authorCloudUrl.value = data.authorCloud || defaultAuthorCloud
        wordStats.value = data.wordStats || []
      }
    } catch (error) {
      ElMessage.error('加载数据失败')
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    loadData()
  })
</script>

<style lang="scss" scoped>
  .word-cloud-container {
    .chart-card {
      margin-bottom: 20px;

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
    }

    .word-cloud-image {
      min-height: 300px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f5f7fa;
      border-radius: 4px;
      margin-bottom: 16px;

      img {
        max-width: 100%;
        max-height: 400px;
        object-fit: contain;
      }
    }

    .cloud-actions {
      display: flex;
      justify-content: center;
      gap: 16px;
    }
  }
</style>
