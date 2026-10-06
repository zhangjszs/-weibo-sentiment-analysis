export const AUTH_TOKEN_KEY = 'weibo_token'
export const USER_CACHE_KEY = 'weibo_user'

let authToken = ''

// /api/auth/me 的进程内缓存（带 TTL，见 getCachedCurrentUser）。仅存内存、
// 不落 localStorage：避免 TTL 过期后仍被复用。登出与 401 都经过
// clearSessionState，缓存随之失效，不会出现登出后守卫仍放行的问题（#19）。
let currentUserCache = { user: null, fetchedAt: 0 }

export const getCachedCurrentUser = (maxAgeMs = 0) => {
  if (!currentUserCache.user) {
    return null
  }
  if (Date.now() - currentUserCache.fetchedAt > maxAgeMs) {
    return null
  }
  return currentUserCache.user
}

export const setCachedCurrentUser = (user) => {
  currentUserCache = {
    user: user && typeof user === 'object' ? user : null,
    fetchedAt: user ? Date.now() : 0,
  }
}

export const clearCurrentUserCache = () => {
  currentUserCache = { user: null, fetchedAt: 0 }
}

const resolveStorage = (storage) => {
  if (storage) {
    return storage
  }

  if (typeof window !== 'undefined' && window.localStorage) {
    return window.localStorage
  }

  return null
}

export const getAuthToken = () => authToken

export const setAuthToken = (token = '') => {
  authToken = token || ''
  return authToken
}

export const getCachedUser = (storage) => {
  const targetStorage = resolveStorage(storage)
  if (!targetStorage) {
    return {}
  }

  const rawValue = targetStorage.getItem(USER_CACHE_KEY)
  if (!rawValue) {
    return {}
  }

  try {
    const parsed = JSON.parse(rawValue)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    targetStorage.removeItem(USER_CACHE_KEY)
    return {}
  }
}

export const setCachedUser = (user, storage) => {
  const targetStorage = resolveStorage(storage)
  if (!targetStorage) {
    return
  }

  targetStorage.removeItem(AUTH_TOKEN_KEY)

  if (user && typeof user === 'object' && Object.keys(user).length > 0) {
    targetStorage.setItem(USER_CACHE_KEY, JSON.stringify(user))
    return
  }

  targetStorage.removeItem(USER_CACHE_KEY)
}

export const clearSessionState = (storage) => {
  authToken = ''
  clearCurrentUserCache()

  const targetStorage = resolveStorage(storage)
  if (!targetStorage) {
    return
  }

  targetStorage.removeItem(AUTH_TOKEN_KEY)
  targetStorage.removeItem(USER_CACHE_KEY)
}
