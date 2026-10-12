import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'

/**
 * #75（T-2）：视图级挂载测试矩阵 —— error 静态页（3 视图）。
 *
 * 静态页无 API 依赖，真实 mount 断言可渲染 + 关键区域（错误码/返回按钮）。
 * 只加测试，不改源码。
 */

import Error403 from '../src/views/error/403.vue'
import Error404 from '../src/views/error/404.vue'
import Error500 from '../src/views/error/500.vue'
import router from '../src/router/index.js'

const mountWithRouter = (component) =>
  mount(component, {
    global: {
      plugins: [router],
    },
  })

describe('视图挂载矩阵 error 静态页（#75 T-2）', () => {
  it('403.vue：渲染拒绝码与返回按钮', () => {
    const wrapper = mountWithRouter(Error403)
    try {
      expect(wrapper.find('.error-page').exists()).toBe(true)
      expect(wrapper.text()).toContain('403')
      expect(wrapper.text()).toContain('返回首页')
    } finally {
      wrapper.unmount()
    }
  })

  it('404.vue：渲染不存在码与返回按钮', () => {
    const wrapper = mountWithRouter(Error404)
    try {
      expect(wrapper.find('.error-page').exists()).toBe(true)
      expect(wrapper.text()).toContain('404')
      expect(wrapper.text()).toContain('返回首页')
    } finally {
      wrapper.unmount()
    }
  })

  it('500.vue：渲染错误页与返回按钮', () => {
    const wrapper = mountWithRouter(Error500)
    try {
      expect(wrapper.find('.error-page').exists()).toBe(true)
      expect(wrapper.text()).toContain('返回首页')
    } finally {
      wrapper.unmount()
    }
  })
})
