<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <div class="logo-wrapper">
          <img
            src="@/assets/images/logo.png"
            alt="Logo"
            class="logo"
          >
        </div>
        <h1>欢迎回来</h1>
        <p>登录微博舆情分析系统</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        size="large"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            class="custom-input"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            show-password
            class="custom-input"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <div class="form-options">
          <el-checkbox v-model="rememberMe">
            记住我
          </el-checkbox>
        </div>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <span>还没有账号？</span>
        <router-link to="/register">
          立即注册
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { ref, reactive } from 'vue'
  import { useRouter, useRoute } from 'vue-router'
  import { ElMessage } from 'element-plus'
  import { useUserStore } from '@/stores/user'

  const router = useRouter()
  const route = useRoute()
  const userStore = useUserStore()

  const loginFormRef = ref(null)
  const loading = ref(false)
  const rememberMe = ref(false)

  const loginForm = reactive({
    username: '',
    password: '',
  })

  const loginRules = {
    username: [
      { required: true, message: '请输入用户名', trigger: 'blur' },
      { min: 3, max: 20, message: '用户名长度为3-20个字符', trigger: 'blur' },
    ],
    password: [
      { required: true, message: '请输入密码', trigger: 'blur' },
      { min: 6, max: 20, message: '密码长度为6-20个字符', trigger: 'blur' },
    ],
  }

  const handleLogin = async () => {
    if (!loginFormRef.value) return

    try {
      await loginFormRef.value.validate()
    } catch {
      return
    }

    loading.value = true
    try {
      const result = await userStore.doLogin(loginForm.username, loginForm.password)

      if (result.success) {
        ElMessage.success('登录成功')
        const redirect = route.query.redirect || '/home'
        router.push(redirect)
      } else {
        ElMessage.error(result.msg || '登录失败')
      }
    } finally {
      loading.value = false
    }
  }
</script>

<style lang="scss" scoped>
  .login-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #f8fafc;
    background-image:
      radial-gradient(at 0% 0%, rgba(37, 99, 235, 0.1) 0px, transparent 50%),
      radial-gradient(at 100% 100%, rgba(16, 185, 129, 0.1) 0px, transparent 50%);
    padding: 20px;
  }

  .login-box {
    width: 100%;
    max-width: 440px;
    background: $surface-color;
    border-radius: $border-radius-large;
    padding: 48px;
    box-shadow:
      0 4px 6px -1px rgba(0, 0, 0, 0.1),
      0 2px 4px -1px rgba(0, 0, 0, 0.06),
      0 20px 25px -5px rgba(0, 0, 0, 0.1),
      0 8px 10px -6px rgba(0, 0, 0, 0.1); // Strong shadow for lift
    transition: transform 0.3s ease;
  }

  .login-header {
    text-align: center;
    margin-bottom: 40px;

    .logo-wrapper {
      width: 64px;
      height: 64px;
      background: $primary-light;
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 24px;
    }

    .logo {
      width: 40px;
      height: auto;
    }

    h1 {
      font-size: 24px;
      font-weight: 700;
      color: $text-primary;
      margin-bottom: 8px;
      letter-spacing: -0.5px;
    }

    p {
      color: $text-secondary;
      font-size: 14px;
    }
  }

  .login-form {
    .custom-input {
      :deep(.el-input__wrapper) {
        padding: 12px 16px;
        box-shadow: 0 0 0 1px $border-color inset !important;

        &.is-focus {
          box-shadow:
            0 0 0 2px rgba($primary-color, 0.2) inset,
            0 0 0 1px $primary-color inset !important;
        }
      }
    }

    .login-btn {
      width: 100%;
      height: 48px;
      font-size: 16px;
      font-weight: 600;
      margin-top: 8px;
      box-shadow: 0 4px 6px -1px rgba($primary-color, 0.3);

      &:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 8px -1px rgba($primary-color, 0.4);
      }
    }
  }

  .form-options {
    display: flex;
    justify-content: flex-start;
    align-items: center;
    margin-bottom: 24px;
  }

  .login-footer {
    text-align: center;
    margin-top: 32px;
    font-size: 14px;
    color: $text-secondary;

    a {
      color: $primary-color;
      font-weight: 600;
      margin-left: 4px;

      &:hover {
        text-decoration: underline;
      }
    }
  }
</style>
