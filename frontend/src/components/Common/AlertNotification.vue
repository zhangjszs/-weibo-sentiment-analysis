<template>
  <div class="alert-notification">
    <el-popover
      v-model:visible="popoverVisible"
      placement="bottom"
      :width="380"
      trigger="click"
    >
      <template #reference>
        <el-badge
          :value="unreadCount"
          :hidden="unreadCount === 0"
          :max="99"
        >
          <el-button
            :icon="Bell"
            circle
          />
        </el-badge>
      </template>

      <div class="alert-popover">
        <div class="alert-header">
          <span class="title">预警通知</span>
          <el-button
            type="primary"
            link
            size="small"
            :disabled="unreadCount === 0"
            @click="handleMarkAllRead"
          >
            全部已读
          </el-button>
        </div>

        <el-tabs
          v-model="activeTab"
          class="alert-tabs"
        >
          <el-tab-pane
            label="全部"
            name="all"
          />
          <el-tab-pane
            label="未读"
            name="unread"
          />
        </el-tabs>

        <div
          v-loading="loading"
          class="alert-list"
        >
          <template v-if="alerts.length > 0">
            <div
              v-for="alert in alerts"
              :key="alert.id"
              class="alert-item"
              :class="{ unread: !alert.is_read }"
              @click="handleAlertClick(alert)"
            >
              <div class="alert-icon">
                <el-icon :class="getLevelClass(alert.level)">
                  <component :is="getLevelIcon(alert.level)" />
                </el-icon>
              </div>
              <div class="alert-content">
                <div class="alert-title">
                  {{ alert.title }}
                </div>
                <div class="alert-message">
                  {{ alert.message }}
                </div>
                <div class="alert-time">
                  {{ formatTime(alert.created_at) }}
                </div>
              </div>
            </div>
          </template>
          <el-empty
            v-else
            description="暂无预警"
            :image-size="60"
          />
        </div>

        <div class="alert-footer">
          <el-button
            type="primary"
            link
            @click="goToAlertCenter"
          >
            查看全部预警
          </el-button>
        </div>
      </div>
    </el-popover>
  </div>
</template>

<script setup>
  import { ref, onMounted, onUnmounted, watch } from 'vue'
  import { useRouter } from 'vue-router'
  import { ElMessage } from 'element-plus'
  import {
    Bell,
    Warning,
    InfoFilled,
    CircleCloseFilled,
  } from '@element-plus/icons-vue'
  import { getAlertHistory, getUnreadCount, markAlertRead, markAllAlertsRead } from '@/api/alert'
  import websocketClient from '@/utils/websocket'
  import { useUserStore } from '@/stores/user'

  const router = useRouter()
  const userStore = useUserStore()

  const popoverVisible = ref(false)
  const activeTab = ref('all')
  const loading = ref(false)
  const alerts = ref([])
  const unreadCount = ref(0)

  let messageHandler = null

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
    const classes = {
      info: 'level-info',
      warning: 'level-warning',
      danger: 'level-danger',
      critical: 'level-critical',
    }
    return classes[level] || 'level-info'
  }

  const formatTime = (timeStr) => {
    const date = new Date(timeStr)
    const now = new Date()
    const diff = now - date

    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
    return date.toLocaleDateString()
  }

  const fetchAlerts = async () => {
    loading.value = true
    try {
      const res = await getAlertHistory({ limit: 10 })
      if (res.code === 200) {
        alerts.value = res.data.alerts
      }
    } catch (error) {
      // 获取预警失败，静默处理
    } finally {
      loading.value = false
    }
  }

  const fetchUnreadCount = async () => {
    try {
      const res = await getUnreadCount()
      if (res.code === 200) {
        unreadCount.value = res.data.unread_count
      }
    } catch (error) {
      // 获取未读数量失败，静默处理
    }
  }

  const handleAlertClick = async (alert) => {
    if (!alert.is_read) {
      try {
        await markAlertRead(alert.id)
        alert.is_read = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      } catch (error) {
        // 标记已读失败，静默处理
      }
    }
  }

  const handleMarkAllRead = async () => {
    try {
      const res = await markAllAlertsRead()
      if (res.code === 200) {
        alerts.value.forEach((a) => (a.is_read = true))
        unreadCount.value = 0
        ElMessage.success('已全部标记为已读')
      }
    } catch (error) {
      ElMessage.error('操作失败')
    }
  }

  const goToAlertCenter = () => {
    popoverVisible.value = false
    router.push('/alert-center')
  }

  const handleWebSocketMessage = (data) => {
    if (data.type === 'alert') {
      alerts.value.unshift(data.data)
      if (!data.data.is_read) {
        unreadCount.value++
      }
      ElMessage({
        message: data.title || '新预警通知',
        type: data.level === 'danger' || data.level === 'critical' ? 'error' : 'warning',
        duration: 5000,
      })
    }
  }

  const connectWebSocket = (token) => {
    if (!token) {
      return
    }

    if (!messageHandler) {
      messageHandler = (data) => handleWebSocketMessage(data)
      websocketClient.on('message', messageHandler)
    }

    if (websocketClient.isConnected) {
      websocketClient.authenticate(token)
      return
    }

    websocketClient.connect(token)
  }

  onMounted(() => {
    fetchAlerts()
    fetchUnreadCount()
  })

  watch(
    () => userStore.token,
    (nextToken) => {
      if (!nextToken) {
        websocketClient.disconnect()
        return
      }

      connectWebSocket(nextToken)
    },
    { immediate: true }
  )

  onUnmounted(() => {
    if (messageHandler) {
      websocketClient.off('message', messageHandler)
    }
    websocketClient.disconnect()
  })
</script>

<style lang="scss" scoped>
  .alert-notification {
    .alert-popover {
      .alert-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--el-border-color-lighter);

        .title {
          font-size: 16px;
          font-weight: 600;
        }
      }

      .alert-tabs {
        margin-top: 8px;
      }

      .alert-list {
        max-height: 400px;
        overflow-y: auto;

        .alert-item {
          display: flex;
          padding: 12px;
          border-radius: 8px;
          cursor: pointer;
          transition: background-color 0.2s;

          &:hover {
            background-color: var(--el-fill-color-light);
          }

          &.unread {
            background-color: var(--el-color-primary-light-9);
          }

          .alert-icon {
            margin-right: 12px;
            font-size: 20px;

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
          }

          .alert-content {
            flex: 1;
            min-width: 0;

            .alert-title {
              font-weight: 500;
              margin-bottom: 4px;
            }

            .alert-message {
              font-size: 13px;
              color: var(--el-text-color-secondary);
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }

            .alert-time {
              font-size: 12px;
              color: var(--el-text-color-placeholder);
              margin-top: 4px;
            }
          }
        }
      }

      .alert-footer {
        padding-top: 12px;
        border-top: 1px solid var(--el-border-color-lighter);
        text-align: center;
      }
    }
  }
</style>
