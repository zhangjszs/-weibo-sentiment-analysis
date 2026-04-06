# PDF/PPT 报告增强实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在现有报告生成器基础上，新增 matplotlib 图表嵌入（饼图/柱状图/折线图/预警分布图）和 3 套预设模板系统。

**Architecture:** 新增 `ChartRenderer` 工具类用 matplotlib Agg 后端渲染图表为 PNG bytes；修改 `PDFReportGenerator` 和 `PPTReportGenerator` 接收并嵌入图表；`ReportConfig` 新增 `template` 和 `sections` 字段；前端模板选择后自动联动章节勾选。

**Tech Stack:** Python matplotlib, reportlab (Image), python-pptx (add_picture), Vue 3, Element Plus

---

### Task 1: 新增 ChartRenderer

**Files:**
- Create: `src/utils/chart_renderer.py`
- Test: `tests/test_chart_renderer.py`

**Step 1: 写失败测试**

```python
# tests/test_chart_renderer.py
import pytest
from utils.chart_renderer import ChartRenderer

@pytest.fixture
def renderer():
    return ChartRenderer()

@pytest.fixture
def sample_data():
    return {
        'summary': {'positive_count': 100, 'neutral_count': 50, 'negative_count': 30},
        'hot_topics': [{'name': f'话题{i}', 'heat': 100-i*10} for i in range(5)],
        'alerts': [
            {'level': 'danger'}, {'level': 'warning'}, {'level': 'warning'}, {'level': 'info'}
        ],
        'trend': [
            {'date': '2026-02-01', 'count': 120},
            {'date': '2026-02-02', 'count': 150},
            {'date': '2026-02-03', 'count': 90},
        ]
    }

def test_render_sentiment_pie_returns_bytes(renderer, sample_data):
    result = renderer.render_sentiment_pie(sample_data)
    assert isinstance(result, bytes)
    assert len(result) > 0

def test_render_topics_bar_returns_bytes(renderer, sample_data):
    result = renderer.render_topics_bar(sample_data)
    assert isinstance(result, bytes)
    assert len(result) > 0

def test_render_trend_line_returns_bytes(renderer, sample_data):
    result = renderer.render_trend_line(sample_data)
    assert isinstance(result, bytes)
    assert len(result) > 0

def test_render_trend_line_no_data_returns_none(renderer):
    result = renderer.render_trend_line({})
    assert result is None

def test_render_alert_bar_returns_bytes(renderer, sample_data):
    result = renderer.render_alert_bar(sample_data)
    assert isinstance(result, bytes)
    assert len(result) > 0

def test_render_alert_bar_no_alerts_returns_none(renderer):
    result = renderer.render_alert_bar({})
    assert result is None
```

**Step 2: 运行确认失败**

```bash
cd "D:/coding/Pycharm/基于python微博舆情分析可视化系统"
python -m pytest tests/test_chart_renderer.py -v
```
Expected: ImportError 或 ModuleNotFoundError

**Step 3: 实现 ChartRenderer**

```python
# src/utils/chart_renderer.py
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib 未安装，图表嵌入功能不可用")


_CHINESE_FONTS = [
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/msyh.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]


def _get_chinese_font():
    import os
    for p in _CHINESE_FONTS:
        if os.path.exists(p):
            return fm.FontProperties(fname=p)
    return None


class ChartRenderer:
    def __init__(self):
        self._font = _get_chinese_font() if MATPLOTLIB_AVAILABLE else None

    def _to_bytes(self, fig) -> bytes:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=120, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def render_sentiment_pie(self, data: dict) -> Optional[bytes]:
        if not MATPLOTLIB_AVAILABLE:
            return None
        summary = data.get('summary', {})
        pos = summary.get('positive_count', 0)
        neu = summary.get('neutral_count', 0)
        neg = summary.get('negative_count', 0)
        if pos + neu + neg == 0:
            return None
        fig, ax = plt.subplots(figsize=(5, 4))
        labels = ['正面', '中性', '负面']
        sizes = [pos, neu, neg]
        colors = ['#4CAF50', '#9E9E9E', '#F44336']
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
               textprops={'fontproperties': self._font} if self._font else {})
        ax.set_title('情感分布', fontproperties=self._font)
        return self._to_bytes(fig)

    def render_topics_bar(self, data: dict) -> Optional[bytes]:
        if not MATPLOTLIB_AVAILABLE:
            return None
        topics = data.get('hot_topics', [])[:10]
        if not topics:
            return None
        names = [t.get('name', '')[:8] for t in topics]
        heats = [t.get('heat', 0) for t in topics]
        fig, ax = plt.subplots(figsize=(7, 4))
        bars = ax.barh(names[::-1], heats[::-1], color='#2196F3')
        ax.set_xlabel('热度', fontproperties=self._font)
        ax.set_title('热门话题 Top 10', fontproperties=self._font)
        if self._font:
            for label in ax.get_yticklabels():
                label.set_fontproperties(self._font)
        return self._to_bytes(fig)

    def render_trend_line(self, data: dict) -> Optional[bytes]:
        if not MATPLOTLIB_AVAILABLE:
            return None
        trend = data.get('trend', [])
        if not trend:
            return None
        dates = [t.get('date', '') for t in trend]
        counts = [t.get('count', 0) for t in trend]
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(dates, counts, marker='o', color='#FF9800')
        ax.set_title('舆情趋势', fontproperties=self._font)
        ax.set_xlabel('日期', fontproperties=self._font)
        ax.set_ylabel('数量', fontproperties=self._font)
        plt.xticks(rotation=30)
        return self._to_bytes(fig)

    def render_alert_bar(self, data: dict) -> Optional[bytes]:
        if not MATPLOTLIB_AVAILABLE:
            return None
        alerts = data.get('alerts', [])
        if not alerts:
            return None
        from collections import Counter
        counts = Counter(a.get('level', 'info') for a in alerts)
        levels = ['danger', 'warning', 'info']
        values = [counts.get(l, 0) for l in levels]
        labels = ['严重', '警告', '提示']
        colors = ['#F44336', '#FF9800', '#2196F3']
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.bar(labels, values, color=colors)
        ax.set_title('预警级别分布', fontproperties=self._font)
        if self._font:
            for label in ax.get_xticklabels():
                label.set_fontproperties(self._font)
        return self._to_bytes(fig)


chart_renderer = ChartRenderer()
```

**Step 4: 运行测试确认通过**

```bash
python -m pytest tests/test_chart_renderer.py -v
```
Expected: 6 passed

**Step 5: 提交**

```bash
git add src/utils/chart_renderer.py tests/test_chart_renderer.py
git commit -m "feat(report): add ChartRenderer with matplotlib Agg backend"
```

---

### Task 2: 修改 ReportConfig，新增 template/sections 字段

**Files:**
- Modify: `src/utils/report_generator.py` (ReportConfig dataclass, ~行 48-57)

**Step 1: 修改 ReportConfig**

在 `src/utils/report_generator.py` 的 `ReportConfig` 中新增两个字段：

```python
@dataclass
class ReportConfig:
    title: str = "舆情分析报告"
    subtitle: str = ""
    author: str = "微博舆情分析系统"
    date_format: str = "%Y年%m月%d日"
    include_charts: bool = True
    include_tables: bool = True
    page_size: str = "A4"
    template: str = "standard"          # 新增
    sections: Optional[List[str]] = None  # 新增，None 时由模板决定
```

同时在文件顶部 `TEMPLATE_SECTIONS` 常量（紧接 import 之后）：

```python
TEMPLATE_SECTIONS = {
    "brief":    ["summary", "sentiment"],
    "standard": ["summary", "sentiment", "topics", "alerts"],
    "detailed": ["summary", "sentiment", "topics", "alerts", "trend"],
}
```

**Step 2: 无需单独测试（Task 3 的测试会覆盖），直接提交**

```bash
git add src/utils/report_generator.py
git commit -m "feat(report): add template/sections fields to ReportConfig"
```

---

### Task 3: 修改 PDFReportGenerator 嵌入图表

**Files:**
- Modify: `src/utils/report_generator.py` (`PDFReportGenerator.generate()`)
- Test: `tests/test_report_generator.py`（新增用例）

**Step 1: 写失败测试**

在 `tests/test_report_generator.py` 末尾追加（若文件不存在则新建）：

```python
# tests/test_report_generator.py
import os, tempfile, pytest
from utils.report_generator import PDFReportGenerator, PPTReportGenerator, ReportConfig

SAMPLE_DATA = {
    'summary': {'total_articles': 100, 'total_comments': 500,
                'positive_count': 60, 'neutral_count': 25, 'negative_count': 15},
    'sentiment_analysis': {'正面占比': '60%', '负面占比': '15%'},
    'hot_topics': [{'name': f'话题{i}', 'heat': 100-i} for i in range(5)],
    'alerts': [{'level': 'warning', 'title': '测试', 'message': '测试消息'}],
    'trend': [{'date': '2026-02-01', 'count': 80}, {'date': '2026-02-02', 'count': 100}],
}

def test_pdf_with_charts_creates_file():
    gen = PDFReportGenerator()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'test.pdf')
        config = ReportConfig(include_charts=True, template='standard')
        result = gen.generate(SAMPLE_DATA, path, config)
        assert result is not None
        assert os.path.exists(result)
        assert os.path.getsize(result) > 1000

def test_pdf_without_charts_creates_file():
    gen = PDFReportGenerator()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'test_no_chart.pdf')
        config = ReportConfig(include_charts=False)
        result = gen.generate(SAMPLE_DATA, path, config)
        assert result is not None

def test_ppt_with_charts_creates_file():
    gen = PPTReportGenerator()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'test.pptx')
        config = ReportConfig(include_charts=True, template='detailed')
        result = gen.generate(SAMPLE_DATA, path, config)
        assert result is not None
        assert os.path.exists(result)
```

**Step 2: 运行确认失败（或部分失败）**

```bash
python -m pytest tests/test_report_generator.py -v
```

**Step 3: 修改 `PDFReportGenerator.generate()`**

在 `src/utils/report_generator.py` 中，`PDFReportGenerator.generate()` 方法里，在 `doc.build(story)` 之前，按章节插入图表。关键改动：

1. 在方法开头导入 `ChartRenderer` 和 `TEMPLATE_SECTIONS`：
   ```python
   from utils.chart_renderer import chart_renderer
   ```
   （放在文件顶部 try/except 块之后）

2. 在 `generate()` 方法中，确定实际 sections：
   ```python
   sections = config.sections or TEMPLATE_SECTIONS.get(config.template, TEMPLATE_SECTIONS["standard"])
   ```

3. 在每个数据章节（summary/sentiment/topics/alerts）之后，若 `config.include_charts` 为 True，插入对应图表：
   - `summary` 章节后：`chart_renderer.render_sentiment_pie(data)`
   - `hot_topics` 章节后：`chart_renderer.render_topics_bar(data)`
   - `alerts` 章节后：`chart_renderer.render_alert_bar(data)`
   - `trend` 章节（新增）：`chart_renderer.render_trend_line(data)`

4. 图表嵌入方式（reportlab）：
   ```python
   chart_bytes = chart_renderer.render_sentiment_pie(data)
   if chart_bytes:
       from io import BytesIO
       story.append(Image(BytesIO(chart_bytes), width=12*cm, height=9*cm))
       story.append(Spacer(1, 10))
   ```

5. 同样用 `sections` 控制哪些章节被渲染（`if 'summary' in sections` 替换原来的 `if 'summary' in data`）。

**Step 4: 运行测试**

```bash
python -m pytest tests/test_report_generator.py -v
```
Expected: 3 passed

**Step 5: 提交**

```bash
git add src/utils/report_generator.py tests/test_report_generator.py
git commit -m "feat(report): embed matplotlib charts into PDF via ChartRenderer"
```

---

### Task 4: 修改 PPTReportGenerator 嵌入图表

**Files:**
- Modify: `src/utils/report_generator.py` (`PPTReportGenerator.generate()` 及各 `_add_*_slide()`)

**Step 1: 修改各 slide 方法签名，接收可选 chart_bytes**

修改 `_add_summary_slide`、`_add_topics_slide`、`_add_alerts_slide` 签名：
```python
def _add_summary_slide(self, summary: Dict, chart_bytes: bytes = None):
def _add_topics_slide(self, topics: List[Dict], chart_bytes: bytes = None):
def _add_alerts_slide(self, alerts: List[Dict], chart_bytes: bytes = None):
```

在每个方法末尾，若 `chart_bytes` 不为 None，嵌入图片：
```python
if chart_bytes:
    from io import BytesIO
    pic_stream = BytesIO(chart_bytes)
    slide.shapes.add_picture(pic_stream, Inches(7), Inches(1.5), Inches(5.5), Inches(4.5))
```

**Step 2: 修改 `generate()` 方法**

```python
sections = config.sections or TEMPLATE_SECTIONS.get(config.template, TEMPLATE_SECTIONS["standard"])

if 'summary' in sections and 'summary' in data:
    chart = chart_renderer.render_sentiment_pie(data) if config.include_charts else None
    self._add_summary_slide(data['summary'], chart)

if 'sentiment' in sections and 'sentiment_analysis' in data:
    self._add_sentiment_slide(data['sentiment_analysis'])

if 'topics' in sections and 'hot_topics' in data:
    chart = chart_renderer.render_topics_bar(data) if config.include_charts else None
    self._add_topics_slide(data['hot_topics'], chart)

if 'alerts' in sections and 'alerts' in data:
    chart = chart_renderer.render_alert_bar(data) if config.include_charts else None
    self._add_alerts_slide(data['alerts'], chart)

if 'trend' in sections and 'trend' in data:
    chart = chart_renderer.render_trend_line(data) if config.include_charts else None
    self._add_trend_slide(data['trend'], chart)
```

新增 `_add_trend_slide()`：
```python
def _add_trend_slide(self, trend: List[Dict], chart_bytes: bytes = None):
    slide_layout = self.prs.slide_layouts[6]
    slide = self.prs.slides.add_slide(slide_layout)
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.333), Inches(0.8))
    tf = title_box.text_frame
    p = tf.paragraphs[0]
    p.text = "舆情趋势"
    p.font.size = Pt(32)
    p.font.bold = True
    if chart_bytes:
        from io import BytesIO
        slide.shapes.add_picture(BytesIO(chart_bytes), Inches(1), Inches(1.5), Inches(11), Inches(5))
```

**Step 3: 运行测试**

```bash
python -m pytest tests/test_report_generator.py -v
```
Expected: 3 passed

**Step 4: 提交**

```bash
git add src/utils/report_generator.py
git commit -m "feat(report): embed matplotlib charts into PPT slides"
```

---

### Task 5: 修改 report_api.py 透传 template/sections

**Files:**
- Modify: `src/views/api/report_api.py`

**Step 1: 修改 `/generate` 接口**

在 `generate_report()` 函数中，从请求体读取 `template` 和 `sections`：

```python
template = data.get('template', 'standard')
sections = data.get('sections', None)

config = ReportConfig(
    title=title,
    subtitle=f"自动生成于 {datetime.now().strftime('%Y年%m月%d日 %H:%M')}",
    author='微博舆情分析系统',
    template=template,
    sections=sections,
)
```

**Step 2: 修改 `/templates` 接口**

在 `get_templates()` 中，为每个模板补充 `chart_slots` 字段：

```python
templates = [
    {
        'id': 'brief',
        'name': '简报',
        'description': '精简版报告，仅包含核心数据',
        'sections': ['summary', 'sentiment'],
        'chart_slots': ['sentiment_pie'],
    },
    {
        'id': 'standard',
        'name': '标准报告',
        'description': '包含数据概览、情感分析、热门话题、预警记录',
        'sections': ['summary', 'sentiment', 'topics', 'alerts'],
        'chart_slots': ['sentiment_pie', 'topics_bar', 'alert_bar'],
    },
    {
        'id': 'detailed',
        'name': '详细报告',
        'description': '完整版报告，包含所有分析内容',
        'sections': ['summary', 'sentiment', 'topics', 'alerts', 'trend'],
        'chart_slots': ['sentiment_pie', 'topics_bar', 'alert_bar', 'trend_line'],
    },
]
```

**Step 3: 提交**

```bash
git add src/views/api/report_api.py
git commit -m "feat(report): pass template/sections through API, add chart_slots to templates"
```

---

### Task 6: 修改前端 report.vue 模板联动 sections

**Files:**
- Modify: `frontend/src/views/system/report.vue`

**Step 1: 修改模板选择逻辑**

在 `<script setup>` 中，监听 `reportForm.value.template` 变化，自动同步 `sections`：

```js
import { ref, onMounted, watch } from 'vue'

// 模板选择后自动同步 sections
watch(() => reportForm.value.template, (templateId) => {
  const tpl = templates.value.find(t => t.id === templateId)
  if (tpl) {
    reportForm.value.sections = [...tpl.sections]
  }
})
```

**Step 2: 修改 `handleGenerate` 请求体**

```js
const res = await generateReport({
  title: reportForm.value.title,
  format: reportForm.value.format,
  template: reportForm.value.template,   // 新增
  sections: reportForm.value.sections,   // 新增
  data: demoData.value
})
```

**Step 3: 提交**

```bash
git add frontend/src/views/system/report.vue
git commit -m "feat(report): template selection auto-syncs sections checkboxes"
```

---

### Task 7: 更新 TODO.md 标记完成

**Files:**
- Modify: `docs/TODO.md`

将 `2.3 PDF/PPT报告增强` 下的两个子项标记为完成：

```markdown
### 2.3 PDF/PPT报告增强 ✅（2026-02-21 完成）
- [x] 图表嵌入功能（matplotlib 渲染 4 种图表）
- [x] 报告模板系统（简报/标准/详细 3 套预设模板）
```

**Step 1: 提交**

```bash
git add docs/TODO.md
git commit -m "docs: mark TODO 2.3 PDF/PPT report enhancement as complete"
```

---

## 验收标准

1. `pytest tests/test_chart_renderer.py` — 6 passed
2. `pytest tests/test_report_generator.py` — 3 passed
3. 生成 PDF 文件大小 > 原来（含图表）
4. 前端选择"简报"模板后，sections 自动变为 `['summary', 'sentiment']`
5. 全量测试无回归：`pytest tests/ -v`

