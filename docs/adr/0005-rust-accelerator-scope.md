# 0005 Rust 加速核：范围与 FFI 边界

## 状态
Accepted (2026-10-15, M7-0 scaffold)；#98/#104/#108 修订（见“补充决策”）。

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

## 补充决策（#104 实测后，2026-10-16）
- **canonical 语义只有一个**：`*_py` 是唯一权威定义，Rust 必须逐 code point 等价，不得"更合理地"解释。“等价”指 CPython 的实际行为，不是 Unicode 规范行为——CPython `str.split()` 的空白集是 Unicode `White_Space` **加上** U+001C–U+001F（bidi class `S`，规范刻意排除），Rust `char::is_whitespace` 只等于 `White_Space`。这是 #104 的根因，已在 `rust/weibo_core/src/text.rs` 用显式谓词修正并双向穷举验证。
- **批量输入只消费一次**：适配层在进入 FFI **之前**把一次性 iterable 物化成 list；Rust 抛错时 fallback 用同一份已保存输入回退。禁止在 `try` 内部消费、在 `except` 之后重新读取调用方 iterable——那会静默返回空批次。list 输入不额外复制。
- **parity 测试必须证明没走 fallback**：等价性测试需断言 native 路径未触发降级，否则“Rust 抛错 + Python 兜底”会让错误内核以正确结果的形式长期潜伏。
- **已知有界差异（不修）**：case 映射绑定 Unicode 数据版本。Rust 表比 CPython 3.12 新，55 个 CPython 仍视为未分配（`Cn`）的 code point 在 Rust 侧有小写映射。刻意不硬编码 deny-list：会在下次 CPython 升级时腐化，且会让含这些未分配码点的文本与其它 Python 消费者行为不一致。已穷举确认这 55 个是全部差异。

## 补充决策（#108 复核后，2026-10-17）
- **工具链固定生效（已实现事实）**：pin 文件更名 `rust/toolchain.toml` → `rust/rust-toolchain.toml`（rustup 只识别后者）。实测：`rustup show` 在 `rust/` 与 `rust/weibo_core/` 均报 `overridden by .../rust/rust-toolchain.toml`；把文件暂时移开则回落为 `it's the default toolchain`（A/B 对照）。CI 的 rust-core job 因此自动使用 1.99.0 + rustfmt/clippy，不再依赖 runner 全局默认。
- **当前单 crate、为何暂不拆（已实现事实 + 边界）**：Rust 侧只有 `rust/weibo_core` 一个 crate；maturin 配置（`rust/weibo_core/pyproject.toml`）只管理这一个可选扩展，根 Flask 包的构建/运行依赖不受影响（maturin/cargo 不进根 requirements）。暂不拆的理由：目前只有一组 FFI 函数与一个 abi3 产物，拆 crate 只会增加版本对齐/编译/发布协调成本，收益为零。**多 crate 触发条件**（满足其一再评估，需走门禁）：出现第二个独立可发布的扩展单元；crate 编译时间或依赖图显著分叉；需要独立 ABI/发布矩阵。
- **wheel 本地构建/安装、不自动发布（已实现事实 + 未决边界）**：`maturin develop --release` 与 `maturin build --release` + 本地 pip 安装均已实测（Linux/WSL；macOS/Windows 未实测）。**不自动发布 PyPI**；任何发布动作（含 CI 自动上传制品）需 Planner/用户明确批准。跨版本 CI 与 artifact 归 #102（当前未授权、未实施）。
- **事实与授权分离**：本节只记录已落地事实与待决边界；ADR 的 Accepted 状态不构成对 M7 新切片/新服务/重大 CI 扩展的用户授权（D-019 pending，D-018 约束维持）。

## 相关
- Issue #96 (epic), #97 (M7-0), #98 (M7-1, benchmarks), #99..#103, #104 (parity 修正), #108 (pin/打包/边界).
