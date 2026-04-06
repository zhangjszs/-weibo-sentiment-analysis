<template>
  <div
    v-if="show"
    class="tag-view"
  >
    <div class="tag-scroll">
      <div
        ref="tagListRef"
        class="tag-list"
      >
        <router-link
          v-for="tag in visitedViews"
          :key="tag.path"
          :to="{ path: tag.path, query: tag.query, fullPath: tag.fullPath }"
          class="tag-item"
          :class="{ 'is-active': isActive(tag) }"
          @click.middle="closeTag(tag)"
          @contextmenu.prevent="openMenu(tag, $event)"
        >
          {{ tag.title }}
          <el-icon
            v-if="!tag.meta.affix"
            class="tag-close"
            @click.prevent.stop="closeTag(tag)"
          >
            <Close />
          </el-icon>
        </router-link>
      </div>
    </div>

    <el-dropdown
      class="tag-more"
      trigger="click"
      @command="handleCommand"
    >
      <el-icon><MoreFilled /></el-icon>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="refresh">
            <el-icon><Refresh /></el-icon>
            刷新当前
          </el-dropdown-item>
          <el-dropdown-item
            command="closeOthers"
            :disabled="activeTag.path === visitedViews[visitedViews.length - 1]?.path"
          >
            <el-icon><Close /></el-icon>
            关闭其他
          </el-dropdown-item>
          <el-dropdown-item command="closeAll">
            <el-icon><Remove /></el-icon>
            关闭所有
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>

    <ul
      v-show="visible"
      class="context-menu"
      :style="{ left: menuLeft + 'px', top: menuTop + 'px' }"
    >
      <li @click="refreshSelectedTag">
        <el-icon><Refresh /></el-icon>
        刷新
      </li>
      <li
        v-if="!isAffix"
        @click="closeSelectedTag"
      >
        <el-icon><Close /></el-icon>
        关闭
      </li>
      <li @click="closeOthersTags">
        <el-icon><Remove /></el-icon>
        关闭其他
      </li>
      <li @click="closeAllTags">
        <el-icon><CircleClose /></el-icon>
        关闭所有
      </li>
    </ul>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted, watch } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { Close, MoreFilled, Refresh, Remove, CircleClose } from '@element-plus/icons-vue'

  const route = useRoute()
  const router = useRouter()

  const visitedViews = ref([])
  const tagListRef = ref(null)
  const visible = ref(false)
  const menuLeft = ref(0)
  const menuTop = ref(0)
  const selectedTag = ref({})

  const show = computed(() => {
    return visitedViews.value.length > 0
  })

  const activeTag = computed(() => {
    return visitedViews.value.find((view) => view.path === route.path) || {}
  })

  const isActive = (tag) => {
    return tag.path === route.path
  }

  const isAffix = (tag) => {
    return tag.meta && tag.meta.affix
  }

  const addTags = () => {
    if (route.name) {
      const visited = visitedViews.value.find((v) => v.path === route.path)
      if (!visited) {
        visitedViews.value.push({
          title: route.meta.title || route.name,
          path: route.path,
          fullPath: route.fullPath,
          meta: route.meta,
        })
      }
    }
  }

  const closeTag = (view) => {
    const index = visitedViews.value.findIndex((v) => v.path === view.path)
    if (index > -1) {
      visitedViews.value.splice(index, 1)
      if (view.path === route.path) {
        const lastView = visitedViews.value[index - 1] || visitedViews.value[0]
        if (lastView) {
          router.push(lastView.path)
        }
      }
    }
  }

  const openMenu = (tag, e) => {
    menuLeft.value = e.clientX
    menuTop.value = e.clientY
    visible.value = true
    selectedTag.value = tag
  }

  const closeMenu = () => {
    visible.value = false
  }

  const refreshSelectedTag = () => {
    const { fullPath } = selectedTag.value
    router.replace({
      path: '/redirect' + fullPath,
    })
  }

  const closeSelectedTag = () => {
    closeTag(selectedTag.value)
  }

  const closeOthersTags = () => {
    router.push(selectedTag.value.path)
    visitedViews.value = visitedViews.value.filter((v) => v.path === selectedTag.value.path)
  }

  const closeAllTags = () => {
    visitedViews.value = []
    router.push('/')
  }

  const handleCommand = (command) => {
    switch (command) {
      case 'refresh':
        router.push({ path: '/redirect' + route.path })
        break
      case 'closeOthers':
        closeOthersTags()
        break
      case 'closeAll':
        closeAllTags()
        break
    }
  }

  watch(
    () => route.path,
    () => {
      addTags()
    }
  )

  watch(visible, (value) => {
    if (value) {
      document.body.addEventListener('click', closeMenu)
    } else {
      document.body.removeEventListener('click', closeMenu)
    }
  })

  onMounted(() => {
    addTags()
  })
</script>

<style lang="scss" scoped>
  .tag-view {
    display: flex;
    align-items: center;
    background: #fff;
    border-bottom: 1px solid #d8dce5;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    padding: 8px 16px;
    height: 40px;
    width: 100%;
  }

  .tag-scroll {
    flex: 1;
    overflow-x: auto;

    &::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }

    &::-webkit-scrollbar-thumb {
      background: #c0c4cc;
      border-radius: 3px;
    }
  }

  .tag-list {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .tag-item {
    display: inline-flex;
    align-items: center;
    padding: 4px 12px;
    border-radius: 4px;
    background: #fff;
    border: 1px solid #d8dce5;
    color: #495060;
    font-size: 12px;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.3s;

    &:hover {
      background: #f0f2f5;
      color: #005aa0;
    }

    &.is-active {
      background: #005aa0;
      color: #fff;
      border-color: #005aa0;

      .tag-close {
        color: #fff;
      }
    }

    .tag-close {
      margin-left: 6px;
      border-radius: 50%;
      text-align: center;
      transition: all 0.3s;

      &:hover {
        background: #b4bccc;
        color: #fff;
      }
    }
  }

  .tag-more {
    padding: 0 12px;
    cursor: pointer;
    display: flex;
    align-items: center;

    &:hover {
      background: #f0f2f5;
    }
  }

  .context-menu {
    position: fixed;
    margin: 0;
    padding: 5px 0;
    background: #fff;
    border-radius: 4px;
    list-style: none;
    z-index: 3000;
    box-shadow: 2px 2px 3px 0 rgba(0, 0, 0, 0.2);
    font-size: 12px;

    li {
      display: flex;
      align-items: center;
      padding: 7px 16px;
      cursor: pointer;

      &:hover {
        background: #f0f2f5;
      }

      .el-icon {
        margin-right: 5px;
      }
    }
  }
</style>
