/**
 * WebSocket 客户端服务
 * 功能：连接管理、消息收发、断线重连
 */

import { ref } from 'vue'

const RECONNECT_DELAY = 5000
const MAX_RECONNECT_ATTEMPTS = 10

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
      console.log('WebSocket已连接，跳过连接')
      if (token && !this.authenticated) {
        this.authenticate(token)
      }
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}`

    try {
      if (window.io) {
        this.socket = window.io(wsUrl, {
          transports: ['websocket', 'polling'],
          reconnection: false,
          autoConnect: true,
        })

        this.socket.on('connect', () => {
          console.log('WebSocket 连接成功')
          this.connected.value = true
          this.reconnectAttempts = 0

          if (token) {
            this.authenticate(token)
          }
        })

        this.socket.on('disconnect', (reason) => {
          console.log('WebSocket 断开连接:', reason)
          this.connected.value = false
          this.authenticated = false
          this.scheduleReconnect(token)
        })

        this.socket.on('connect_error', (error) => {
          console.error('WebSocket 连接错误:', error)
          this.scheduleReconnect(token)
        })

        this.socket.on('message', (data) => {
          this.handleMessage(data)
        })

        this.socket.on('connected', (data) => {
          console.log('WebSocket 已连接:', data)
        })

        this.socket.on('auth_success', (data) => {
          console.log('WebSocket 认证成功:', data)
          this.authenticated = true
        })

        this.socket.on('auth_error', (data) => {
          console.error('WebSocket 认证失败:', data)
        })

        this.socket.on('subscribed', (data) => {
          console.log('WebSocket 订阅成功:', data)
        })

        this.socket.on('unsubscribed', (data) => {
          console.log('WebSocket 取消订阅:', data)
        })

        this.socket.on('subscribe_error', (data) => {
          console.error('WebSocket 订阅失败:', data)
        })

        this.socket.on('pong', (data) => {
          console.debug('WebSocket Pong:', data)
        })
      } else {
        console.error('Socket.IO 未加载')
      }
    } catch (error) {
      console.error('WebSocket 连接异常:', error)
      this.scheduleReconnect(token)
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

  handleMessage(data) {
    console.debug('收到WebSocket消息:', data)
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
    const delay = RECONNECT_DELAY * this.reconnectAttempts

    console.log(
      `WebSocket ${delay / 1000}秒后尝试重连 (${this.reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`
    )

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
