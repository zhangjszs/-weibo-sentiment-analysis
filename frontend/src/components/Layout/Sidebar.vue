<template>
  <div class="sidebar-container">
    <div class="logo-container">
      <img
        src="@/assets/images/logo.png"
        alt="Logo"
        class="logo"
      >
      <transition name="fade">
        <span
          v-if="!collapsed"
          class="title"
        >微博舆情分析</span>
      </transition>
    </div>
    <el-menu
      :default-active="activeMenu"
      :collapse="collapsed"
      :collapse-transition="false"
      class="sidebar-menu"
      background-color="var(--el-bg-color)"
      text-color="var(--el-text-color-regular)"
      active-text-color="var(--el-color-primary)"
      router
    >
      <template
        v-for="route in menuRoutes"
        :key="route.path"
      >
        <el-menu-item :index="route.path">
          <el-icon><component :is="route.meta.icon" /></el-icon>
          <template #title>
            {{ route.meta.title }}
          </template>
        </el-menu-item>
      </template>
    </el-menu>
  </div>
</template>

<script setup>
  import { computed } from 'vue'
  import { useRoute } from 'vue-router'
  import { useUserStore } from '@/stores/user'

  defineProps({
    collapsed: {
      type: Boolean,
      default: false,
    },
  })

  const route = useRoute()
  const userStore = useUserStore()

  const menuRoutes = computed(() => {
    const parentRoute = route.matched.find((r) => r.children)?.path
    if (!parentRoute) return []

    const parent = route.matched.find((r) => r.children && r.children.some((c) => c.meta))
    const isAdmin = userStore.isAdmin
    return (
      parent?.children.filter((child) => {
        if (!child.meta || child.meta.public) return false
        if (child.meta.adminOnly && !isAdmin) return false
        return true
      }) || []
    )
  })

  const activeMenu = computed(() => route.path)
</script>

<style lang="scss" scoped>
  .sidebar-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--el-gradient-surface);
    border-right: 1px solid var(--el-border-color-light);
    box-shadow: 2px 0 10px rgba(0, 0, 0, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .logo-container {
    height: 72px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 16px;
    overflow: hidden;
    border-bottom: 1px solid var(--el-border-color-light);
    position: relative;

    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 16px;
      right: 16px;
      height: 1px;
      background: var(--el-gradient-primary);
      opacity: 0.3;
    }

    .logo {
      height: 36px;
      width: auto;
      flex-shrink: 0;
      transition: transform 0.3s ease;

      &:hover {
        transform: scale(1.05);
      }
    }

    .title {
      margin-left: 16px;
      font-size: 18px;
      font-weight: 700;
      color: var(--el-text-color-primary);
      white-space: nowrap;
      overflow: hidden;
      letter-spacing: 0.8px;
      background: var(--el-gradient-primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      transition: all 0.3s ease;
    }
  }

  .sidebar-menu {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    border-right: none;
    padding: 16px 0;

    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-track {
      background: var(--el-bg-color-page);
      border-radius: 3px;
    }

    &::-webkit-scrollbar-thumb {
      background: var(--el-border-color);
      border-radius: 3px;
      transition: background 0.3s ease;

      &:hover {
        background: var(--el-color-primary-light-3);
      }
    }

    :deep(.el-menu-item) {
      margin: 6px 16px;
      height: 52px;
      line-height: 52px;
      border-radius: var(--el-border-radius-base);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      overflow: hidden;

      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        width: 4px;
        height: 100%;
        background: var(--el-gradient-primary);
        transform: scaleY(0);
        transition: transform 0.3s ease;
        border-radius: var(--el-border-radius-small) 0 0 var(--el-border-radius-small);
      }

      &:hover {
        background-color: var(--el-color-primary-light-9) !important;
        color: var(--el-color-primary) !important;
        transform: translateX(4px);

        &::before {
          transform: scaleY(1);
        }
      }

      &.is-active {
        background-color: var(--el-color-primary-light-9) !important;
        color: var(--el-color-primary) !important;
        font-weight: 600;
        transform: translateX(4px);

        &::before {
          transform: scaleY(1);
        }
      }

      .el-icon {
        font-size: 20px;
        margin-right: 16px;
        transition: transform 0.3s ease;

        &:hover {
          transform: scale(1.1);
        }
      }
    }
  }
</style>
