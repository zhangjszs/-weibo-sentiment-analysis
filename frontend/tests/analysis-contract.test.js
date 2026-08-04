import { describe, it, expect } from 'vitest'

/**
 * Contract tests for the analysis response structure.
 *
 * These tests validate the shape of a demo AnalysisSnapshot so the frontend
 * can depend on stable field paths.  They do NOT call the backend — they
 * check the expected JSON contract against a known fixture.
 */

const demoSnapshot = {
  topic: 'test',
  start_at: '2026-07-01T00:00:00+00:00',
  end_at: '2026-08-01T00:00:00+00:00',
  generated_at: '2026-08-03T12:00:00+00:00',
  meta: {
    source_type: 'demo',
    source_name: 'weibo',
    is_demo: true,
    model_name: 'snownlp + rule-based',
    model_version: '1.0',
    time_range: {
      start: '2026-07-01T00:00:00+00:00',
      end: '2026-08-01T00:00:00+00:00',
    },
    data_count: 100,
    generated_at: '2026-08-03T12:00:00+00:00',
    limitations: ['演示数据：此数据为模拟生成，不代表真实分析结果。'],
  },
  summary: {
    total_articles: 33,
    total_comments: 67,
    total_count: 100,
  },
  trend: [
    { date: '2026-07-01', count: 150 },
    { date: '2026-07-02', count: 200 },
  ],
  sentiment: {
    distribution: { positive: 50, neutral: 30, negative: 20 },
    index: 0.3,
  },
  top_articles: [
    { id: 'a1', content: 'Article 1', like_count: 100 },
  ],
  top_comments: [
    { id: 'c1', content: 'Comment 1', like_count: 50 },
  ],
  propagation: {
    max_depth: 3,
    total_nodes: 100,
    key_influencers: ['user_001'],
  },
}

describe('AnalysisSnapshot contract', () => {
  it('has all required top-level keys', () => {
    const required = ['topic', 'start_at', 'end_at', 'generated_at', 'meta']
    for (const key of required) {
      expect(demoSnapshot).toHaveProperty(key)
    }
  })

  it('has all analysis data keys', () => {
    const required = ['summary', 'trend', 'sentiment', 'top_articles', 'top_comments', 'propagation']
    for (const key of required) {
      expect(demoSnapshot).toHaveProperty(key)
    }
  })

  it('meta has required provenance fields', () => {
    const meta = demoSnapshot.meta
    const required = [
      'source_type',
      'source_name',
      'is_demo',
      'model_name',
      'model_version',
      'time_range',
      'data_count',
      'generated_at',
      'limitations',
    ]
    for (const key of required) {
      expect(meta).toHaveProperty(key)
    }
  })

  it('meta.source_type is one of real/demo/experimental', () => {
    expect(['real', 'demo', 'experimental']).toContain(demoSnapshot.meta.source_type)
  })

  it('summary has total_articles, total_comments, total_count', () => {
    expect(demoSnapshot.summary).toHaveProperty('total_articles')
    expect(demoSnapshot.summary).toHaveProperty('total_comments')
    expect(demoSnapshot.summary).toHaveProperty('total_count')
  })

  it('trend is an array of {date, count} objects', () => {
    expect(Array.isArray(demoSnapshot.trend)).toBe(true)
    if (demoSnapshot.trend.length > 0) {
      expect(demoSnapshot.trend[0]).toHaveProperty('date')
      expect(demoSnapshot.trend[0]).toHaveProperty('count')
    }
  })

  it('sentiment has distribution and index', () => {
    expect(demoSnapshot.sentiment).toHaveProperty('distribution')
    expect(demoSnapshot.sentiment).toHaveProperty('index')
  })

  it('propagation has max_depth, total_nodes, key_influencers', () => {
    expect(demoSnapshot.propagation).toHaveProperty('max_depth')
    expect(demoSnapshot.propagation).toHaveProperty('total_nodes')
    expect(demoSnapshot.propagation).toHaveProperty('key_influencers')
  })
})