/**
 * WebSocket 客户端服务
 * 功能：连接管理、消息收发、断线重连
 */

import { ref } from 'vue'
import { io } from 'socket.io-client'
import { getAuthToken } from '@/utils/authSession'

const RECONNECT_DELAY = 5000
const MAX_RECONNECT_ATTEMPTS = 10
const MAX_RECONNECT_DELAY = 60000

class WebSocketClient {
  constructor() {
    this.socket = null
    this.connected = ref(false)
    this.reconnectAttempts = 0
    this.reconnectTimer = null
    this.messageHandlers = {}
    this.authenticated = false
  }

  get isConnected() {
    return this.connected.value
  }

  connect(token) {
    if (this.socket) {
      if (token && !this.authenticated) {
        this.authenticate(token)
      }
      return
    }

    // socket.io-client 直接 import：此前依赖全局 window.io，但 index.html
    // 从未引入 socket.io 脚本，永远走「Socket.IO 未加载」分支（#20）。
    // 同源连接走 /socket.io 默认路径（vite/nginx 均已配代理与 Upgrade）。
    const wsUrl = `${window.location.protocol}//${window.location.host}`
    const authToken = token || getAuthToken()

    try {
      this.socket = io(wsUrl, {
        transports: ['websocket', 'polling'],
        reconnection: false,
        autoConnect: true,
      })

      this.socket.on('connect', () => {
        this.connected.value = true
        this.reconnectAttempts = 0

        if (authToken) {
          this.authenticate(authToken)
        }
      })

      this.socket.on('disconnect', (reason) => {
        this.connected.value = false
        this.authenticated = false
        this.scheduleReconnect(authToken)
      })

      this.socket.on('connect_error', (error) => {
        console.error('WebSocket 连接错误:', error)
        this.scheduleReconnect(authToken)
      })


      this.socket.on('connected', (data) => {
      })

      this.socket.on('auth_success', (data) => {
        this.authenticated = true
      })

      this.socket.on('auth_error', (data) => {
        console.error('WebSocket 认证失败:', data)
      })

      this.socket.on('subscribed', (data) => {
      })

      this.socket.on('unsubscribed', (data) => {
      })

      this.socket.on('subscribe_error', (data) => {
        console.error('WebSocket 订阅失败:', data)
      })

      this.socket.on('pong', (data) => {
      })
    } catch (error) {
      console.error('WebSocket 连接异常:', error)
      this.scheduleReconnect(authToken)
    }
  }

  authenticate(token) {
    if (!this.socket) {
      console.warn('WebSocket 未连接，无法认证')
      return
    }
    this.socket.emit('authenticate', { token })
  }

  subscribe(type, target) {
    if (!this.socket) {
      console.warn('WebSocket 未连接，无法订阅')
      return
    }
    this.socket.emit('subscribe', { type, target })
  }

  unsubscribe(type, target) {
    if (!this.socket) {
      console.warn('WebSocket 未连接，无法取消订阅')
      return
    }
    this.socket.emit('unsubscribe', { type, target })
  }

  getRooms() {
    if (!this.socket) {
      return Promise.resolve({ rooms: [] })
    }
    return new Promise((resolve) => {
      this.socket.emit('get_rooms', (response) => {
        resolve(response)
      })
    })
  }

  ping() {
    if (this.socket) {
      this.socket.emit('ping')
    }
  }

  on(event, handler) {
    if (!this.messageHandlers[event]) {
      this.messageHandlers[event] = []
    }
    this.messageHandlers[event].push(handler)

    if (this.socket) {
      this.socket.on(event, handler)
    }
  }

  off(event, handler) {
    if (this.messageHandlers[event]) {
      this.messageHandlers[event] = this.messageHandlers[event].filter((h) => h !== handler)
    }
    if (this.socket) {
      this.socket.off(event, handler)
    }
  }


  scheduleReconnect(token) {
    if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.error('WebSocket 重连次数已达上限，停止重连')
      return
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    this.reconnectAttempts++
    // 指数退避 + 抖动：固定间隔会让断线服务恢复瞬间的所有客户端同时重连
    // （惊群），抖动把重连打散（#20）
    const exponential = Math.min(RECONNECT_DELAY * 2 ** (this.reconnectAttempts - 1), MAX_RECONNECT_DELAY)
    const delay = exponential * (0.5 + Math.random())

    this.reconnectTimer = setTimeout(() => {
      this.disconnect()
      this.connect(token)
    }, delay)
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
    this.connected.value = false
    this.authenticated = false
  }
}

const websocketClient = new WebSocketClient()

export default websocketClient
export { websocketClient, WebSocketClient }
