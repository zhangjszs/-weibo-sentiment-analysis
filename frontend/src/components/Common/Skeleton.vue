<template>
  <div
    class="skeleton-wrapper"
    :style="wrapperStyle"
  >
    <template
      v-for="(row, rowIndex) in rows"
      :key="rowIndex"
    >
      <div class="skeleton-row">
        <template
          v-for="(item, itemIndex) in row"
          :key="itemIndex"
        >
          <div
            class="skeleton-item"
            :style="getItemStyle(item)"
          >
            <div
              v-if="item.avatar"
              class="skeleton-avatar"
            />
            <div
              v-if="item.title"
              class="skeleton-title"
            />
            <div
              v-if="item.text"
              class="skeleton-text"
            />
          </div>
        </template>
      </div>
    </template>
  </div>
</template>

<script setup>
  import { computed } from 'vue'

  const props = defineProps({
    rows: {
      type: Array,
      default: () => [
        [{ title: true, text: 3 }],
        [{ avatar: true }, { title: true }, { text: 2 }],
        [{ title: true, text: 4 }],
      ],
    },
    height: {
      type: String,
      default: '200px',
    },
    animated: {
      type: Boolean,
      default: true,
    },
  })

  const wrapperStyle = computed(() => ({
    height: props.height,
  }))

  const getItemStyle = (item) => {
    const styles = {}

    if (item.width) {
      styles.width = typeof item.width === 'number' ? `${item.width}px` : item.width
    }

    if (item.height) {
      styles.height = typeof item.height === 'number' ? `${item.height}px` : item.height
    }

    return styles
  }
</script>

<style lang="scss" scoped>
  .skeleton-wrapper {
    padding: 20px;
  }

  .skeleton-row {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .skeleton-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .skeleton-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(90deg, #f5f5f5 25%, #eaeaea 50%, #f5f5f5 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s ease-in-out infinite;
  }

  .skeleton-title {
    width: 60%;
    height: 20px;
    border-radius: 6px;
    background: linear-gradient(90deg, #f5f5f5 25%, #eaeaea 50%, #f5f5f5 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s ease-in-out infinite;
  }

  .skeleton-text {
    width: 100%;
    height: 14px;
    border-radius: 6px;
    background: linear-gradient(90deg, #f5f5f5 25%, #eaeaea 50%, #f5f5f5 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s ease-in-out infinite;

    &:nth-child(2) {
      width: 80%;
    }

    &:nth-child(3) {
      width: 60%;
    }
  }

  @keyframes shimmer {
    0% {
      background-position: -200% 0;
    }
    100% {
      background-position: 200% 0;
    }
  }
</style>
