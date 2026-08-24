<template>
  <div class="task-list-wrapper">
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
              <span class="header-title">爬虫历史</span>
            </div>
          </template>
          <el-table
            :data="spiderHistory"
            style="width: 100%"
            height="360"
          >
            <el-table-column
              prop="time"
              label="时间"
              width="180"
            />
            <el-table-column
              prop="action"
              label="动作"
              min-width="160"
              show-overflow-tooltip
            />
            <el-table-column
              prop="status"
              label="状态"
              width="120"
              align="center"
            >
              <template #default="{ row }">
                <el-tag
                  :type="row.status === 'success' ? 'success' : 'danger'"
                  effect="plain"
                  round
                >
                  {{ row.status === 'success' ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              prop="count"
              label="条数"
              width="90"
              align="center"
            />
            <el-table-column
              prop="detail"
              label="详情"
              min-width="160"
              show-overflow-tooltip
            />
          </el-table>
        </el-card>
      </el-col>

      <el-col
        :xs="24"
        :lg="12"
      >
        <el-card>
          <template #header>
            <div class="card-header">
              <span class="header-title">运行日志</span>
              <div class="header-actions">
                <el-input-number
                  :model-value="logLines"
                  :min="50"
                  :max="500"
                  size="small"
                  style="width: 120px"
                  @update:model-value="$emit('update:logLines', $event)"
                />
                <el-button
                  :icon="Refresh"
                  :loading="logsLoading"
                  @click="$emit('refreshLogs')"
                >
                  刷新
                </el-button>
              </div>
            </div>
          </template>

          <div class="log-container">
            <div
              v-if="logs.length === 0"
              class="empty"
            >
              <el-empty
                description="暂无日志"
                :image-size="60"
              />
            </div>
            <div v-else>
              <div
                v-for="(line, idx) in logs"
                :key="idx"
                class="log-line"
                :class="getLogLevel(line)"
              >
                {{ line }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="mb-4">
      <template #header>
        <div class="card-header">
          <span class="header-title">预热结果</span>
        </div>
      </template>
      <el-table
        :data="startupWarmupResults"
        style="width: 100%"
        max-height="260"
      >
        <el-table-column
          prop="path"
          label="预热接口"
          min-width="280"
          show-overflow-tooltip
        />
        <el-table-column
          prop="status_code"
          label="状态码"
          width="110"
          align="center"
        >
          <template #default="{ row }">
            <el-tag
              :type="
                row.status_code >= 200 && row.status_code < 400
                  ? 'success'
                  : row.status_code
                    ? 'danger'
                    : 'info'
              "
              effect="plain"
              round
            >
              {{ row.status_code || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="duration_seconds"
          label="耗时(s)"
          width="100"
          align="center"
        />
        <el-table-column
          prop="error"
          label="错误信息"
          min-width="220"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            {{ row.error || '-' }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <span class="header-title">Celery 任务查询</span>
        </div>
      </template>

      <el-form
        :inline="true"
        class="query-form"
        @submit.prevent
      >
        <el-form-item label="Task ID">
          <el-input
            :model-value="taskId"
            placeholder="输入 task_id"
            clearable
            style="width: 420px"
            @update:model-value="$emit('update:taskId', $event)"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :icon="Search"
            :disabled="!taskId.trim()"
            :loading="taskLoading"
            @click="$emit('queryTask')"
          >
            查询
          </el-button>
          <el-button
            :disabled="recentTasks.length === 0"
            @click="$emit('clearRecent')"
          >
            清空记录
          </el-button>
        </el-form-item>
      </el-form>

      <div
        v-if="taskResult"
        class="task-result"
      >
        <el-descriptions
          :column="2"
          border
        >
          <el-descriptions-item label="状态">
            {{ taskResult.state || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="进度">
            {{
              taskResult.progress != null ? taskResult.progress + '%' : '-'
            }}
          </el-descriptions-item>
          <el-descriptions-item
            label="消息"
            :span="2"
          >
            {{
              taskResult.message || '-'
            }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <div
        v-if="recentTasks.length > 0"
        class="recent"
      >
        <div class="recent-title">
          最近查询
        </div>
        <el-space wrap>
          <el-tag
            v-for="id in recentTasks"
            :key="id"
            closable
            effect="plain"
            class="recent-tag"
            @close="$emit('removeRecent', id)"
            @click="$emit('selectRecent', id)"
          >
            {{ id }}
          </el-tag>
        </el-space>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { Refresh, Search } from '@element-plus/icons-vue'

defineProps({
  spiderHistory: {
    type: Array,
    default: () => [],
  },
  logs: {
    type: Array,
    default: () => [],
  },
  logsLoading: {
    type: Boolean,
    default: false,
  },
  logLines: {
    type: Number,
    default: 200,
  },
  startupWarmupResults: {
    type: Array,
    default: () => [],
  },
  taskId: {
    type: String,
    default: '',
  },
  taskLoading: {
    type: Boolean,
    default: false,
  },
  taskResult: {
    type: Object,
    default: () => null,
  },
  recentTasks: {
    type: Array,
    default: () => [],
  },
})

defineEmits([
  'update:logLines',
  'update:taskId',
  'refreshLogs',
  'queryTask',
  'clearRecent',
  'removeRecent',
  'selectRecent',
])

function getLogLevel(line) {
  if (line.includes('ERROR') || line.includes('CRITICAL')) return 'log-error'
  if (line.includes('WARNING')) return 'log-warn'
  if (line.includes('INFO')) return 'log-info'
  return 'log-debug'
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

.log-container {
  height: 420px;
  overflow: auto;
  border: 1px solid $border-color-light;
  border-radius: $border-radius-base;
  background: $background-color;
  padding: 12px;
}

.log-line {
  font-family:
    ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New',
    monospace;
  font-size: 12px;
  line-height: 1.6;
  padding: 2px 6px;
  border-radius: 4px;
  color: $text-regular;
  word-break: break-word;
}

.log-info {
  background: rgba(59, 130, 246, 0.06);
}

.log-warn {
  background: rgba(245, 158, 11, 0.08);
}

.log-error {
  background: rgba(239, 68, 68, 0.08);
}

.query-form {
  margin-bottom: 12px;
}

.task-result {
  margin: 12px 0 16px;
}

.recent-title {
  font-size: 13px;
  color: $text-secondary;
  margin-bottom: 8px;
}

.recent-tag {
  cursor: pointer;
}

.mb-4 {
  margin-bottom: 16px;
}
</style>
