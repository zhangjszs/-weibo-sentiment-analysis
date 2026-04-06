import request from '@/api'

export function getPlatformList() {
  return request({
    url: '/api/platform/list',
    method: 'get',
  })
}

export function getPlatformData(platform, params = {}) {
  return request({
    url: `/api/platform/data/${platform}`,
    method: 'get',
    params,
  })
}

export function getAllPlatformsData(params = {}) {
  return request({
    url: '/api/platform/all',
    method: 'get',
    params,
  })
}

export function getPlatformStats(platform) {
  return request({
    url: `/api/platform/stats/${platform}`,
    method: 'get',
  })
}

export function comparePlatforms(platforms) {
  return request({
    url: '/api/platform/compare',
    method: 'post',
    data: { platforms },
  })
}
