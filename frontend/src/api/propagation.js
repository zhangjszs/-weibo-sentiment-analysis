import request from '@/api'

// 仅保留实际被 propagation.vue 使用的两个接口（#21 死代码清理）

export function analyzePropagation(articleId, params = {}) {
  return request({
    url: `/api/propagation/analyze/${articleId}`,
    method: 'get',
    params,
  })
}

export function getPropagationGraph(articleId, params = {}) {
  return request({
    url: `/api/propagation/graph/${articleId}`,
    method: 'get',
    params,
  })
}
