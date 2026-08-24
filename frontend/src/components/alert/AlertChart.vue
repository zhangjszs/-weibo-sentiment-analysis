<template>
  <div class="alert-chart-wrapper">
    <el-row
      :gutter="24"
      class="mb-4"
    >
      <el-col
        :xs="24"
        :sm="8"
        :md="6"
      >
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon info">
              <el-icon><Bell /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">
                {{ stats.total_alerts || 0 }}
              </div>
              <div class="stat-label">
                总预警数
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col
        :xs="24"
        :sm="8"
        :md="6"
      >
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon warning">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">
                {{ stats.unread_count || 0 }}
              </div>
              <div class="stat-label">
                未读预警
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col
        :xs="24"
        :sm="8"
        :md="6"
      >
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon danger">
              <el-icon><CircleCloseFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">
                {{ stats.level_distribution?.danger || 0 }}
              </div>
              <div class="stat-label">
                高危预警
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col
        :xs="24"
        :sm="8"
        :md="6"
      >
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon success">
              <el-icon><Setting /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">
                {{ stats.active_rules || 0 }}
              </div>
              <div class="stat-label">
                活跃规则
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="chart-card">
      <template #header>
        <span>预警级别分布</span>
      </template>
      <BaseChart
        :options="chartOptions"
        height="300px"
      />
    </el-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Bell, Warning, CircleCloseFilled, Setting } from '@element-plus/icons-vue'
import BaseChart from '@/components/Charts/BaseChart.vue'

const props = defineProps({
  stats: {
    type: Object,
    default: () => ({}),
  },
})

const chartOptions = computed(() => {
  const dist = props.stats.level_distribution || {}
  return {
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
          borderRadius: 4,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: { show: false },
        data: [
          { value: dist.info || 0, name: '信息', itemStyle: { color: '#909399' } },
          { value: dist.warning || 0, name: '警告', itemStyle: { color: '#E6A23C' } },
          { value: dist.danger || 0, name: '危险', itemStyle: { color: '#F56C6C' } },
          { value: dist.critical || 0, name: '严重', itemStyle: { color: '#FF0000' } },
        ],
      },
    ],
  }
})
</script>

<style lang="scss" scoped>
.chart-card {
  margin-bottom: 16px;
}
</style>
