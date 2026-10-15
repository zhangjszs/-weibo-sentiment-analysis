# 0005 Rust 加速核：范围与 FFI 边界

## 状态
Accepted (2026-10-15, M7-0 scaffold)；#98 修订（见“补充决策”）。

## 上下文
项目 M7 引入 Rust 加速核（`rust/weibo_core`，PyO3 + maturin）以降低文本预处理/去重/爬虫Normalize的CPU耗时并作为展示亮点，但不能破坏现有 Flask/SQLAlchemy/Celery/ORM 与测试基线。

## 决策
- **范围**：仅迁移纯函数/高 CPU/高调用频切片（去重、文本 normalize、HTML stripping），每次一垂直切片、带 criterion before/after。
- **不迁移**：ML 推理（torch/transformers/onnxruntime 留 Python）、ORM/数据库、爬虫 HTTP/会话管理。
- **FFI 边界**：所有 Rust 入口函数 (1) 接收 `&str`/基本类型，不做 Python 对象长期借用；(2) 用 `catch_unwind` 把 panic 转成 `PyErr`，禁止 panic 跨 FFI；(3) 对不可恢复输入返回错误而非 panic；(4) 不持有 GIL 之外的状态；(5) 支持无 Rust 构建（Python fallback）。
- **接入方式**：Python 适配层 `src/services/rust_bridge`，env gate `WEIBO_CORE_RUST=0|1`，默认探测；缺失时 fallback 到 Python；CI 两条路径（有/无 Rust）均跑契约测试。
- **构建**：maturin abi3-py3.11 wheel，Python 3.11/3.12 都能装； contributions 可选安装。
- **版本**：crate 版本与 Python 包 minor 版本对齐；每次迁移新切片 bump 微版本。

## 后果
- CI 增加 rust-core job（fmt/clippy/test/maturin build）；导出的 wheel 不入 main 依赖，按 opt-in 安装。
- 测试基线（1460 unit/api）保持 100% 绿；bridge 函数必须在两 impl 下相等。

## 补充决策（#98 实测后，2026-10-15）
- **切片选择规则收紧**：薄字符串 op（`str.lower/split/join`、set 去重这类 CPython 已是 C 速度的）不迁——实测 per-item FFI ~0.66x、batch ~0.9x、dedup ~0.4x（marshaling 主导，数据见 `docs/benchmarks/m7-1-dedup.md`）。后续切片必须先 profile，目标锁定“Rust 自有 buffer 上的重计算”或“纯 Python 慢循环”。
- **批量优先**：凡跨 FFI 的批量数据一律走单次调用 API（如 `normalize_posts`），逐条调用只保留作兼容。
- **版本**：首个真实切片落地即 bump 到 0.2.0（已执行）；规则不变。

## 相关
- Issue #96 (epic), #97 (M7-0), #98 (M7-1, benchmarks), #99..#103.
