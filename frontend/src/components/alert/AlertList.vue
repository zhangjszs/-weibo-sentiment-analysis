<template>
  <el-card class="history-card">
    <template #header>
      <div class="card-header">
        <span>预警历史</span>
        <div class="header-actions">
          <el-select
            :model-value="filterLevel"
            placeholder="预警级别"
            clearable
            size="small"
            style="width: 120px"
            @update:model-value="$emit('update:filterLevel', $event)"
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
            @click="$emit('markAllRead')"
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
            @click="$emit('showDetail', row)"
          >
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-container">
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @update:current-page="$emit('update:currentPage', $event)"
        @current-change="$emit('pageChange', $event)"
      />
    </div>
  </el-card>
</template>

<script setup>
import { Warning, CircleCloseFilled, InfoFilled } from '@element-plus/icons-vue'

defineProps({
  alerts: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  filterLevel: {
    type: String,
    default: '',
  },
  currentPage: {
    type: Number,
    default: 1,
  },
  pageSize: {
    type: Number,
    default: 20,
  },
  total: {
    type: Number,
    default: 0,
  },
  stats: {
    type: Object,
    default: () => ({}),
  },
})

defineEmits(['update:filterLevel', 'update:currentPage', 'markAllRead', 'pageChange', 'showDetail'])

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
</script>

<style lang="scss" scoped>
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
</style>
