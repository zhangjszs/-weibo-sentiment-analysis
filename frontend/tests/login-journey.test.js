import { describe, it, expect, vi, beforeEach } from 'vitest'
import { nextTick } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

/**
 * #64（T-1）：登录与注册旅程补 vitest 覆盖。
 *
 * 只加测试，不改源码。mock 层级：@/api/auth 的 login/register（真实执行
 * stores/user.js 的 doLogin）；路由用真实 router（plugin 挂载），跳转断言
 * 落在 currentRoute；ElMessage 用 spyOn（不断言 DOM toast，断言调用——与
 * response-envelope.test.js 同约定）。
 *
 * axios mock 照抄 router-guard.test.js：router/index.js 内建 meClient，
 * 成功登录后 push 受保护路由会触发守卫的 /api/auth/me。
 *
 * 注意两处测试环境语义（详见执行报告「歧义处理」）：
 * 1. 路由懒加载 chunk 需要真实时间：导航断言用 vi.waitFor 轮询，不用固定
 *    flush 次数（后者在负载高时会 flake）。
 * 2. el-form 内部校验在本测试环境挂载下不生效（已实证：空用户名提交仍会
 *    调接口），故不含「校验拦截」用例；成功/失败路径均使用合法表单数据。
 */

vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  checkSession: vi.fn(),
  extendSession: vi.fn(),
  getUserInfo: vi.fn(),
}))

const meGet = vi.fn()
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      get: (...args) => meGet(...args),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    })),
  },
}))

import { ElMessage } from 'element-plus'
import { login, register } from '@/api/auth'
import { clearSessionState, getAuthToken } from '@/utils/authSession'
import { useUserStore } from '@/stores/user'
import router from '@/router/index.js'
import Login from '../src/views/auth/Login.vue'
import Register from '../src/views/auth/Register.vue'

const mePayload = (user) => ({ data: { code: 200, msg: 'ok', data: user } })
const loginOk = () => ({
  code: 200,
  msg: 'ok',
  data: { token: 'tok-123', user: { id: 7, username: 'tester1', is_admin: false } },
})

const mountWithRouter = (component) => {
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(component, {
    global: {
      plugins: [pinia, router],
    },
  })
}

const setInput = async (wrapper, placeholder, value) => {
  await wrapper.find(`input[placeholder="${placeholder}"]`).setValue(value)
}

const fillLogin = async (wrapper, user = 'tester1', pass = 'secret123') => {
  await setInput(wrapper, '请输入用户名', user)
  await setInput(wrapper, '请输入密码', pass)
}

const fillRegister = async (wrapper, user = 'newuser1', pass = 'secret123') => {
  await setInput(wrapper, '请输入用户名', user)
  await setInput(wrapper, '请输入密码', pass)
  await setInput(wrapper, '请确认密码', pass)
}

// el-form 的 async-validator 走多轮 microtask，保险起见排空多次。
const settle = async (rounds = 4) => {
  for (let i = 0; i < rounds; i++) {
    await flushPromises()
    await nextTick()
  }
}

const awaitRoute = (path) =>
  vi.waitFor(() => expect(router.currentRoute.value.path).toBe(path), { timeout: 5000 })

beforeEach(async () => {
  vi.clearAllMocks()
  clearSessionState()
  setActivePinia(createPinia())
  meGet.mockReset()
  meGet.mockResolvedValue(mePayload({ username: 'tester', is_admin: false }))
  vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
  vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
  await router.push('/login')
  await flushPromises()
})

describe('登录旅程 (#64)', () => {
  it('成功：填表提交 → doLogin 被调用、token 落库、跳转 /home', async () => {
    login.mockResolvedValue(loginOk())
    const wrapper = mountWithRouter(Login)
    const store = useUserStore()

    await fillLogin(wrapper)
    await wrapper.find('.login-btn').trigger('click')

    await awaitRoute('/home')
    expect(login).toHaveBeenCalledWith('tester1', 'secret123')
    expect(getAuthToken()).toBe('tok-123')
    expect(store.userInfo.username).toBe('tester1')
    expect(ElMessage.success).toHaveBeenCalledWith('登录成功')
  })

  it('成功带 redirect：跳转 query 指定的路由', async () => {
    login.mockResolvedValue(loginOk())
    await router.push('/login?redirect=/help')
    const wrapper = mountWithRouter(Login)

    await fillLogin(wrapper)
    await wrapper.find('.login-btn').trigger('click')

    await awaitRoute('/help')
    expect(getAuthToken()).toBe('tok-123')
  })

  it('失败（401 业务码）：错误提示、token 未写入、未跳转', async () => {
    login.mockResolvedValue({ code: 401, msg: '用户名或密码错误' })
    const wrapper = mountWithRouter(Login)

    await fillLogin(wrapper, 'tester1', 'wrongpass')
    await wrapper.find('.login-btn').trigger('click')
    await settle()

    expect(login).toHaveBeenCalled()
    expect(ElMessage.error).toHaveBeenCalledWith('用户名或密码错误')
    expect(getAuthToken()).toBe('')
    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('失败（网络错误）：错误提示、token 未写入、未跳转', async () => {
    login.mockRejectedValue(new Error('Network Error'))
    const wrapper = mountWithRouter(Login)

    await fillLogin(wrapper)
    await wrapper.find('.login-btn').trigger('click')
    await settle()

    expect(ElMessage.error).toHaveBeenCalled()
    expect(getAuthToken()).toBe('')
    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('提交中：按钮进入 loading 态，完成后恢复', async () => {
    let release
    login.mockReturnValue(new Promise((resolve) => (release = resolve)))
    const wrapper = mountWithRouter(Login)

    await fillLogin(wrapper)
    await wrapper.find('.login-btn').trigger('click')
    await settle()

    // 接口 pending 时按钮应处于 loading（handleLogin 的 loading 语义）
    expect(wrapper.find('.login-btn.is-loading').exists()).toBe(true)

    release(loginOk())
    await awaitRoute('/home')
    expect(wrapper.find('.login-btn.is-loading').exists()).toBe(false)
  })
})

describe('注册旅程 (#64)', () => {
  it('成功：提交 → 注册接口被调用、提示成功、跳转 /login', async () => {
    register.mockResolvedValue({ code: 200, msg: 'ok', data: {} })
    await router.push('/register')
    const wrapper = mountWithRouter(Register)

    await fillRegister(wrapper)
    await wrapper.find('.register-btn').trigger('click')
    await settle()

    expect(register).toHaveBeenCalledWith('newuser1', 'secret123', 'secret123')
    await awaitRoute('/login')
    expect(ElMessage.success).toHaveBeenCalledWith('注册成功，请登录')
  })

  it('失败（业务码）：错误提示、不跳转', async () => {
    register.mockResolvedValue({ code: 400, msg: '用户名已存在' })
    await router.push('/register')
    const wrapper = mountWithRouter(Register)

    await fillRegister(wrapper)
    await wrapper.find('.register-btn').trigger('click')
    await settle()

    expect(ElMessage.error).toHaveBeenCalledWith('用户名已存在')
    expect(router.currentRoute.value.path).toBe('/register')
  })

  it('失败（网络异常）：统一错误提示、不跳转', async () => {
    register.mockRejectedValue(new Error('Network Error'))
    await router.push('/register')
    const wrapper = mountWithRouter(Register)

    await fillRegister(wrapper)
    await wrapper.find('.register-btn').trigger('click')
    await settle()

    expect(ElMessage.error).toHaveBeenCalledWith('注册失败')
    expect(router.currentRoute.value.path).toBe('/register')
  })
})
