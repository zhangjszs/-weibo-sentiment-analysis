<template>
  <div class="analysis-summary">
    <div class="summary-header">
      <h3 class="summary-title">
        <el-icon :size="20">
          <DataAnalysis />
        </el-icon>
        分析摘要
      </h3>
      <ProvenanceBadge
        v-if="meta"
        :meta="meta"
        size="small"
      />
    </div>

    <div class="summary-body">
      <!-- One-line conclusion -->
      <p class="summary-conclusion">
        {{ conclusion }}
      </p>

      <!-- Key metrics -->
      <el-row
        :gutter="16"
        class="summary-metrics"
      >
        <el-col
          v-for="metric in metrics"
          :key="metric.label"
          :xs="12"
          :sm="6"
        >
          <div class="metric-card">
            <span class="metric-value">{{ metric.value }}</span>
            <span class="metric-label">{{ metric.label }}</span>
          </div>
        </el-col>
      </el-row>

      <!-- Data source info -->
      <div
        v-if="meta"
        class="summary-source"
      >
        <span class="source-label">数据范围：</span>
        <span class="source-value">
          <template v-if="meta.time_range?.start">
            {{ formatDate(meta.time_range.start) }} ~ {{ formatDate(meta.time_range.end) }}
          </template>
          <template v-else>未指定</template>
          ｜ 数据量：{{ meta.data_count ?? '-' }}
          <template v-if="meta.source_name"> ｜ 来源：{{ meta.source_name }}</template>
        </span>
      </div>

      <!-- Limitations -->
      <el-alert
        v-if="meta?.limitations?.length"
        :title="meta.limitations.join('; ')"
        type="warning"
        show-icon
        :closable="false"
        class="summary-limitations"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { DataAnalysis } from '@element-plus/icons-vue'
import ProvenanceBadge from '@/components/Common/ProvenanceBadge.vue'

const props = defineProps({
  meta: { type: Object, default: null },
  summary: { type: Object, default: () => ({}) },
})

const metrics = computed(() => [
  { label: '文章数', value: props.summary?.total_articles ?? '-' },
  { label: '评论数', value: props.summary?.total_comments ?? '-' },
  { label: '总量', value: props.summary?.total_count ?? '-' },
  { label: '情感指数', value: formatIndex(props.meta) },
])

const conclusion = computed(() => {
  const total = props.summary?.total_count || 0
  if (total === 0) return '暂无足够数据进行分析。'
  return `共采集到 ${total} 条相关内容进行分析。`
})

function formatDate(iso) {
  if (!iso) return '-'
  try { return new Date(iso).toLocaleDateString('zh-CN') }
  catch { return iso }
}

function formatIndex(meta) {
  const idx = meta?.data_count > 0 ? 'available' : '-'
  return idx
}
</script>

<style lang="scss" scoped>
.analysis-summary {
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: var(--el-box-shadow-light);
}

.summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.summary-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.summary-conclusion {
  font-size: 15px;
  color: var(--el-text-color-primary);
  margin: 0 0 16px;
  padding: 12px 16px;
  background: var(--el-fill-color-light);
  border-radius: 6px;
  line-height: 1.6;
}

.summary-metrics {
  margin-bottom: 12px;
}

.metric-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  background: var(--el-fill-color-lighter);
  border-radius: 6px;

  .metric-value {
    font-size: 22px;
    font-weight: 700;
    color: var(--el-color-primary);
  }

  .metric-label {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-top: 4px;
  }
}

.summary-source {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;

  .source-label { font-weight: 500; }
}

.summary-limitations {
  margin-top: 8px;
}
</style>