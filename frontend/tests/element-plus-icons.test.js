// #39 的守护测试：src/plugins/elementPlus.js 的最小全局注册必须覆盖 src 中
// 所有「以字符串形式解析」的图标引用。字符串 icon（icon="Search" prop、
// <component :is="'X'">、prop 默认值等）走全局组件解析，漏注册不会让
// lint/build/其他测试报错，只会在运行时渲染空白——所以用源码扫描兜底。
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { createApp } from 'vue'
import * as icons from '@element-plus/icons-vue'
import { ICON_COMPONENTS, installElementPlus } from '@/plugins/elementPlus'

const ICON_NAMES = new Set(Object.keys(icons))

// 与图标同名的非图标字符串（逐个核实过）：
// - 'Help'：router/index.js 的路由名（name: 'Help'），与图标无关
const NON_ICON_STRINGS = new Set(['Help'])

// jsdom 环境下 import.meta.url 不是 file:// 协议；vitest 固定以 frontend/ 为 cwd
const SRC_DIR = resolve(process.cwd(), 'src')

// 收集 src 内以字符串字面量形式出现的图标名及其所在文件
function collectIconStringRefs(dir, acc = {}) {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry)
    if (statSync(full).isDirectory()) {
      collectIconStringRefs(full, acc)
    } else if (/\.(vue|js)$/.test(entry)) {
      const text = readFileSync(full, 'utf8')
      for (const m of text.matchAll(/['"]([A-Z][A-Za-z0-9]+)['"]/g)) {
        const name = m[1]
        if (ICON_NAMES.has(name) && !NON_ICON_STRINGS.has(name)) {
          ;(acc[name] ??= []).push(full.slice(SRC_DIR.length + 1))
        }
      }
    }
  }
  return acc
}

describe('#39 element-plus 最小全局注册守护', () => {
  it('ICON_COMPONENTS 每个名字都是真实图标且会被 installElementPlus 注册', () => {
    const app = createApp({ render: () => null })
    installElementPlus(app)
    for (const [name, component] of Object.entries(ICON_COMPONENTS)) {
      expect(ICON_NAMES.has(name), `${name} 不是 @element-plus/icons-vue 的导出（拼写错误?）`).toBe(true)
      expect(app.component(name), `组件 ${name} 未被 installElementPlus 注册`).toBe(component)
    }
  })

  it('src 中字符串引用的图标必须全部在 ICON_COMPONENTS 内', () => {
    const refs = collectIconStringRefs(SRC_DIR)
    const registered = new Set(Object.keys(ICON_COMPONENTS))
    const missing = Object.keys(refs).filter((name) => !registered.has(name))
    const detail = missing.map((name) => `${name} ← ${refs[name].join(', ')}`).join('\n')
    expect(
      missing,
      `以下图标以字符串形式被引用但未全局注册，请补进 src/plugins/elementPlus.js 的 ICON_COMPONENTS：\n${detail}`
    ).toEqual([])
  })
})
