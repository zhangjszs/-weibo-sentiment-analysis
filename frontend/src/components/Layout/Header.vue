<template>
  <el-header class="header-content">
    <div class="header-left">
      <el-icon
        class="collapse-btn"
        role="button"
        tabindex="0"
        aria-label="切换侧边栏"
        @click="$emit('toggle')"
        @keydown.enter.prevent="$emit('toggle')"
        @keydown.space.prevent="$emit('toggle')"
      >
        <Fold v-if="!appStore.sidebarCollapsed" />
        <Expand v-else />
      </el-icon>
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">
          首页
        </el-breadcrumb-item>
        <el-breadcrumb-item v-if="currentRoute.path !== '/'">
          {{
            currentRoute.meta?.title || ''
          }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="header-right">
      <el-dropdown
        trigger="click"
        @command="handleCommand"
      >
        <span class="user-info">
          <el-avatar
            :size="32"
            :src="userInfo.avatar"
            class="user-avatar"
          >
            {{ username.charAt(0).toUpperCase() }}
          </el-avatar>
          <span class="username">{{ username }}</span>
          <el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu class="user-dropdown">
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>
              个人中心
            </el-dropdown-item>
            <el-dropdown-item command="favorites">
              <el-icon><Star /></el-icon>
              我的收藏
            </el-dropdown-item>
            <el-dropdown-item command="help">
              <el-icon><QuestionFilled /></el-icon>
              帮助中心
            </el-dropdown-item>
            <el-dropdown-item command="theme">
              <el-icon><component :is="themeIcon" /></el-icon>
              {{ isDark ? '切换亮色模式' : '切换暗黑模式' }}
            </el-dropdown-item>
            <el-dropdown-item
              divided
              command="logout"
            >
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<script setup>
  import { computed } from 'vue'
  import {
    ArrowDown,
    Expand,
    Fold,
    Moon,
    QuestionFilled,
    Star,
    Sunny,
    SwitchButton,
    User,
  } from '@element-plus/icons-vue'
  import { useRoute, useRouter } from 'vue-router'
  import { useUserStore } from '@/stores/user'
  import { useAppStore } from '@/stores/app'
  import { ElMessageBox } from 'element-plus'

  defineEmits(['toggle'])

  const route = useRoute()
  const router = useRouter()
  const userStore = useUserStore()
  const appStore = useAppStore()

  const currentRoute = computed(() => route)
  const username = computed(() => userStore.username)
  const userInfo = computed(() => userStore.userInfo)
  const isDark = computed(() => appStore.theme === 'dark')
  const themeIcon = computed(() => (isDark.value ? Sunny : Moon))

  const handleCommand = (command) => {
    switch (command) {
      case 'profile':
        router.push('/profile')
        break
      case 'favorites':
        router.push('/favorites')
        break
      case 'help':
        router.push('/help')
        break
      case 'theme':
        appStore.toggleTheme()
        break
      case 'logout':
        ElMessageBox.confirm('确定要退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
          title: '提示',
        }).then(() => {
          userStore.doLogout()
        })
        break
    }
  }
</script>

<style lang="scss" scoped>
  .header-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    background: var(--el-gradient-surface);
    height: 72px;
    border-bottom: 1px solid var(--el-border-color-light);
    box-shadow: var(--el-box-shadow-light);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: var(--el-gradient-primary);
    }
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 24px;

    .collapse-btn {
      font-size: 24px;
      cursor: pointer;
      color: var(--el-text-color-regular);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      padding: 8px;
      border-radius: var(--el-border-radius-small);

      &:hover {
        color: var(--el-color-primary);
        background-color: var(--el-color-primary-light-9);
        transform: scale(1.05);
      }
    }

    :deep(.el-breadcrumb) {
      font-size: 14px;
      font-weight: 500;

      .el-breadcrumb__inner {
        color: var(--el-text-color-regular);
        transition: color 0.3s ease;

        &.is-link:hover {
          color: var(--el-color-primary);
          text-decoration: underline;
          text-decoration-thickness: 2px;
          text-decoration-color: var(--el-color-primary-light-3);
        }
      }

      .el-breadcrumb__item:last-child .el-breadcrumb__inner {
        color: var(--el-text-color-primary);
        font-weight: 600;
      }
    }
  }

  .header-right {
    display: flex;
    align-items: center;

    .user-info {
      display: flex;
      align-items: center;
      gap: 12px;
      cursor: pointer;
      padding: 8px 16px;
      border-radius: var(--el-border-radius-base);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      background-color: var(--el-bg-color);
      box-shadow: var(--el-box-shadow-lighter);

      &:hover {
        background-color: var(--el-color-primary-light-9);
        box-shadow: var(--el-box-shadow-light);
        transform: translateY(-1px);
      }

      .user-avatar {
        background: var(--el-gradient-primary);
        color: white;
        font-weight: 600;
        box-shadow: var(--el-box-shadow-light);
        transition: transform 0.3s ease;

        &:hover {
          transform: scale(1.1);
        }
      }

      .username {
        font-size: 14px;
        color: var(--el-text-color-primary);
        font-weight: 500;
        transition: color 0.3s ease;
      }

      .el-icon--right {
        color: var(--el-text-color-regular);
        transition: all 0.3s ease;
      }

      &:hover .el-icon--right {
        transform: rotate(180deg);
      }
    }
  }

  :deep(.el-dropdown-menu) {
    border-radius: var(--el-border-radius-base);
    box-shadow: var(--el-box-shadow-dark);
    border: none;
    overflow: hidden;

    .el-dropdown-item {
      padding: 10px 16px;
      transition: all 0.2s ease;
      font-weight: 500;

      &:hover {
        background-color: var(--el-color-primary-light-9);
        color: var(--el-color-primary);
      }

      .el-icon {
        margin-right: 8px;
      }
    }
  }
</style>
