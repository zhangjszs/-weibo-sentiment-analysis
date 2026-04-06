<template>
  <div class="alert-center-container">
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

    <el-row :gutter="24">
      <el-col
        :xs="24"
        :lg="16"
      >
        <el-card class="history-card">
          <template #header>
            <div class="card-header">
              <span>预警历史</span>
              <div class="header-actions">
                <el-select
                  v-model="filterLevel"
                  placeholder="预警级别"
                  clearable
                  size="small"
                  style="width: 120px"
                >
                  <el-option
                    label="全部"
                    value=""
                  />
                  <el-option
                    label="信息"
                    value="info"
                  />
                  <el-option
                    label="警告"
                    value="warning"
                  />
                  <el-option
                    label="危险"
                    value="danger"
                  />
                  <el-option
                    label="严重"
                    value="critical"
                  />
                </el-select>
                <el-button
                  type="primary"
                  size="small"
                  :disabled="stats.unread_count === 0"
                  @click="handleMarkAllRead"
                >
                  全部已读
                </el-button>
              </div>
            </div>
          </template>

          <el-table
            v-loading="loading"
            :data="alerts"
            style="width: 100%"
          >
            <el-table-column
              width="60"
              align="center"
            >
              <template #default="{ row }">
                <el-icon
                  :class="getLevelClass(row.level)"
                  size="20"
                >
                  <component :is="getLevelIcon(row.level)" />
                </el-icon>
              </template>
            </el-table-column>
            <el-table-column
              prop="title"
              label="标题"
              min-width="150"
            />
            <el-table-column
              prop="message"
              label="内容"
              min-width="250"
              show-overflow-tooltip
            />
            <el-table-column
              prop="level"
              label="级别"
              width="100"
              align="center"
            >
              <template #default="{ row }">
                <el-tag
                  :type="getLevelTagType(row.level)"
                  size="small"
                >
                  {{ getLevelLabel(row.level) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              prop="alert_type"
              label="类型"
              width="120"
              align="center"
            >
              <template #default="{ row }">
                {{ getTypeLabel(row.alert_type) }}
              </template>
            </el-table-column>
            <el-table-column
              prop="created_at"
              label="时间"
              width="180"
              align="center"
            >
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column
              label="状态"
              width="80"
              align="center"
            >
              <template #default="{ row }">
                <el-tag
                  v-if="!row.is_read"
                  type="danger"
                  size="small"
                >
                  未读
                </el-tag>
                <el-tag
                  v-else
                  type="info"
                  size="small"
                >
                  已读
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              label="操作"
              width="100"
              align="center"
            >
              <template #default="{ row }">
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="showAlertDetail(row)"
                >
                  详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="pageSize"
              :total="total"
              layout="total, prev, pager, next"
              @current-change="fetchAlerts"
            />
          </div>
        </el-card>
      </el-col>

      <el-col
        :xs="24"
        :lg="8"
      >
        <el-card class="rules-card">
          <template #header>
            <div class="card-header">
              <span>预警规则</span>
              <el-button
                type="primary"
                size="small"
                @click="showRuleDialog = true"
              >
                新增规则
              </el-button>
            </div>
          </template>

          <div class="rules-list">
            <div
              v-for="rule in rules"
              :key="rule.id"
              class="rule-item"
            >
              <div class="rule-info">
                <div class="rule-name">
                  {{ rule.name }}
                </div>
                <div class="rule-type">
                  {{ getTypeLabel(rule.alert_type) }}
                </div>
              </div>
              <div class="rule-actions">
                <el-switch
                  v-model="rule.enabled"
                  @change="handleToggleRule(rule)"
                />
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="test-card mt-4">
          <template #header>
            <span>测试预警</span>
          </template>
          <el-form
            :model="testForm"
            label-position="top"
          >
            <el-form-item label="预警级别">
              <el-select
                v-model="testForm.level"
                style="width: 100%"
              >
                <el-option
                  label="信息"
                  value="info"
                />
                <el-option
                  label="警告"
                  value="warning"
                />
                <el-option
                  label="危险"
                  value="danger"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="消息内容">
              <el-input
                v-model="testForm.message"
                type="textarea"
                :rows="2"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :loading="testing"
                @click="handleTestAlert"
              >
                发送测试预警
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog
      v-model="showDetailDialog"
      title="预警详情"
      width="500px"
    >
      <el-descriptions
        v-if="selectedAlert"
        :column="1"
        border
      >
        <el-descriptions-item label="预警标题">
          {{ selectedAlert.title }}
        </el-descriptions-item>
        <el-descriptions-item label="预警级别">
          <el-tag :type="getLevelTagType(selectedAlert.level)">
            {{ getLevelLabel(selectedAlert.level) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="预警类型">
          {{
            getTypeLabel(selectedAlert.alert_type)
          }}
        </el-descriptions-item>
        <el-descriptions-item label="预警内容">
          {{ selectedAlert.message }}
        </el-descriptions-item>
        <el-descriptions-item label="触发时间">
          {{
            formatTime(selectedAlert.created_at)
          }}
        </el-descriptions-item>
        <el-descriptions-item
          v-if="selectedAlert.data"
          label="附加数据"
        >
          <pre class="data-json">{{ JSON.stringify(selectedAlert.data, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog
      v-model="showRuleDialog"
      title="新增预警规则"
      width="500px"
    >
      <el-form
        :model="ruleForm"
        label-position="top"
      >
        <el-form-item label="规则ID">
          <el-input
            v-model="ruleForm.id"
            placeholder="唯一标识符"
          />
        </el-form-item>
        <el-form-item label="规则名称">
          <el-input
            v-model="ruleForm.name"
            placeholder="规则显示名称"
          />
        </el-form-item>
        <el-form-item label="预警类型">
          <el-select
            v-model="ruleForm.alert_type"
            style="width: 100%"
          >
            <el-option
              label="讨论量激增"
              value="volume_spike"
            />
            <el-option
              label="负面舆情激增"
              value="negative_surge"
            />
            <el-option
              label="情感突变"
              value="sentiment_shift"
            />
            <el-option
              label="热点话题"
              value="hot_topic"
            />
            <el-option
              label="关键词匹配"
              value="keyword_match"
            />
            <el-option
              label="自定义"
              value="custom"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="预警级别">
          <el-select
            v-model="ruleForm.level"
            style="width: 100%"
          >
            <el-option
              label="信息"
              value="info"
            />
            <el-option
              label="警告"
              value="warning"
            />
            <el-option
              label="危险"
              value="danger"
            />
            <el-option
              label="严重"
              value="critical"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="冷却时间(分钟)">
          <el-input-number
            v-model="ruleForm.cooldown_minutes"
            :min="1"
            :max="1440"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRuleDialog = false">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="creating"
          @click="handleCreateRule"
        >
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
  import { ref, onMounted, computed } from 'vue'
  import { ElMessage } from 'element-plus'
  import { Bell, Warning, CircleCloseFilled, Setting, InfoFilled } from '@element-plus/icons-vue'
  import {
    getAlertHistory,
    getAlertStats,
    getAlertRules,
    createAlertRule,
    toggleAlertRule,
    markAllAlertsRead,
    testAlert,
  } from '@/api/alert'

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

  const fetchAlerts = async () => {
    loading.value = true
    try {
      const res = await getAlertHistory({
        limit: pageSize.value,
        level: filterLevel.value || undefined,
      })
      if (res.code === 200) {
        alerts.value = res.data.alerts
        total.value = res.data.total
      }
    } catch (error) {
      console.error('获取预警历史失败:', error)
    } finally {
      loading.value = false
    }
  }

  const fetchStats = async () => {
    try {
      const res = await getAlertStats()
      if (res.code === 200) {
        stats.value = res.data
      }
    } catch (error) {
      console.error('获取预警统计失败:', error)
    }
  }

  const fetchRules = async () => {
    try {
      const res = await getAlertRules()
      if (res.code === 200) {
        rules.value = res.data.rules
      }
    } catch (error) {
      console.error('获取预警规则失败:', error)
    }
  }

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
    } catch (error) {
      ElMessage.error('操作失败')
    }
  }

  const handleToggleRule = async (rule) => {
    try {
      await toggleAlertRule(rule.id)
      ElMessage.success(rule.enabled ? '规则已启用' : '规则已禁用')
    } catch (error) {
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
    } catch (error) {
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
    } catch (error) {
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
</script>

<style lang="scss" scoped>
  .alert-center-container {
    .stat-card {
      .stat-content {
        display: flex;
        align-items: center;

        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          margin-right: 16px;

          &.info {
            background: var(--el-color-info-light-8);
            color: var(--el-color-info);
          }
          &.warning {
            background: var(--el-color-warning-light-8);
            color: var(--el-color-warning);
          }
          &.danger {
            background: var(--el-color-danger-light-8);
            color: var(--el-color-danger);
          }
          &.success {
            background: var(--el-color-success-light-8);
            color: var(--el-color-success);
          }
        }

        .stat-info {
          .stat-value {
            font-size: 24px;
            font-weight: 600;
          }
          .stat-label {
            font-size: 14px;
            color: var(--el-text-color-secondary);
          }
        }
      }
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-actions {
        display: flex;
        gap: 12px;
      }
    }

    .level-info {
      color: var(--el-color-info);
    }
    .level-warning {
      color: var(--el-color-warning);
    }
    .level-danger {
      color: var(--el-color-danger);
    }
    .level-critical {
      color: var(--el-color-danger);
    }

    .pagination-container {
      margin-top: 16px;
      display: flex;
      justify-content: flex-end;
    }

    .rules-list {
      .rule-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px;
        border-bottom: 1px solid var(--el-border-color-lighter);

        &:last-child {
          border-bottom: none;
        }

        .rule-info {
          .rule-name {
            font-weight: 500;
          }
          .rule-type {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
      }
    }

    .data-json {
      background: var(--el-fill-color-light);
      padding: 8px;
      border-radius: 4px;
      font-size: 12px;
      max-height: 200px;
      overflow: auto;
    }

    .mt-4 {
      margin-top: 16px;
    }
    .mb-4 {
      margin-bottom: 16px;
    }
  }
</style>
