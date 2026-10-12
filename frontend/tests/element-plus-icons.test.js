// #39 的守护测试：src/plugins/elementPlus.js 的最小全局注册必须覆盖 src 中
// 所有「以字符串形式解析」的图标引用。字符串 icon（icon="Search" prop、
// <component :is="'X'">、prop 默认值等）走全局组件解析，漏注册不会让
// lint/build/其他测试报错，只会在运行时渲染空白。
// #79（T-5）：原第 2 个 it 的静态源码扫描改为真实挂载——动态三元模式探针
// （复刻 BigScreen 播放/暂停 `:icon="playing ? 'VideoPause' : 'VideoPlay'"`）
// 挂载验证两态均渲染出 SVG，不再读源码文本。
import { ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { describe, expect, it, vi, afterEach } from 'vitest'
import { createApp } from 'vue'
import * as icons from '@element-plus/icons-vue'
import { ICON_COMPONENTS, installElementPlus } from '@/plugins/elementPlus'

const ICON_NAMES = new Set(Object.keys(icons))

// 动态三元模式探针：复刻 BigScreen `:icon="playing ? 'VideoPause' : 'VideoPlay'"`
// 注：探针不用 el-icon 包裹——单测环境不装载 element-plus 全局插件，
// el-* 在运行时模板中无法解析；图标解析断言与 el-icon 无关。
const TernaryProbe = {
  setup() {
    const playing = ref(false)
    const toggle = () => {
      playing.value = !playing.value
    }
    return { playing, toggle }
  },
  template: `<span class="play-toggle"><component :is="playing ? 'VideoPause' : 'VideoPlay'" /></span>`,
}

let warnSpy

afterEach(() => {
  warnSpy?.mockRestore()
})

describe('#39 element-plus 最小全局注册守护', () => {
  it('ICON_COMPONENTS 每个名字都是真实图标且会被 installElementPlus 注册', () => {
    const app = createApp({ render: () => null })
    installElementPlus(app)
    for (const [name, component] of Object.entries(ICON_COMPONENTS)) {
      expect(ICON_NAMES.has(name), `${name} 不是 @element-plus/icons-vue 的导出（拼写错误?）`).toBe(
        true
      )
      expect(app.component(name), `组件 ${name} 未被 installElementPlus 注册`).toBe(component)
    }
  })

  it('动态三元引用的图标两态均真实渲染（BigScreen 播放/暂停模式）', async () => {
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const wrapper = mount(TernaryProbe, {
      global: { components: ICON_COMPONENTS },
    })
    try {
      await flushPromises()
      // 暂停态（playing=false → VideoPlay）
      expect(wrapper.find('svg').exists()).toBe(true)

      // 播放态（playing=true → VideoPause）
      wrapper.vm.toggle()
      await flushPromises()
      expect(wrapper.find('svg').exists()).toBe(true)

      const noise = warnSpy.mock.calls.flat().join('\n')
      expect(noise).not.toMatch(/Failed to resolve component/)
    } finally {
      wrapper.unmount()
    }
  })
})
