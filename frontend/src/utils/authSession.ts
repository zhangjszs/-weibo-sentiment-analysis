/**
 * #139：会话 token 与用户缓存的类型化迁移。运行时语义逐字不变。
 *
 * 会话用户对象采用宽松记录类型：api 层（§2 第二批）尚未类型化，
 * 故此处**不自造** id / username / is_admin 等字段结构——待 api 层
 * 给出契约后再收紧。
 */
export type SessionUser = Record<string, unknown>

export const AUTH_TOKEN_KEY = 'weibo_token'
export const USER_CACHE_KEY = 'weibo_user'

let authToken = ''

// /api/auth/me 的进程内缓存（带 TTL，见 getCachedCurrentUser）。仅存内存、
// 不落 localStorage：避免 TTL 过期后仍被复用。登出与 401 都经过
// clearSessionState，缓存随之失效，不会出现登出后守卫仍放行的问题（#19）。
let currentUserCache: { user: SessionUser | null; fetchedAt: number } = { user: null, fetchedAt: 0 }

export const getCachedCurrentUser = (maxAgeMs = 0): SessionUser | null => {
  if (!currentUserCache.user) {
    return null
  }
  if (Date.now() - currentUserCache.fetchedAt > maxAgeMs) {
    return null
  }
  return currentUserCache.user
}

export const setCachedCurrentUser = (user: SessionUser | null | undefined): void => {
  currentUserCache = {
    user: user && typeof user === 'object' ? user : null,
    fetchedAt: user ? Date.now() : 0,
  }
}

export const clearCurrentUserCache = (): void => {
  currentUserCache = { user: null, fetchedAt: 0 }
}

const resolveStorage = (storage?: Storage | null): Storage | null => {
  if (storage) {
    return storage
  }

  if (typeof window !== 'undefined' && window.localStorage) {
    return window.localStorage
  }

  return null
}

export const getAuthToken = (): string => authToken

export const setAuthToken = (token = ''): string => {
  authToken = token || ''
  return authToken
}

export const getCachedUser = (storage?: Storage | null): SessionUser => {
  const targetStorage = resolveStorage(storage)
  if (!targetStorage) {
    return {}
  }

  const rawValue = targetStorage.getItem(USER_CACHE_KEY)
  if (!rawValue) {
    return {}
  }

  try {
    // 断言而非校验：保持迁移前的宽松恢复行为——不对持久化内容做字段校验、
    // 不过滤脏数据、不新增回退分支。
    const parsed = JSON.parse(rawValue) as SessionUser
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    targetStorage.removeItem(USER_CACHE_KEY)
    return {}
  }
}

export const setCachedUser = (
  user: SessionUser | null | undefined,
  storage?: Storage | null
): void => {
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

export const clearSessionState = (storage?: Storage | null): void => {
  authToken = ''
  clearCurrentUserCache()

  const targetStorage = resolveStorage(storage)
  if (!targetStorage) {
    return
  }

  targetStorage.removeItem(AUTH_TOKEN_KEY)
  targetStorage.removeItem(USER_CACHE_KEY)
}
