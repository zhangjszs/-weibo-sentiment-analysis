<template>
  <div class="analysis-empty-state">
    <el-empty :image-size="imageSize">
      <template #image>
        <div class="analysis-empty-state__icon">
          <el-icon :size="iconSize">
            <component :is="iconComponent" />
          </el-icon>
        </div>
      </template>
      <template #description>
        <div class="analysis-empty-state__content">
          <p class="analysis-empty-state__title">
            {{ title }}
          </p>
          <p class="analysis-empty-state__reason">
            {{ reason }}
          </p>
        </div>
      </template>
      <template
        v-if="hasActions"
        #default
      >
        <div class="analysis-empty-state__actions">
          <slot name="actions">
            <el-button
              v-if="actionLabel"
              :type="actionType"
              @click="$emit('action')"
            >
              {{ actionLabel }}
            </el-button>
          </slot>
        </div>
      </template>
    </el-empty>
  </div>
</template>

<script setup>
import { computed, useSlots } from 'vue'
import {
  FolderDelete,
  Connection,
  Search,
  WarningFilled,
  Platform,
} from '@element-plus/icons-vue'

const props = defineProps({
  /** One of: no-data, not-connected, no-results, experimental-only, error */
  type: {
    type: String,
    default: 'no-data',
  },
  /** Override default title */
  title: {
    type: String,
    default: '',
  },
  /** Override default reason text */
  reason: {
    type: String,
    default: '',
  },
  /** Button label (omit to hide button) */
  actionLabel: {
    type: String,
    default: '',
  },
  actionType: {
    type: String,
    default: 'primary',
  },
  imageSize: {
    type: Number,
    default: 120,
  },
})

defineEmits(['action'])

const slots = useSlots()
const iconSize = computed(() => Math.max(props.imageSize * 0.55, 40))

const defaults = {
  'no-data': {
    title: '暂无数据',
    reason: '当前话题在所选时间范围内没有采集到数据。建议更换关键词或扩大时间范围。',
    icon: FolderDelete,
  },
  'not-connected': {
    title: '采集服务未连接',
    reason: '微博采集服务尚未启动或配置不完整。请检查环境配置中的 WEIBO_COOKIE 和 SPIDER_SERVICE_ENABLED。',
    icon: Connection,
  },
  'no-results': {
    title: '筛选范围无结果',
    reason: '当前筛选条件没有匹配到数据，请尝试调整话题关键词或时间范围。',
    icon: Search,
  },
  'experimental-only': {
    title: '实验能力',
    reason: '该分析目前为实验能力，数据可能不完整或不可靠。',
    icon: Platform,
  },
  error: {
    title: '分析服务异常',
    reason: '分析服务暂时不可用，请稍后重试。',
    icon: WarningFilled,
  },
}

const iconComponent = computed(() => {
  const typeDefaults = defaults[props.type]
  // Dynamic icon resolution for element-plus
  return typeDefaults?.icon || FolderDelete
})

const hasActions = computed(() => !!(props.actionLabel || slots.actions))

// Ensure defaults remain reactive
const title = computed(() => props.title || defaults[props.type]?.title || defaults['no-data'].title)
const reason = computed(() => props.reason || defaults[props.type]?.reason || defaults['no-data'].reason)
</script>

<style lang="scss" scoped>
.analysis-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  width: 100%;

  &__icon {
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--el-color-info);
    opacity: 0.6;
  }

  &__content {
    text-align: center;
    max-width: 320px;
  }

  &__title {
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 16px 0 8px;
  }

  &__reason {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    line-height: 1.6;
    margin: 0;
  }

  &__actions {
    margin-top: 20px;
  }
}
</style>