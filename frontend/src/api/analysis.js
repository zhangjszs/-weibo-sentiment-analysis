import request from './request'

/**
 * Execute the analysis pipeline for a topic + time range.
 *
 * @param {string} topic      - Keyword to analyse.
 * @param {string} startAt    - ISO-8601 start datetime.
 * @param {string} endAt      - ISO-8601 end datetime.
 * @param {boolean} [demo]    - Use demo data.
 * @returns {Promise<object>} Analysis snapshot with meta.
 */
export function runAnalysis({ topic, startAt, endAt, demo = false }) {
  const params = { topic }
  if (startAt) params.start_at = startAt
  if (endAt) params.end_at = endAt
  if (demo) params.demo = 'true'

  return request.get('/api/v1/analysis', { params }).then((res) => res.data)
}

/**
 * Convenience: fetch demo analysis data for quick prototyping.
 * @param {string} topic
 * @returns {Promise<object>}
 */
export function fetchDemoAnalysis(topic = '微博热点') {
  return runAnalysis({ topic, demo: true })
}