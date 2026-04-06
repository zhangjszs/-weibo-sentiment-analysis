import test from 'node:test'
import assert from 'node:assert/strict'

import {
  AUTH_TOKEN_KEY,
  USER_CACHE_KEY,
  clearSessionState,
  getAuthToken,
  getCachedUser,
  setAuthToken,
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

test('auth token stays in memory and is never persisted to storage', () => {
  const storage = createStorage()

  setAuthToken('memory-only-token')

  assert.equal(getAuthToken(), 'memory-only-token')
  assert.equal(storage.getItem(AUTH_TOKEN_KEY), null)

  clearSessionState(storage)
  assert.equal(getAuthToken(), '')
})

test('cached user profile is stored without persisting any auth token', () => {
  const storage = createStorage()
  const user = { id: 7, username: 'alice', is_admin: true }

  setCachedUser(user, storage)

  assert.deepEqual(getCachedUser(storage), user)
  assert.equal(storage.getItem(USER_CACHE_KEY), JSON.stringify(user))
  assert.equal(storage.getItem(AUTH_TOKEN_KEY), null)
})

test('invalid cached user data is discarded safely', () => {
  const storage = createStorage({ [USER_CACHE_KEY]: '{bad json' })

  assert.deepEqual(getCachedUser(storage), {})
  assert.equal(storage.getItem(USER_CACHE_KEY), null)
})
