import { describe, it, expect } from 'vitest'

/**
 * #74（D-2）：日期/数字格式化单源锁定。
 *
 * 覆盖 utils/index.js 的格式化函数：
 * 1. formatNumber 默认口径（亿/万/k，decimals 透传）；
 * 2. formatNumber compact 'wk' 口径 == platform.vue 旧本地实现逐字行为
 *    （0→'0'、999→'999'、1000→'1.0k'、2500→'2.5k'、9999→'10.0k'、
 *    10000→'1.0w'、15000→'1.5w'、123456→'12.3w'）；
 * 3. formatDateTime / formatLocalDate / formatLocalMonthDay 与旧本地实现
 *    等价（含 falsy 与非法输入守卫）。
 */

import {
  formatNumber,
  formatDateTime,
  formatLocalDate,
  formatLocalMonthDay,
  formatDuration,
} from '../src/utils/index.js'

describe('formatNumber 默认口径（#74 D-2）', () => {
  it('亿/万/k 缩写与 decimals 透传', () => {
    expect(formatNumber(250000000)).toBe('2.50亿')
    expect(formatNumber(15000)).toBe('1.50万')
    expect(formatNumber(2500)).toBe('2.50k')
    expect(formatNumber(250000000, 1)).toBe('2.5亿')
    expect(formatNumber(15000, 0)).toBe('2万')
  })

  it('小数字与空值', () => {
    expect(formatNumber(999)).toBe((999).toLocaleString())
    expect(formatNumber(0)).toBe((0).toLocaleString())
    expect(formatNumber(null)).toBe('-')
    expect(formatNumber(undefined)).toBe('-')
  })

  it('默认口径不受 compact 影响（无 options 时走老路）', () => {
    expect(formatNumber(15000, 2, {})).toBe('1.50万')
  })
})

describe("formatNumber compact 'wk'（platform 旧口径逐字锁定）", () => {
  const cases = [
    [0, '0'],
    [5, '5'],
    [999, '999'],
    [1000, '1.0k'],
    [2500, '2.5k'],
    [9999, '10.0k'],
    [10000, '1.0w'],
    [15000, '1.5w'],
    [123456, '12.3w'],
    [10000000, '1000.0w'],
  ]

  for (const [input, expected] of cases) {
    it(`${input} → ${expected}`, () => {
      expect(formatNumber(input, 1, { compact: 'wk' })).toBe(expected)
    })
  }

  it('空值守卫', () => {
    expect(formatNumber(null, 1, { compact: 'wk' })).toBe('-')
    expect(formatNumber(undefined, 1, { compact: 'wk' })).toBe('-')
  })
})

describe('日期口径单源（#74 D-2）', () => {
  it('formatDateTime == 旧 useTasks/TaskProgress 本地实现', () => {
    const stamp = '2026-10-01T10:00:00'
    expect(formatDateTime(stamp)).toBe(new Date(stamp).toLocaleString())
    expect(formatDateTime('')).toBe('-')
    expect(formatDateTime(null)).toBe('-')
    expect(formatDateTime('not-a-date')).toBe('-')
  })

  it('formatLocalDate == 旧 AnalysisSummary 本地实现', () => {
    const iso = '2026-10-01T10:00:00'
    expect(formatLocalDate(iso)).toBe(new Date(iso).toLocaleDateString('zh-CN'))
    expect(formatLocalDate('')).toBe('-')
    expect(formatLocalDate(null)).toBe('-')
  })

  it('formatLocalMonthDay == 旧 platform formatTime 本地实现', () => {
    const stamp = '2026-10-01T10:00:00'
    expect(formatLocalMonthDay(stamp)).toBe(
      new Date(stamp).toLocaleDateString('zh-CN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    )
    expect(formatLocalMonthDay('')).toBe('')
    expect(formatLocalMonthDay(null)).toBe('')
  })
})

describe('formatDuration 单源（#86）', () => {
  it('毫秒与秒两态映射', () => {
    expect(formatDuration(0.5)).toBe('500 ms')
    expect(formatDuration(0)).toBe('0 ms')
    expect(formatDuration(1)).toBe('1.000 s')
    expect(formatDuration(2.34567)).toBe('2.346 s')
  })

  it('空值与非法输入守卫', () => {
    expect(formatDuration(null)).toBe('-')
    expect(formatDuration(undefined)).toBe('-')
    expect(formatDuration('abc')).toBe('-')
  })
})
