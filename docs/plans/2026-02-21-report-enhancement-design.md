# PDF/PPT 报告增强设计文档

> 日期：2026-02-21
> 任务：TODO 2.3 PDF/PPT 报告增强

---

## 目标

在现有报告生成器基础上，新增：
1. **图表嵌入**：后端用 matplotlib 渲染 4 种图表，以图片形式嵌入 PDF/PPT
2. **预设模板系统**：3 套模板（简报/标准/详细），前端选择后自动切换章节配置

---

## 架构设计

### 后端改动

#### 1. 新增 `ChartRenderer`（`src/utils/chart_renderer.py`）

负责用 matplotlib 渲染图表，返回 `bytes`（PNG）：

| 方法 | 图表类型 | 数据来源 |
|------|---------|---------|
| `render_sentiment_pie(data)` | 情感分布饼图 | `summary.positive/neutral/negative_count` |
| `render_topics_bar(data)` | 热门话题柱状图 | `hot_topics[:10]` |
| `render_trend_line(data)` | 舆情趋势折线图 | `trend` 字段（可选，无则跳过） |
| `render_alert_bar(data)` | 预警级别分布图 | `alerts` 列表 |

所有方法使用非交互后端（`matplotlib.use('Agg')`），线程安全。

#### 2. 修改 `PDFReportGenerator.generate()`

- 接收 `config.include_charts: bool`（已有字段，现在真正生效）
- 调用 `ChartRenderer`，将图片字节流用 `reportlab.platypus.Image` 嵌入对应章节

#### 3. 修改 `PPTReportGenerator`

- 各 `_add_*_slide()` 方法接收可选 `chart_bytes`
- 用 `pptx.util` + `slide.shapes.add_picture()` 嵌入图片

#### 4. 修改 `ReportConfig`

新增字段：
```python
template: str = "standard"   # "brief" | "standard" | "detailed"
sections: list[str] = None   # None 时由模板决定
```

#### 5. 修改 `report_api.py` `/generate` 接口

- 请求体新增 `template`、`sections` 字段
- 透传给 `ReportConfig`

#### 6. 修改 `/templates` 接口

补充每个模板的 `chart_slots` 字段，告知前端该模板包含哪些图表。

---

### 前端改动

#### `report.vue`

- 模板选择后，自动同步勾选对应的 `sections`（联动）
- 生成请求体新增 `template` 字段
- 无需 html2canvas，图表由后端生成

---

## 模板定义

| 模板 ID | 名称 | 章节 | 图表 |
|---------|------|------|------|
| `brief` | 简报 | summary, sentiment | 情感饼图 |
| `standard` | 标准报告 | summary, sentiment, topics, alerts | 情感饼图 + 话题柱状图 + 预警分布图 |
| `detailed` | 详细报告 | summary, sentiment, topics, alerts, trend | 全部 4 种图表 |

---

## 数据流

```
前端选择模板 → 发送 {template, sections, data}
  → report_api.py 解析 sections
  → ChartRenderer 渲染图表 → bytes
  → PDFReportGenerator / PPTReportGenerator 嵌入图片
  → 返回文件下载链接
```

---

## 不做的事（YAGNI）

- 不做自定义图表颜色配置
- 不做图表尺寸调节
- 不做 Word 格式支持
- 不做图表交互（静态图片即可）

---

## 文件变更清单

| 文件 | 操作 |
|------|------|
| `src/utils/chart_renderer.py` | 新增 |
| `src/utils/report_generator.py` | 修改（嵌入图表逻辑） |
| `src/views/api/report_api.py` | 修改（透传 template/sections） |
| `frontend/src/views/system/report.vue` | 修改（模板联动 sections） |
