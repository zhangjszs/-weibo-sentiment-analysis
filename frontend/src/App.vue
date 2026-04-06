<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup>
  import { onMounted } from 'vue'
  import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
  import { useAppStore } from '@/stores/app'
  import { useUserStore } from '@/stores/user'

  const appStore = useAppStore()
  const userStore = useUserStore()

  onMounted(() => {
    const savedTheme = localStorage.getItem('weibo_theme') || 'light'
    appStore.setTheme(savedTheme)
    userStore.initAuth()
  })
</script>
