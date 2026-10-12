import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ElMessage } from 'element-plus'

/**
 * #76（T-3）：usePredict 失败可回归底线。
 *
 * 经 harness 真实执行 usePredict（mock @/api/predict）：
 * 1. 成功：模型信息落位；预测成功落结果 + 记历史；
 * 2. 失败：预测 reject → ElMessage.error，predicting 复位，结果不变；
 * 3. 空数据：空文本守卫拦截（不调接口）+ 模型空对象落位无崩。
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

import { predictSentiment, getModelInfo } from '@/api/predict'
import { usePredict } from '../src/composables/usePredict.js'

const harness = {
  template: '<div />',
  setup() {
    return usePredict()
  },
}

const mountHarness = async () => {
  const wrapper = mount(harness)
  await flushPromises()
  return wrapper
}

let errorSpy
let successSpy
let warningSpy

beforeEach(() => {
  vi.clearAllMocks()
  getModelInfo.mockResolvedValue({
    code: 200,
    msg: 'ok',
    data: { model_type: 'TF-IDF', accuracy: 0.9 },
  })
  predictSentiment.mockResolvedValue({
    code: 200,
    msg: 'ok',
    data: { label: 'positive', score: 0.95, source: 'model' },
  })
  errorSpy = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
  successSpy = vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
  warningSpy = vi.spyOn(ElMessage, 'warning').mockImplementation(() => {})
})

afterEach(() => {
  errorSpy.mockRestore()
  successSpy.mockRestore()
  warningSpy.mockRestore()
})

describe('usePredict 底线（#76 T-3）', () => {
  it('成功：模型信息落位，预测落结果并记历史', async () => {
    const wrapper = await mountHarness()
    try {
      expect(wrapper.vm.modelInfo.model_type).toBe('TF-IDF')
      expect(wrapper.vm.loadingModelInfo).toBe(false)

      wrapper.vm.predictForm.text = '今天心情很好'
      await wrapper.vm.handlePredict()
      await flushPromises()

      expect(wrapper.vm.predictResult.label).toBe('positive')
      expect(wrapper.vm.historyList).toHaveLength(1)
      expect(wrapper.vm.historyList[0].text).toContain('今天心情很好')
      expect(wrapper.vm.predicting).toBe(false)
      expect(successSpy).toHaveBeenCalledWith('预测完成')
    } finally {
      wrapper.unmount()
    }
  })

  it('失败：预测 reject → 报错且复位，结果不变', async () => {
    const wrapper = await mountHarness()
    try {
      wrapper.vm.predictForm.text = '今天心情很好'
      predictSentiment.mockRejectedValue(new Error('predict down'))
      await wrapper.vm.handlePredict()
      await flushPromises()

      expect(errorSpy).toHaveBeenCalledWith('预测请求失败')
      expect(wrapper.vm.predicting).toBe(false)
      expect(wrapper.vm.predictResult).toBeNull()
      expect(wrapper.vm.historyList).toHaveLength(0)
    } finally {
      wrapper.unmount()
    }
  })

  it('空数据：空文本守卫拦截，模型空对象落位无崩', async () => {
    getModelInfo.mockResolvedValue({ code: 200, msg: 'ok', data: {} })
    const wrapper = await mountHarness()
    try {
      // 空模型对象落位不崩
      expect(wrapper.vm.modelInfo).toEqual({})

      // 空文本不调接口
      wrapper.vm.predictForm.text = '   '
      await wrapper.vm.handlePredict()
      await flushPromises()

      expect(predictSentiment).not.toHaveBeenCalled()
      expect(warningSpy).toHaveBeenCalledWith('请输入需要分析的文本')
      expect(wrapper.vm.predictResult).toBeNull()
    } finally {
      wrapper.unmount()
    }
  })
})
