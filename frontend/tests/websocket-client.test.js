import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

/**
 * #20：WebSocket 客户端接入 socket.io-client。
 * - 直接 import 的 io()，不再依赖 index.html 从未引入的 window.io
 * - 同源 wsUrl 走 /socket.io 默认路径（vite/nginx 代理）
 * - 重连退避：指数 + 抖动，不再固定间隔惊群
 */

const ioMock = vi.fn(() => ({ on: vi.fn(), emit: vi.fn(), disconnect: vi.fn() }))
vi.mock('socket.io-client', () => ({
  io: (...args) => ioMock(...args),
}))

import { WebSocketClient } from '@/utils/websocket.js'

const handlerFor = (client, event) => {
  const on = ioMock.mock.results.at(-1).value.on
  const call = on.mock.calls.find(([name]) => name === event)
  return call?.[1]
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('websocket 客户端 (#20)', () => {
  it('connect 直接调用 socket.io-client 的 io()，不依赖 window.io', () => {
    const client = new WebSocketClient()
    client.connect('tok-1')
    expect(ioMock).toHaveBeenCalledTimes(1)
    expect(ioMock.mock.calls[0][0]).toBe(`${window.location.protocol}//${window.location.host}`)
    expect(client.isConnected).toBe(false)
  })

  it('connect 成功后用传入 token 触发 authenticate', () => {
    const client = new WebSocketClient()
    client.connect('tok-1')
    handlerFor(client, 'connect')()
    expect(client.isConnected).toBe(true)
    const emit = ioMock.mock.results.at(-1).value.emit
    expect(emit).toHaveBeenCalledWith('authenticate', { token: 'tok-1' })
  })

  it('重连退避带抖动：第一次延迟在 [2.5s, 7.5s)，指数增长', () => {
    vi.spyOn(Math, 'random').mockReturnValue(0) // 抖动取下界 0.5x
    const client = new WebSocketClient()
    client.connect('tok-1')

    handlerFor(client, 'connect_error')(new Error('down'))
    // 第一次：5000 * 2^0 * 0.5 = 2500ms
    vi.advanceTimersByTime(2499)
    expect(ioMock).toHaveBeenCalledTimes(1)
    vi.advanceTimersByTime(1)
    expect(ioMock).toHaveBeenCalledTimes(2)

    // 第二次：5000 * 2^1 * 0.5 = 5000ms
    handlerFor(client, 'connect_error')(new Error('down'))
    vi.advanceTimersByTime(4999)
    expect(ioMock).toHaveBeenCalledTimes(2)
    vi.advanceTimersByTime(1)
    expect(ioMock).toHaveBeenCalledTimes(3)
  })
})
