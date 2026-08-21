# 显式应用工厂：import 无副作用

原 `src/app.py` 在模块导入时即完成目录创建、日志配置、配置校验、蓝图装配与后台预热调度，导致 `import app` 自带副作用且 `gunicorn -w N` 每 worker 重复引导。改为显式工厂 `create_app()`，导入无副作用，急切构造仅发生在组合根（`run.py` 及后续 worker 入口）；否决了 `lazy proxy` 方案，因其仅将副作用延迟至首次属性访问，并未消除。已知多 worker 重复引导暂保留现状、仅记录为可观测的 `启动状态`。
