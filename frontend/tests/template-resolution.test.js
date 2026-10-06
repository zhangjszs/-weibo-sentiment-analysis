import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AnalysisEmptyState from '../src/components/Common/AnalysisEmptyState.vue'

/**
 * #49：模板级组件解析契约。
 *
 * vitest 与生产构建共用 config/components.mjs 的 Components + resolver 配置
 * 后，模板中的 <el-*> 应解析为真实 Element Plus 组件而不是未知元素。
 * 防回归机制：vitest.setup.js 刻意不装完整 ElementPlus，若有人把 vitest 侧
 * 的 resolver 移除/改坏，本用例会失败（未知元素没有 el-* 结构类，
 * findComponent 也命中不到组件实例）——已做过一次性反例验证。
 */
describe('模板级组件解析契约 (#49)', () => {
  const mountEmptyState = () =>
    mount(AnalysisEmptyState, {
      props: { type: 'no-data', actionLabel: '重试' },
    })

  it('el-empty / el-button / el-icon 解析为真实 Element Plus 组件', () => {
    const wrapper = mountEmptyState()

    // DOM 特征：真实 Element Plus 组件渲染出 el-* 结构类；未知元素只会
    // 留下裸的 <el-empty> 等标签（jsdom 不报错，但没有任何结构类）
    expect(wrapper.find('.el-empty').exists()).toBe(true)
    expect(wrapper.find('.el-button').exists()).toBe(true)
    expect(wrapper.find('.el-icon').exists()).toBe(true)

    // 组件实例特征：按 Element Plus 的组件 name 命中实例
    expect(wrapper.findComponent({ name: 'ElEmpty' }).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'ElButton' }).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'ElIcon' }).exists()).toBe(true)
  })

  it('解析后的组件渲染完整结构（description 插槽内容可见）', () => {
    const wrapper = mountEmptyState()

    // el-empty 渲染自定义 #description 内容，说明组件真的执行了渲染逻辑
    //（未知元素不会渲染任何插槽）
    expect(wrapper.find('.analysis-empty-state__title').text()).toBe('暂无数据')
    expect(wrapper.find('.el-button').text()).toBe('重试')
  })
})
