import { describe, it, expect, vi } from 'vitest'
import { useTable } from '@/composables/useTable.js'

/**
 * #19：useTable 失败态与竞态防护。
 * - 失败置 loadError（区分「真无数据」与「加载失败」），旧数据保留不清空
 * - 慢的旧响应不得覆盖新响应（快速翻页/连续搜索）
 */

const flush = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('useTable 失败态 (#19)', () => {
  it('加载失败置 loadError=true 且保留旧数据与旧 total', async () => {
    let shouldFail = false
    const rows = [{ id: 1 }, { id: 2 }]
    const table = useTable(
      async () => {
        if (shouldFail) throw new Error('network down')
        return { code: 200, data: { list: rows, total: 2 } }
      },
      { immediate: false }
    )

    await table.loadData()
    expect(table.loadError.value).toBe(false)
    expect(table.tableData.value).toEqual(rows)

    shouldFail = true
    await table.loadData()
    expect(table.loadError.value).toBe(true)
    expect(table.tableData.value).toEqual(rows)
    expect(table.total.value).toBe(2)
    expect(table.loading.value).toBe(false)
  })

  it('失败后恢复成功则清除 loadError', async () => {
    let shouldFail = true
    const table = useTable(
      async () => {
        if (shouldFail) throw new Error('down')
        return { code: 200, data: { list: [{ id: 9 }], total: 1 } }
      },
      { immediate: false }
    )

    await table.loadData()
    expect(table.loadError.value).toBe(true)

    shouldFail = false
    await table.loadData()
    expect(table.loadError.value).toBe(false)
    expect(table.tableData.value).toEqual([{ id: 9 }])
  })
})

describe('useTable 竞态防护 (#19)', () => {
  it('慢的旧响应不覆盖新响应', async () => {
    let resolveSlow
    const slowResult = { code: 200, data: { list: [{ id: 'stale' }], total: 99 } }
    const table = useTable(
      vi
        .fn()
        .mockImplementationOnce(
          () => new Promise((resolve) => { resolveSlow = resolve })
        )
        .mockImplementationOnce(async () => ({ code: 200, data: { list: [{ id: 'fresh' }], total: 1 } })),
      { immediate: false }
    )

    const slow = table.loadData()
    const fast = table.loadData()
    await fast
    resolveSlow(slowResult)
    await slow
    await flush()

    expect(table.tableData.value).toEqual([{ id: 'fresh' }])
    expect(table.total.value).toBe(1)
    // 过期响应不得把 loading 卡在 true 或误报失败
    expect(table.loading.value).toBe(false)
    expect(table.loadError.value).toBe(false)
  })

  it('过期响应的异常不误报 loadError', async () => {
    let rejectSlow
    const table = useTable(
      vi
        .fn()
        .mockImplementationOnce(() => new Promise((_, reject) => { rejectSlow = reject }))
        .mockImplementationOnce(async () => ({ code: 200, data: { list: [], total: 0 } })),
      { immediate: false }
    )

    const slow = table.loadData()
    await table.loadData()
    rejectSlow(new Error('late failure'))
    await slow
    await flush()

    expect(table.loadError.value).toBe(false)
  })
})
