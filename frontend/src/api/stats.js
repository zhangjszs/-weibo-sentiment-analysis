import request from '@/api'

export function getHomeStats() {
  return request({
    url: '/getAllData/getHomeData',
    method: 'get',
    loadingOptions: { text: '加载首页数据...' },
  })
}

export function getTodayStats() {
  return request({
    url: '/api/stats/today',
    method: 'get',
    loadingOptions: { text: '加载今日统计...' },
  })
}

export function refreshSpiderData(data = {}) {
  return request({
    url: '/api/spider/refresh',
    method: 'post',
    data,
    loadingOptions: { text: '正在刷新数据...' },
  })
}

export function getHotWords(hotWord = '') {
  return request({
    url: '/getAllData/getTableData',
    method: 'get',
    params: { hotWord },
    loadingOptions: hotWord ? { text: '搜索中...' } : { text: '加载热词数据...' },
  })
}

export function getTableData(params = {}) {
  return request({
    url: '/getAllData/getTableData',
    method: 'get',
    params,
    loadingOptions: { text: '加载表格数据...' },
  })
}

export function getArticleData(params = {}) {
  return request({
    url: '/getAllData/getArticleData',
    method: 'get',
    params,
    loadingOptions: { text: '加载文章分析数据...' },
  })
}

export function getCommentData(params = {}) {
  return request({
    url: '/getAllData/getCommentData',
    method: 'get',
    params,
    loadingOptions: { text: '加载评论分析数据...' },
  })
}

export function getIPData(params = {}) {
  return request({
    url: '/getAllData/getIPData',
    method: 'get',
    params,
    loadingOptions: { text: '加载IP分析数据...' },
  })
}

export function getYuqingData(params = {}) {
  return request({
    url: '/getAllData/getYuqingData',
    method: 'get',
    params,
    loadingOptions: { text: '加载舆情分析数据...' },
  })
}

export function getContentCloudData(params = {}) {
  return request({
    url: '/getAllData/getContentCloudData',
    method: 'get',
    params,
    loadingOptions: { text: '加载词云数据...' },
  })
}

// 清空缓存
export function clearCache() {
  return request({
    url: '/getAllData/clearCache',
    method: 'post',
    loadingOptions: { text: '清空缓存...' },
  })
}

// ========== 数据大屏 API ==========

// 获取大屏统计数据
export function getBigScreenStats() {
  return request({
    url: '/api/bigscreen/stats',
    method: 'get',
  })
}

// 获取地区分布数据
export function getBigScreenRegion() {
  return request({
    url: '/api/bigscreen/region',
    method: 'get',
  })
}

// 获取趋势数据
export function getBigScreenTrend(hours = 24) {
  return request({
    url: '/api/bigscreen/trend',
    method: 'get',
    params: { hours },
  })
}

// 获取热门话题
export function getBigScreenHotTopics(limit = 10) {
  return request({
    url: '/api/bigscreen/hot-topics',
    method: 'get',
    params: { limit },
  })
}

// 获取最近预警
export function getBigScreenAlerts(limit = 5) {
  return request({
    url: '/api/bigscreen/alerts',
    method: 'get',
    params: { limit },
  })
}

// 获取所有大屏数据（用于初始化）
export function getBigScreenAllData(hours = 24) {
  return request({
    url: '/api/bigscreen/all',
    method: 'get',
    params: { hours },
  })
}
