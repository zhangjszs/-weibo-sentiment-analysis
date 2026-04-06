<template>
  <div class="error-page">
    <div class="error-content">
      <h1 class="error-code">
        404
      </h1>
      <p class="error-message">
        页面不存在
      </p>
      <p class="error-desc">
        抱歉，您访问的页面不存在或已被删除
      </p>
      <el-button
        type="primary"
        @click="goHome"
      >
        返回首页
      </el-button>
    </div>
  </div>
</template>

<script setup>
  import { useRouter } from 'vue-router'

  const router = useRouter()

  const goHome = () => {
    router.push('/')
  }
</script>

<style lang="scss" scoped>
  .error-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f5f7fa;
  }

  .error-content {
    text-align: center;

    .error-code {
      font-size: 120px;
      font-weight: bold;
      color: #667eea;
      margin-bottom: 16px;
    }

    .error-message {
      font-size: 24px;
      font-weight: 500;
      color: #333;
      margin-bottom: 8px;
    }

    .error-desc {
      color: #999;
      margin-bottom: 32px;
    }
  }
</style>
