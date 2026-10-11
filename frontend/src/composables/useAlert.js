import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Warning, CircleCloseFilled, InfoFilled } from '@element-plus/icons-vue'
import {
  getAlertHistory,
  getAlertStats,
  getAlertRules,
  createAlertRule,
  toggleAlertRule,
  markAllAlertsRead,
  testAlert,
} from '@/api/alert'

export function useAlert() {
  const loading = ref(false)
  const alerts = ref([])
  const stats = ref({})
  const rules = ref([])
  const filterLevel = ref('')
  const currentPage = ref(1)
  const pageSize = ref(20)
  const total = ref(0)

  const showDetailDialog = ref(false)
  const selectedAlert = ref(null)
  const showRuleDialog = ref(false)
  const testing = ref(false)
  const creating = ref(false)

  const testForm = ref({
    level: 'warning',
    message: '这是一条测试预警消息',
  })

  const ruleForm = ref({
    id: '',
    name: '',
    alert_type: 'custom',
    level: 'warning',
    cooldown_minutes: 30,
    conditions: {},
  })

  const getLevelIcon = (level) => {
    const icons = {
      info: InfoFilled,
      warning: Warning,
      danger: CircleCloseFilled,
      critical: CircleCloseFilled,
    }
    return icons[level] || InfoFilled
  }

  const getLevelClass = (level) => {
    return `level-${level}`
  }

  const getLevelTagType = (level) => {
    const types = {
      info: 'info',
      warning: 'warning',
      danger: 'danger',
      critical: 'danger',
    }
    return types[level] || 'info'
  }

  const getLevelLabel = (level) => {
    const labels = {
      info: '信息',
      warning: '警告',
      danger: '危险',
      critical: '严重',
    }
    return labels[level] || level
  }

  const getTypeLabel = (type) => {
    const labels = {
      volume_spike: '讨论量激增',
      negative_surge: '负面激增',
      sentiment_shift: '情感突变',
      hot_topic: '热点话题',
      keyword_match: '关键词匹配',
      custom: '自定义',
    }
    return labels[type] || type
  }

  const formatTime = (timeStr) => {
    if (!timeStr) return ''
    const date = new Date(timeStr)
    return date.toLocaleString()
  }

  const alertsError = ref(null)
  const statsLoading = ref(false)
  const statsError = ref(null)
  const rulesLoading = ref(false)
  const rulesError = ref(null)

  const fetchAlerts = async () => {
    loading.value = true
    alertsError.value = null
    try {
      const res = await getAlertHistory({
        limit: pageSize.value,
        level: filterLevel.value || undefined,
      })
      if (res && res.code === 200 && res.data) {
        alerts.value = res.data.alerts || []
        total.value = res.data.total || 0
      } else {
        alertsError.value = (res && res.msg) || '获取预警历史失败，请重试'
      }
    } catch (error) {
      console.error('获取预警历史失败:', error)
      alertsError.value = '获取预警历史失败，已保留原有数据'
    } finally {
      loading.value = false
    }
  }

  const fetchStats = async () => {
    statsLoading.value = true
    statsError.value = null
    try {
      const res = await getAlertStats()
      if (res && res.code === 200 && res.data) {
        stats.value = res.data
      } else {
        statsError.value = (res && res.msg) || '获取预警统计失败，请重试'
      }
    } catch (error) {
      console.error('获取预警统计失败:', error)
      statsError.value = '获取预警统计失败，已保留原有数据'
    } finally {
      statsLoading.value = false
    }
  }

  const fetchRules = async () => {
    rulesLoading.value = true
    rulesError.value = null
    try {
      const res = await getAlertRules()
      if (res && res.code === 200 && res.data) {
        rules.value = res.data.rules || []
      } else {
        rulesError.value = (res && res.msg) || '获取预警规则失败，请重试'
      }
    } catch (error) {
      console.error('获取预警规则失败:', error)
      rulesError.value = '获取预警规则失败，已保留原有数据'
    } finally {
      rulesLoading.value = false
    }
  }

  const retryAlerts = () => fetchAlerts()
  const retryStats = () => fetchStats()
  const retryRules = () => fetchRules()

  const showAlertDetail = (alert) => {
    selectedAlert.value = alert
    showDetailDialog.value = true
  }

  const handleMarkAllRead = async () => {
    try {
      const res = await markAllAlertsRead()
      if (res.code === 200) {
        ElMessage.success('已全部标记为已读')
        fetchAlerts()
        fetchStats()
      }
    } catch {
      ElMessage.error('操作失败')
    }
  }

  const handleToggleRule = async (rule) => {
    try {
      await toggleAlertRule(rule.id)
      ElMessage.success(rule.enabled ? '规则已启用' : '规则已禁用')
    } catch {
      rule.enabled = !rule.enabled
      ElMessage.error('操作失败')
    }
  }

  const handleTestAlert = async () => {
    testing.value = true
    try {
      const res = await testAlert(testForm.value)
      if (res.code === 200) {
        ElMessage.success('测试预警已发送')
        fetchAlerts()
        fetchStats()
      }
    } catch {
      ElMessage.error('发送失败')
    } finally {
      testing.value = false
    }
  }

  const handleCreateRule = async () => {
    if (!ruleForm.value.id || !ruleForm.value.name) {
      ElMessage.warning('请填写规则ID和名称')
      return
    }

    creating.value = true
    try {
      const res = await createAlertRule(ruleForm.value)
      if (res.code === 201) {
        ElMessage.success('规则创建成功')
        showRuleDialog.value = false
        fetchRules()
      }
    } catch {
      ElMessage.error('创建失败')
    } finally {
      creating.value = false
    }
  }

  onMounted(() => {
    fetchAlerts()
    fetchStats()
    fetchRules()
  })

  return {
    loading,
    alertsLoading: loading,
    alertsError,
    retryAlerts,
    statsLoading,
    statsError,
    retryStats,
    rulesLoading,
    rulesError,
    retryRules,
    alerts,
    stats,
    rules,
    filterLevel,
    currentPage,
    pageSize,
    total,
    showDetailDialog,
    selectedAlert,
    showRuleDialog,
    testing,
    creating,
    testForm,
    ruleForm,
    getLevelIcon,
    getLevelClass,
    getLevelTagType,
    getLevelLabel,
    getTypeLabel,
    formatTime,
    fetchAlerts,
    fetchStats,
    fetchRules,
    showAlertDetail,
    handleMarkAllRead,
    handleToggleRule,
    handleTestAlert,
    handleCreateRule,
  }
}
