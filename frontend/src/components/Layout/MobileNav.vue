<template>
  <div v-if="isMobile" class="mobile-nav">
    <router-link
      v-for="item in navItems"
      :key="item.path"
      :to="item.path"
      class="nav-item"
      :class="{ active: isActive(item.path) }"
    >
      <el-icon :size="20">
        <component :is="item.icon" />
      </el-icon>
      <span class="nav-label">{{ item.label }}</span>
    </router-link>
  </div>
</template>

<script setup>
  import {
    Bell,
    ChatDotRound,
    DataAnalysis,
    HomeFilled,
    TrendCharts,
  } from '@element-plus/icons-vue'
  import { useRoute } from 'vue-router'

  // R-1（#72）：受控组件——isMobile 由 Layout 以 prop 传入，本文件不再持有
  // 自有 ref/listener/768 字面量，全仓唯一判定点在 Layout/index.vue。
  defineProps({
    isMobile: {
      type: Boolean,
      default: false,
    },
  })

  const route = useRoute()

  const navItems = [
    { path: '/home', label: '首页', icon: HomeFilled },
    { path: '/sentiment-analysis', label: '舆情', icon: TrendCharts },
    { path: '/comment-analysis', label: '评论', icon: ChatDotRound },
    { path: '/alert-center', label: '预警', icon: Bell },
    { path: '/hot-words', label: '热词', icon: DataAnalysis },
  ]

  const isActive = (path) => {
    return route.path === path || route.path.startsWith(path + '/')
  }
</script>

<style lang="scss" scoped>
  .mobile-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    display: flex;
    justify-content: space-around;
    align-items: center;
    height: 60px;
    background: var(--el-bg-color);
    border-top: 1px solid var(--el-border-color-light);
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
    z-index: 1000;

    .nav-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      flex: 1;
      padding: 8px;
      color: var(--el-text-color-secondary);
      text-decoration: none;
      transition: color 0.2s;

      &.active {
        color: var(--el-color-primary);
      }

      .nav-label {
        font-size: 12px;
        margin-top: 4px;
      }
    }
  }
</style>
