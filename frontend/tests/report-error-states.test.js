import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

/**
 * #69（U-6）：report.vue 补齐错误态。
 *
 * 覆盖：
 * 1. 模板 fetch 失败 → 可见错误态（.templates-error）与重试入口，且不伪装成空态（#19）；
 * 2. 报告数据 fetch 失败 → 预览区可见错误态（.preview-error）与重试入口，零值不再无解释；
 * 3. 重试成功后错误态消失；
 * 4. 模板成功但为空 → 明确空态（.templates-empty / 暂无可用模板）。
 *
 * mock 层级：@/api/report 全函数。
 */

vi.mock('@/api/report', () => ({
  generateReport: vi.fn(),
  generateAllReports: vi.fn(),
  getReportTemplates: vi.fn(),
  getReportData: vi.fn(),
  getDemoData: vi.fn(),
  downloadReport: vi.fn(),
  previewReport: vi.fn(),
}))

import { getReportTemplates, getReportData } from '@/api/report'
import Report from '../src/views/system/report.vue'

const templatesOk = (
  templates = [{ id: 'standard', name: '标准模板', sections: ['summary'] }]
) => ({
  code: 200,
  msg: 'ok',
  data: { templates },
})

const reportDataOk = () => ({
  code: 200,
  msg: 'ok',
  data: {
    data_source: 'real',
    summary: {
      total_articles: 42,
      total_comments: 7,
      positive_count: 20,
      neutral_count: 15,
      negative_count: 7,
    },
    hot_topics: [{ name: '话题A', heat: 99 }],
  },
})

const mockAllSuccess = () => {
  getReportTemplates.mockResolvedValue(templatesOk())
  getReportData.mockResolvedValue(reportDataOk())
}

const mountView = () => mount(Report)

let consoleErrorSpy

beforeEach(() => {
  vi.clearAllMocks()
  mockAllSuccess()
  consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
})

afterEach(() => {
  consoleErrorSpy.mockRestore()
})

describe('report 错误态（#69 U-6）', () => {
  it('模板失败时显示错误态与重试，且不伪装成空态（#19）', async () => {
    getReportTemplates.mockRejectedValue(new Error('templates down'))
    const wrapper = mountView()
    try {
      await flushPromises()

      expect(wrapper.find('.templates-error').exists()).toBe(true)
      expect(wrapper.find('.templates-error').text()).toContain('获取报告模板失败')
      expect(wrapper.find('.templates-error').text()).toContain('templates down')
      expect(wrapper.find('.templates-error .el-button').exists()).toBe(true)

      // 失败不伪装成空态：无「暂无可用模板」
      expect(wrapper.find('.templates-empty').exists()).toBe(false)
      expect(wrapper.text()).not.toContain('暂无可用模板')
      expect(consoleErrorSpy).toHaveBeenCalled()
    } finally {
      wrapper.unmount()
    }
  })

  it('报告数据失败时预览区显示错误态与重试，零值不再无解释', async () => {
    getReportData.mockRejectedValue(new Error('report data down'))
    const wrapper = mountView()
    try {
      await flushPromises()

      expect(wrapper.find('.preview-error').exists()).toBe(true)
      expect(wrapper.find('.preview-error').text()).toContain('获取报告数据失败')
      expect(wrapper.find('.preview-error').text()).toContain('report data down')
      expect(wrapper.find('.preview-error .el-button').exists()).toBe(true)
      expect(consoleErrorSpy).toHaveBeenCalled()
    } finally {
      wrapper.unmount()
    }
  })

  it('重试成功后错误态消失', async () => {
    getReportTemplates.mockRejectedValueOnce(new Error('temporary failure'))
    const wrapper = mountView()
    try {
      await flushPromises()
      expect(wrapper.find('.templates-error').exists()).toBe(true)

      getReportTemplates.mockResolvedValue(templatesOk())
      await wrapper.find('.templates-error .el-button').trigger('click')
      await flushPromises()

      expect(wrapper.find('.templates-error').exists()).toBe(false)
      expect(wrapper.text()).toContain('标准模板')
      expect(consoleErrorSpy).toHaveBeenCalled()
    } finally {
      wrapper.unmount()
    }
  })

  it('模板成功但为空时渲染明确空态', async () => {
    getReportTemplates.mockResolvedValue(templatesOk([]))
    const wrapper = mountView()
    try {
      await flushPromises()

      expect(wrapper.find('.templates-error').exists()).toBe(false)
      expect(wrapper.find('.templates-empty').exists()).toBe(true)
      expect(wrapper.text()).toContain('暂无可用模板')
    } finally {
      wrapper.unmount()
    }
  })
})
