<template>
  <span
    class="provenance-badge"
    :class="[`provenance-badge--${type}`, sizeClass]"
    :title="badgeTitle"
  >
    <span class="provenance-badge__dot" />
    <span class="provenance-badge__label">{{ badgeLabel }}</span>
    <el-tooltip
      v-if="showTooltip && meta && meta.limitations && meta.limitations.length > 0"
      :content="meta.limitations.join('; ')"
      placement="top"
      effect="dark"
    >
      <el-icon class="provenance-badge__info" :size="14"><WarningFilled /></el-icon>
    </el-tooltip>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { WarningFilled } from '@element-plus/icons-vue'

const props = defineProps({
  meta: {
    type: Object,
    default: null,
  },
  sourceType: {
    type: String,
    default: null, // override meta.source_type if provided directly
  },
  size: {
    type: String,
    default: 'default', // small, default, large
  },
  showTooltip: {
    type: Boolean,
    default: true,
  },
})

const type = computed(() => props.sourceType || props.meta?.source_type || 'unknown')

const badgeLabel = computed(() => {
  const map = {
    real: '真实数据',
    demo: '演示数据',
    experimental: '实验能力',
    unknown: '未知来源',
  }
  return map[type.value] || map.unknown
})

const badgeTitle = computed(() => {
  if (!props.meta) return badgeLabel.value
  const { source_name, source_type, model_name, data_count } = props.meta
  const parts = [badgeLabel.value]
  if (source_name) parts.push(`来源: ${source_name}`)
  if (data_count !== undefined) parts.push(`数据量: ${data_count}`)
  if (model_name) parts.push(`模型: ${model_name}`)
  return parts.join(' | ')
})

const sizeClass = computed(() => `provenance-badge--${props.size}`)
</script>

<style lang="scss" scoped>
.provenance-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.5;
  white-space: nowrap;
  user-select: none;

  &__dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  &__label {
    flex-shrink: 0;
  }

  &__info {
    cursor: help;
    opacity: 0.6;
    transition: opacity 0.2s;
    &:hover { opacity: 1; }
  }

  /* ---------- type colours ---------- */
  &--real {
    background: #ecfdf5;
    color: #065f46;
    .provenance-badge__dot { background: #10b981; }
  }
  &--demo {
    background: #fffbeb;
    color: #92400e;
    .provenance-badge__dot { background: #f59e0b; }
  }
  &--experimental {
    background: #f0f9ff;
    color: #075985;
    .provenance-badge__dot { background: #0ea5e9; }
  }
  &--unknown {
    background: #f9fafb;
    color: #6b7280;
    .provenance-badge__dot { background: #9ca3af; }
  }

  /* ---------- sizes ---------- */
  &--small { font-size: 10px; padding: 1px 6px; }
  &--large { font-size: 14px; padding: 4px 12px; gap: 6px; }
}

/* Dark mode */
.dark {
  .provenance-badge--real { background: #064e3b; color: #a7f3d0; }
  .provenance-badge--demo { background: #78350f; color: #fde68a; }
  .provenance-badge--experimental { background: #0c4a6e; color: #bae6fd; }
  .provenance-badge--unknown { background: #374151; color: #d1d5db; }
}
</style>