import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

/**
 * #128：utils/chinaMap.js 的模块级单例与失败复位语义（#40 顺序依赖修复）。
 * 每个用例前 vi.resetModules() + 动态 import，保证 ready 不跨用例泄漏；
 * fetch 与 echarts.registerMap 全部 mock，不加载真实资产。
 */

const { registerMapMock, fetchMock } = vi.hoisted(() => ({
  registerMapMock: vi.fn(),
  fetchMock: vi.fn(),
}))

vi.mock('@/utils/echarts', () => ({
  default: { registerMap: registerMapMock },
}))

const mapData = () => ({ type: 'FeatureCollection', features: [{ id: 'bj' }] })

const okResponse = (data) => ({
  ok: true,
  status: 200,
  json: vi.fn(() => Promise.resolve(data)),
})

const failedResponse = (status) => ({
  ok: false,
  status,
  json: vi.fn(),
})

const loadChinaMap = async () => {
  vi.resetModules()
  return import('@/utils/chinaMap')
}

beforeEach(() => {
  fetchMock.mockReset()
  registerMapMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('ensureChinaMap 单例语义 (#128)', () => {
  it('首次调用：fetch 恰好一次，json 结果注册为 china 地图并原样返回', async () => {
    const data = mapData()
    fetchMock.mockResolvedValue(okResponse(data))
    const { ensureChinaMap } = await loadChinaMap()

    const result = await ensureChinaMap()

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(String(fetchMock.mock.calls[0][0])).toContain('assets/china.json')
    expect(registerMapMock).toHaveBeenCalledTimes(1)
    expect(registerMapMock).toHaveBeenCalledWith('china', data)
    expect(result).toBe(data)
  })

  it('并发两次调用：共用同一 promise，fetch 仅一次', async () => {
    const data = mapData()
    fetchMock.mockResolvedValue(okResponse(data))
    const { ensureChinaMap } = await loadChinaMap()

    const first = ensureChinaMap()
    const second = ensureChinaMap()

    expect(second).toBe(first)
    await expect(first).resolves.toBe(data)
    await expect(second).resolves.toBe(data)
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(registerMapMock).toHaveBeenCalledTimes(1)
  })

  it('成功后再调用：不重新 fetch，返回同一 data 对象', async () => {
    const data = mapData()
    fetchMock.mockResolvedValue(okResponse(data))
    const { ensureChinaMap } = await loadChinaMap()

    const first = await ensureChinaMap()
    const second = await ensureChinaMap()

    expect(second).toBe(first)
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(registerMapMock).toHaveBeenCalledTimes(1)
  })
})

describe('ensureChinaMap 失败与重试 (#128)', () => {
  it('res.ok=false：抛含 HTTP 状态的错误，且不注册地图', async () => {
    fetchMock.mockResolvedValue(failedResponse(503))
    const { ensureChinaMap } = await loadChinaMap()

    await expect(ensureChinaMap()).rejects.toThrow('HTTP 503')
    expect(registerMapMock).not.toHaveBeenCalled()
  })

  it('失败后重试：ready 已复位，再次 fetch 并可成功', async () => {
    const data = mapData()
    fetchMock.mockResolvedValueOnce(failedResponse(404)).mockResolvedValueOnce(okResponse(data))
    const { ensureChinaMap } = await loadChinaMap()

    await expect(ensureChinaMap()).rejects.toThrow('HTTP 404')
    expect(registerMapMock).not.toHaveBeenCalled()

    await expect(ensureChinaMap()).resolves.toBe(data)
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(registerMapMock).toHaveBeenCalledTimes(1)
    expect(registerMapMock).toHaveBeenCalledWith('china', data)
  })

  it('fetch 抛网络错误：原错误冒泡，之后仍可重试成功', async () => {
    const data = mapData()
    const networkError = new Error('Network Error')
    fetchMock.mockRejectedValueOnce(networkError).mockResolvedValueOnce(okResponse(data))
    const { ensureChinaMap } = await loadChinaMap()

    await expect(ensureChinaMap()).rejects.toBe(networkError)
    expect(registerMapMock).not.toHaveBeenCalled()

    await expect(ensureChinaMap()).resolves.toBe(data)
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(registerMapMock).toHaveBeenCalledTimes(1)
  })
})
