import request from '@/api'

export function getArticles(params = {}) {
  return request({
    url: '/api/articles',
    method: 'get',
    params,
    loadingOptions: { text: '加载文章列表...' },
  })
}

export function getComments(params = {}) {
  return request({
    url: '/api/comments',
    method: 'get',
    params,
    loadingOptions: { text: '加载评论列表...' },
  })
}
