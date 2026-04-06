import { ref, onMounted, onUnmounted } from 'vue'
import {
  formatNumber,
  formatPercent,
  formatDate,
  formatRelativeTime,
  copyToClipboard,
} from '@/utils'

export function useDebounce(fn, delay = 300) {
  let timer = null

  const debouncedFn = (...args) => {
    if (timer) {
      clearTimeout(timer)
    }
    timer = setTimeout(() => {
      fn(...args)
    }, delay)
  }

  const cancel = () => {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }

  onUnmounted(cancel)

  return {
    debouncedFn,
    cancel,
  }
}

export function useThrottle(fn, delay = 300) {
  let lastTime = 0

  const throttledFn = (...args) => {
    const now = Date.now()
    if (now - lastTime >= delay) {
      fn(...args)
      lastTime = now
    }
  }

  return throttledFn
}

export function useClickOutside(targetRef, callback) {
  const isClickOutside = ref(false)

  const handleClick = (event) => {
    if (targetRef.value) {
      isClickOutside.value = !targetRef.value.contains(event.target)
      if (isClickOutside.value) {
        callback(event)
      }
    }
  }

  onMounted(() => {
    document.addEventListener('click', handleClick)
  })

  onUnmounted(() => {
    document.removeEventListener('click', handleClick)
  })

  return {
    isClickOutside,
  }
}

export function useCopyToClipboard() {
  const copied = ref(false)

  const copy = async (text) => {
    try {
      await copyToClipboard(text)
      copied.value = true
      setTimeout(() => {
        copied.value = false
      }, 2000)
      return true
    } catch (error) {
      return false
    }
  }

  return {
    copied,
    copy,
  }
}

export function useLocalStorage() {
  const get = (key, defaultValue = null) => {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : defaultValue
    } catch (error) {
      return defaultValue
    }
  }

  const set = (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value))
      return true
    } catch (error) {
      return false
    }
  }

  const remove = (key) => {
    try {
      localStorage.removeItem(key)
      return true
    } catch (error) {
      return false
    }
  }

  return {
    get,
    set,
    remove,
  }
}

export function useNumberFormat() {
  return {
    format: formatNumber,
    formatPercent,
  }
}

export function useDateFormat() {
  return {
    format: formatDate,
    formatRelative: formatRelativeTime,
  }
}
