import { afterEach, describe, expect, it, vi } from 'vitest'

/**
 * #124：补齐 utils/index.js 中未被 format-utils.test.js 覆盖的公开函数。
 * 纯函数断言真实输入/输出；计时器函数用 fake timers；浏览器 API 用
 * stub/spy 模拟并断言用户可见副作用（Blob 内容、链接 href/download、URL 撤销）。
 */

import {
  copyToClipboard,
  debounce,
  deepClone,
  downloadBlob,
  downloadCsv,
  downloadFile,
  formatDate,
  formatFileSize,
  formatPercent,
  formatRelativeTime,
  generateId,
  getEnumLabel,
  isEmpty,
  throttle,
} from '../src/utils/index.js'

function stubObjectUrl() {
  const createObjectURL = vi.fn(() => 'blob:mock-url')
  const revokeObjectURL = vi.fn()
  vi.stubGlobal('URL', { createObjectURL, revokeObjectURL })
  return { createObjectURL, revokeObjectURL }
}

afterEach(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
  delete document.execCommand
})

describe('formatPercent', () => {
  it('空值返回占位符', () => {
    expect(formatPercent(null)).toBe('-%')
    expect(formatPercent(undefined)).toBe('-%')
  })

  it('按小数位换算百分比', () => {
    expect(formatPercent(0)).toBe('0.00%')
    expect(formatPercent(0.1234)).toBe('12.34%')
    expect(formatPercent(0.1234, 1)).toBe('12.3%')
    expect(formatPercent(1)).toBe('100.00%')
  })
})

describe('formatDate', () => {
  it('按 pattern 输出本地时间', () => {
    const date = new Date(2026, 9, 5, 3, 4, 5)
    expect(formatDate(date)).toBe('2026-10-05 03:04:05')
    expect(formatDate(date, 'YYYY/MM/DD')).toBe('2026/10/05')
    expect(formatDate(date, 'HH:mm:ss')).toBe('03:04:05')
  })

  it('空值守卫', () => {
    expect(formatDate('')).toBe('-')
    expect(formatDate(null)).toBe('-')
    expect(formatDate(undefined)).toBe('-')
  })
})

describe('formatRelativeTime', () => {
  const now = new Date(2026, 9, 23, 12, 0, 0).getTime()

  function relative(date) {
    vi.useFakeTimers()
    vi.setSystemTime(now)
    return formatRelativeTime(date)
  }

  it('按秒/分/时/天分档', () => {
    expect(relative(now - 30 * 1000)).toBe('刚刚')
    expect(relative(now - 5 * 60 * 1000)).toBe('5分钟前')
    expect(relative(now - 3 * 3600 * 1000)).toBe('3小时前')
    expect(relative(now - 2 * 86400 * 1000)).toBe('2天前')
  })

  it('超过 7 天回退为绝对日期', () => {
    expect(relative(new Date(2026, 8, 1, 12, 0, 0).getTime())).toBe('2026-09-01')
  })

  it('空值守卫', () => {
    expect(formatRelativeTime('')).toBe('-')
    expect(formatRelativeTime(null)).toBe('-')
  })
})

describe('formatFileSize', () => {
  it('按 1024 进制换算单位', () => {
    expect(formatFileSize(0)).toBe('0 B')
    expect(formatFileSize(512)).toBe('512 B')
    expect(formatFileSize(1024)).toBe('1 KB')
    expect(formatFileSize(1536)).toBe('1.5 KB')
    expect(formatFileSize(1048576)).toBe('1 MB')
    expect(formatFileSize(1073741824)).toBe('1 GB')
  })
})

describe('debounce', () => {
  it('delay 前不调用，仅以最后一次参数调用一次', () => {
    vi.useFakeTimers()
    const fn = vi.fn()
    const debounced = debounce(fn, 200)

    debounced('a')
    vi.advanceTimersByTime(100)
    debounced('b', 2)
    expect(fn).not.toHaveBeenCalled()

    vi.advanceTimersByTime(199)
    expect(fn).not.toHaveBeenCalled()

    vi.advanceTimersByTime(1)
    expect(fn).toHaveBeenCalledTimes(1)
    expect(fn.mock.calls[0]).toEqual(['b', 2])
  })

  it('透传调用时的 this', () => {
    vi.useFakeTimers()
    const seen = []
    const obj = {
      id: 'ctx',
      run: debounce(function (value) {
        seen.push({ thisValue: this, value })
      }, 50),
    }

    obj.run('x')
    vi.advanceTimersByTime(50)

    expect(seen).toEqual([{ thisValue: obj, value: 'x' }])
  })

  it('默认延迟 300ms', () => {
    vi.useFakeTimers()
    const fn = vi.fn()
    const debounced = debounce(fn)

    debounced()
    vi.advanceTimersByTime(299)
    expect(fn).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(fn).toHaveBeenCalledTimes(1)
  })
})

describe('throttle', () => {
  it('窗口内重复调用被折叠，窗口结束后再次触发', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 9, 23, 12, 0, 0))
    const fn = vi.fn()
    const throttled = throttle(fn, 100)

    throttled('a')
    throttled('b')
    expect(fn).toHaveBeenCalledTimes(1)
    expect(fn.mock.calls[0]).toEqual(['a'])

    vi.advanceTimersByTime(100)
    throttled('c')
    expect(fn).toHaveBeenCalledTimes(2)
    expect(fn.mock.calls[1]).toEqual(['c'])
  })

  it('透传调用时的 this', () => {
    vi.useFakeTimers()
    const seen = []
    const obj = {
      id: 'ctx',
      run: throttle(function (value) {
        seen.push({ thisValue: this, value })
      }, 50),
    }

    obj.run('x')
    obj.run('y')
    expect(seen).toEqual([{ thisValue: obj, value: 'x' }])
  })
})

describe('copyToClipboard', () => {
  it('优先使用 Clipboard API', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', { clipboard: { writeText } })

    await expect(copyToClipboard('你好')).resolves.toBeUndefined()
    expect(writeText).toHaveBeenCalledWith('你好')
  })

  it('无 Clipboard API 时回退 execCommand 并清理 textarea', async () => {
    vi.stubGlobal('navigator', {})
    const execCommand = vi.fn(() => {
      const textarea = document.querySelector('textarea')
      expect(textarea).not.toBeNull()
      expect(textarea.value).toBe('fallback')
      return true
    })
    document.execCommand = execCommand

    await expect(copyToClipboard('fallback')).resolves.toBe(true)
    expect(execCommand).toHaveBeenCalledWith('copy')
    expect(document.querySelectorAll('textarea')).toHaveLength(0)
  })

  it('execCommand 抛错时 reject 并清理 textarea', async () => {
    vi.stubGlobal('navigator', {})
    document.execCommand = vi.fn(() => {
      throw new Error('copy failed')
    })

    await expect(copyToClipboard('x')).rejects.toThrow('copy failed')
    expect(document.querySelectorAll('textarea')).toHaveLength(0)
  })
})

describe('generateId', () => {
  it('格式为 Date.now()-9 位随机串且两次调用不重复', () => {
    vi.spyOn(Date, 'now').mockReturnValue(1700000000123)
    vi.spyOn(Math, 'random').mockReturnValueOnce(0.123456789).mockReturnValueOnce(0.987654321)

    const first = generateId()
    const second = generateId()

    expect(first).toMatch(/^1700000000123-[a-z0-9]{9}$/)
    expect(second).toMatch(/^1700000000123-[a-z0-9]{9}$/)
    expect(first).not.toBe(second)
  })
})

describe('deepClone', () => {
  it('原始值原样返回', () => {
    expect(deepClone(null)).toBeNull()
    expect(deepClone(undefined)).toBeUndefined()
    expect(deepClone(42)).toBe(42)
    expect(deepClone('x')).toBe('x')
    expect(deepClone(false)).toBe(false)
  })

  it('Date 复制为新实例且时间相同', () => {
    const source = new Date(2026, 9, 23, 12, 0, 0)
    const clone = deepClone(source)

    expect(clone).toBeInstanceOf(Date)
    expect(clone).not.toBe(source)
    expect(clone.getTime()).toBe(source.getTime())
  })

  it('数组与嵌套对象不共享引用', () => {
    const source = { list: [1, { deep: 'v' }], nested: { a: 1 } }
    const clone = deepClone(source)

    expect(clone).toEqual(source)
    expect(clone).not.toBe(source)
    expect(clone.list).not.toBe(source.list)
    expect(clone.list[1]).not.toBe(source.list[1])
    expect(clone.nested).not.toBe(source.nested)

    clone.list[1].deep = 'changed'
    expect(source.list[1].deep).toBe('v')
  })

  it('只复制自有属性', () => {
    const source = Object.create({ inherited: true })
    source.own = 1

    const clone = deepClone(source)

    expect(clone).toEqual({ own: 1 })
    expect(Object.prototype.hasOwnProperty.call(clone, 'inherited')).toBe(false)
  })
})

describe('downloadFile', () => {
  it('创建带 href/download 的链接，点击后移除', () => {
    let clicked = null
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function () {
      clicked = {
        href: this.href,
        download: this.download,
        connected: document.body.contains(this),
      }
    })

    downloadFile('https://example.com/report.csv', 'report.csv')

    expect(click).toHaveBeenCalledTimes(1)
    expect(clicked).toEqual({
      href: 'https://example.com/report.csv',
      download: 'report.csv',
      connected: true,
    })
    expect(document.querySelectorAll('a')).toHaveLength(0)
  })
})

describe('downloadBlob', () => {
  it('用 createObjectURL 生成链接并在点击后撤销', () => {
    const { createObjectURL, revokeObjectURL } = stubObjectUrl()
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function () {
      expect(this.href).toBe('blob:mock-url')
      expect(this.download).toBe('export.csv')
      expect(document.body.contains(this)).toBe(true)
    })
    const blob = new Blob(['data'], { type: 'text/plain' })

    downloadBlob(blob, 'export.csv')

    expect(createObjectURL).toHaveBeenCalledWith(blob)
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
    expect(click).toHaveBeenCalledTimes(1)
    expect(document.querySelectorAll('a')).toHaveLength(0)
  })
})

describe('isEmpty', () => {
  const cases = [
    [null, true],
    [undefined, true],
    ['', true],
    ['   ', true],
    [[], true],
    [{}, true],
    [[1], false],
    [{ a: 1 }, false],
    [0, false],
    [false, false],
    ['x', false],
  ]

  for (const [value, expected] of cases) {
    it(`isEmpty(${JSON.stringify(value)}) → ${expected}`, () => {
      expect(isEmpty(value)).toBe(expected)
    })
  }
})

describe('getEnumLabel', () => {
  const status = { PENDING: 'pending', DONE: 'done' }

  it('按值反查枚举名', () => {
    expect(getEnumLabel(status, 'pending')).toBe('PENDING')
    expect(getEnumLabel(status, 'done')).toBe('DONE')
  })

  it('未匹配时返回字符串化原值', () => {
    expect(getEnumLabel(status, 'missing')).toBe('missing')
    expect(getEnumLabel(status, 42)).toBe('42')
  })
})

describe('downloadCsv', () => {
  it('生成带 BOM 的 CSV，转义引号/逗号/换行并清空 null/undefined', () => {
    const { createObjectURL, revokeObjectURL } = stubObjectUrl()
    const CapturedBlob = class {
      constructor(parts, options) {
        this.parts = parts
        this.type = options && options.type
      }
    }
    vi.stubGlobal('Blob', CapturedBlob)
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function () {
      expect(this.download).toBe('out.csv')
      expect(this.href).toBe('blob:mock-url')
    })

    downloadCsv(
      'out.csv',
      ['名称', '备注', '数值'],
      [
        ['foo', 'a,b', 'say "hi"'],
        [null, undefined, 'line1\nline2'],
      ]
    )

    expect(createObjectURL).toHaveBeenCalledTimes(1)
    expect(click).toHaveBeenCalledTimes(1)
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')

    const blob = createObjectURL.mock.calls[0][0]
    expect(blob).toBeInstanceOf(CapturedBlob)
    expect(blob.type).toBe('text/csv;charset=utf-8')
    expect(blob.parts).toEqual(['\uFEFF名称,备注,数值\nfoo,"a,b","say ""hi"""\n,,"line1\nline2"'])
  })
})
