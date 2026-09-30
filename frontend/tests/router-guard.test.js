import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

/**
 * #19：路由守卫。
 * - public 路由（含 404 catch-all）不要求登录，/404 不再死在登录重定向下
 * - /api/auth/me 结果带 TTL 缓存，路由间切换不放大 QPS
 * - adminOnly 拒绝时跳 /403（/home 会让 403 页面变成死页面）
 */

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
}))

const fetchMock = vi.fn()
vi.stubGlobal('fetch', fetchMock)

const mePayload = (user) => ({
  ok: true,
  json: async () => ({ code: 200, msg: 'ok', data: user }),
})

import { clearSessionState } from '@/utils/authSession'
import router from '@/router/index.js'

const meUser = { username: 'tester', is_admin: false }

beforeEach(() => {
  vi.clearAllMocks()
  clearSessionState()
  setActivePinia(createPinia())
})

describe('路由守卫 (#19)', () => {
  it('未登录访问未匹配路径：放行 404 页面，不发 /api/auth/me', async () => {
    await router.push('/no-such-page-xyz')
    expect(router.currentRoute.value.name).toBe('NotFound')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('未登录访问受保护路由：重定向登录且请求 /api/auth/me', async () => {
    fetchMock.mockResolvedValue({ ok: false, json: async () => ({}) })
    await router.push('/home')
    expect(fetchMock).toHaveBeenCalledWith('/api/auth/me', expect.anything())
    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('me 结果在 TTL 内复用：第二次导航不再发请求', async () => {
    fetchMock.mockResolvedValue(mePayload(meUser))
    await router.push('/home')
    expect(fetchMock).toHaveBeenCalledTimes(1)
    await router.push('/help')
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(router.currentRoute.value.path).toBe('/help')
  })

  it('非管理员访问 adminOnly 页面：跳转 /403', async () => {
    fetchMock.mockResolvedValue(mePayload(meUser))
    await router.push('/spider')
    expect(router.currentRoute.value.path).toBe('/403')
  })

  it('管理员访问 adminOnly 页面：放行', async () => {
    fetchMock.mockResolvedValue(mePayload({ username: 'admin', is_admin: true }))
    await router.push('/tasks')
    expect(router.currentRoute.value.name).toBe('TaskCenter')
  })
})
