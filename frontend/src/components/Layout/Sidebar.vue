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
    background-color: var(--el-bg-color); 
    border-right: 1px solid var(--el-border-color-light); 
  }

  .logo-container {
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 16px;
    overflow: hidden;
    border-bottom: 1px solid var(--el-border-color-light);

    .logo {
      height: 32px;
      width: auto;
      flex-shrink: 0;
    }

    .title {
      margin-left: 12px;
      font-size: 16px;
      font-weight: 700;
      color: var(--el-text-color-primary);
      white-space: nowrap;
      overflow: hidden;
      letter-spacing: 0.5px;
    }
  }

  .sidebar-menu {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    border-right: none;
    padding-top: 12px;

    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-thumb {
      background: var(--el-border-color);
      border-radius: 3px;
    }

    :deep(.el-menu-item) {
      margin: 4px 12px;
      height: 48px;
      line-height: 48px;
      border-radius: 8px;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

      &:hover {
        background-color: var(--el-color-primary-light-9) !important;
        color: var(--el-color-primary) !important;
      }

      &.is-active {
        background-color: var(--el-color-primary-light-9) !important;
        color: var(--el-color-primary) !important;
        font-weight: 600;
        
        &::before {
          content: '';
          position: absolute;
          left: -12px;
          top: 25%;
          height: 50%;
          width: 4px;
          border-radius: 0 4px 4px 0;
          background-color: var(--el-color-primary);
        }
      }

      .el-icon {
        font-size: 18px;
        margin-right: 12px;
      }
    }
  }
</style>
