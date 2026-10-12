import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

/**
 * #77（U-9）：predict.vue 模型信息加载失败可见化。
 *
 * 覆盖：
 * 1. getModelInfo reject → 可见错误态（.model-info-error）与重试入口，
 *    且不伪装成「暂无模型信息」空态；
 * 2. 非 200 业务码 → 错误态含服务端 msg；
 * 3. 重试成功后错误态消失并渲染模型信息。
 *
 * mock 层级：@/api/predict 全函数；子组件 + BaseChart stub。
 */

vi.mock('@/api/predict', () => ({
  predictSentiment: vi.fn(),
  predictBatch: vi.fn(),
  getModelInfo: vi.fn(),
}))

vi.mock('@/utils', async (importOriginal) => ({
  ...(await importOriginal()),
  downloadCsv: vi.fn(),
}))

import { getModelInfo } from '@/api/predict'
import Predict from '../src/views/analysis/predict.vue'

const modelInfoOk = () => ({
  code: 200,
  msg: 'ok',
  data: { model_type: 'TF-IDF', best_model: 'NaiveBayes', accuracy: 0.9 },
})

const mountView = () =>
  mount(Predict, {
    global: {
      stubs: { BaseChart: true, PredictInput: true, PredictResult: true },
    },
  })

beforeEach(() => {
  vi.clearAllMocks()
  getModelInfo.mockResolvedValue(modelInfoOk())
})

describe('predict 模型信息错误态（#77 U-9）', () => {
  it('加载失败时显示错误态与重试，不伪装成空态', async () => {
    getModelInfo.mockRejectedValue(new Error('model info down'))
    const wrapper = mountView()
    try {
      await flushPromises()

      expect(wrapper.find('.model-info-error').exists()).toBe(true)
      expect(wrapper.find('.model-info-error').text()).toContain('获取模型信息失败')
      expect(wrapper.find('.model-info-error').text()).toContain('model info down')
      expect(wrapper.find('.model-info-error .el-button').exists()).toBe(true)

      // 失败不伪装成空态
      expect(wrapper.text()).not.toContain('暂无模型信息')
    } finally {
      wrapper.unmount()
    }
  })

  it('非 200 时错误态含服务端 msg', async () => {
    getModelInfo.mockResolvedValue({ code: 500, msg: '模型服务异常', data: null })
    const wrapper = mountView()
    try {
      await flushPromises()

      expect(wrapper.find('.model-info-error').exists()).toBe(true)
      expect(wrapper.find('.model-info-error').text()).toContain('模型服务异常')
      expect(wrapper.text()).not.toContain('暂无模型信息')
    } finally {
      wrapper.unmount()
    }
  })

  it('重试成功后错误态消失并渲染模型信息', async () => {
    getModelInfo.mockRejectedValueOnce(new Error('temporary failure'))
    const wrapper = mountView()
    try {
      await flushPromises()
      expect(wrapper.find('.model-info-error').exists()).toBe(true)

      getModelInfo.mockResolvedValue(modelInfoOk())
      await wrapper.find('.model-info-error .el-button').trigger('click')
      await flushPromises()

      expect(wrapper.find('.model-info-error').exists()).toBe(false)
      expect(wrapper.text()).toContain('TF-IDF')
    } finally {
      wrapper.unmount()
    }
  })
})
