import request from '@/api'

export function generateReport(data) {
  return request({
    url: '/api/report/generate',
    method: 'post',
    data,
    loadingOptions: { text: '正在生成报告...' },
  })
}

export function generateAllReports(data) {
  return request({
    url: '/api/report/generate-all',
    method: 'post',
    data,
    loadingOptions: { text: '正在生成所有报告...' },
  })
}

export function getReportTemplates() {
  return request({
    url: '/api/report/templates',
    method: 'get',
  })
}

export function getReportData(params = {}) {
  return request({
    url: '/api/report/data',
    method: 'get',
    params,
  })
}

export function getDemoData() {
  return getReportData({ demo: true })
}

export function downloadReport(filename) {
  return `/api/report/download/${filename}`
}

export function previewReport(filename) {
  return `/api/report/preview/${filename}`
}
