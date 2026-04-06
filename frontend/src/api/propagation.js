import request from '@/api'

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

export function getKOLAnalysis(articleId, params = {}) {
  return request({
    url: `/api/propagation/kol/${articleId}`,
    method: 'get',
    params,
  })
}

export function getPropagationTimeline(articleId, params = {}) {
  return request({
    url: `/api/propagation/timeline/${articleId}`,
    method: 'get',
    params,
  })
}

export function getDepthDistribution(articleId) {
  return request({
    url: `/api/propagation/depth/${articleId}`,
    method: 'get',
  })
}

export function comparePropagation(articleIds) {
  return request({
    url: '/api/propagation/compare',
    method: 'post',
    data: { article_ids: articleIds },
  })
}
