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
    background: var(--el-gradient-surface);
    position: relative;
  }

  .sidebar {
    background: var(--el-gradient-surface);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
    flex-shrink: 0;
    border-right: 1px solid var(--el-border-color-light);
    box-shadow: 2px 0 10px rgba(0, 0, 0, 0.05);

    &.is-collapsed {
      width: 64px !important;
      box-shadow: 1px 0 5px rgba(0, 0, 0, 0.05);
    }
  }

  .header {
    padding: 0;
    background: var(--el-gradient-surface);
    border-bottom: 1px solid var(--el-border-color-light);
    height: 72px;
    line-height: 72px;
    flex-shrink: 0;
    z-index: 10;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  }

  .main-content {
    background: var(--el-bg-color-page);
    padding: 32px;
    overflow: auto;
    height: calc(100vh - 72px - 40px);
    position: relative;

    // Artistic background element
    &::before {
      content: '';
      position: fixed;
      top: 72px;
      right: 0;
      width: 300px;
      height: 300px;
      background: var(--el-gradient-primary);
      opacity: 0.05;
      border-radius: 50%;
      transform: translate(50%, -50%);
      z-index: 1;
      pointer-events: none;
    }

    // Custom scrollbar
    &::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }

    &::-webkit-scrollbar-track {
      background: var(--el-bg-color-page);
      border-radius: 4px;
    }

    &::-webkit-scrollbar-thumb {
      background: var(--el-border-color);
      border-radius: 4px;
      transition: all 0.3s ease;

      &:hover {
        background: var(--el-color-primary-light-3);
      }
    }

    &.mobile-content {
      padding: 16px;
      height: calc(100vh - 72px - 60px);
    }
  }

  .mobile-mode {
    .header {
      &.mobile-header {
        height: 60px;
        line-height: 60px;
      }
    }

    .main-content {
      &.mobile-content {
        padding: 16px;
      }
    }
  }

  // Smooth transitions
  .fade-enter-active,
  .fade-leave-active {
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .fade-enter-from {
    opacity: 0;
    transform: translateY(20px);
  }

  .fade-leave-to {
    opacity: 0;
    transform: translateY(-20px);
  }
</style>
