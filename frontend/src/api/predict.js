import request from '@/api'

export function predictSentiment(text, mode = 'custom') {
  return request({
    url: '/api/sentiment/analyze',
    method: 'post',
    data: { text, mode },
    loadingOptions: { text: '分析中...' },
  })
}

export function predictBatch(texts, mode = 'custom') {
  return request({
    url: '/api/predict/batch',
    method: 'post',
    data: { texts, mode },
    loadingOptions: { text: '批量分析中...' },
  })
}

export function getModelInfo() {
  return request({
    url: '/api/model/info',
    method: 'get',
    loadingOptions: { text: '获取模型信息...' },
  })
}

export function retrainModel(params = {}) {
  return request({
    url: '/api/model/retrain',
    method: 'post',
    data: params,
    loadingOptions: { text: '模型训练中...' },
  })
}
