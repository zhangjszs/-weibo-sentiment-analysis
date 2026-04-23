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
    border-radius: var(--el-border-radius-base);
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    background: var(--el-gradient-surface);
    box-shadow: var(--el-box-shadow-light);

    &:hover {
      box-shadow: var(--el-box-shadow-artistic);
      transform: translateY(-4px);
    }

    :deep(.el-card__header) {
      padding: $spacing-md $spacing-lg;
      border-bottom: 1px solid var(--el-border-color-lighter);
      background: var(--el-gradient-surface);
      position: relative;

      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 60px;
        height: 3px;
        background: var(--el-gradient-primary);
        border-radius: var(--el-border-radius-small);
      }
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
          font-size: 18px;
          font-weight: 600;
          color: $text-primary;
          letter-spacing: 0.8px;
          background: var(--el-gradient-primary);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          transition: all 0.3s ease;

          &:hover {
            transform: translateX(4px);
          }
        }
      }
    }

    .base-card-body {
      height: 100%;
      display: flex;
      flex-direction: column;
      padding: $spacing-lg;
    }
  }

  /* Dark mode overrides */
  .dark .base-card {
    background: var(--el-gradient-surface);
    border: 1px solid #334155;

    :deep(.el-card__header) {
      border-bottom-color: #334155;
      background: var(--el-gradient-surface);

      &::after {
        background: var(--el-gradient-primary);
      }
    }

    .base-card-title .title-text {
      background: var(--el-gradient-primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  }
</style>
