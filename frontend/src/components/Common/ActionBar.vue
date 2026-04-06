<template>
  <div
    class="action-bar"
    :class="{ 'is-sticky': sticky }"
  >
    <div class="action-bar__left">
      <slot name="left">
        <h3
          v-if="title"
          class="action-bar__title"
        >
          {{ title }}
        </h3>
        <p
          v-if="description"
          class="action-bar__description"
        >
          {{ description }}
        </p>
      </slot>
    </div>
    <div class="action-bar__right">
      <slot name="right">
        <el-button-group>
          <el-button
            v-for="action in actions"
            :key="action.key"
            :type="action.type"
            :icon="action.icon"
            :loading="action.loading"
            :disabled="action.disabled"
            @click="handleAction(action)"
          >
            {{ action.label }}
          </el-button>
        </el-button-group>
      </slot>
    </div>
  </div>
</template>

<script setup>
  defineProps({
    title: {
      type: String,
      default: '',
    },
    description: {
      type: String,
      default: '',
    },
    sticky: {
      type: Boolean,
      default: false,
    },
    actions: {
      type: Array,
      default: () => [],
    },
  })

  const emit = defineEmits(['action'])

  const handleAction = (action) => {
    if (action.callback) {
      action.callback()
    }
    emit('action', action.key)
  }
</script>

<style lang="scss" scoped>
  .action-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: #fff;
    border-radius: 8px;
    margin-bottom: 20px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);

    &.is-sticky {
      position: sticky;
      top: 0;
      z-index: 100;
    }

    &__left {
      flex: 1;
    }

    &__title {
      font-size: 18px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 4px;
    }

    &__description {
      font-size: 14px;
      color: #909399;
      margin: 0;
    }

    &__right {
      flex-shrink: 0;
      margin-left: 20px;
    }
  }
</style>
