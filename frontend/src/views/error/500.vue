<template>
  <div class="error-page">
    <div class="error-content">
      <div class="error-code">
        500
      </div>
      <div class="error-title">
        服务器错误
      </div>
      <p class="error-desc">
        抱歉，服务器出现了一些问题，请稍后再试
      </p>
      <div class="error-actions">
        <el-button
          type="primary"
          @click="refresh"
        >
          刷新页面
        </el-button>
        <el-button @click="goHome">
          返回首页
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { useRouter } from 'vue-router'

  const router = useRouter()

  const refresh = () => {
    window.location.reload()
  }

  const goHome = () => {
    router.push('/home')
  }
</script>

<style lang="scss" scoped>
  .error-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }

  .error-content {
    text-align: center;
    color: #fff;
  }

  .error-code {
    font-size: 120px;
    font-weight: bold;
    line-height: 1;
    text-shadow: 4px 4px 0 rgba(0, 0, 0, 0.1);
  }

  .error-title {
    font-size: 32px;
    margin: 20px 0 10px;
  }

  .error-desc {
    font-size: 16px;
    margin-bottom: 30px;
    opacity: 0.9;
  }

  .error-actions {
    display: flex;
    gap: 16px;
    justify-content: center;
  }
</style>
