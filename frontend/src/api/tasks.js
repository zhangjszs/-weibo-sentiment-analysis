import request from '@/api'

export function getTaskStatus(taskId) {
  return request({
    url: `/api/tasks/${encodeURIComponent(taskId)}/status`,
    method: 'get',
    loadingOptions: false,
  })
}

export function getStartupStatus() {
  return request({
    url: '/api/startup/status',
    method: 'get',
    loadingOptions: false,
  })
}
