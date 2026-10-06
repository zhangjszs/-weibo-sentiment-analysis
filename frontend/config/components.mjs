// vite 与 vitest 共用的模板级组件解析配置（#49）。
//
// 两份构建/测试配置必须引用本文件而不是各自定义 resolver：此前 vitest.config.js
// 没有 Components 插件，jsdom 里 <el-*> 按未知元素渲染且不报错，模板级组件
// 解析在单测中是盲区；两处手工维护也随时可能漂移。
//
// - ElementPlusResolver：模板中的 <el-*> 按需引入组件与样式（#39）
// - iconResolver：模板中的图标标签（<Star /> 等）按需引入（#39）；
//   字符串形式的引用（icon="X" prop、<component :is="'X'">）不走这里，
//   由 src/plugins/elementPlus.js 的最小全局注册负责——两套机制互不重叠。
//
// 每次调用返回全新插件实例：vite build 与 vitest 是两个独立进程/配置，
// 不共享插件内部状态。
//
// importStyle 参数：vite（默认 'css'）按需注入组件样式；vitest 必须传 false
// ——jsdom 无视觉断言，而 resolver 注入的 element-plus 样式导入在 vitest 的
// node_modules 外部化下会以「Unknown file extension .css」崩掉测试收集。
// resolver 清单本身两处完全一致，不存在漂移。
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import * as elementPlusIcons from '@element-plus/icons-vue'

const ICON_NAMES = new Set(Object.keys(elementPlusIcons))
const iconResolver = (name) => {
  if (ICON_NAMES.has(name)) {
    return { name, from: '@element-plus/icons-vue' }
  }
}

export function createComponentsPlugin({ importStyle = 'css' } = {}) {
  return Components({
    resolvers: [ElementPlusResolver({ importStyle }), iconResolver],
    dts: false,
  })
}
