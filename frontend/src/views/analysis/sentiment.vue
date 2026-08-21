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
import { CircleCheck, Remove, CircleClose, Refresh } from '@element-plus/icons-vue'
import StatCard from '@/components/Common/StatCard.vue'
import BaseChart from '@/components/Charts/BaseChart.vue'
import { useSentiment } from '@/composables/useSentiment'
const { loading, rawList, sentimentStats, sentimentData, trendData, keywords, currentPage, pageSize, total, filters, sentimentPieRef, trendChartRef, emotionBarRef, scoreDistRef, sentimentPieOptions, trendChartOptions, emotionBarOptions, scoreDistOptions, getSentimentType, getScoreClass, getEmotionType, filteredList, filteredTotal, pagedList, loadData, handleSizeChange, handlePageChange, resetFilters, handlePieClick, handleTrendClick } = useSentiment()
</script>

<style lang="scss" scoped src="./sentiment.scss"></style>
