import request from '@/api'

export function login(username, password) {
  return request({
    url: '/api/auth/login',
    method: 'post',
    data: { username, password },
  })
}

export function register(username, password, confirmPassword) {
  return request({
    url: '/api/auth/register',
    method: 'post',
    data: { username, password, confirmPassword },
  })
}

export function logout() {
  return request({
    url: '/api/auth/logout',
    method: 'post',
  })
}

export function checkSession() {
  return request({
    url: '/api/session/check',
    method: 'get',
  })
}

export function extendSession() {
  return request({
    url: '/api/session/extend',
    method: 'post',
  })
}

export function getUserInfo() {
  return request({
    url: '/api/auth/me',
    method: 'get',
  })
}
