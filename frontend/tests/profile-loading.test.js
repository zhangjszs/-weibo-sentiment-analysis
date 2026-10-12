import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

/**
 * #70（U-7）：Profile.vue 补资料加载态。
 *
 * 覆盖：
 * 1. loadProfile pending 期间资料卡区域渲染 skeleton（.profile-loading），
 *    不出现默认值「用户 / 未知」的中间态；
 * 2. 加载完成后 skeleton 消失并渲染真实值。
 *
 * mock 层级：@/api/user 全函数；pinia 用真实 createPinia（useUserStore 只在
 * 保存路径使用，加载路径不触达）。
 */

vi.mock('@/api/user', () => ({
  getProfile: vi.fn(),
  updateProfile: vi.fn(),
  changePassword: vi.fn(),
}))

import { getProfile } from '@/api/user'
import Profile from '../src/views/user/Profile.vue'

const profileOk = () => ({
  code: 200,
  msg: 'ok',
  data: {
    username: 'tester1',
    nickname: '测试昵称',
    email: 'tester1@example.com',
    bio: '个人简介',
    avatar_color: '#2563EB',
    create_time: '2026-01-01 10:00:00',
    is_admin: false,
  },
})

const mountView = () => {
  setActivePinia(createPinia())
  return mount(Profile)
}

beforeEach(() => {
  vi.clearAllMocks()
  getProfile.mockResolvedValue(profileOk())
})

describe('Profile 资料加载态（#70 U-7）', () => {
  it('loadProfile pending 期间渲染 skeleton，不出现默认值中间态', async () => {
    let resolveProfile
    getProfile.mockReturnValue(
      new Promise((resolve) => {
        resolveProfile = resolve
      })
    )
    const wrapper = mountView()
    try {
      await flushPromises()

      // 加载态渲染，真实资料区隐藏
      expect(wrapper.find('.profile-loading').exists()).toBe(true)
      expect(wrapper.find('.profile-loading .el-skeleton').exists()).toBe(true)
      expect(wrapper.find('.profile-card-content').exists()).toBe(false)

      // 不得出现默认值「用户 / 未知」的中间态
      expect(wrapper.text()).not.toContain('未知')

      resolveProfile(profileOk())
      await flushPromises()

      expect(wrapper.find('.profile-loading').exists()).toBe(false)
      expect(wrapper.find('.profile-card-content').exists()).toBe(true)
      expect(wrapper.text()).toContain('测试昵称')
    } finally {
      wrapper.unmount()
    }
  })

  it('加载完成后渲染真实值', async () => {
    const wrapper = mountView()
    try {
      await flushPromises()

      expect(wrapper.find('.profile-loading').exists()).toBe(false)
      expect(wrapper.text()).toContain('测试昵称')
      expect(wrapper.text()).toContain('@tester1')
      expect(wrapper.text()).toContain('tester1@example.com')
    } finally {
      wrapper.unmount()
    }
  })
})
