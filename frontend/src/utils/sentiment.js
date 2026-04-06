export function getSentimentLabel(score) {
  if (score > 0.5) {
    return '正面'
  } else if (score === 0.5) {
    return '中性'
  } else {
    return '负面'
  }
}

export function getSentimentType(score) {
  if (score > 0.5) {
    return 'positive'
  } else if (score === 0.5) {
    return 'neutral'
  } else {
    return 'negative'
  }
}

export function getSentimentTagType(score) {
  if (score > 0.5) {
    return 'success'
  } else if (score === 0.5) {
    return 'warning'
  } else {
    return 'danger'
  }
}

export function getSentimentColor(score) {
  if (score > 0.5) {
    return '#67C23A'
  } else if (score === 0.5) {
    return '#E6A23C'
  } else {
    return '#F56C6C'
  }
}

export function getEmotionType(score) {
  return getSentimentType(score)
}

export function analyzeSentimentDistribution(scores) {
  if (!scores || scores.length === 0) {
    return {
      positive: 0,
      neutral: 0,
      negative: 0,
      total: 0,
      average: 0,
    }
  }

  const positive = scores.filter((s) => s > 0.5).length
  const neutral = scores.filter((s) => s === 0.5).length
  const negative = scores.filter((s) => s < 0.5).length
  const total = scores.length
  const average = scores.reduce((a, b) => a + b, 0) / total

  return {
    positive,
    neutral,
    negative,
    total,
    average: Math.round(average * 10000) / 10000,
    positiveRatio: Math.round((positive / total) * 10000) / 10000,
    neutralRatio: Math.round((neutral / total) * 10000) / 10000,
    negativeRatio: Math.round((negative / total) * 10000) / 10000,
  }
}

export function getLogLevel(level) {
  const levelMap = {
    DEBUG: 'info',
    INFO: 'primary',
    WARNING: 'warning',
    ERROR: 'danger',
    CRITICAL: 'danger',
  }
  return levelMap[level?.toUpperCase()] || 'info'
}
