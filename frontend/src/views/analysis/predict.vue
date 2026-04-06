<template>
  <div class="predict-container">
    <el-row
      :gutter="24"
      class="mb-4"
    >
      <el-col :span="24">
        <el-card class="input-card">
          <template #header>
            <div class="card-header">
              <span class="header-title">内容情感预测</span>
              <el-radio-group
                v-model="predictMode"
                size="small"
              >
                <el-radio-button label="custom">
                  自定义模型
                </el-radio-button>
                <el-radio-button label="smart">
                  智能分析
                </el-radio-button>
                <el-radio-button label="simple">
                  快速分析
                </el-radio-button>
              </el-radio-group>
            </div>
          </template>

          <el-form
            :model="predictForm"
            label-position="top"
          >
            <el-form-item label="输入文本">
              <el-input
                v-model="predictForm.text"
                type="textarea"
                :rows="4"
                placeholder="请输入需要分析的微博内容或评论文本..."
                maxlength="1000"
                show-word-limit
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="predicting"
                :disabled="!predictForm.text.trim()"
                @click="handlePredict"
              >
                <el-icon class="mr-1">
                  <TrendCharts />
                </el-icon>
                开始预测
              </el-button>
              <el-button @click="clearInput">
                清空
              </el-button>
              <el-button
                type="success"
                plain
                @click="showBatchDialog = true"
              >
                <el-icon class="mr-1">
                  <Upload />
                </el-icon>
                批量预测
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-row
      v-if="predictResult"
      :gutter="24"
      class="mb-4"
    >
      <el-col :span="24">
        <el-card class="result-card">
          <template #header>
            <div class="card-header">
              <span class="header-title">预测结果</span>
              <el-tag
                :type="getSentimentTagType(predictResult.label)"
                size="large"
              >
                {{ getSentimentLabel(predictResult.label) }}
              </el-tag>
            </div>
          </template>

          <el-row :gutter="24">
            <el-col
              :xs="24"
              :md="8"
            >
              <div class="result-item">
                <div class="result-label">
                  情感得分
                </div>
                <div class="result-score">
                  <el-progress
                    :percentage="Math.round(predictResult.score * 100)"
                    :color="getScoreColor(predictResult.score)"
                    :stroke-width="20"
                    :text-inside="true"
                  />
                </div>
              </div>
            </el-col>

            <el-col
              :xs="24"
              :md="8"
            >
              <div class="result-item">
                <div class="result-label">
                  情感倾向
                </div>
                <div
                  class="result-value"
                  :class="getSentimentClass(predictResult.label)"
                >
                  {{ getSentimentLabel(predictResult.label) }}
                </div>
              </div>
            </el-col>

            <el-col
              :xs="24"
              :md="8"
            >
              <div class="result-item">
                <div class="result-label">
                  分析来源
                </div>
                <div class="result-value source">
                  <el-tag
                    type="info"
                    size="small"
                  >
                    {{ predictResult.source || '模型预测' }}
                  </el-tag>
                </div>
              </div>
            </el-col>
          </el-row>

          <el-divider />

          <el-row
            v-if="predictResult.keywords && predictResult.keywords.length"
            :gutter="24"
          >
            <el-col :span="24">
              <div class="result-item">
                <div class="result-label">
                  关键词提取
                </div>
                <div class="keywords-list">
                  <el-tag
                    v-for="(keyword, index) in predictResult.keywords"
                    :key="index"
                    class="keyword-tag"
                    effect="plain"
                  >
                    {{ keyword }}
                  </el-tag>
                </div>
              </div>
            </el-col>
          </el-row>

          <el-row
            v-if="predictResult.reasoning"
            :gutter="24"
            class="mt-3"
          >
            <el-col :span="24">
              <div class="result-item">
                <div class="result-label">
                  分析理由
                </div>
                <div class="reasoning-text">
                  {{ predictResult.reasoning }}
                </div>
              </div>
            </el-col>
          </el-row>

          <el-row
            v-if="predictResult.emotion"
            :gutter="24"
            class="mt-3"
          >
            <el-col :span="24">
              <div class="result-item">
                <div class="result-label">
                  细粒度情感
                </div>
                <el-tag
                  effect="dark"
                  :type="getEmotionTagType(predictResult.emotion)"
                >
                  {{ predictResult.emotion }}
                </el-tag>
              </div>
            </el-col>
          </el-row>
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
            <span class="header-title">情感分布可视化</span>
          </template>
          <BaseChart
            ref="gaugeChartRef"
            :options="gaugeChartOptions"
            height="300px"
          />
        </el-card>
      </el-col>

      <el-col
        :xs="24"
        :lg="12"
      >
        <el-card class="chart-card">
          <template #header>
            <span class="header-title">模型信息</span>
          </template>
          <div
            v-loading="loadingModelInfo"
            class="model-info"
          >
            <el-descriptions
              v-if="modelInfo"
              :column="1"
              border
            >
              <el-descriptions-item label="模型类型">
                {{
                  modelInfo.model_type || 'TF-IDF + 分类器'
                }}
              </el-descriptions-item>
              <el-descriptions-item label="最佳算法">
                {{
                  modelInfo.best_model || 'NaiveBayes'
                }}
              </el-descriptions-item>
              <el-descriptions-item label="准确率">
                {{
                  modelInfo.accuracy ? (modelInfo.accuracy * 100).toFixed(2) + '%' : 'N/A'
                }}
              </el-descriptions-item>
              <el-descriptions-item label="F1分数">
                {{
                  modelInfo.f1_score ? modelInfo.f1_score.toFixed(4) : 'N/A'
                }}
              </el-descriptions-item>
              <el-descriptions-item label="训练样本">
                {{
                  modelInfo.training_samples || 'N/A'
                }}
              </el-descriptions-item>
              <el-descriptions-item label="最后更新">
                {{
                  modelInfo.last_updated || 'N/A'
                }}
              </el-descriptions-item>
            </el-descriptions>
            <el-empty
              v-else
              description="暂无模型信息"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="24">
      <el-col :span="24">
        <el-card class="history-card">
          <template #header>
            <div class="card-header">
              <span class="header-title">预测历史</span>
              <el-button
                type="danger"
                plain
                size="small"
                :disabled="historyList.length === 0"
                @click="clearHistory"
              >
                清空历史
              </el-button>
            </div>
          </template>
          <el-table
            :data="historyList"
            style="width: 100%"
            max-height="400"
          >
            <el-table-column
              prop="text"
              label="文本内容"
              min-width="300"
              show-overflow-tooltip
            />
            <el-table-column
              prop="sentiment"
              label="情感"
              width="100"
              align="center"
            >
              <template #default="{ row }">
                <el-tag
                  :type="getSentimentTagType(row.label)"
                  size="small"
                >
                  {{ getSentimentLabel(row.label) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              prop="score"
              label="得分"
              width="100"
              align="center"
            >
              <template #default="{ row }">
                <span :class="getScoreClass(row.score)">{{ (row.score * 100).toFixed(1) }}%</span>
              </template>
            </el-table-column>
            <el-table-column
              prop="source"
              label="来源"
              width="120"
              align="center"
            >
              <template #default="{ row }">
                <el-tag
                  type="info"
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
            <el-table-column
              label="操作"
              width="100"
              align="center"
            >
              <template #default="{ row }">
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="retryPredict(row)"
                >
                  重试
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty
            v-if="historyList.length === 0"
            description="暂无预测历史"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog
      v-model="showBatchDialog"
      title="批量预测"
      width="600px"
    >
      <el-form
        :model="batchForm"
        label-position="top"
      >
        <el-form-item label="输入文本（每行一条）">
          <el-input
            v-model="batchForm.texts"
            type="textarea"
            :rows="10"
            placeholder="请输入需要批量分析的文本，每行一条..."
          />
        </el-form-item>
        <el-form-item label="或上传文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :show-file-list="true"
            :limit="1"
            accept=".txt,.csv"
            :on-change="handleFileChange"
          >
            <template #trigger>
              <el-button
                type="primary"
                plain
              >
                选择文件
              </el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                支持 .txt 或 .csv 文件，每行一条文本
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchDialog = false">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="batchPredicting"
          @click="handleBatchPredict"
        >
          开始批量预测
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showBatchResultDialog"
      title="批量预测结果"
      width="800px"
    >
      <el-table
        :data="batchResults"
        style="width: 100%"
        max-height="500"
      >
        <el-table-column
          type="index"
          label="序号"
          width="60"
          align="center"
        />
        <el-table-column
          prop="text"
          label="文本"
          min-width="300"
          show-overflow-tooltip
        />
        <el-table-column
          prop="label"
          label="情感"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <el-tag
              :type="getSentimentTagType(row.label)"
              size="small"
            >
              {{ getSentimentLabel(row.label) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="score"
          label="得分"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <span :class="getScoreClass(row.score)">{{ (row.score * 100).toFixed(1) }}%</span>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showBatchResultDialog = false">
          关闭
        </el-button>
        <el-button
          type="success"
          @click="exportBatchResults"
        >
          导出结果
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted } from 'vue'
  import { ElMessage } from 'element-plus'
  import { TrendCharts, Upload } from '@element-plus/icons-vue'
  import BaseChart from '@/components/Charts/BaseChart.vue'
  import { predictSentiment, predictBatch, getModelInfo } from '@/api/predict'
  import { downloadCsv } from '@/utils'

  const predictMode = ref('custom')
  const predictForm = ref({ text: '' })
  const predicting = ref(false)
  const predictResult = ref(null)
  const historyList = ref([])
  const loadingModelInfo = ref(false)
  const modelInfo = ref(null)

  const gaugeChartRef = ref(null)
  const showBatchDialog = ref(false)
  const showBatchResultDialog = ref(false)
  const batchForm = ref({ texts: '' })
  const batchPredicting = ref(false)
  const batchResults = ref([])
  const uploadRef = ref(null)

  const gaugeChartOptions = computed(() => {
    const score = predictResult.value?.score || 0.5
    return {
      series: [
        {
          type: 'gauge',
          startAngle: 180,
          endAngle: 0,
          min: 0,
          max: 1,
          splitNumber: 5,
          axisLine: {
            lineStyle: {
              width: 30,
              color: [
                [0.4, '#EF4444'],
                [0.6, '#64748B'],
                [1, '#10B981'],
              ],
            },
          },
          pointer: {
            icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
            length: '60%',
            width: 10,
            offsetCenter: [0, '-10%'],
            itemStyle: { color: 'auto' },
          },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { show: false },
          title: {
            offsetCenter: [0, '30%'],
            fontSize: 14,
            color: '#64748B',
          },
          detail: {
            fontSize: 24,
            offsetCenter: [0, '0%'],
            valueAnimation: true,
            formatter: (value) => (value * 100).toFixed(1) + '%',
            color: 'inherit',
          },
          data: [
            {
              value: score,
              name: predictResult.value ? getSentimentLabel(predictResult.value.label) : '等待预测',
            },
          ],
        },
      ],
    }
  })

  const getSentimentLabel = (label) => {
    const labels = {
      positive: '正面',
      neutral: '中性',
      negative: '负面',
    }
    return labels[label] || label || '未知'
  }

  const getSentimentTagType = (label) => {
    const types = {
      positive: 'success',
      neutral: 'info',
      negative: 'danger',
    }
    return types[label] || 'info'
  }

  const getSentimentClass = (label) => {
    const classes = {
      positive: 'text-success',
      neutral: 'text-muted',
      negative: 'text-danger',
    }
    return classes[label] || ''
  }

  const getScoreColor = (score) => {
    if (score > 0.6) return '#10B981'
    if (score < 0.4) return '#EF4444'
    return '#64748B'
  }

  const getScoreClass = (score) => {
    if (score > 0.6) return 'text-success'
    if (score < 0.4) return 'text-danger'
    return 'text-muted'
  }

  const getEmotionTagType = (emotion) => {
    const emotionMap = {
      喜悦: 'success',
      愤怒: 'danger',
      悲伤: 'info',
      焦虑: 'warning',
      期待: 'primary',
      讽刺: 'warning',
      无感: 'info',
    }
    return emotionMap[emotion] || 'info'
  }

  const handlePredict = async () => {
    if (!predictForm.value.text.trim()) {
      ElMessage.warning('请输入需要分析的文本')
      return
    }

    predicting.value = true
    try {
      const res = await predictSentiment(predictForm.value.text, predictMode.value)
      if (res.code === 200) {
        predictResult.value = res.data

        historyList.value.unshift({
          text:
            predictForm.value.text.substring(0, 100) +
            (predictForm.value.text.length > 100 ? '...' : ''),
          label: res.data.label,
          score: res.data.score,
          source: res.data.source,
          time: new Date().toLocaleString(),
        })

        if (historyList.value.length > 50) {
          historyList.value = historyList.value.slice(0, 50)
        }

        ElMessage.success('预测完成')
      } else {
        ElMessage.error(res.msg || '预测失败')
      }
    } catch (error) {
      ElMessage.error('预测请求失败')
    } finally {
      predicting.value = false
    }
  }

  const clearInput = () => {
    predictForm.value.text = ''
    predictResult.value = null
  }

  const clearHistory = () => {
    historyList.value = []
    ElMessage.success('历史记录已清空')
  }

  const retryPredict = (row) => {
    predictForm.value.text = row.text
    handlePredict()
  }

  const loadModelInfo = async () => {
    loadingModelInfo.value = true
    try {
      const res = await getModelInfo()
      if (res.code === 200) {
        modelInfo.value = res.data
      }
    } catch (error) {
      console.error('获取模型信息失败:', error)
    } finally {
      loadingModelInfo.value = false
    }
  }

  const handleFileChange = (file) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      batchForm.value.texts = e.target.result
    }
    reader.readAsText(file.raw)
  }

  const handleBatchPredict = async () => {
    const texts = batchForm.value.texts
      .split('\n')
      .map((t) => t.trim())
      .filter((t) => t.length > 0)

    if (texts.length === 0) {
      ElMessage.warning('请输入至少一条文本')
      return
    }

    if (texts.length > 100) {
      ElMessage.warning('单次最多预测100条文本')
      return
    }

    batchPredicting.value = true
    try {
      const res = await predictBatch(texts, predictMode.value)
      if (res.code === 200) {
        batchResults.value = res.data.results.map((r, i) => ({
          text: texts[i],
          label: r.label,
          score: r.score,
          source: r.source,
        }))
        showBatchResultDialog.value = true
        showBatchDialog.value = false
        ElMessage.success(`成功预测 ${batchResults.value.length} 条文本`)
      } else {
        ElMessage.error(res.msg || '批量预测失败')
      }
    } catch (error) {
      ElMessage.error('批量预测请求失败')
    } finally {
      batchPredicting.value = false
    }
  }

  const exportBatchResults = () => {
    const headers = ['序号', '文本', '情感', '得分', '来源']
    const rows = batchResults.value.map((r, i) => [
      i + 1,
      r.text,
      getSentimentLabel(r.label),
      (r.score * 100).toFixed(2) + '%',
      r.source,
    ])
    downloadCsv(`batch_predict_${Date.now()}.csv`, headers, rows)
  }

  onMounted(() => {
    loadModelInfo()
  })
</script>

<style lang="scss" scoped>
  .predict-container {
    .input-card,
    .result-card,
    .chart-card,
    .history-card {
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

    .result-card {
      .result-item {
        padding: 12px 0;

        .result-label {
          font-size: 13px;
          color: $text-secondary;
          margin-bottom: 8px;
        }

        .result-score {
          padding: 8px 0;
        }

        .result-value {
          font-size: 20px;
          font-weight: 600;

          &.text-success {
            color: $success-color;
          }
          &.text-muted {
            color: $text-secondary;
          }
          &.text-danger {
            color: $danger-color;
          }

          &.source {
            font-size: 14px;
            font-weight: normal;
          }
        }
      }

      .keywords-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;

        .keyword-tag {
          cursor: default;
        }
      }

      .reasoning-text {
        padding: 12px;
        background: $background-color;
        border-radius: $border-radius-base;
        color: $text-primary;
        line-height: 1.6;
      }
    }

    .model-info {
      padding: 8px 0;
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

    .mr-1 {
      margin-right: 4px;
    }
    .mt-3 {
      margin-top: 12px;
    }
    .mb-4 {
      margin-bottom: 16px;
    }
  }
</style>
