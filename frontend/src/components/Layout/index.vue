<template>
  <el-container
    class="layout-container"
    :class="{ 'mobile-mode': isMobile }"
  >
    <el-aside
      v-if="!isMobile"
      :width="isCollapsed ? '64px' : '240px'"
      class="sidebar"
      :class="{ 'is-collapsed': isCollapsed }"
    >
      <Sidebar :collapsed="isCollapsed" />
    </el-aside>
    <el-container>
      <el-header
        class="header"
        :class="{ 'mobile-header': isMobile }"
      >
        <Header
          :is-mobile="isMobile"
          @toggle="toggleSidebar"
          @toggle-mobile="toggleMobileMenu"
        />
      </el-header>
      <TabBar v-if="!isMobile" />
      <el-main
        class="main-content"
        :class="{ 'mobile-content': isMobile }"
      >
        <router-view v-slot="{ Component }">
          <transition
            name="fade"
            mode="out-in"
          >
            <keep-alive :include="tabsStore.cachedViews">
              <component :is="Component" />
            </keep-alive>
          </transition>
        </router-view>
      </el-main>
    </el-container>
    <MobileNav v-if="isMobile" />
  </el-container>
</template>

<script setup>
  import { ref, computed, onMounted, onUnmounted } from 'vue'
  import { useAppStore } from '@/stores/app'
  import Sidebar from './Sidebar.vue'
  import Header from './Header.vue'
  import MobileNav from './MobileNav.vue'
  import TabBar from './TabBar.vue'
  import { useTabsStore } from '@/stores/tabs'

  const tabsStore = useTabsStore()
  const appStore = useAppStore()
  const isCollapsed = computed(() => appStore.sidebarCollapsed)
  const isMobile = ref(false)
  const isMobileMenuOpen = ref(false)

  const toggleSidebar = () => {
    appStore.toggleSidebar()
  }

  const toggleMobileMenu = () => {
    isMobileMenuOpen.value = !isMobileMenuOpen.value
  }

  const checkMobile = () => {
    isMobile.value = window.innerWidth < 768
  }

  onMounted(() => {
    checkMobile()
    window.addEventListener('resize', checkMobile)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', checkMobile)
  })
</script>

<style lang="scss" scoped>
  .layout-container {
    height: 100vh;
    overflow: hidden;
    background-color: var(--el-bg-color-page);
  }

  .sidebar {
    background-color: var(--el-bg-color);
    transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
    flex-shrink: 0;
    border-right: 1px solid var(--el-border-color-light);

    &.is-collapsed {
      width: 64px !important;
    }
  }

  .header {
    padding: 0;
    background: $surface-color;
    border-bottom: 1px solid var(--el-border-color-light);
    height: 64px;
    line-height: 64px;
    flex-shrink: 0;
    z-index: 10;
  }

  .main-content {
    background: var(--el-bg-color-page);
    padding: 24px;
    overflow: auto;
    height: calc(100vh - 64px - 40px);

    // Custom scrollbar
    &::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }

    &::-webkit-scrollbar-thumb {
      background: var(--el-border-color);
      border-radius: 4px;

      &:hover {
        background: var(--el-text-color-placeholder);
      }
    }

    &::-webkit-scrollbar-track {
      background: transparent;
    }

    &.mobile-content {
      padding: 12px;
      height: calc(100vh - 64px - 60px);
    }
  }

  .mobile-mode {
    .header {
      &.mobile-header {
        height: 50px;
        line-height: 50px;
      }
    }

    .main-content {
      &.mobile-content {
        padding: 12px;
      }
    }
  }
</style>
