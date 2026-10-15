#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../rust/weibo_core"
export PATH="${HOME}/.cargo/bin:${PATH}"
python -m maturin develop --release
