import request from '@/api'

// 获取爬虫概览数据
export function getSpiderOverview() {
  return request({
    url: '/api/spider/overview',
    method: 'get',
    loadingOptions: { text: '加载爬虫概览...' },
  })
}

// 触发爬取任务
export function startCrawl(data = {}) {
  return request({
    url: '/api/spider/crawl',
    method: 'post',
    data,
    loadingOptions: false, // 不显示全局 loading，页面自行处理
  })
}

// 获取爬虫状态
export function getSpiderStatus() {
  return request({
    url: '/api/spider/status',
    method: 'get',
    loadingOptions: false,
  })
}

// 获取爬虫日志
export function getSpiderLogs(lines = 100) {
  return request({
    url: '/api/spider/logs',
    method: 'get',
    params: { lines },
    loadingOptions: false,
  })
}
