import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

/**
 * #127：stores/user.js 的会话恢复（initAuth）与登出分支锁定。
 * mock 层级：@/api/auth 五函数 + @/router（currentRoute/replace/push）；
 * tabs 用真实 store，断言 resetAuthState 的 #20 清理语义。
 */

const { replaceMock, pushMock, routeState } = vi.hoisted(() => ({
  replaceMock: vi.fn(() => Promise.resolve()),
  pushMock: vi.fn(() => Promise.resolve()),
  routeState: { value: { fullPath: '/home' } },
}))

vi.mock('@/router', () => ({
  default: { currentRoute: routeState, replace: replaceMock, push: pushMock },
}))

vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  checkSession: vi.fn(),
  extendSession: vi.fn(),
  getUserInfo: vi.fn(),
}))

import { checkSession, extendSession, getUserInfo, logout } from '@/api/auth'
import { useTabsStore } from '@/stores/tabs'
import { useUserStore } from '@/stores/user'
import {
  clearSessionState,
  getAuthToken,
  getCachedUser,
  setAuthToken,
  setCachedUser,
} from '@/utils/authSession'

const sessionOk = () => ({ code: 200, data: { authenticated: true } })
const userPayload = (user) => ({ code: 200, data: user })

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  clearSessionState()
  setActivePinia(createPinia())
  routeState.value = { fullPath: '/home' }
  replaceMock.mockResolvedValue(undefined)
  pushMock.mockResolvedValue(undefined)
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('computed 与 updateUserInfo (#127)', () => {
  it('无用户时三个 computed 返回默认值', () => {
    const store = useUserStore()

    expect(store.isLoggedIn).toBe(false)
    expect(store.username).toBe('')
    expect(store.isAdmin).toBe(false)
  })

  it('updateUserInfo 合并新字段并保留旧字段，同时写入缓存', () => {
    const store = useUserStore()

    store.updateUserInfo({ id: 7, username: 'alice' })
    store.updateUserInfo({ is_admin: true })

    expect(store.userInfo).toEqual({ id: 7, username: 'alice', is_admin: true })
    expect(store.isLoggedIn).toBe(true)
    expect(store.username).toBe('alice')
    expect(store.isAdmin).toBe(true)
    expect(getCachedUser()).toEqual({ id: 7, username: 'alice', is_admin: true })
  })
})

describe('initAuth 正常分支 (#127)', () => {
  it('会话未认证：清态返回 false，且不再请求 extend/getUserInfo', async () => {
    setCachedUser({ id: 1, username: 'stale' })
    setAuthToken('stale-token')
    checkSession.mockResolvedValue({ code: 200, data: { authenticated: false } })
    const store = useUserStore()
    expect(store.userInfo.username).toBe('stale')

    await expect(store.initAuth()).resolves.toBe(false)

    expect(extendSession).not.toHaveBeenCalled()
    expect(getUserInfo).not.toHaveBeenCalled()
    expect(store.userInfo).toEqual({})
    expect(store.token).toBe('')
    expect(getAuthToken()).toBe('')
    expect(getCachedUser()).toEqual({})
  })

  it('extend 成功：写入新 token 并返回 true', async () => {
    checkSession.mockResolvedValue(sessionOk())
    extendSession.mockResolvedValue({ code: 200, data: { token: 'tok-ext' } })
    getUserInfo.mockResolvedValue(userPayload({ id: 5, username: 'bob' }))
    const store = useUserStore()

    await expect(store.initAuth()).resolves.toBe(true)

    expect(extendSession).toHaveBeenCalledTimes(1)
    expect(store.token).toBe('tok-ext')
    expect(getAuthToken()).toBe('tok-ext')
    expect(store.userInfo).toEqual({ id: 5, username: 'bob' })
  })

  it('extend 非 200：不改写既有 token，仍继续取用户信息', async () => {
    setAuthToken('tok-old')
    checkSession.mockResolvedValue(sessionOk())
    extendSession.mockResolvedValue({ code: 500, msg: 'extend failed' })
    getUserInfo.mockResolvedValue(userPayload({ id: 5, username: 'bob' }))
    const store = useUserStore()
    expect(store.token).toBe('tok-old')

    await expect(store.initAuth()).resolves.toBe(true)

    expect(store.token).toBe('tok-old')
    expect(getUserInfo).toHaveBeenCalledTimes(1)
  })

  it('extend 抛错：token 置空，但仍继续调用 getUserInfo', async () => {
    setAuthToken('tok-old')
    checkSession.mockResolvedValue(sessionOk())
    extendSession.mockRejectedValue(new Error('extend boom'))
    getUserInfo.mockResolvedValue(userPayload({ id: 5, username: 'bob' }))
    const store = useUserStore()

    await expect(store.initAuth()).resolves.toBe(true)

    expect(store.token).toBe('')
    expect(getAuthToken()).toBe('')
    expect(getUserInfo).toHaveBeenCalledTimes(1)
    expect(store.userInfo).toEqual({ id: 5, username: 'bob' })
  })

  it('getUserInfo 非 200：返回 false 且不清空已有状态', async () => {
    setCachedUser({ id: 9, username: 'carol' })
    checkSession.mockResolvedValue(sessionOk())
    extendSession.mockResolvedValue({ code: 200, data: { token: 'tok' } })
    getUserInfo.mockResolvedValue({ code: 500, msg: 'me failed' })
    const store = useUserStore()

    await expect(store.initAuth()).resolves.toBe(false)

    expect(store.userInfo).toEqual({ id: 9, username: 'carol' })
    expect(store.token).toBe('tok')
    expect(replaceMock).not.toHaveBeenCalled()
  })
})

describe('initAuth 异常与重定向 (#127)', () => {
  it('checkSession 抛错：清态返回 false，默认不跳转', async () => {
    setCachedUser({ id: 3, username: 'dave' })
    setAuthToken('tok')
    checkSession.mockRejectedValue(new Error('network down'))
    const store = useUserStore()

    await expect(store.initAuth()).resolves.toBe(false)

    expect(store.userInfo).toEqual({})
    expect(store.token).toBe('')
    expect(replaceMock).not.toHaveBeenCalled()
  })

  it('redirectOnFailure=true：跳转登录页并编码当前 fullPath', async () => {
    const fullPath = '/analysis/ip?topic=weibo&page=2'
    routeState.value = { fullPath }
    checkSession.mockRejectedValue(new Error('401'))
    const store = useUserStore()

    await expect(store.initAuth({ redirectOnFailure: true })).resolves.toBe(false)

    expect(replaceMock).toHaveBeenCalledTimes(1)
    expect(replaceMock).toHaveBeenCalledWith(`/login?redirect=${encodeURIComponent(fullPath)}`)
    expect(replaceMock.mock.calls[0][0]).toContain('redirect=%2Fanalysis%2Fip')
  })

  it('redirectOnFailure=true 且 currentRoute 缺失：回退 /home', async () => {
    routeState.value = null
    checkSession.mockRejectedValue(new Error('401'))
    const store = useUserStore()

    await expect(store.initAuth({ redirectOnFailure: true })).resolves.toBe(false)

    expect(replaceMock).toHaveBeenCalledWith('/login?redirect=%2Fhome')
  })
})

describe('doLogout (#127)', () => {
  it('logout 成功：清态并 push /login', async () => {
    setCachedUser({ id: 1, username: 'alice' })
    setAuthToken('tok')
    logout.mockResolvedValue({ code: 200 })
    const store = useUserStore()

    await store.doLogout()

    expect(logout).toHaveBeenCalledTimes(1)
    expect(store.userInfo).toEqual({})
    expect(store.token).toBe('')
    expect(pushMock).toHaveBeenCalledWith('/login')
  })

  it('logout 失败：仍清态并 push /login，错误经 console.error 记录', async () => {
    setCachedUser({ id: 1, username: 'alice' })
    const error = new Error('logout boom')
    logout.mockRejectedValue(error)
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const store = useUserStore()

    await store.doLogout()

    expect(consoleSpy).toHaveBeenCalledWith('登出请求失败', error)
    expect(store.userInfo).toEqual({})
    expect(pushMock).toHaveBeenCalledWith('/login')
  })

  it('重置工作区 tabs（#20）：仅保留首页并清 localStorage', async () => {
    const tabs = useTabsStore()
    tabs.addTab({ name: 'Analysis', path: '/analysis', meta: { title: '分析' } })
    expect(tabs.tabs.map((tab) => tab.name)).toEqual(['Home', 'Analysis'])
    logout.mockResolvedValue({ code: 200 })
    const store = useUserStore()

    await store.doLogout()

    expect(tabs.tabs.map((tab) => tab.name)).toEqual(['Home'])
    expect(tabs.activeTab).toBe('Home')
    expect(localStorage.getItem('weibo_tabs')).toBeNull()
  })
})
