import { describe, it, expect } from 'vitest'
import { resolveVisualMapMax } from '../src/composables/useBigScreen.js'

// #52：大屏地图 visualMap.max 在 regionData 为空时曾取 Math.max() ===
// -Infinity，连续渐变求色抛 addColorStop(undefined)（真实浏览器 pageerror）。
// 空数据分支收敛到 resolveVisualMapMax 纯函数，这里覆盖三个分支。

describe('resolveVisualMapMax（#52 空数据兜底）', () => {
  it('空数组回落 1000（与 map 演示数据同尺度）', () => {
    expect(resolveVisualMapMax([])).toBe(1000)
    expect(resolveVisualMapMax(undefined)).toBe(1000)
  })

  it('非空取真实最大值', () => {
    expect(resolveVisualMapMax([{ name: '北京', value: 985 }])).toBe(985)
    expect(
      resolveVisualMapMax([
        { name: 'a', value: 3 },
        { name: 'b', value: 7 },
      ])
    ).toBe(7)
  })

  it('全 0 行时下限 1，避免 min=max 渐变退化', () => {
    expect(resolveVisualMapMax([{ name: 'x', value: 0 }])).toBe(1)
  })
})
