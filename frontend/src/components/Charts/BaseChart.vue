<template>
  <div
    ref="chartRef"
    class="base-chart"
    :style="{ height: height, width: width }"
  />
</template>

<script setup>
  import { ref, onMounted, onUnmounted, watch, nextTick, markRaw } from 'vue'
  import echarts from '@/utils/echarts'

  const props = defineProps({
    options: {
      type: Object,
      required: true,
    },
    height: {
      type: String,
      default: '300px',
    },
    width: {
      type: String,
      default: '100%',
    },
    theme: {
      type: String,
      default: 'auto',
    },
    autoResize: {
      type: Boolean,
      default: true,
    },
  })

  const emit = defineEmits(['click', 'legendselectchanged'])

  const chartRef = ref(null)
  let chartInstance = null
  let observer = null

  const getAutoTheme = () => {
    return document.documentElement.classList.contains('dark') ? 'dark' : null
  }

  const initInstance = (themeName) => {
    if (!chartRef.value) return
    chartInstance = markRaw(echarts.init(chartRef.value, themeName))
    chartInstance.setOption(props.options, true)

    chartInstance.on('click', (params) => {
      emit('click', params)
    })

    chartInstance.on('legendselectchanged', (params) => {
      emit('legendselectchanged', params)
    })
  }

  const initChart = () => {
    if (chartRef.value) {
      const themeName = props.theme === 'auto' ? getAutoTheme() : props.theme
      initInstance(themeName)

      if (props.autoResize) {
        window.addEventListener('resize', handleResize)
      }
    }
  }

  const handleResize = () => {
    chartInstance?.resize()
  }

  const updateOptions = (newOptions) => {
    chartInstance?.setOption(newOptions, { notMerge: false })
  }

  watch(
    () => props.options,
    (newOptions) => {
      nextTick(() => {
        updateOptions(newOptions)
      })
    },
    { deep: true }
  )

  watch(
    () => props.theme,
    (newTheme) => {
      const themeName = newTheme === 'auto' ? getAutoTheme() : newTheme
      chartInstance?.dispose()
      initInstance(themeName)
    }
  )

  onMounted(() => {
    nextTick(() => {
      initChart()
      if (props.theme === 'auto') {
        observer = new MutationObserver(() => {
          const themeName = getAutoTheme()
          chartInstance?.dispose()
          initInstance(themeName)
        })
        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
      }
    })
  })

  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    observer?.disconnect()
    chartInstance?.dispose()
  })

  defineExpose({
    resize: handleResize,
    getInstance: () => chartInstance,
  })
</script>

<style lang="scss" scoped>
  .base-chart {
    min-height: 200px;
  }
</style>
