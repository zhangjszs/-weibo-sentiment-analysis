import request from '@/api'

/**
 * 获取用户完整个人资料
 */
export function getProfile() {
  return request.get('/api/user/profile')
}

/**
 * 更新用户个人资料
 * @param {Object} data - { nickname, email, bio, avatar_color }
 */
export function updateProfile(data) {
  return request.put('/api/user/profile', data)
}

/**
 * 修改密码
 * @param {Object} data - { oldPassword, newPassword, confirmPassword }
 */
export function changePassword(data) {
  return request.put('/api/user/password', data)
}
