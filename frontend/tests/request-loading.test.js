import { describe, it, expect, vi, beforeEach } from 'vitest'

/**
 * #19：全局 loading 触发条件与计数对称性。
 * - 显式传 loadingOptions（如 { text }）即触发，不再要求 fullscreen === true
 *   （此前全仓无调用方传过 fullscreen，全局 ElLoading 从未出现过）
 * - hide 只由真正展示过 loading 的请求触发：并发下不偷计数、不漏关
 */

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
  ElLoading: { service: vi.fn(() => ({ close: vi.fn() })) },
}))

const replaceMock = vi.fn(() => Promise.resolve())
vi.mock('@/router', () => ({
  default: {
    currentRoute: { value: { fullPath: '/home' } },
    replace: (...args) => replaceMock(...args),
  },
}))

import { ElLoading } from 'element-plus'
import request from '@/api/request.js'

// adapter 必须回填 axios 传入的合并 config（内置 xhr/http adapter 的行为），
// 否则拦截器读不到 _loadingShown 标记，hide 分支不会执行。
const okAdapter =
  (data = {}) =>
  (config) =>
    Promise.resolve({
      data: { code: 200, msg: 'ok', data },
      status: 200,
      statusText: 'OK',
      headers: {},
      config,
    })

const serviceCalls = () => ElLoading.service.mock.calls
const lastClose = () => ElLoading.service.mock.results.at(-1).value.close

beforeEach(() => {
  vi.clearAllMocks()
})

describe('loading 触发条件 (#19)', () => {
  it('传 { text } 即触发全局 loading，无需 fullscreen', async () => {
    await request.get('/api/x', { adapter: okAdapter(), loadingOptions: { text: '加载中' } })
    expect(serviceCalls()).toHaveLength(1)
    expect(serviceCalls()[0][0].text).toBe('加载中')
  })

  it('未传 loadingOptions 不触发', async () => {
    await request.get('/api/x', { adapter: okAdapter() })
    expect(ElLoading.service).not.toHaveBeenCalled()
  })

  it('loadingOptions: false 与 hideLoading: true 均不触发', async () => {
    await request.get('/api/x', { adapter: okAdapter(), loadingOptions: false })
    await request.get('/api/x', {
      adapter: okAdapter(),
      hideLoading: true,
      loadingOptions: { text: 'x' },
    })
    expect(ElLoading.service).not.toHaveBeenCalled()
  })
})

describe('loading 计数对称性 (#19)', () => {
  it('并发两个展示请求：service 一次，全部响应后恰好 close 一次', async () => {
    const p1 = request.get('/api/a', { adapter: okAdapter(), loadingOptions: { text: 'a' } })
    const p2 = request.get('/api/b', { adapter: okAdapter(), loadingOptions: { text: 'b' } })
    await Promise.all([p1, p2])
    expect(serviceCalls()).toHaveLength(1)
    expect(lastClose()).toHaveBeenCalledTimes(1)
  })

  it('未展示 loading 的请求不消耗计数', async () => {
    const p1 = request.get('/api/a', { adapter: okAdapter(), loadingOptions: { text: 'a' } })
    const p2 = request.get('/api/b', { adapter: okAdapter() })
    await Promise.all([p1, p2])
    expect(lastClose()).toHaveBeenCalledTimes(1)
    // 计数已归零：下一个展示请求能重新建实例（若被 p2 偷减会提前 close，此处复用则不会）
    await request.get('/api/c', { adapter: okAdapter(), loadingOptions: { text: 'c' } })
    expect(serviceCalls()).toHaveLength(2)
  })

  it('业务错误响应同样释放计数', async () => {
    const failAdapter = (config) =>
      Promise.resolve({
        data: { code: 500, msg: 'boom', data: {} },
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      })
    await expect(
      request.get('/api/a', { adapter: failAdapter, loadingOptions: { text: 'a' } })
    ).rejects.toThrow('boom')
    await request.get('/api/b', { adapter: okAdapter(), loadingOptions: { text: 'b' } })
    expect(serviceCalls()).toHaveLength(2)
  })

  it('网络错误（error.response 缺失）也释放计数', async () => {
    const netFailAdapter = (config) => {
      const err = new Error('network down')
      err.config = config
      return Promise.reject(err)
    }
    await expect(
      request.get('/api/a', { adapter: netFailAdapter, loadingOptions: { text: 'a' } })
    ).rejects.toThrow('network down')
    await request.get('/api/b', { adapter: okAdapter(), loadingOptions: { text: 'b' } })
    expect(serviceCalls()).toHaveLength(2)
  })
})
