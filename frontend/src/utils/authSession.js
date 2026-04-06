export const AUTH_TOKEN_KEY = 'weibo_token'
export const USER_CACHE_KEY = 'weibo_user'

let authToken = ''

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
  } catch (error) {
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

  const targetStorage = resolveStorage(storage)
  if (!targetStorage) {
    return
  }

  targetStorage.removeItem(AUTH_TOKEN_KEY)
  targetStorage.removeItem(USER_CACHE_KEY)
}
