import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

import { ICON_COMPONENTS } from '../src/plugins/elementPlus.js'
import Help from '../src/views/system/Help.vue'
import router from '../src/router/index.js'

// #79（T-5）：原静态源码扫描（walk src + 正则）替换为真实挂载断言。
// 注册表完整性不再读源码文本：逐个挂载验证每个注册名真实解析出 SVG；
// 字符串引用不断链由真实消费者（Help 特性卡 `icon: 'X'`）挂载覆盖。

const REGISTERED = Object.keys(ICON_COMPONENTS)

const AllIconsProbe = {
  setup() {
    return { names: REGISTERED }
  },
  template: '<div><component v-for="n in names" :key="n" :is="n" /></div>',
}

let warnSpy
const mountProbe = () => {
  warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
  return mount(AllIconsProbe, {
    // 复刻生产入口的全局图标注册
    global: { components: ICON_COMPONENTS },
  })
}

afterEach(() => {
  warnSpy?.mockRestore()
})

describe('字符串图标引用的注册完整性（#39，真实挂载版）', () => {
  it('每个注册名都真实解析并渲染出 SVG', async () => {
    // 防空转：注册表非空
    expect(REGISTERED.length).toBeGreaterThan(0)
    const wrapper = mountProbe()
    try {
      await flushPromises()
      // 每个注册图标恰好渲染一个 svg（缺注册即渲染空白，计数对不上）
      expect(wrapper.findAll('svg')).toHaveLength(REGISTERED.length)
      const noise = warnSpy.mock.calls.flat().join('\n')
      expect(noise).not.toMatch(/Failed to resolve component/)
    } finally {
      wrapper.unmount()
    }
  })

  it('字符串引用消费者（Help 特性卡 icon: X）图标全部渲染', async () => {
    const wrapper = mount(Help, {
      global: {
        plugins: [router],
        // 字符串 icon 走全局组件解析，复刻生产注册
        components: ICON_COMPONENTS,
      },
    })
    try {
      await flushPromises()
      const icons = wrapper.findAll('.feature-icon')
      // 防空转：特性卡真实存在
      expect(icons.length).toBeGreaterThan(0)
      for (const icon of icons) {
        expect(icon.find('svg').exists()).toBe(true)
      }
    } finally {
      wrapper.unmount()
    }
  })
})
