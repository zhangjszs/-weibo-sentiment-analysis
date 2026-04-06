import { ref, computed, onMounted, onUnmounted } from 'vue'

const MOBILE_BREAKPOINT = 768
const TABLET_BREAKPOINT = 1024

export function useResponsive() {
  const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 0)
  const windowHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 0)

  const isMobile = computed(() => windowWidth.value < MOBILE_BREAKPOINT)
  const isTablet = computed(
    () => windowWidth.value >= MOBILE_BREAKPOINT && windowWidth.value < TABLET_BREAKPOINT
  )
  const isDesktop = computed(() => windowWidth.value >= TABLET_BREAKPOINT)

  const breakpoints = computed(() => ({
    xs: windowWidth.value < 480,
    sm: windowWidth.value >= 480 && windowWidth.value < MOBILE_BREAKPOINT,
    md: windowWidth.value >= MOBILE_BREAKPOINT && windowWidth.value < TABLET_BREAKPOINT,
    lg: windowWidth.value >= TABLET_BREAKPOINT && windowWidth.value < 1440,
    xl: windowWidth.value >= 1440,
  }))

  const colSpan = computed(() => {
    if (isMobile.value) return 24
    if (isTablet.value) return 12
    return 6
  })

  const updateSize = () => {
    if (typeof window !== 'undefined') {
      windowWidth.value = window.innerWidth
      windowHeight.value = window.innerHeight
    }
  }

  onMounted(() => {
    updateSize()
    window.addEventListener('resize', updateSize)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', updateSize)
  })

  return {
    windowWidth,
    windowHeight,
    isMobile,
    isTablet,
    isDesktop,
    breakpoints,
    colSpan,
  }
}

export function useTouch() {
  const touchStartX = ref(0)
  const touchStartY = ref(0)
  const touchEndX = ref(0)
  const touchEndY = ref(0)

  const onTouchStart = (e) => {
    touchStartX.value = e.touches[0].clientX
    touchStartY.value = e.touches[0].clientY
  }

  const onTouchEnd = (e) => {
    touchEndX.value = e.changedTouches[0].clientX
    touchEndY.value = e.changedTouches[0].clientY
  }

  const getSwipeDirection = () => {
    const diffX = touchEndX.value - touchStartX.value
    const diffY = touchEndY.value - touchStartY.value

    if (Math.abs(diffX) > Math.abs(diffY)) {
      return diffX > 0 ? 'right' : 'left'
    } else {
      return diffY > 0 ? 'down' : 'up'
    }
  }

  const getSwipeDistance = () => {
    return {
      x: touchEndX.value - touchStartX.value,
      y: touchEndY.value - touchStartY.value,
    }
  }

  const isSwipe = (minDistance = 50) => {
    const distance = getSwipeDistance()
    return Math.abs(distance.x) > minDistance || Math.abs(distance.y) > minDistance
  }

  return {
    onTouchStart,
    onTouchEnd,
    getSwipeDirection,
    getSwipeDistance,
    isSwipe,
    touchStartX,
    touchStartY,
    touchEndX,
    touchEndY,
  }
}

export function usePullRefresh(callback) {
  const isRefreshing = ref(false)
  const startY = ref(0)
  const currentY = ref(0)
  const pullDistance = ref(0)
  const isPulling = ref(false)

  const onTouchStart = (e) => {
    if (window.scrollY === 0) {
      startY.value = e.touches[0].clientY
      isPulling.value = true
    }
  }

  const onTouchMove = (e) => {
    if (isPulling.value) {
      currentY.value = e.touches[0].clientY
      pullDistance.value = Math.max(0, currentY.value - startY.value)
    }
  }

  const onTouchEnd = async () => {
    if (pullDistance.value > 60) {
      isRefreshing.value = true
      try {
        await callback?.()
      } finally {
        isRefreshing.value = false
      }
    }
    isPulling.value = false
    pullDistance.value = 0
  }

  return {
    isRefreshing,
    pullDistance,
    onTouchStart,
    onTouchMove,
    onTouchEnd,
  }
}

export function useGesture(elementRef) {
  const scale = ref(1)
  const isLongPress = ref(false)
  let longPressTimer = null
  let initialDistance = 0

  const getDistance = (touches) => {
    const dx = touches[0].clientX - touches[1].clientX
    const dy = touches[0].clientY - touches[1].clientY
    return Math.sqrt(dx * dx + dy * dy)
  }

  const onTouchStart = (e) => {
    if (e.touches.length === 2) {
      initialDistance = getDistance(e.touches)
    }
    if (e.touches.length === 1) {
      longPressTimer = setTimeout(() => {
        isLongPress.value = true
      }, 500)
    }
  }

  const onTouchMove = (e) => {
    if (e.touches.length === 2 && initialDistance > 0) {
      const currentDistance = getDistance(e.touches)
      scale.value = Math.min(3, Math.max(0.5, currentDistance / initialDistance))
    }
    if (longPressTimer) {
      clearTimeout(longPressTimer)
      longPressTimer = null
    }
  }

  const onTouchEnd = () => {
    initialDistance = 0
    isLongPress.value = false
    if (longPressTimer) {
      clearTimeout(longPressTimer)
      longPressTimer = null
    }
  }

  const resetScale = () => {
    scale.value = 1
  }

  return {
    scale,
    isLongPress,
    onTouchStart,
    onTouchMove,
    onTouchEnd,
    resetScale,
  }
}

export function useMobileChart(containerRef) {
  const { isMobile, isTablet } = useResponsive()
  const chartWidth = ref(0)
  const chartHeight = ref(0)

  const updateChartSize = () => {
    const el = containerRef?.value
    if (el) {
      chartWidth.value = el.clientWidth || el.offsetWidth
    } else if (typeof window !== 'undefined') {
      chartWidth.value = window.innerWidth
    }
    if (isMobile.value) {
      chartHeight.value = Math.round(chartWidth.value * 0.6)
    } else if (isTablet.value) {
      chartHeight.value = Math.round(chartWidth.value * 0.5)
    } else {
      chartHeight.value = Math.round(chartWidth.value * 0.4)
    }
  }

  const chartOption = (baseOption) => {
    if (!isMobile.value) return baseOption
    return {
      ...baseOption,
      legend: { ...(baseOption.legend || {}), show: false },
      grid: { top: 30, right: 10, bottom: 40, left: 40, ...(baseOption.grid || {}) },
      xAxis: Array.isArray(baseOption.xAxis)
        ? baseOption.xAxis.map((a) => ({
            ...a,
            axisLabel: { ...(a.axisLabel || {}), fontSize: 10 },
          }))
        : {
            ...baseOption.xAxis,
            axisLabel: { ...(baseOption.xAxis?.axisLabel || {}), fontSize: 10 },
          },
    }
  }

  onMounted(() => {
    updateChartSize()
    window.addEventListener('resize', updateChartSize)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', updateChartSize)
  })

  return {
    chartWidth,
    chartHeight,
    chartOption,
    updateChartSize,
  }
}

export default {
  useResponsive,
  useTouch,
  usePullRefresh,
  useGesture,
  useMobileChart,
}
