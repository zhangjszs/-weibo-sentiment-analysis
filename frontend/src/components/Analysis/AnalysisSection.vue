<template>
  <div class="analysis-section">
    <!-- Loading state -->
    <div
      v-if="status === 'loading'"
      class="section-loading"
    >
      <el-skeleton
        :rows="3"
        animated
      />
    </div>

    <!-- Error state -->
    <div
      v-else-if="status === 'error'"
      class="section-error"
    >
      <AnalysisEmptyState
        type="error"
        :title="errorTitle"
        :reason="errorReason"
        :action-label="retryLabel"
        @action="$emit('retry')"
      />
    </div>

    <!-- Degraded state (data available but incomplete) -->
    <div
      v-else-if="status === 'degraded'"
      class="section-degraded"
    >
      <el-alert
        :title="degradedMessage"
        type="warning"
        show-icon
        :closable="false"
        class="degraded-banner"
      />
      <div class="section-content">
        <slot />
      </div>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="status === 'empty'"
      class="section-empty"
    >
      <AnalysisEmptyState
        type="no-data"
        :title="emptyTitle"
        :reason="emptyReason"
        :action-label="emptyActionLabel"
        @action="$emit('empty-action')"
      />
    </div>

    <!-- Normal state -->
    <div
      v-else
      class="section-content"
    >
      <slot />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AnalysisEmptyState from '@/components/Common/AnalysisEmptyState.vue'

const props = defineProps({
  /** loading | empty | degraded | error | normal */
  status: { type: String, default: 'loading' },
  errorTitle: { type: String, default: '加载失败' },
  errorReason: { type: String, default: '数据加载过程中出现异常，请重试。' },
  retryLabel: { type: String, default: '重试' },
  degradedMessage: { type: String, default: '部分数据不可用，以下展示已有结果。' },
  emptyTitle: { type: String, default: '' },
  emptyReason: { type: String, default: '' },
  emptyActionLabel: { type: String, default: '' },
})

defineEmits(['retry', 'empty-action'])
</script>

<style lang="scss" scoped>
.analysis-section {
  margin-bottom: 16px;
}

.section-loading {
  padding: 40px 20px;
}

.section-error,
.section-empty {
  display: flex;
  justify-content: center;
}

.degraded-banner {
  margin-bottom: 12px;
}

.section-content {
  min-height: 60px;
}
</style>