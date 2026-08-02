# Development — Contracts

## Setup

1. Install Rust (stable) and wasm target:

   ```bash
   ./scripts/install-rust.sh
   ```

   Works on Replit and WSL (curl + rustup).

2. From `contracts/` run:

   ```bash
   make test    # unit tests
   make build   # wasm32 artifacts per crate
   ```

## Workspace

- Root `Cargo.toml` is the workspace (currently **`tx-tel` only**).
- Add sibling crates when scaffolding the next tX*; keep unused planned names out of `members` until crates exist.

## Best practices

- Keep instantiate/execute/query interfaces minimal.
- Enforce PoREX gates on-chain (do not trust client-only checks).
- Admin/oracle minter pattern for Phase 7 lab; rotate minter via `UpdateMinter`.
- Include unit tests that cover pass/fail gate boundaries.
