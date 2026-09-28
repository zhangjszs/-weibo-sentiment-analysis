import { describe, it, expect, vi, beforeEach } from 'vitest'

/**
 * #18 契约测试：响应拦截器必须接受 2xx 包络（200/201/202），
 * 409 按业务分支透出（不弹全局错误、不 reject）。
 *
 * 后端契约（包络 code 与 HTTP 状态对齐）：
 * - POST /api/alert/rules → 201（规则创建）
 * - POST /api/sentiment/analyze + async → 202（含 task_id/check_url)
 * - POST /api/spider/crawl|quick-crawl 任务运行中 → 409
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

import { ElMessage } from 'element-plus'
import request from '@/api/request.js'

// 按包络 code 伪造 axios 响应（经自定义 adapter，不触网）。
const envelopeAdapter =
  (code, payload = {}, msg = 'ok') =>
  () =>
    Promise.resolve({
      data: { code, msg, data: payload },
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {},
    })

beforeEach(() => {
  vi.clearAllMocks()
})

describe('response envelope contract (#18)', () => {
  it('200 成功包络直接透出', async () => {
    const res = await request.get('/api/spider/status', {
      adapter: envelopeAdapter(200, { isRunning: false }),
    })
    expect(res.code).toBe(200)
    expect(res.data).toEqual({ isRunning: false })
  })

  it('201 创建成功可达（useAlert handleCreateRule 分支）', async () => {
    const res = await request.post(
      '/api/alert/rules',
      {
        id: 'r1',
        name: 'n',
      },
      {
        adapter: envelopeAdapter(201, { rule: { id: 'r1' } }, '预警规则创建成功'),
      }
    )
    expect(res.code).toBe(201)
    expect(ElMessage.error).not.toHaveBeenCalled()
  })

  it('202 异步任务可达且携带 task_id/check_url', async () => {
    const res = await request.post(
      '/api/sentiment/analyze',
      { text: '今天很开心', mode: 'simple', async: true },
      {
        adapter: envelopeAdapter(
          202,
          { task_id: 't-1', status: 'PENDING', check_url: '/api/tasks/t-1/status' },
          '任务已提交'
        ),
      }
    )
    expect(res.code).toBe(202)
    expect(res.data.task_id).toBe('t-1')
    expect(res.data.check_url).toContain('/api/tasks/')
    expect(ElMessage.error).not.toHaveBeenCalled()
  })

  it('409 运行中分支透出给调用方（不 toast、不 reject）', async () => {
    const res = await request.post(
      '/api/spider/crawl',
      { type: 'hot' },
      { adapter: envelopeAdapter(409, { isRunning: true }, '爬虫任务运行中') }
    )
    expect(res.code).toBe(409)
    expect(ElMessage.error).not.toHaveBeenCalled()
  })

  it('400 仍走错误通道（reject + toast）', async () => {
    await expect(
      request.post('/api/alert/rules', {}, { adapter: envelopeAdapter(400, {}, '参数错误') })
    ).rejects.toThrow('参数错误')
    expect(ElMessage.error).toHaveBeenCalled()
  })

  it('401 仍触发登录过期（警告 + 跳转登录）', async () => {
    await expect(
      request.get('/api/spider/status', { adapter: envelopeAdapter(401, {}, '未登录') })
    ).rejects.toThrow()
    expect(ElMessage.warning).toHaveBeenCalledWith('登录已过期，请重新登录')
    expect(replaceMock).toHaveBeenCalled()
  })
})
