import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSpiderLogs, getSpiderOverview } from '@/api/spider'
import { getStartupStatus, getTaskStatus } from '@/api/tasks'

export function useTasks() {
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
    } catch (_e) {
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
    } catch (_e) {
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
    } catch (_e) {
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
    } catch (_e) {
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
    } catch (_e) {
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

  return {
    spiderLoading,
    startupLoading,
    logsLoading,
    taskLoading,
    spiderOverview,
    startupStatus,
    logs,
    logLines,
    taskId,
    taskResult,
    recentTasks,
    spiderHistory,
    startupWarmup,
    startupWarmupResults,
    warmupProgress,
    warmupProgressStatus,
    warmupTagType,
    warmupStatusText,
    adminBootstrapType,
    adminBootstrapText,
    refreshSpider,
    refreshLogs,
    refreshStartup,
    formatDateTime,
    formatDuration,
    removeRecent,
    clearRecent,
    selectRecent,
    queryTask,
    getLogLevel,
  }
}
