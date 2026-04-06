/**
 * 图表相关组合式函数
 * 提供 ECharts 图表的通用逻辑封装
 */

import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import echarts from '@/utils/echarts'

/**
 * 使用 ECharts 图表
 * @param {Function} getOption - 返回图表配置的函数
 * @param {Object} options - 可选配置
 */
export function useChart(getOption, options = {}) {
  const { autoResize = true, theme = 'light' } = options

  const chartRef = ref(null)
  const chartInstance = ref(null)
  const loading = ref(false)

  // 初始化图表
  const initChart = () => {
    if (!chartRef.value) return

    chartInstance.value = echarts.init(chartRef.value, theme)
    chartInstance.value.setOption(getOption())

    if (autoResize) {
      window.addEventListener('resize', handleResize)
    }
  }

  // 更新图表
  const updateChart = (newOption) => {
    if (chartInstance.value) {
      chartInstance.value.setOption(newOption || getOption(), { notMerge: false })
    }
  }

  // 重置大小
  const handleResize = () => {
    chartInstance.value?.resize()
  }

  // 显示加载
  const showLoading = () => {
    loading.value = true
    chartInstance.value?.showLoading({
      text: '加载中...',
      color: '#0078D4',
      textColor: '#333',
      maskColor: 'rgba(255, 255, 255, 0.8)',
    })
  }

  // 隐藏加载
  const hideLoading = () => {
    loading.value = false
    chartInstance.value?.hideLoading()
  }

  // 获取实例
  const getInstance = () => chartInstance.value

  // 销毁图表
  const dispose = () => {
    if (chartInstance.value) {
      chartInstance.value.dispose()
      chartInstance.value = null
    }
    window.removeEventListener('resize', handleResize)
  }

  onMounted(() => {
    nextTick(() => {
      initChart()
    })
  })

  onUnmounted(() => {
    dispose()
  })

  return {
    chartRef,
    chartInstance,
    loading,
    initChart,
    updateChart,
    handleResize,
    showLoading,
    hideLoading,
    getInstance,
    dispose,
  }
}

/**
 * 创建折线图配置
 */
export function createLineChartOption(data, options = {}) {
  const { title = '', xData = [], yData = [], smooth = true, areaStyle = true } = options

  return {
    title: title ? { text: title, left: 'center' } : undefined,
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: xData,
      boundaryGap: false,
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: title,
        type: 'line',
        smooth,
        areaStyle: areaStyle ? { color: 'rgba(0, 120, 212, 0.2)' } : undefined,
        data: yData,
      },
    ],
  }
}

/**
 * 创建饼图配置
 */
export function createPieChartOption(data, options = {}) {
  const { title = '', radius = '70%' } = options

  return {
    title: title ? { text: title, left: 'center' } : undefined,
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', right: 10, top: 'middle' },
    series: [
      {
        type: 'pie',
        radius,
        data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  }
}

/**
 * 创建柱状图配置
 */
export function createBarChartOption(data, options = {}) {
  const { title = '', xData = [], yData = [] } = options

  return {
    title: title ? { text: title, left: 'center' } : undefined,
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: xData },
    yAxis: { type: 'value' },
    series: [
      {
        name: title,
        type: 'bar',
        data: yData,
        itemStyle: { color: '#0078D4' },
      },
    ],
  }
}
