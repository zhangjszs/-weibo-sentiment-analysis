import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskList from '../src/components/system/TaskList.vue'

/**
 * #68（U-5）：tasks.vue 两张表格补加载态。
 *
 * 验收要求：
 * - TaskList.vue:11 与 :77 两张表均绑定 loading，挂载/刷新期间可见；
 * - 补一条 mount 断言：loading 传入为 true 时两表渲染加载指示。
 */

describe('TaskList 表格加载态绑定（#68 U-5）', () => {
  it('spiderLoading 为 true 时爬虫历史表格渲染 loading mask', () => {
    const wrapper = mount(TaskList, {
      props: {
        spiderLoading: true,
        startupLoading: false,
      },
    })
    try {
      const tables = wrapper.findAll('.el-table')
      expect(tables.length).toBe(2)

      // 爬虫历史表格（第一个表格）带 loading 遮罩
      expect(tables[0].find('.el-loading-mask').exists()).toBe(true)
      // 预热结果表格（第二个表格）无 loading 遮罩
      expect(tables[1].find('.el-loading-mask').exists()).toBe(false)
    } finally {
      wrapper.unmount()
    }
  })

  it('startupLoading 为 true 时预热结果表格渲染 loading mask', () => {
    const wrapper = mount(TaskList, {
      props: {
        spiderLoading: false,
        startupLoading: true,
      },
    })
    try {
      const tables = wrapper.findAll('.el-table')
      expect(tables.length).toBe(2)

      // 爬虫历史表格无 loading 遮罩
      expect(tables[0].find('.el-loading-mask').exists()).toBe(false)
      // 预热结果表格带 loading 遮罩
      expect(tables[1].find('.el-loading-mask').exists()).toBe(true)
    } finally {
      wrapper.unmount()
    }
  })

  it('两者同时为 true 时两张表格均渲染 loading mask，同时为 false 时均无遮罩', () => {
    const wrapperBoth = mount(TaskList, {
      props: {
        spiderLoading: true,
        startupLoading: true,
      },
    })
    try {
      const tables = wrapperBoth.findAll('.el-table')
      expect(tables[0].find('.el-loading-mask').exists()).toBe(true)
      expect(tables[1].find('.el-loading-mask').exists()).toBe(true)
    } finally {
      wrapperBoth.unmount()
    }

    const wrapperNone = mount(TaskList, {
      props: {
        spiderLoading: false,
        startupLoading: false,
      },
    })
    try {
      const tables = wrapperNone.findAll('.el-table')
      expect(tables[0].find('.el-loading-mask').exists()).toBe(false)
      expect(tables[1].find('.el-loading-mask').exists()).toBe(false)
    } finally {
      wrapperNone.unmount()
    }
  })
})
