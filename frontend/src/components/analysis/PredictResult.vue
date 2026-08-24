<template>
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
              </div><div class="result-score">
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
              </div><div class="result-value">
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
                置信度
              </div><div class="result-value">
                {{ (predictResult.score * 100).toFixed(1) }}%
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
              </div><div class="keywords-list">
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
              </div><div class="reasoning-text">
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
              </div><el-tag
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
</template>
<script setup>
defineProps({ predictResult: Object, getSentimentTagType: Function, getSentimentLabel: Function, getScoreColor: Function, getEmotionTagType: Function })
</script>
