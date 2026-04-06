import request from '@/api'

/**
 * 添加收藏
 */
export function addFavorite(articleId) {
  return request.post(`/api/favorites/${articleId}`)
}

/**
 * 取消收藏
 */
export function removeFavorite(articleId) {
  return request.delete(`/api/favorites/${articleId}`)
}

/**
 * 检查是否已收藏
 */
export function checkFavorite(articleId) {
  return request.get(`/api/favorites/check/${articleId}`)
}

/**
 * 获取收藏列表
 */
export function getFavorites(params = {}) {
  return request.get('/api/favorites', { params })
}

/**
 * 批量检查收藏状态
 */
export function batchCheckFavorites(articleIds) {
  return request.post('/api/favorites/batch-check', { article_ids: articleIds })
}
