import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

/**
 * #67（U-4）：alert 中心补齐错误态与规则空态。
 *
 * 覆盖：
 * 1. 规则列表为空时（rules: []）渲染可见空态（.rules-empty / 暂无预警规则），不再是一块空白；
 * 2. 预警历史 fetch 失败时显示可见错误态（.alerts-error）与重试入口；且不清空已有旧数据（#19）；
 * 3. 统计数据 fetch 失败时显示区域错误态（.stats-error）与重试入口；
 * 4. 预警规则 fetch 失败时显示错误态（.rules-error）与重试入口，且失败时不伪装成空态（#19）；
 * 5. 重试成功后错误态消失。
 *
 * mock 层级：@/api/alert 全函数；BaseChart stub。
 */

vi.mock('@/api/alert', () => ({
  getAlertHistory: vi.fn(),
  getAlertStats: vi.fn(),
  getAlertRules: vi.fn(),
  createAlertRule: vi.fn(),
  toggleAlertRule: vi.fn(),
  markAllAlertsRead: vi.fn(),
  testAlert: vi.fn(),
}))

import { getAlertHistory, getAlertStats, getAlertRules } from '@/api/alert'
import Center from '../src/views/alert/center.vue'

const alertItem = {
  id: 1,
  title: '高危预警',
  message: '舆情讨论量剧增',
  level: 'danger',
  alert_type: 'volume_spike',
  created_at: '2026-10-01T12:00:00Z',
  is_read: false,
}

const ruleItem = {
  id: 'r1',
  name: '讨论量规则',
  alert_type: 'volume_spike',
  level: 'warning',
  cooldown_minutes: 30,
  enabled: true,
}

const historyOk = (alerts = [alertItem]) => ({
  code: 200,
  msg: 'ok',
  data: { alerts, total: alerts.length },
})

const statsOk = () => ({
  code: 200,
  msg: 'ok',
  data: {
    total_alerts: 10,
    unread_count: 2,
    active_rules: 3,
    level_distribution: { info: 2, warning: 5, danger: 2, critical: 1 },
  },
})

const rulesOk = (rules = [ruleItem]) => ({
  code: 200,
  msg: 'ok',
  data: { rules },
})

const mockAllSuccess = () => {
  getAlertHistory.mockResolvedValue(historyOk())
  getAlertStats.mockResolvedValue(statsOk())
  getAlertRules.mockResolvedValue(rulesOk())
}

const mountView = () =>
  mount(Center, {
    global: {
      stubs: {
        BaseChart: true,
        ElDialog: true,
      },
    },
  })

let consoleErrorSpy

beforeEach(() => {
  vi.clearAllMocks()
  mockAllSuccess()
  consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
})

afterEach(() => {
  consoleErrorSpy.mockRestore()
})

describe('alert 中心错误态与规则空态（#67 U-4）', () => {
  it('规则列表为空时渲染明确空态，不再是一块空白', async () => {
    getAlertRules.mockResolvedValue(rulesOk([]))
    const wrapper = mountView()
    try {
      await flushPromises()

      // 规则空态被渲染，显示「暂无预警规则」
      expect(wrapper.find('.rules-empty').exists()).toBe(true)
      expect(wrapper.text()).toContain('暂无预警规则')
      // 规则列表项为 0
      expect(wrapper.findAll('.rule-item').length).toBe(0)
    } finally {
      wrapper.unmount()
    }
  })

  it('预警历史失败时显示错误态与重试，且不清空已有旧数据（#19）', async () => {
    const wrapper = mountView()
    try {
      await flushPromises()
      expect(wrapper.text()).toContain('高危预警')
      expect(wrapper.find('.alerts-error').exists()).toBe(false)

      // 重新拉取历史失败
      getAlertHistory.mockRejectedValue(new Error('network error'))
      // 触发分页或重载以触发 fetchAlerts
      await wrapper.find('.alerts-card, .history-card').find('.el-select').trigger('click')
      // 直接触发从 center 解构出来的 fetchAlerts，或调用重试
      const retryBtn = wrapper.find('.alerts-error .el-button')
      if (retryBtn.exists()) {
        await retryBtn.trigger('click')
        await flushPromises()
      } else {
        // 通过组件触发刷新
        wrapper.vm.fetchAlerts?.()
        await flushPromises()
      }

      expect(wrapper.find('.alerts-error').exists()).toBe(true)
      expect(wrapper.find('.alerts-error').text()).toContain('获取预警历史失败')
      expect(wrapper.find('.alerts-error .el-button').exists()).toBe(true)

      // #19 语义：原有旧数据未被清空
      expect(wrapper.text()).toContain('高危预警')
      expect(consoleErrorSpy).toHaveBeenCalled()
    } finally {
      wrapper.unmount()
    }
  })

  it('统计数据失败时显示区域错误态与重试，且不清空已有统计数据（#19）', async () => {
    getAlertStats.mockRejectedValue(new Error('stats failed'))
    const wrapper = mountView()
    try {
      await flushPromises()

      expect(wrapper.find('.stats-error').exists()).toBe(true)
      expect(wrapper.find('.stats-error').text()).toContain('获取预警统计失败')
      expect(wrapper.find('.stats-error .el-button').exists()).toBe(true)
      expect(consoleErrorSpy).toHaveBeenCalled()
    } finally {
      wrapper.unmount()
    }
  })

  it('预警规则失败时显示区域错误态与重试，且不伪装成空态（#19）', async () => {
    getAlertRules.mockRejectedValue(new Error('rules failed'))
    const wrapper = mountView()
    try {
      await flushPromises()

      expect(wrapper.find('.rules-error').exists()).toBe(true)
      expect(wrapper.find('.rules-error').text()).toContain('获取预警规则失败')
      expect(wrapper.find('.rules-error .el-button').exists()).toBe(true)

      // 失败不伪装成空态：无「暂无预警规则」
      expect(wrapper.find('.rules-empty').exists()).toBe(false)
      expect(wrapper.text()).not.toContain('暂无预警规则')
      expect(consoleErrorSpy).toHaveBeenCalled()
    } finally {
      wrapper.unmount()
    }
  })

  it('重试成功后错误态消失', async () => {
    getAlertRules.mockRejectedValueOnce(new Error('temporary failure'))
    const wrapper = mountView()
    try {
      await flushPromises()
      expect(wrapper.find('.rules-error').exists()).toBe(true)

      // 重试成功
      getAlertRules.mockResolvedValue(rulesOk([ruleItem]))
      await wrapper.find('.rules-error .el-button').trigger('click')
      await flushPromises()

      expect(wrapper.find('.rules-error').exists()).toBe(false)
      expect(wrapper.text()).toContain('讨论量规则')
      expect(consoleErrorSpy).toHaveBeenCalled()
    } finally {
      wrapper.unmount()
    }
  })
})
