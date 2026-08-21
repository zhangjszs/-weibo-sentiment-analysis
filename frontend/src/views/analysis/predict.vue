<template>
  <div class="predict-container">
    <PredictInput v-model:predictMode="predictMode" v-model:predictForm="predictForm" :predicting="predicting" @predict="handlePredict" @clear="clearInput" @openBatch="showBatchDialog = true" />
    <PredictResult :predictResult="predictResult" :getSentimentTagType="getSentimentTagType" :getSentimentLabel="getSentimentLabel" :getScoreColor="getScoreColor" :getEmotionTagType="getEmotionTagType" />
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
import PredictInput from '@/components/analysis/PredictInput.vue'
import PredictResult from '@/components/analysis/PredictResult.vue'
import { usePredict } from '@/composables/usePredict'
const { predictMode, predictForm, predicting, predictResult, historyList, loadingModelInfo, modelInfo, gaugeChartRef, showBatchDialog, showBatchResultDialog, batchForm, batchPredicting, batchResults, uploadRef, gaugeChartOptions, getSentimentTagType, getSentimentLabel, getScoreColor, getEmotionTagType, handlePredict, clearInput, handleBatchPredict, handleFileUpload, loadModelInfo } = usePredict()
</script>

<style lang="scss" scoped src="./predict.scss"></style>
