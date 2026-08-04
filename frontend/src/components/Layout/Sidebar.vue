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
      <!-- Main analysis workflows -->
      <template v-if="!collapsed">
        <div class="menu-group-label">
          主链路分析
        </div>
      </template>
      <template
        v-for="route in analysisRoutes"
        :key="route.path"
      >
        <el-menu-item :index="route.path">
          <el-icon><component :is="route.meta.icon" /></el-icon>
          <template #title>
            {{ route.meta.title }}
          </template>
        </el-menu-item>
      </template>

      <!-- Lab / experimental features -->
      <template v-if="labRoutes.length > 0 && !collapsed">
        <div class="menu-group-label menu-group-label--lab">
          实验 / 运维
        </div>
      </template>
      <template
        v-for="route in labRoutes"
        :key="route.path"
      >
        <el-menu-item :index="route.path">
          <el-icon><component :is="route.meta.icon" /></el-icon>
          <template #title>
            {{ route.meta.title }}
            <el-tag
              size="small"
              type="warning"
              class="lab-tag"
            >
              实验
            </el-tag>
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
  collapsed: { type: Boolean, default: false },
})

const route = useRoute()
const userStore = useUserStore()

const allChildren = computed(() => {
  const parent = route.matched.find((r) => r.children && r.children.some((c) => c.meta))
  if (!parent) return []
  return parent.children.filter((child) => {
    if (!child.meta || child.meta.public) return false
    if (child.meta.adminOnly && !userStore.isAdmin) return false
    return true
  })
})

const analysisRoutes = computed(() =>
  allChildren.value.filter((r) => r.meta?.group === 'analysis')
)

const labRoutes = computed(() =>
  allChildren.value.filter((r) => r.meta?.group === 'lab')
)

const activeMenu = computed(() => route.path)
</script>

<style lang="scss" scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--el-gradient-surface);
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid var(--el-border-color-light);
  padding: 0 16px;

  .logo {
    width: 32px;
    height: 32px;
    object-fit: contain;
    flex-shrink: 0;
  }

  .title {
    font-size: 16px;
    font-weight: 700;
    color: var(--el-text-color-primary);
    white-space: nowrap;
  }
}

.sidebar-menu {
  flex: 1;
  overflow-y: auto;
  border-right: none;
  padding-top: 4px;
}

.menu-group-label {
  padding: 12px 20px 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--el-text-color-placeholder);

  &--lab {
    margin-top: 8px;
    border-top: 1px solid var(--el-border-color-light);
    padding-top: 16px;
  }
}

.lab-tag {
  margin-left: 6px;
  vertical-align: middle;
}
</style>