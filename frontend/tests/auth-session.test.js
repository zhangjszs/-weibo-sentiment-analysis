import { describe, it, expect } from 'vitest'

// #21：本文件原为 node:test 语法且被 vitest exclude，鉴权主逻辑从未进
// 套件。改写为 vitest 并纳入运行（含 #19 新增的 me 缓存用例）。

import {
  AUTH_TOKEN_KEY,
  USER_CACHE_KEY,
  clearSessionState,
  clearCurrentUserCache,
  getCachedCurrentUser,
  getAuthToken,
  getCachedUser,
  setAuthToken,
  setCachedCurrentUser,
  setCachedUser,
} from '../src/utils/authSession.js'

function createStorage(initial = {}) {
  const data = new Map(Object.entries(initial))
  return {
    getItem(key) {
      return data.has(key) ? data.get(key) : null
    },
    setItem(key, value) {
      data.set(key, String(value))
    },
    removeItem(key) {
      data.delete(key)
    },
  }
}

describe('authSession', () => {
  it('auth token stays in memory and is never persisted to storage', () => {
    const storage = createStorage()

    setAuthToken('memory-only-token')

    expect(getAuthToken()).toBe('memory-only-token')
    expect(storage.getItem(AUTH_TOKEN_KEY)).toBeNull()

    clearSessionState(storage)
    expect(getAuthToken()).toBe('')
  })

  it('cached user profile is stored without persisting any auth token', () => {
    const storage = createStorage()
    const user = { id: 7, username: 'alice', is_admin: true }

    setCachedUser(user, storage)

    expect(getCachedUser(storage)).toEqual(user)
    expect(storage.getItem(USER_CACHE_KEY)).toBe(JSON.stringify(user))
    expect(storage.getItem(AUTH_TOKEN_KEY)).toBeNull()
  })

  it('invalid cached user data is discarded safely', () => {
    const storage = createStorage({ [USER_CACHE_KEY]: '{bad json' })

    expect(getCachedUser(storage)).toEqual({})
    expect(storage.getItem(USER_CACHE_KEY)).toBeNull()
  })

  it('clearSessionState clears user cache from storage', () => {
    const storage = createStorage()
    setCachedUser({ id: 1, username: 'bob' }, storage)

    clearSessionState(storage)

    expect(getCachedUser(storage)).toEqual({})
  })
})

describe('currentUser 内存缓存（#19 路由守卫 me TTL）', () => {
  it('set 后 TTL 内可取，clearSessionState 一并失效', () => {
    const user = { username: 'carol', is_admin: false }
    setCachedCurrentUser(user)

    expect(getCachedCurrentUser(60_000)).toEqual(user)
    // -1 表示「任何已流逝时间都算过期」，避免同毫秒判断的时钟竞争
    expect(getCachedCurrentUser(-1)).toBeNull()

    clearCurrentUserCache()
    expect(getCachedCurrentUser(60_000)).toBeNull()
  })

  it('非对象输入按空处理', () => {
    setCachedCurrentUser(null)
    expect(getCachedCurrentUser(60_000)).toBeNull()
  })
})
