<template>
  <div class="tasks-page">
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
                  @click="refreshSpider"
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
                  v-model="logLines"
                  :min="50"
                  :max="500"
                  size="small"
                  style="width: 120px"
                />
                <el-button
                  :icon="Refresh"
                  :loading="logsLoading"
                  @click="refreshLogs"
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
              @click="refreshStartup"
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
            v-model="taskId"
            placeholder="输入 task_id"
            clearable
            style="width: 420px"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :icon="Search"
            :disabled="!taskId.trim()"
            :loading="taskLoading"
            @click="queryTask"
          >
            查询
          </el-button>
          <el-button
            :disabled="recentTasks.length === 0"
            @click="clearRecent"
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
            @close="removeRecent(id)"
            @click="selectRecent(id)"
          >
            {{ id }}
          </el-tag>
        </el-space>
      </div>
    </el-card>
  </div>
</template>

<script setup>
  import { computed, onMounted, onUnmounted, ref } from 'vue'
  import { ElMessage } from 'element-plus'
  import { Refresh, Search } from '@element-plus/icons-vue'
  import { getSpiderLogs, getSpiderOverview } from '@/api/spider'
  import { getStartupStatus, getTaskStatus } from '@/api/tasks'

  const spiderLoading = ref(false)
  const startupLoading = ref(false)
  const logsLoading = ref(false)
  const taskLoading = ref(false)

  const spiderOverview = ref(null)
  const startupStatus = ref(null)
  const logs = ref([])
  const logLines = ref(200)

  const taskId = ref('')
  const taskResult = ref(null)
  const recentTasks = ref([])
  let startupPollTimer = null

  const spiderHistory = computed(() => spiderOverview.value?.history || [])
  const startupWarmup = computed(() => startupStatus.value?.warmup || {})
  const startupWarmupResults = computed(() => startupWarmup.value?.results || [])
  const warmupProgress = computed(() => {
    const total = Number(startupWarmup.value?.paths_total || 0)
    const done = Number(startupWarmup.value?.paths_done || 0)
    if (total <= 0) return 0
    return Math.min(100, Math.round((done / total) * 100))
  })
  const warmupProgressStatus = computed(() => {
    if (startupWarmup.value?.running) return undefined
    if (startupWarmup.value?.error) return 'exception'
    if (!startupWarmup.value?.enabled) return 'warning'
    return 'success'
  })
  const warmupTagType = computed(() => {
    if (startupWarmup.value?.running) return 'warning'
    if (startupWarmup.value?.error) return 'danger'
    if (!startupWarmup.value?.enabled) return 'info'
    return 'success'
  })
  const warmupStatusText = computed(() => {
    if (startupWarmup.value?.running) return '预热中'
    if (startupWarmup.value?.error) return '预热异常'
    if (!startupWarmup.value?.enabled) return '未启用'
    return '已完成'
  })
  const adminBootstrapType = computed(() => {
    const action = startupStatus.value?.admin_bootstrap?.action
    if (action === 'created' || action === 'reset_password') return 'success'
    if (action === 'exists' || action === 'skipped' || action === 'not_run') return 'info'
    if (action === 'invalid_config') return 'warning'
    if (action === 'error') return 'danger'
    return 'info'
  })
  const adminBootstrapText = computed(() => {
    const action = startupStatus.value?.admin_bootstrap?.action
    if (action === 'created') return '已创建'
    if (action === 'reset_password') return '已重置密码'
    if (action === 'exists') return '已存在'
    if (action === 'invalid_config') return '配置无效'
    if (action === 'error') return '执行失败'
    if (action === 'skipped') return '已跳过'
    return '未执行'
  })

  const refreshSpider = async () => {
    spiderLoading.value = true
    try {
      const res = await getSpiderOverview()
      if (res.code === 200) {
        spiderOverview.value = res.data || {}
      }
    } catch (e) {
      ElMessage.error('加载爬虫概览失败')
    } finally {
      spiderLoading.value = false
    }
  }

  const refreshLogs = async () => {
    logsLoading.value = true
    try {
      const res = await getSpiderLogs(logLines.value)
      if (res.code === 200) {
        logs.value = res.data?.logs || []
      }
    } catch (e) {
      ElMessage.error('加载日志失败')
    } finally {
      logsLoading.value = false
    }
  }

  const startStartupPolling = () => {
    if (startupPollTimer) return
    startupPollTimer = window.setInterval(() => {
      refreshStartup()
    }, 3000)
  }

  const stopStartupPolling = () => {
    if (!startupPollTimer) return
    window.clearInterval(startupPollTimer)
    startupPollTimer = null
  }

  const syncStartupPolling = () => {
    if (startupWarmup.value?.running) {
      startStartupPolling()
    } else {
      stopStartupPolling()
    }
  }

  const refreshStartup = async () => {
    startupLoading.value = true
    try {
      const res = await getStartupStatus()
      if (res.code === 200) {
        startupStatus.value = res.data || {}
        syncStartupPolling()
      }
    } catch (e) {
      stopStartupPolling()
      ElMessage.error('加载启动状态失败')
    } finally {
      startupLoading.value = false
    }
  }

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

  const loadRecent = () => {
    try {
      const raw = localStorage.getItem('weibo_recent_tasks')
      recentTasks.value = raw ? JSON.parse(raw) : []
    } catch (e) {
      recentTasks.value = []
    }
  }

  const saveRecent = () => {
    localStorage.setItem('weibo_recent_tasks', JSON.stringify(recentTasks.value.slice(0, 20)))
  }

  const addRecent = (id) => {
    const next = [id, ...recentTasks.value.filter((x) => x !== id)]
    recentTasks.value = next.slice(0, 20)
    saveRecent()
  }

  const removeRecent = (id) => {
    recentTasks.value = recentTasks.value.filter((x) => x !== id)
    saveRecent()
  }

  const clearRecent = () => {
    recentTasks.value = []
    saveRecent()
  }

  const selectRecent = (id) => {
    taskId.value = id
    queryTask()
  }

  const queryTask = async () => {
    const id = taskId.value.trim()
    if (!id) return
    taskLoading.value = true
    try {
      const res = await getTaskStatus(id)
      if (res.code === 200) {
        taskResult.value = res.data || null
        addRecent(id)
      }
    } catch (e) {
      ElMessage.error('查询任务状态失败')
    } finally {
      taskLoading.value = false
    }
  }

  function getLogLevel(line) {
    if (line.includes('ERROR') || line.includes('CRITICAL')) return 'log-error'
    if (line.includes('WARNING')) return 'log-warn'
    if (line.includes('INFO')) return 'log-info'
    return 'log-debug'
  }

  onMounted(async () => {
    loadRecent()
    await Promise.all([refreshSpider(), refreshLogs(), refreshStartup()])
  })

  onUnmounted(() => {
    stopStartupPolling()
  })
</script>

<style lang="scss" scoped>
  .tasks-page {
    max-width: 1400px;
    margin: 0 auto;
  }

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

  .startup-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 12px 20px;
    color: $text-secondary;
    font-size: 13px;
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
</style>
