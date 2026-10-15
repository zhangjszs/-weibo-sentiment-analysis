# 可观测性：OpenTelemetry tracing + metrics (#99)

> 默认关闭、零开销；`OTEL_ENABLED=1` 显式启用。失败永远降级为无观测，
> 绝不阻断启动与请求。

## 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `OTEL_ENABLED` | `0` | `1/true/yes/on` 启用 |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4318` | OTLP HTTP 端点；`console` 输出到 stdout（本地演示/测试） |
| `OTEL_SERVICE_NAME` | `weibo-sentiment-analysis` | service 名称 |

## 本地演示（无 Docker 也可跑）

```bash
OTEL_ENABLED=1 OTEL_EXPORTER_OTLP_ENDPOINT=console \
  .venv/bin/python scripts/demo_otel_trace.py   # 或见下 trace 样本
```

实测输出样本：`docs/observability/trace-sample.txt`（span `GET /ping` +
`weibo.sentiment.analyze.count` / `weibo.sentiment.analyze.duration`），
由 `tests/test_observability.py` 的子进程探针逐行断言。

```json
{
    "name": "GET /ping",
    "kind": "SpanKind.SERVER",
    "attributes": {
        "http.method": "GET",
        "http.route": "/ping",
        "http.status_code": 200
    }
}
```

## Docker 全链路（Jaeger）

```bash
docker compose --profile observability up -d jaeger otel-collector
OTEL_ENABLED=1 OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 \
  gunicorn -w 2 -b 0.0.0.0:5000 run:app
# 打开 http://localhost:16686，service 选 weibo-sentiment-analysis
```

数据流：app —OTLP/HTTP→ collector（`docs/observability/otelcol-config.yaml`）
—OTLP/gRPC→ Jaeger。直连 Jaeger（跳过 collector）同样可用：
endpoint 保持 `http://localhost:4318`（Jaeger 原生收 OTLP/HTTP）。

> 说明：本机无 Docker，Jaeger UI 截图待有 Docker 的环境补
> （console exporter 输出已实测入库，见上）。

## 代码接入点

- `src/utils/observability.py`：`init_otel(app)`（幂等；缺包/异常一律降级）、
  `observe_sentiment_analysis(mode, duration_ms, ok)`（counter + histogram，
  默认 no-op）、`get_tracer()`。
- `src/app.py::create_app`：建 Flask 实例后即 `init_otel(app)`（5 行，try 包裹）。
- `src/views/api/ml_routes.py::analyze_sentiment`：同步分析计时并记录
  `weibo.sentiment.analyze.*`（失败走原有 except，不污染错误语义）。
- 自动埋点：`FlaskInstrumentor.instrument_app` 覆盖 `/health`、`/ready`、
  `/api/sentiment/analyze`、bigscreen `/api/bigscreen/*` 等全部路由。
  未做 `requests` 全局 patch（避免影响爬虫/测试），如需出站 span 另立 issue。

## 测试

`tests/test_observability.py`（unit）：默认关闭断言 + 子进程端到端
（console exporter：span JSON 可解析、counter/histogram 出现、mode 属性）。
Enabled 路径刻意放在子进程，避免给 gate 进程安装全局 provider
（否则每个后续请求都同步导出 span，拖慢门禁）。

## 指标一览

- `weibo.sentiment.analyze.count`（counter，attrs: `mode`, `ok`）
- `weibo.sentiment.analyze.duration`（histogram，ms，attrs: `mode`, `ok`）
- Flask 自带：`http.server.duration`、`http.server.active_requests`
