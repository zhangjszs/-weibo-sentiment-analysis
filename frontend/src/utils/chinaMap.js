import echarts from './echarts'

let ready = null

// #40：1MB 的 china.json（minify 后 ~520KB）曾是 ip 路由 chunk 的绝对大头
// （占 98.6%）。改为运行时按需拉取静态资产：vite 构建时经 new URL(…, import.meta.url)
// 发出带 hash 的 json 资产，浏览器可长期缓存，且不再阻塞路由 JS 的下载与解析。
// registerMap 是 echarts 全局状态：promise 复用保证并发/重复调用只注册一次，
// 并使 BigScreen 直接访问时地图同样可用（修复原先「先访问 IP 页才能渲染大屏地图」
// 的顺序依赖问题）。
export function ensureChinaMap() {
  ready ??= fetch(new URL('../assets/china.json', import.meta.url))
    .then((res) => {
      if (!res.ok) {
        throw new Error(`地图资产加载失败：HTTP ${res.status}`)
      }
      return res.json()
    })
    .then((data) => {
      echarts.registerMap('china', data)
      return data
    })
    .catch((error) => {
      ready = null // 失败后允许重试
      throw error
    })
  return ready
}
