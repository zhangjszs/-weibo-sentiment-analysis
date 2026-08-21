# 前端分层：容器/图表/数据

`BigScreen.vue` 1399 行等页面将容器、ECharts 图表、数据拉取糊在一处，且 `pinia` 已装却直连 `axios` 无缓存。决定按容器/图表/数据三层拆分（`components/charts/*` + `composables/useAnalysis`），高频轮询收敛到 `stores/analysis` 的 SWR 缓存，图表复用优先于领域自治。
