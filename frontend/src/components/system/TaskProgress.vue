<template>
  <div class="task-progress-wrapper">
    <el-row
      :gutter="20"
      class="mb-4"
    >
      <el-col
        :xs="24"
        :lg="12"
      >
        <el-card>
          <template #header>
            <div class="card-header">
              <span class="header-title">爬虫任务</span>
              <div class="header-actions">
                <el-button
                  :icon="Refresh"
                  :loading="spiderLoading"
                  @click="$emit('refreshSpider')"
                >
                  刷新
                </el-button>
              </div>
            </div>
          </template>

          <div class="status-row">
            <el-tag
              :type="spiderOverview?.isRunning ? 'warning' : 'success'"
              effect="plain"
              round
            >
              {{ spiderOverview?.isRunning ? '运行中' : '空闲' }}
            </el-tag>
            <span class="status-text">{{ spiderOverview?.currentTask || '—' }}</span>
            <span class="status-text">{{ spiderOverview?.message || '' }}</span>
          </div>

          <el-progress
            :percentage="Number(spiderOverview?.progress || 0)"
            :stroke-width="8"
            :status="spiderOverview?.isRunning ? undefined : 'success'"
            class="mb-4"
          />
        </el-card>
      </el-col>

      <el-col
        :xs="24"
        :lg="12"
      >
        <el-card>
          <template #header>
            <div class="card-header">
              <span class="header-title">启动预热状态</span>
              <div class="header-actions">
                <el-tag
                  :type="warmupTagType"
                  effect="plain"
                  round
                >
                  {{ warmupStatusText }}
                </el-tag>
                <el-button
                  :icon="Refresh"
                  :loading="startupLoading"
                  @click="$emit('refreshStartup')"
                >
                  刷新
                </el-button>
              </div>
            </div>
          </template>

          <el-descriptions
            :column="2"
            border
            class="mb-4"
          >
            <el-descriptions-item label="管理员引导">
              <el-tag
                :type="adminBootstrapType"
                effect="plain"
                round
              >
                {{ adminBootstrapText }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="账号">
              {{ startupStatus?.admin_bootstrap?.username || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="执行时间">
              {{ formatDateTime(startupStatus?.admin_bootstrap?.timestamp) }}
            </el-descriptions-item>
            <el-descriptions-item label="预热耗时">
              {{ formatDuration(startupWarmup?.duration_seconds) }}
            </el-descriptions-item>
          </el-descriptions>

          <el-progress
            :percentage="warmupProgress"
            :status="warmupProgressStatus"
            :stroke-width="8"
            class="mb-4"
          />

          <div class="startup-meta mb-4">
            <span>已完成 {{ startupWarmup?.paths_done || 0 }} / {{ startupWarmup?.paths_total || 0 }}</span>
            <span v-if="startupWarmup?.started_at">开始时间：{{ formatDateTime(startupWarmup?.started_at) }}</span>
            <span v-if="startupWarmup?.finished_at">结束时间：{{ formatDateTime(startupWarmup?.finished_at) }}</span>
          </div>

          <el-alert
            v-if="startupWarmup?.error"
            :title="`预热线程异常：${startupWarmup.error}`"
            type="error"
            :closable="false"
            show-icon
            class="mb-4"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { Refresh } from '@element-plus/icons-vue'

defineProps({
  spiderOverview: {
    type: Object,
    default: () => null,
  },
  startupStatus: {
    type: Object,
    default: () => null,
  },
  startupWarmup: {
    type: Object,
    default: () => ({}),
  },
  warmupProgress: {
    type: Number,
    default: 0,
  },
  warmupProgressStatus: {
    type: String,
    default: undefined,
  },
  warmupTagType: {
    type: String,
    default: 'info',
  },
  warmupStatusText: {
    type: String,
    default: '',
  },
  adminBootstrapType: {
    type: String,
    default: 'info',
  },
  adminBootstrapText: {
    type: String,
    default: '',
  },
  spiderLoading: {
    type: Boolean,
    default: false,
  },
  startupLoading: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['refreshSpider', 'refreshStartup'])

const formatDateTime = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleString()
}

const formatDuration = (seconds) => {
  if (seconds == null || Number.isNaN(Number(seconds))) return '-'
  const value = Number(seconds)
  if (value < 1) return `${Math.round(value * 1000)} ms`
  return `${value.toFixed(3)} s`
}
</script>

<style lang="scss" scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: $text-primary;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.status-text {
  color: $text-secondary;
  font-size: 13px;
}

.startup-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 20px;
  color: $text-secondary;
  font-size: 13px;
}

.mb-4 {
  margin-bottom: 16px;
}
</style>
