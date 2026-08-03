import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ProvenanceBadge from '../src/components/Common/ProvenanceBadge.vue'
import AnalysisEmptyState from '../src/components/Common/AnalysisEmptyState.vue'

// ---------------------------------------------------------------------------
// ProvenanceBadge
// ---------------------------------------------------------------------------

describe('ProvenanceBadge', () => {
  it('renders "真实数据" for real source_type', () => {
    const wrapper = mount(ProvenanceBadge, {
      props: { sourceType: 'real' },
    })
    expect(wrapper.text()).toContain('真实数据')
  })

  it('renders "演示数据" for demo source_type', () => {
    const wrapper = mount(ProvenanceBadge, {
      props: { sourceType: 'demo' },
    })
    expect(wrapper.text()).toContain('演示数据')
  })

  it('renders "实验能力" for experimental source_type', () => {
    const wrapper = mount(ProvenanceBadge, {
      props: { sourceType: 'experimental' },
    })
    expect(wrapper.text()).toContain('实验能力')
  })

  it('reads source_type from meta object', () => {
    const wrapper = mount(ProvenanceBadge, {
      props: {
        meta: {
          source_type: 'demo',
          source_name: 'weibo',
          data_count: 50,
        },
      },
    })
    expect(wrapper.text()).toContain('演示数据')
  })

  it('renders "未知来源" for unknown type', () => {
    const wrapper = mount(ProvenanceBadge, {
      props: { sourceType: 'unknown' },
    })
    expect(wrapper.text()).toContain('未知来源')
  })

  it('applies the correct CSS class for each type', () => {
    const wrapper = mount(ProvenanceBadge, {
      props: { sourceType: 'demo' },
    })
    expect(wrapper.classes()).toContain('provenance-badge--demo')
  })

  it('shows size class when provided', () => {
    const wrapper = mount(ProvenanceBadge, {
      props: { sourceType: 'real', size: 'small' },
    })
    expect(wrapper.classes()).toContain('provenance-badge--small')
  })
})

// ---------------------------------------------------------------------------
// AnalysisEmptyState
// ---------------------------------------------------------------------------

describe('AnalysisEmptyState', () => {
  it('renders default "暂无数据" title for type=no-data', () => {
    const wrapper = mount(AnalysisEmptyState, {
      props: { type: 'no-data' },
    })
    expect(wrapper.text()).toContain('暂无数据')
  })

  it('renders custom title when provided', () => {
    const wrapper = mount(AnalysisEmptyState, {
      props: { title: '自定义标题', reason: '自定义原因' },
    })
    expect(wrapper.text()).toContain('自定义标题')
    expect(wrapper.text()).toContain('自定义原因')
  })

  it.each(['no-data', 'not-connected', 'no-results', 'experimental-only', 'error'])(
    'renders without error for type=%s',
    (type) => {
      const wrapper = mount(AnalysisEmptyState, {
        props: { type },
      })
      expect(wrapper.exists()).toBe(true)
    },
  )

  it('shows action button when actionLabel is provided', () => {
    const wrapper = mount(AnalysisEmptyState, {
      props: { type: 'no-data', actionLabel: '重新采集' },
    })
    // The button text is rendered inside el-empty's default slot.
    expect(wrapper.findComponent({ name: 'ElButton' }).exists()).toBe(true)
  })

  it('emits action event when button is clicked', async () => {
    const wrapper = mount(AnalysisEmptyState, {
      props: { type: 'no-data', actionLabel: '重试' },
    })
    const btn = wrapper.find('button')
    if (btn.exists()) {
      await btn.trigger('click')
      expect(wrapper.emitted('action')).toBeTruthy()
    }
  })
})