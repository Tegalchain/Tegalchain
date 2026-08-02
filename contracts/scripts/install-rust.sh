#!/usr/bin/env bash
# Install Rust toolchain + wasm32 target (Replit / WSL / Linux).
set -euo pipefail

export CARGO_HOME="${CARGO_HOME:-$HOME/.cargo}"
export RUSTUP_HOME="${RUSTUP_HOME:-$HOME/.rustup}"
export PATH="${HOME}/.local/bin:${CARGO_HOME}/bin:${PATH}"

if ! command -v rustup >/dev/null 2>&1; then
  echo "==> Installing rustup (stable)"
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
fi

# shellcheck disable=SC1091
source "${CARGO_HOME}/env"

rustup default stable
rustup target add wasm32-unknown-unknown

# Host C compiler for cargo build-scripts (proc-macros). Prefer system gcc/clang.
if ! command -v cc >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    echo "==> No cc on PATH — install build-essential if you can:"
    echo "    sudo apt-get install -y build-essential"
  fi
  echo "WARN: cargo unit tests need a C linker named 'cc'."
fi

echo "OK: $(rustc --version)"
echo "OK: wasm32-unknown-unknown $(rustup target list --installed | grep wasm32 || true)"
