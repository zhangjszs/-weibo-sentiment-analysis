import request from '@/api'

export function getAlertRules() {
  return request({
    url: '/api/alert/rules',
    method: 'get',
  })
}

export function createAlertRule(data) {
  return request({
    url: '/api/alert/rules',
    method: 'post',
    data,
  })
}

export function updateAlertRule(ruleId, data) {
  return request({
    url: `/api/alert/rules/${ruleId}`,
    method: 'put',
    data,
  })
}

export function deleteAlertRule(ruleId) {
  return request({
    url: `/api/alert/rules/${ruleId}`,
    method: 'delete',
  })
}

export function toggleAlertRule(ruleId) {
  return request({
    url: `/api/alert/rules/${ruleId}/toggle`,
    method: 'post',
  })
}

export function getAlertHistory(params = {}) {
  return request({
    url: '/api/alert/history',
    method: 'get',
    params,
  })
}

export function getAlertStats() {
  return request({
    url: '/api/alert/stats',
    method: 'get',
  })
}

export function getUnreadCount() {
  return request({
    url: '/api/alert/unread-count',
    method: 'get',
  })
}

export function markAlertRead(alertId) {
  return request({
    url: `/api/alert/${alertId}/read`,
    method: 'post',
  })
}

export function markAllAlertsRead() {
  return request({
    url: '/api/alert/read-all',
    method: 'post',
  })
}

export function testAlert(data) {
  return request({
    url: '/api/alert/test',
    method: 'post',
    data,
  })
}

export function evaluateAlert(data) {
  return request({
    url: '/api/alert/evaluate',
    method: 'post',
    data,
  })
}
