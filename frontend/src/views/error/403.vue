<template>
  <div class="error-page">
    <div class="error-content">
      <div class="error-code">
        403
      </div>
      <div class="error-title">
        访问被拒绝
      </div>
      <p class="error-desc">
        抱歉，您没有权限访问此页面
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
    router.push('/home')
  }
</script>

<style lang="scss" scoped>
  .error-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #ff9a56 0%, #ff6b6b 100%);
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
</style>
