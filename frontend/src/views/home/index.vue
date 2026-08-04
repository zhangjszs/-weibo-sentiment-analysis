<template>
  <div class="home-container">
    <!-- Analysis filters -->
    <AnalysisFilters
      v-model="filters"
      @search="onSearch"
    />

    <!-- Analysis summary (shown after search) -->
    <template v-if="snapshot">
      <AnalysisSummary
        :meta="snapshot.meta"
        :summary="snapshot.summary"
      />

      <!-- Analysis sections -->
      <el-row :gutter="16">
        <el-col :span="24">
          <AnalysisSection
            :status="trendStatus"
            empty-title="暂无趋势数据"
            empty-reason="当前话题在所选时间范围内没有数据。"
          >
            <BaseCard title="趋势">
              <div class="chart-placeholder">
                趋势图表区域
              </div>
            </BaseCard>
          </AnalysisSection>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <AnalysisSection
            :status="sentimentStatus"
            empty-title="暂无情感数据"
          >
            <BaseCard title="情感分布">
              <div class="chart-placeholder">
                情感分布图表区域
              </div>
            </BaseCard>
          </AnalysisSection>
        </el-col>

        <el-col :span="12">
          <AnalysisSection
            :status="propagationStatus"
            empty-title="暂无传播数据"
          >
            <BaseCard title="传播摘要">
              <div class="chart-placeholder">
                传播分析摘要区域
              </div>
            </BaseCard>
          </AnalysisSection>
        </el-col>
      </el-row>
    </template>

    <!-- Before first search -->
    <div
      v-else
      class="home-welcome"
    >
      <el-empty
        image-size="160"
        description="在上方输入关键词开始分析"
      />
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import AnalysisFilters from '@/components/Analysis/AnalysisFilters.vue'
import AnalysisSummary from '@/components/Analysis/AnalysisSummary.vue'
import AnalysisSection from '@/components/Analysis/AnalysisSection.vue'
import BaseCard from '@/components/Common/BaseCard.vue'

const filters = reactive({
  topic: '',
  startAt: '',
  endAt: '',
  demo: false,
})

const snapshot = ref(null)

const trendStatus = ref('empty')
const sentimentStatus = ref('empty')
const propagationStatus = ref('empty')

async function onSearch(value) {
  snapshot.value = null
  try {
    const params = { topic: value.topic }
    if (value.startAt) params.start_at = `${value.startAt}T00:00:00`
    if (value.endAt) params.end_at = `${value.endAt}T23:59:59`
    if (value.demo) params.demo = 'true'

    const resp = await fetch(`/api/v1/analysis?${new URLSearchParams(params)}`, {
      credentials: 'include',
    })
    const body = await resp.json()
    if (!body?.data) {
      ElMessage.warning(body?.msg || '分析请求失败')
      return
    }

    snapshot.value = body.data
    const meta = body.data.meta || {}

    // Determine section statuses based on data availability
    trendStatus.value = body.data.trend?.length > 0 ? 'normal' : 'empty'
    sentimentStatus.value = meta.source_type === 'demo' || (body.data.sentiment?.distribution?.positive ?? 0) > 0
      ? 'normal'
      : 'empty'
    propagationStatus.value = meta.source_type === 'demo' || (body.data.propagation?.total_nodes ?? 0) > 0
      ? 'normal'
      : 'empty'

    if (meta.limitations?.length > 0) {
      console.info('Analysis limitations:', meta.limitations)
    }
  } catch (err) {
    ElMessage.error('分析请求失败: ' + (err.message || '未知错误'))
  }
}
</script>

<style lang="scss" scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
}

.home-welcome {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.chart-placeholder {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-placeholder);
  font-size: 14px;
}
</style>