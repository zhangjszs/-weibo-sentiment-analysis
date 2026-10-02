// ElLoading 默认导出是带 install 的插件对象（注册 v-loading 指令 + $loading）。
// 注意 2.14.2 没有 es/components/loading/plugin 子路径，深路径只有 …/loading/index。
import ElLoading from 'element-plus/es/components/loading/index'

// #39：element-plus 组件与图标不再全量注册。
// - 组件：vite.config 的 Components 插件 + ElementPlusResolver 按模板标签自动按需引入
// - 图标：模板标签形式（<Star />）由 iconResolver 按需引入
// 本文件只保留**以字符串形式解析**所需的最小全局注册：
// 1) v-loading 指令（全仓 6 处，来自 ElLoading 插件）
// 2) 字符串引用的图标：el-* 的 icon="Search" prop、StatCard 的 icon 默认值
//    'DataLine'、tabs 默认页签的 'HomeFilled'、Help 特性卡配置、BigScreen
//    动态三元等——字符串 icon 走全局组件解析，必须注册才能渲染。
//    路由 meta.icon 本身是组件引用，但页签持久化/恢复后可能退化为名字字符串，
//    故路由用到的图标一并注册（每个 <1KB，稳妥优先）。
// 新增字符串引用的图标时，务必同步加进 ICON_COMPONENTS
// （tests/element-plus-icons.test.js 扫描 src 的字符串图标引用做守护）。
import {
  Bell,
  ChatDotRound,
  ChatLineRound,
  CircleCheck,
  CircleClose,
  Cloudy,
  Connection,
  Cpu,
  DataAnalysis,
  DataLine,
  Delete,
  Document,
  Download,
  HomeFilled,
  Location,
  Lock,
  Monitor,
  QuestionFilled,
  Refresh,
  Remove,
  Search,
  Share,
  Star,
  Tickets,
  TrendCharts,
  User,
  VideoPause,
  VideoPlay,
  View,
} from '@element-plus/icons-vue'

export const ICON_COMPONENTS = {
  Bell,
  ChatDotRound,
  ChatLineRound,
  CircleCheck,
  CircleClose,
  Cloudy,
  Connection,
  Cpu,
  DataAnalysis,
  DataLine,
  Delete,
  Document,
  Download,
  HomeFilled,
  Location,
  Lock,
  Monitor,
  QuestionFilled,
  Refresh,
  Remove,
  Search,
  Share,
  Star,
  Tickets,
  TrendCharts,
  User,
  VideoPause,
  VideoPlay,
  View,
}

export function installElementPlus(app) {
  app.use(ElLoading)

  for (const [name, component] of Object.entries(ICON_COMPONENTS)) {
    app.component(name, component)
  }
}
