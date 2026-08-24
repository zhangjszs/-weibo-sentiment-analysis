import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { predictSentiment, predictBatch, getModelInfo } from '@/api/predict'
import { downloadCsv } from '@/utils'

export function usePredict() {
  const predictMode = ref('custom')
  const predictForm = ref({ text: '' })
  const predicting = ref(false)
  const predictResult = ref(null)
  const historyList = ref([])
  const loadingModelInfo = ref(false)
  const modelInfo = ref(null)

  const gaugeChartRef = ref(null)
  const showBatchDialog = ref(false)
  const showBatchResultDialog = ref(false)
  const batchForm = ref({ texts: '' })
  const batchPredicting = ref(false)
  const batchResults = ref([])
  const uploadRef = ref(null)

  const gaugeChartOptions = computed(() => {
    const score = predictResult.value?.score || 0.5
    return {
      series: [
        {
          type: 'gauge',
          startAngle: 180,
          endAngle: 0,
          min: 0,
          max: 1,
          splitNumber: 5,
          axisLine: {
            lineStyle: {
              width: 30,
              color: [
                [0.4, '#EF4444'],
                [0.6, '#64748B'],
                [1, '#10B981'],
              ],
            },
          },
          pointer: {
            icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
            length: '60%',
            width: 10,
            offsetCenter: [0, '-10%'],
            itemStyle: { color: 'auto' },
          },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { show: false },
          title: {
            offsetCenter: [0, '30%'],
            fontSize: 14,
            color: '#64748B',
          },
          detail: {
            fontSize: 24,
            offsetCenter: [0, '0%'],
            valueAnimation: true,
            formatter: (value) => (value * 100).toFixed(1) + '%',
            color: 'inherit',
          },
          data: [
            {
              value: score,
              name: predictResult.value ? getSentimentLabel(predictResult.value.label) : '等待预测',
            },
          ],
        },
      ],
    }
  })

  const getSentimentLabel = (label) => {
    const labels = {
      positive: '正面',
      neutral: '中性',
      negative: '负面',
    }
    return labels[label] || label || '未知'
  }

  const getSentimentTagType = (label) => {
    const types = {
      positive: 'success',
      neutral: 'info',
      negative: 'danger',
    }
    return types[label] || 'info'
  }

  const getSentimentClass = (label) => {
    const classes = {
      positive: 'text-success',
      neutral: 'text-muted',
      negative: 'text-danger',
    }
    return classes[label] || ''
  }

  const getScoreColor = (score) => {
    if (score > 0.6) return '#10B981'
    if (score < 0.4) return '#EF4444'
    return '#64748B'
  }

  const getScoreClass = (score) => {
    if (score > 0.6) return 'text-success'
    if (score < 0.4) return 'text-danger'
    return 'text-muted'
  }

  const getEmotionTagType = (emotion) => {
    const emotionMap = {
      喜悦: 'success',
      愤怒: 'danger',
      悲伤: 'info',
      焦虑: 'warning',
      期待: 'primary',
      讽刺: 'warning',
      无感: 'info',
    }
    return emotionMap[emotion] || 'info'
  }

  const handlePredict = async () => {
    if (!predictForm.value.text.trim()) {
      ElMessage.warning('请输入需要分析的文本')
      return
    }

    predicting.value = true
    try {
      const res = await predictSentiment(predictForm.value.text, predictMode.value)
      if (res.code === 200) {
        predictResult.value = res.data

        historyList.value.unshift({
          text:
            predictForm.value.text.substring(0, 100) +
            (predictForm.value.text.length > 100 ? '...' : ''),
          label: res.data.label,
          score: res.data.score,
          source: res.data.source,
          time: new Date().toLocaleString(),
        })

        if (historyList.value.length > 50) {
          historyList.value = historyList.value.slice(0, 50)
        }

        ElMessage.success('预测完成')
      } else {
        ElMessage.error(res.msg || '预测失败')
      }
    } catch (error) {
      ElMessage.error('预测请求失败')
    } finally {
      predicting.value = false
    }
  }

  const clearInput = () => {
    predictForm.value.text = ''
    predictResult.value = null
  }

  const clearHistory = () => {
    historyList.value = []
    ElMessage.success('历史记录已清空')
  }

  const retryPredict = (row) => {
    predictForm.value.text = row.text
    handlePredict()
  }

  const loadModelInfo = async () => {
    loadingModelInfo.value = true
    try {
      const res = await getModelInfo()
      if (res.code === 200) {
        modelInfo.value = res.data
      }
    } catch (error) {
      console.error('获取模型信息失败:', error)
    } finally {
      loadingModelInfo.value = false
    }
  }

  const handleFileChange = (file) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      batchForm.value.texts = e.target.result
    }
    reader.readAsText(file.raw)
  }

  const handleBatchPredict = async () => {
    const texts = batchForm.value.texts
      .split('\n')
      .map((t) => t.trim())
      .filter((t) => t.length > 0)

    if (texts.length === 0) {
      ElMessage.warning('请输入至少一条文本')
      return
    }

    if (texts.length > 100) {
      ElMessage.warning('单次最多预测100条文本')
      return
    }

    batchPredicting.value = true
    try {
      const res = await predictBatch(texts, predictMode.value)
      if (res.code === 200) {
        batchResults.value = res.data.results.map((r, i) => ({
          text: texts[i],
          label: r.label,
          score: r.score,
          source: r.source,
        }))
        showBatchResultDialog.value = true
        showBatchDialog.value = false
        ElMessage.success(`成功预测 ${batchResults.value.length} 条文本`)
      } else {
        ElMessage.error(res.msg || '批量预测失败')
      }
    } catch (error) {
      ElMessage.error('批量预测请求失败')
    } finally {
      batchPredicting.value = false
    }
  }

  const exportBatchResults = () => {
    const headers = ['序号', '文本', '情感', '得分', '来源']
    const rows = batchResults.value.map((r, i) => [
      i + 1,
      r.text,
      getSentimentLabel(r.label),
      (r.score * 100).toFixed(2) + '%',
      r.source,
    ])
    downloadCsv(`batch_predict_${Date.now()}.csv`, headers, rows)
  }

  onMounted(() => {
    loadModelInfo()
  })

  return { predictMode, predictForm, predicting, predictResult, historyList, loadingModelInfo, modelInfo, gaugeChartRef, showBatchDialog, showBatchResultDialog, batchForm, batchPredicting, batchResults, uploadRef, gaugeChartOptions, getSentimentTagType, getSentimentLabel, getSentimentClass, getScoreColor, getScoreClass, getEmotionTagType, handlePredict, clearInput, clearHistory, retryPredict, handleBatchPredict, handleFileChange, exportBatchResults, loadModelInfo }
}
