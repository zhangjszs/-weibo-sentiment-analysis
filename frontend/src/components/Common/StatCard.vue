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

    // Hover effect is handled globally by .el-card in index.scss
  }

  .stat-content {
    display: flex;
    align-items: center;
    gap: 20px;
  }

  .stat-icon {
    width: 56px;
    height: 56px;
    border-radius: 16px; // Soft square
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: transform 0.3s ease;
  }

  .stat-card:hover .stat-icon {
    transform: scale(1.05);
  }

  .stat-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .stat-label {
    font-size: 14px;
    color: $text-secondary;
    font-weight: 500;
    margin-bottom: 4px;
  }

  .stat-value {
    font-size: 28px;
    font-weight: 700;
    color: $text-primary;
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-family: 'SF Pro Display', $font-family-base; // Use display font if available
    letter-spacing: -0.5px;
    font-variant-numeric: tabular-nums;
  }

  .stat-footer {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid $border-color-light;
  }
</style>
