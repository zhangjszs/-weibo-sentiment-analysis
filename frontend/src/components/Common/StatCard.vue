<template>
  <el-card
    class="stat-card"
    :body-style="{ padding: '24px' }"
  >
    <div class="stat-content">
      <div
        class="stat-icon"
        :style="{
          backgroundColor: bgColor,
          color: iconColor,
        }"
      >
        <el-icon :size="24">
          <component :is="icon" />
        </el-icon>
      </div>
      <div class="stat-info">
        <div class="stat-label">
          {{ label }}
        </div>
        <div
          class="stat-value"
          :title="formattedValue"
        >
          {{ formattedValue }}
        </div>
      </div>
    </div>
    <div
      v-if="$slots.footer"
      class="stat-footer"
    >
      <slot name="footer" />
    </div>
  </el-card>
</template>

<script setup>
  import { computed } from 'vue'

  const props = defineProps({
    value: {
      type: [String, Number],
      required: true,
    },
    label: {
      type: String,
      default: '',
    },
    icon: {
      type: String,
      default: 'DataLine',
    },
    bgColor: {
      type: String,
      default: '#EFF6FF', // Blue 50
    },
    iconColor: {
      type: String,
      default: '#2563EB', // Blue 600
    },
  })

  const formattedValue = computed(() => {
    if (typeof props.value === 'number') {
      return props.value.toLocaleString()
    }
    return props.value
  })
</script>

<style lang="scss" scoped>
  .stat-card {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    border: none !important;
    background: var(--el-gradient-surface);
    border-radius: var(--el-border-radius-base);
    box-shadow: var(--el-box-shadow-light);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 4px;
      height: 100%;
      background: var(--el-gradient-primary);
      border-radius: var(--el-border-radius-small) 0 0 var(--el-border-radius-small);
    }

    &:hover {
      transform: translateY(-8px);
      box-shadow: var(--el-box-shadow-artistic);
    }
  }

  .stat-content {
    display: flex;
    align-items: center;
    gap: 24px;
    position: relative;
    z-index: 2;
  }

  .stat-icon {
    width: 64px;
    height: 64px;
    border-radius: var(--el-border-radius-base);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: var(--el-box-shadow-light);
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 100%);
      z-index: 1;
    }

    .el-icon {
      position: relative;
      z-index: 2;
      transition: transform 0.3s ease;
    }
  }

  .stat-card:hover .stat-icon {
    transform: scale(1.1) rotate(5deg);
    box-shadow: var(--el-box-shadow-dark);
  }

  .stat-card:hover .stat-icon .el-icon {
    transform: scale(1.1);
  }

  .stat-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    position: relative;
    z-index: 2;
  }

  .stat-label {
    font-size: 14px;
    color: $text-secondary;
    font-weight: 500;
    margin-bottom: 8px;
    letter-spacing: 0.5px;
    transition: color 0.3s ease;
  }

  .stat-card:hover .stat-label {
    color: var(--el-color-primary);
  }

  .stat-value {
    font-size: 32px;
    font-weight: 700;
    color: $text-primary;
    line-height: 1.1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-family: 'Inter', $font-family-base;
    letter-spacing: -0.8px;
    font-variant-numeric: tabular-nums;
    transition: all 0.3s ease;
    background: var(--el-gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .stat-card:hover .stat-value {
    transform: translateX(4px);
  }

  .stat-footer {
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid var(--el-border-color-light);
    position: relative;
    z-index: 2;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 60px;
      height: 1px;
      background: var(--el-gradient-primary);
    }
  }

  /* Dark mode overrides */
  .dark .stat-card {
    background: var(--el-gradient-surface);
    box-shadow: var(--el-box-shadow-dark);

    &::before {
      background: var(--el-gradient-primary);
    }

    .stat-icon {
      box-shadow: var(--el-box-shadow-dark);
    }

    .stat-label {
      color: var(--el-text-color-secondary);

      &:hover {
        color: var(--el-color-primary);
      }
    }

    .stat-value {
      background: var(--el-gradient-primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .stat-footer {
      border-top-color: #334155;

      &::before {
        background: var(--el-gradient-primary);
      }
    }
  }
</style>
