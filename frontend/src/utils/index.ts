/**
 * #140：前端 utils 桶文件（`@/utils`）的类型化迁移。运行时语义逐字不变。
 *
 * 本文件是 `src/utils/` 的桶入口——`@/utils` 即解析到它。
 */

/** 日期类格式化函数接受的输入：Date 对象 / 可解析的字符串 / 毫秒时间戳。 */
export type DateInput = Date | string | number

/** D-2（#74）：`formatNumber` 的紧凑口径选项——调用方显式 opt-in，默认亿/万/k 口径不变。 */
export interface FormatNumberOptions {
  compact?: 'wk'
}

export function formatNumber(
  num?: number | null,
  decimals = 2,
  options: FormatNumberOptions = {}
): string {
  if (num === null || num === undefined) return '-'

  // D-2（#74）：compact 'wk' 复刻 platform.vue 旧本地口径（w/k 缩写），
  // 调用方显式 opt-in，默认 亿/万/k 口径不变。
  if (options.compact === 'wk') {
    if (num >= 10000) {
      return (num / 10000).toFixed(decimals) + 'w'
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(decimals) + 'k'
    }
    return num.toString()
  }

  if (num >= 100000000) {
    return (num / 100000000).toFixed(decimals) + '亿'
  }
  if (num >= 10000) {
    return (num / 10000).toFixed(decimals) + '万'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(decimals) + 'k'
  }

  return num.toLocaleString()
}

export function formatPercent(value?: number | null, decimals = 2): string {
  if (value === null || value === undefined) return '-%'
  return (value * 100).toFixed(decimals) + '%'
}

export function formatDate(date?: DateInput | null, pattern = 'YYYY-MM-DD HH:mm:ss'): string {
  if (!date) return '-'

  const d = new Date(date)
  // #140：原为 `d.getFullYear()`（number），TS 的 `String.replace` 的
  // `replaceValue` 形参只接受 string。此处改用 `String(...)`——JS 运行时本来
  // 就会对 replaceValue 做 ToString 转换，二者结果逐字相同。
  const year = String(d.getFullYear())
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const minute = String(d.getMinutes()).padStart(2, '0')
  const second = String(d.getSeconds()).padStart(2, '0')

  return pattern
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hour)
    .replace('mm', minute)
    .replace('ss', second)
}

// D-2（#74）：本地 locale 日期口径单源（以下三函数分别收敛
// AnalysisSummary / useTasks+TaskProgress / platform formatTime 的旧本地实现，
// 可见输出与收敛前逐字一致）。
export function formatDateTime(value?: DateInput | null): string {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleString()
}

/**
 * 注意：catch 分支返回**原始输入**（而非字符串）——这是迁移前的既有行为，
 * 本切片逐字保留。因此返回类型如实为 `string | DateInput`。
 */
export function formatLocalDate(value?: DateInput | null): string | DateInput {
  if (!value) return '-'
  try {
    return new Date(value).toLocaleDateString('zh-CN')
  } catch {
    return value
  }
}

export function formatLocalMonthDay(value?: DateInput | null): string {
  if (!value) return ''
  return new Date(value).toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// D-2 后续（#86）：秒→ms/s 口径单源（收敛 useTasks/TaskProgress 旧本地实现）。
export function formatDuration(seconds?: number | string | null): string {
  if (seconds == null || Number.isNaN(Number(seconds))) return '-'
  const value = Number(seconds)
  if (value < 1) return `${Math.round(value * 1000)} ms`
  return `${value.toFixed(3)} s`
}

export function formatRelativeTime(date?: DateInput | null): string {
  if (!date) return '-'

  const now = new Date()
  const target = new Date(date)
  // #140：原为 `now - target`，TS 不允许 Date 参与算术运算。JS 运行时走
  // ToPrimitive(hint number) → valueOf()，与 `getTime()` 逐字等价。
  const diff = now.getTime() - target.getTime()

  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (seconds < 60) {
    return '刚刚'
  }
  if (minutes < 60) {
    return `${minutes}分钟前`
  }
  if (hours < 24) {
    return `${hours}小时前`
  }
  if (days < 7) {
    return `${days}天前`
  }

  return formatDate(date, 'YYYY-MM-DD')
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export function debounce<TArgs extends unknown[], TThis>(
  fn: (this: TThis, ...args: TArgs) => void,
  delay = 300
): (this: TThis, ...args: TArgs) => void {
  let timer: ReturnType<typeof setTimeout> | null = null

  return function (this: TThis, ...args: TArgs) {
    if (timer) {
      clearTimeout(timer)
    }
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

export function throttle<TArgs extends unknown[], TThis>(
  fn: (this: TThis, ...args: TArgs) => void,
  delay = 300
): (this: TThis, ...args: TArgs) => void {
  let lastTime = 0

  return function (this: TThis, ...args: TArgs) {
    const now = Date.now()
    if (now - lastTime >= delay) {
      fn.apply(this, args)
      lastTime = now
    }
  }
}

export function copyToClipboard(text: string): Promise<void | boolean> {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text)
  }

  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()

  try {
    document.execCommand('copy')
    return Promise.resolve(true)
  } catch (error) {
    return Promise.reject(error)
  } finally {
    document.body.removeChild(textarea)
  }
}

export function generateId(): string {
  return Date.now() + '-' + Math.random().toString(36).substr(2, 9)
}

export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj
  }

  if (obj instanceof Date) {
    return new Date(obj.getTime()) as unknown as T
  }

  if (obj instanceof Array) {
    return obj.map((item) => deepClone(item)) as unknown as T
  }

  if (obj instanceof Object) {
    const clonedObj: Record<string, unknown> = {}
    // #140：`obj as Record<string, unknown>` 是**编译期擦除**的断言，输出的
    // JS 与迁移前逐字相同（仍是 `for (const key in obj)` 与 `obj[key]`）。
    for (const key in obj as Record<string, unknown>) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        clonedObj[key] = deepClone((obj as Record<string, unknown>)[key])
      }
    }
    return clonedObj as unknown as T
  }

  return obj
}

export function downloadFile(url: string, filename: string): void {
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export function isEmpty(value: unknown): boolean {
  if (value === null || value === undefined) {
    return true
  }
  if (typeof value === 'string') {
    return value.trim() === ''
  }
  if (Array.isArray(value)) {
    return value.length === 0
  }
  if (typeof value === 'object') {
    return Object.keys(value).length === 0
  }
  return false
}

export function getEnumLabel(enumObj: Record<string, unknown>, value: unknown): string {
  const found = Object.entries(enumObj).find(([, val]) => val === value)
  return found ? found[0] : String(value)
}

export function downloadCsv(filename: string, headers: string[], rows: unknown[][]): void {
  const escapeCell = (value: unknown): string => {
    if (value === null || value === undefined) return ''
    const str = String(value)
    const escaped = str.replaceAll('"', '""')
    if (/[",\n\r]/.test(escaped)) return `"${escaped}"`
    return escaped
  }

  const lines: string[] = []
  lines.push(headers.map(escapeCell).join(','))
  for (const row of rows) {
    lines.push(row.map(escapeCell).join(','))
  }

  const bom = '\uFEFF'
  const blob = new Blob([bom + lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  downloadBlob(blob, filename)
}
