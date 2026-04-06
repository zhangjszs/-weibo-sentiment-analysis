import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { checkSession, extendSession, getUserInfo, login, logout } from '@/api/auth'
import router from '@/router'
import {
  clearSessionState,
  getAuthToken,
  getCachedUser,
  setAuthToken,
  setCachedUser,
} from '@/utils/authSession'

export const useUserStore = defineStore('user', () => {
  const token = ref(getAuthToken())
  const userInfo = ref(getCachedUser())

  const isLoggedIn = computed(() => !!(userInfo.value?.id || userInfo.value?.username))
  const username = computed(() => userInfo.value?.username || '')
  const isAdmin = computed(() => userInfo.value?.is_admin === true)

  function applyToken(nextToken = '') {
    token.value = setAuthToken(nextToken)
  }

  function applyUserInfo(nextUser = {}) {
    userInfo.value = nextUser && typeof nextUser === 'object' ? nextUser : {}
    setCachedUser(userInfo.value)
  }

  function resetAuthState() {
    clearSessionState()
    token.value = ''
    userInfo.value = {}
  }

  async function doLogin(username, password) {
    try {
      const res = await login(username, password)
      if (res.code === 200) {
        applyToken(res.data.token || '')
        applyUserInfo(res.data.user || {})
        return { success: true }
      }
      return { success: false, msg: res.msg }
    } catch (error) {
      return { success: false, msg: error.message }
    }
  }

  async function doLogout() {
    try {
      await logout()
    } catch (error) {
      console.error('登出请求失败', error)
    } finally {
      resetAuthState()
      router.push('/login')
    }
  }

  async function initAuth({ redirectOnFailure = false } = {}) {
    try {
      const sessionRes = await checkSession()
      const sessionData = sessionRes?.data || {}

      if (!sessionData.authenticated) {
        resetAuthState()
        return false
      }

      try {
        const extendRes = await extendSession()
        if (extendRes.code === 200) {
          applyToken(extendRes.data?.token || '')
        }
      } catch (error) {
        applyToken('')
      }

      const res = await getUserInfo()
      if (res.code === 200) {
        applyUserInfo(res.data || {})
        return true
      }
    } catch (e) {
      resetAuthState()
      if (redirectOnFailure) {
        const target = router.currentRoute?.value?.fullPath || '/home'
        router.replace(`/login?redirect=${encodeURIComponent(target)}`)
      }
      return false
    }

    return false
  }

  function updateUserInfo(info) {
    applyUserInfo({ ...userInfo.value, ...info })
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    username,
    isAdmin,
    doLogin,
    doLogout,
    initAuth,
    updateUserInfo,
  }
})
