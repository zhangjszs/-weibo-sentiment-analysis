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
      <el-tooltip content="快速爬取" placement="bottom">
        <el-button
          circle
          :icon="Download"
          class="quick-crawl-btn"
          @click="showCrawlDialog = true"
        />
      </el-tooltip>
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
    <!-- 快速爬取弹窗 -->
    <el-dialog
      v-model="showCrawlDialog"
      title="快速爬取"
      width="420px"
      :close-on-click-modal="false"
      destroy-on-close
      @closed="stopCrawlPolling"
    >
      <el-form
        :model="crawlForm"
        label-position="top"
        class="crawl-form"
      >
        <el-form-item label="爬取类型">
          <el-radio-group v-model="crawlForm.type">
            <el-radio-button label="hot">
              <el-icon><Sunny /></el-icon> 热门微博
            </el-radio-button>
            <el-radio-button label="search">
              <el-icon><Search /></el-icon> 关键词搜索
            </el-radio-button>
            <el-radio-button label="comments">
              <el-icon><ChatLineRound /></el-icon> 评论数据
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item
          v-if="crawlForm.type === 'search'"
          label="关键词"
        >
          <el-input
            v-model="crawlForm.keyword"
            placeholder="输入搜索关键词"
            clearable
          />
        </el-form-item>

        <el-form-item label="爬取页数">
          <el-input-number
            v-model="crawlForm.pageNum"
            :min="1"
            :max="10"
            style="width: 120px"
          />
          <span class="form-hint">页数越多，数据越全，耗时越长</span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCrawlDialog = false">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="crawlLoading"
          @click="handleQuickCrawl"
        >
          开始爬取
        </el-button>
      </template>
    </el-dialog>
  </el-header>
</template>

<script setup>
  import { computed, ref, reactive, onBeforeUnmount } from 'vue'
  import {
    ArrowDown,
    ChatLineRound,
    Download,
    Expand,
    Fold,
    Moon,
    QuestionFilled,
    Search,
    Star,
    Sunny,
    SwitchButton,
    User,
  } from '@element-plus/icons-vue'
  import { useRoute, useRouter } from 'vue-router'
  import { useUserStore } from '@/stores/user'
  import { useAppStore } from '@/stores/app'
  import { ElMessage, ElMessageBox } from 'element-plus'
  import { quickCrawl, getSpiderStatus } from '@/api/spider'

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

  // 快速爬取弹窗
  const showCrawlDialog = ref(false)
  const crawlForm = reactive({
    type: 'hot',
    keyword: '',
    pageNum: 3,
  })
  const crawlLoading = ref(false)
  const crawlPollingTimer = ref(null)

  const stopCrawlPolling = () => {
    if (crawlPollingTimer.value) {
      clearInterval(crawlPollingTimer.value)
      crawlPollingTimer.value = null
    }
  }

  const startCrawlPolling = () => {
    stopCrawlPolling()
    crawlPollingTimer.value = setInterval(async () => {
      try {
        const res = await getSpiderStatus()
        if (res.code === 200 && res.data && !res.data.isRunning) {
          stopCrawlPolling()
          ElMessage.success('爬取任务已完成')
        }
      } catch (e) {
        console.error('轮询爬取状态失败:', e)
      }
    }, 3000)
  }

  const handleQuickCrawl = async () => {
    if (crawlForm.type === 'search' && !crawlForm.keyword.trim()) {
      ElMessage.warning('请输入搜索关键词')
      return
    }
    crawlLoading.value = true
    try {
      const params = {
        type: crawlForm.type,
        pageNum: crawlForm.pageNum,
      }
      if (crawlForm.type === 'search') {
        params.keyword = crawlForm.keyword.trim()
      }
      const res = await quickCrawl(params)
      if (res.code === 200) {
        ElMessage.success(res.msg || '爬取任务已启动')
        showCrawlDialog.value = false
        startCrawlPolling()
      } else {
        ElMessage.warning(res.msg || '启动失败')
      }
    } catch (e) {
      ElMessage.error('请求失败: ' + (e.message || e))
    } finally {
      crawlLoading.value = false
    }
  }

  onBeforeUnmount(() => {
    stopCrawlPolling()
  })

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

  .quick-crawl-btn {
    margin-right: 12px;
    font-size: 16px;
  }

  .crawl-form {
    .el-radio-group {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .form-hint {
      margin-left: 8px;
      color: var(--el-text-color-secondary);
      font-size: 12px;
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
