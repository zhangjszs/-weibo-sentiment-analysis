/**
 * Vue 图片懒加载指令
 * 使用 IntersectionObserver 实现，当图片进入视口时才加载
 *
 * 用法：<img v-lazy="imageUrl" />
 */

const loadImage = (el, binding) => {
  const src = binding.value
  if (!src) return

  el.setAttribute('loading', 'lazy')

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            el.src = src
            el.classList.add('lazy-loaded')
            observer.unobserve(el)
          }
        })
      },
      { rootMargin: '100px' }
    )
    observer.observe(el)
    el._lazyObserver = observer
  } else {
    // Fallback: load immediately
    el.src = src
  }
}

export const lazyLoad = {
  mounted(el, binding) {
    loadImage(el, binding)
  },
  updated(el, binding) {
    if (binding.value !== binding.oldValue) {
      if (el._lazyObserver) {
        el._lazyObserver.unobserve(el)
      }
      loadImage(el, binding)
    }
  },
  unmounted(el) {
    if (el._lazyObserver) {
      el._lazyObserver.unobserve(el)
      delete el._lazyObserver
    }
  },
}

export default lazyLoad
