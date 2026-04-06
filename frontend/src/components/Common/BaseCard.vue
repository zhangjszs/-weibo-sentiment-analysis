<template>
  <el-card
    class="base-card"
    :shadow="shadow"
    :body-style="bodyStyle"
  >
    <template
      v-if="title || $slots.header"
      #header
    >
      <div class="base-card-header">
        <slot name="header">
          <div class="base-card-title">
            <span class="title-text">{{ title }}</span>
            <slot name="extra" />
          </div>
        </slot>
      </div>
    </template>
    <div class="base-card-body">
      <slot />
    </div>
  </el-card>
</template>

<script setup>
  defineProps({
    title: {
      type: String,
      default: '',
    },
    shadow: {
      type: String,
      default: 'hover', // always, hover, never
    },
    bodyStyle: {
      type: Object,
      default: () => ({ padding: '24px' }),
    },
  })
</script>

<style lang="scss" scoped>
  .base-card {
    // Styles inherited from global .el-card in index.scss
    :deep(.el-card__header) {
      padding: $spacing-md $spacing-lg;
      border-bottom: 1px solid var(--el-border-color-lighter);
      background-color: transparent;
    }

    .base-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .base-card-title {
        display: flex;
        align-items: center;
        width: 100%;
        justify-content: space-between;

        .title-text {
          font-size: 16px;
          font-weight: 600;
          color: $text-primary;
          letter-spacing: 0.5px;
        }
      }
    }

    .base-card-body {
      height: 100%;
      display: flex;
      flex-direction: column;
    }
  }

  /* Dark mode overrides */
  .dark .base-card {
    background-color: #1e293b;
    border: 1px solid #334155;

    :deep(.el-card__header) {
      border-bottom-color: #334155;
    }
  }
</style>
