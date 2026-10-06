import { describe, it, expect } from 'vitest'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

import { ICON_COMPONENTS } from '../src/plugins/elementPlus.js'

// #39：element-plus 组件与图标改为按需加载后，模板里以**字符串**形式引用
// 的图标（icon="X"、icon: 'X'、动态三元）仍依赖最小全局注册（ICON_COMPONENTS）。
// 本测试静态扫描源码，确保每个被字符串引用的图标都已注册，防止运行期图标
// 静默消失。

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const SRC = join(ROOT, 'src')

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name)
    const st = statSync(full)
    if (st.isDirectory()) {
      yield* walk(full)
    } else if (/\.(vue|js)$/.test(name)) {
      yield full
    }
  }
}

describe('字符串图标引用的注册完整性（#39）', () => {
  it('源码中所有字符串形式引用的图标都在 ICON_COMPONENTS 中注册', () => {
    const referenced = new Set()
    const patterns = [
      /icon="([A-Z][A-Za-z]+)"/g, // icon="CircleCheck"
      /icon: '([A-Z][A-Za-z]+)'/g, // icon: 'Document'（Help 特性卡等）
      /:icon="'([A-Z][A-Za-z]+)'"/g, // :icon="'Search'"
      /'(VideoPause|VideoPlay)'/g, // 动态三元字面量（BigScreen 播放/暂停）
    ]

    for (const file of walk(SRC)) {
      // plugins/elementPlus.js 是注册表本身，排除
      if (file.endsWith('elementPlus.js')) continue
      const content = readFileSync(file, 'utf8')
      for (const re of patterns) {
        for (const match of content.matchAll(re)) {
          referenced.add(match[1])
        }
      }
    }

    const registered = new Set(Object.keys(ICON_COMPONENTS))
    const missing = [...referenced].filter((name) => !registered.has(name))
    expect(missing).toEqual([])
  })

  it('ICON_COMPONENTS 的每个键都是 @element-plus/icons-vue 的真实导出', async () => {
    const icons = await import('@element-plus/icons-vue')
    for (const name of Object.keys(ICON_COMPONENTS)) {
      expect(icons[name], `未知图标名: ${name}`).toBeTruthy()
    }
  })
})
