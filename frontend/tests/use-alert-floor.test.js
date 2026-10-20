import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

/**
 * #76（T-3）：useAlert 失败可回归底线。
 *
 * 经 harness 真实执行 useAlert（mock @/api/alert）：
 * 1. 成功：三路数据落位，错误态为空，loading 复位；
 * 2. 失败：错误状态可被观测（alertsError/statsError/rulesError），且保留旧数据（#19）；
 * 3. 空数据：空数组落位，无错误态（失败不伪装成空态的反面：空成功不报错误）。
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
import { useAlert } from '../src/composables/useAlert.js'

const harness = {
  template: '<div />',
  setup() {
    return useAlert()
  },
}

const alertItem = { id: 1, title: '高危预警', level: 'danger' }
const ruleItem = { id: 'r1', name: '讨论量规则', enabled: true }

const mockAllSuccess = () => {
  getAlertHistory.mockResolvedValue({
    code: 200,
    msg: 'ok',
    data: { alerts: [alertItem], total: 1 },
  })
  getAlertStats.mockResolvedValue({ code: 200, msg: 'ok', data: { total_alerts: 10 } })
  getAlertRules.mockResolvedValue({ code: 200, msg: 'ok', data: { rules: [ruleItem] } })
}

let consoleErrorSpy

beforeEach(() => {
  vi.clearAllMocks()
  mockAllSuccess()
  consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
})

afterEach(() => {
  consoleErrorSpy.mockRestore()
})

describe('useAlert 底线（#76 T-3）', () => {
  it('成功：三路数据落位，无错误态', async () => {
    const wrapper = mount(harness)
    try {
      await flushPromises()
      expect(wrapper.vm.alerts).toEqual([alertItem])
      expect(wrapper.vm.stats).toEqual({ total_alerts: 10 })
      expect(wrapper.vm.rules).toEqual([ruleItem])
      expect(wrapper.vm.alertsError).toBeNull()
      expect(wrapper.vm.statsError).toBeNull()
      expect(wrapper.vm.rulesError).toBeNull()
      expect(wrapper.vm.loading).toBe(false)
    } finally {
      wrapper.unmount()
    }
  })

  it('失败：错误状态可被观测，且保留旧数据（#19）', async () => {
    const wrapper = mount(harness)
    try {
      await flushPromises()
      expect(wrapper.vm.alerts).toEqual([alertItem])

      getAlertHistory.mockRejectedValue(new Error('history down'))
      getAlertStats.mockRejectedValue(new Error('stats down'))
      getAlertRules.mockRejectedValue(new Error('rules down'))
      await wrapper.vm.fetchAlerts()
      await wrapper.vm.fetchStats()
      await wrapper.vm.fetchRules()
      await flushPromises()

      // 错误状态可被观测（与 #67 错误态预期的行为一致）
      expect(wrapper.vm.alertsError).toBeTruthy()
      expect(wrapper.vm.statsError).toBeTruthy()
      expect(wrapper.vm.rulesError).toBeTruthy()
      // 旧数据未被清空
      expect(wrapper.vm.alerts).toEqual([alertItem])
      expect(wrapper.vm.rules).toEqual([ruleItem])
      expect(wrapper.vm.loading).toBe(false)
      expect(consoleErrorSpy).toHaveBeenCalled()
    } finally {
      wrapper.unmount()
    }
  })

  it('空数据：空数组落位，无错误态', async () => {
    getAlertHistory.mockResolvedValue({ code: 200, msg: 'ok', data: { alerts: [], total: 0 } })
    getAlertRules.mockResolvedValue({ code: 200, msg: 'ok', data: { rules: [] } })
    const wrapper = mount(harness)
    try {
      await flushPromises()
      expect(wrapper.vm.alerts).toEqual([])
      expect(wrapper.vm.rules).toEqual([])
      expect(wrapper.vm.alertsError).toBeNull()
      expect(wrapper.vm.rulesError).toBeNull()
    } finally {
      wrapper.unmount()
    }
  })
})
