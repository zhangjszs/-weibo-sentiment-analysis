import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

/**
 * #125：request.js 响应/错误拦截器分支锁定。
 * 用自定义 axios adapter 注入包络与失败对象，断言用户可见结果：
 * 提示文案、reject 的 message/对象身份、401 登出跳转目标与防重入。
 */

const { replaceMock, routeState } = vi.hoisted(() => ({
  replaceMock: vi.fn(() => Promise.resolve()),
  routeState: { value: { fullPath: '/home' } },
}))

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
  ElLoading: { service: vi.fn(() => ({ close: vi.fn() })) },
}))

vi.mock('@/router', () => ({
  default: { currentRoute: routeState, replace: replaceMock },
}))

import { ElMessage } from 'element-plus'
import request from '@/api/request.js'

const okAdapter =
  (payload, httpStatus = 200) =>
  (config) =>
    Promise.resolve({
      data: payload,
      status: httpStatus,
      statusText: 'OK',
      headers: {},
      config,
    })

const rejectAdapter = (error) => (config) => {
  error.config = config
  return Promise.reject(error)
}

const httpError = (status, data) => {
  const error = new Error(`Request failed with status code ${status}`)
  error.response = { status, data, headers: {} }
  error.request = {}
  return error
}

const networkError = (extra = {}) => {
  const error = new Error('Network Error')
  error.request = {}
  return Object.assign(error, extra)
}

const settle = (promise) => promise.catch((error) => error)

beforeEach(() => {
  vi.clearAllMocks()
  routeState.value = { fullPath: '/home' }
})

afterEach(async () => {
  // 让 router.replace().finally 复位 401 防重入标记，避免污染后续用例
  await new Promise((resolve) => setTimeout(resolve, 0))
})

describe('响应包络透传', () => {
  for (const code of [200, 201, 202]) {
    it(`业务码 ${code} 原样返回包络`, async () => {
      const payload = { code, msg: 'ok', data: { id: code } }
      await expect(request.get('/api/x', { adapter: okAdapter(payload, code) })).resolves.toEqual(
        payload
      )
      expect(ElMessage.error).not.toHaveBeenCalled()
      expect(ElMessage.warning).not.toHaveBeenCalled()
    })
  }

  it('409 原样返回包络且不弹错误提示', async () => {
    const payload = { code: 409, msg: '任务运行中', data: null }
    await expect(request.get('/api/x', { adapter: okAdapter(payload, 409) })).resolves.toEqual(
      payload
    )
    expect(ElMessage.error).not.toHaveBeenCalled()
    expect(ElMessage.warning).not.toHaveBeenCalled()
  })
})

describe('业务码错误分支', () => {
  const cases = [
    [403, '没有权限访问该资源'],
    [404, '请求的资源不存在'],
    [500, '服务器内部错误，请稍后重试'],
  ]

  for (const [code, text] of cases) {
    it(`业务码 ${code} → 「${text}」并 reject 包络 msg`, async () => {
      const error = await settle(
        request.get('/api/x', { adapter: okAdapter({ code, msg: `biz-${code}`, data: null }) })
      )

      expect(error).toBeInstanceOf(Error)
      expect(error.message).toBe(`biz-${code}`)
      expect(ElMessage.error).toHaveBeenCalledWith(text)
    })
  }

  it('未知业务码使用包络 msg', async () => {
    const error = await settle(
      request.get('/api/x', { adapter: okAdapter({ code: 400, msg: '参数错误', data: null }) })
    )

    expect(error.message).toBe('参数错误')
    expect(ElMessage.error).toHaveBeenCalledWith('参数错误')
  })

  it('未知业务码缺省 msg 时回退「请求失败」', async () => {
    const error = await settle(
      request.get('/api/x', { adapter: okAdapter({ code: 400, data: null }) })
    )

    expect(error.message).toBe('请求失败')
    expect(ElMessage.error).toHaveBeenCalledWith('请求失败')
  })
})

describe('业务码 401 强制登出', () => {
  it('提示过期、按当前路径编码跳转并 reject', async () => {
    routeState.value = { fullPath: '/analysis?tab=1&name=x' }

    const error = await settle(
      request.get('/api/x', { adapter: okAdapter({ code: 401, msg: '未授权', data: null }) })
    )

    expect(error.message).toBe('未授权')
    expect(ElMessage.warning).toHaveBeenCalledWith('登录已过期，请重新登录')
    expect(ElMessage.error).not.toHaveBeenCalled()
    expect(replaceMock).toHaveBeenCalledTimes(1)
    expect(replaceMock).toHaveBeenCalledWith('/login?redirect=%2Fanalysis%3Ftab%3D1%26name%3Dx')
  })

  it('并发两个 401 只跳转一次', async () => {
    let resolveReplace
    replaceMock.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveReplace = resolve
        })
    )

    const [first, second] = await Promise.all([
      settle(request.get('/api/a', { adapter: okAdapter({ code: 401, msg: 'a', data: null }) })),
      settle(request.get('/api/b', { adapter: okAdapter({ code: 401, msg: 'b', data: null }) })),
    ])

    expect(first.message).toBe('a')
    expect(second.message).toBe('b')
    expect(replaceMock).toHaveBeenCalledTimes(1)
    resolveReplace()
  })

  it('跳转完成后可再次触发跳转', async () => {
    await settle(request.get('/api/a', { adapter: okAdapter({ code: 401, msg: 'a', data: null }) }))
    await new Promise((resolve) => setTimeout(resolve, 0))
    await settle(request.get('/api/b', { adapter: okAdapter({ code: 401, msg: 'b', data: null }) }))

    expect(replaceMock).toHaveBeenCalledTimes(2)
  })

  it('当前路由缺失时回退 /home', async () => {
    routeState.value = null

    await settle(request.get('/api/a', { adapter: okAdapter({ code: 401, msg: 'a', data: null }) }))

    expect(replaceMock).toHaveBeenCalledWith('/login?redirect=%2Fhome')
  })
})

describe('HTTP 错误状态分支', () => {
  const cases = [
    [403, '没有权限访问'],
    [404, '请求的资源不存在'],
    [408, '请求超时，请检查网络连接'],
    [500, '服务器错误，请稍后重试'],
    [502, '网关错误，请稍后重试'],
    [503, '服务暂时不可用，请稍后重试'],
  ]

  for (const [status, text] of cases) {
    it(`HTTP ${status} → 「${text}」并 reject 原始 error`, async () => {
      const original = httpError(status, { msg: 'server says' })
      const error = await settle(request.get('/api/x', { adapter: rejectAdapter(original) }))

      expect(error).toBe(original)
      expect(ElMessage.error).toHaveBeenCalledWith(text)
    })
  }

  it('HTTP 401 → 过期提示并强制登出，reject 原始 error', async () => {
    const original = httpError(401, { msg: 'unauthorized' })
    const error = await settle(request.get('/api/x', { adapter: rejectAdapter(original) }))

    expect(error).toBe(original)
    expect(ElMessage.warning).toHaveBeenCalledWith('登录已过期，请重新登录')
    expect(replaceMock).toHaveBeenCalledTimes(1)
    expect(replaceMock).toHaveBeenCalledWith('/login?redirect=%2Fhome')
  })

  it('其他 HTTP 状态优先使用响应体 msg', async () => {
    const original = httpError(418, { msg: 'teapot' })
    const error = await settle(request.get('/api/x', { adapter: rejectAdapter(original) }))

    expect(error).toBe(original)
    expect(ElMessage.error).toHaveBeenCalledWith('teapot')
  })

  it('其他 HTTP 状态缺省 msg 时回退状态码文案', async () => {
    const original = httpError(418, undefined)
    await settle(request.get('/api/x', { adapter: rejectAdapter(original) }))

    expect(ElMessage.error).toHaveBeenCalledWith('请求失败 (418)')
  })
})

describe('无响应错误分支', () => {
  it('ECONNABORTED → 超时提示', async () => {
    const original = networkError({ code: 'ECONNABORTED' })
    const error = await settle(request.get('/api/x', { adapter: rejectAdapter(original) }))

    expect(error).toBe(original)
    expect(ElMessage.error).toHaveBeenCalledWith('请求超时，请检查网络连接')
  })

  it('有 request 无 response → 网络错误提示', async () => {
    const original = networkError()
    const error = await settle(request.get('/api/x', { adapter: rejectAdapter(original) }))

    expect(error).toBe(original)
    expect(ElMessage.error).toHaveBeenCalledWith('网络错误，请检查网络连接')
  })

  it('请求配置错误（无 request/response）→ 配置错误提示', async () => {
    const original = new Error('adapter config invalid')
    const error = await settle(request.get('/api/x', { adapter: rejectAdapter(original) }))

    expect(error).toBe(original)
    expect(ElMessage.error).toHaveBeenCalledWith('请求配置错误')
  })
})
