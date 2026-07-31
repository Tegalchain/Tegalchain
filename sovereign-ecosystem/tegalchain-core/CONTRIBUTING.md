# Contributing to Tegalchain

Thank you for contributing! This file explains how to contribute to the project across the Go, Python and Rust (CosmWasm) stacks.

Getting started
- Fork the repo and create a feature branch using prefixes: `feature/`, `bugfix/`, `docs/`.
- Follow commit message guidelines: Conventional Commits recommended (feat, fix, chore, docs, test).

Development stacks
- Rust / CosmWasm contracts: see `contracts/DEVELOPMENT.md`.
- Go services (Cosmos SDK modules & consensus): standard Go modules, `go test`.
- Python services (telemetry/analytics): use virtualenv, run tests with pytest.

Testing & CI
- Run unit tests for each stack before submitting a PR.
- Linting: `golangci-lint` for Go, `clippy` and `cargo fmt` for Rust, `black`/`flake8` for Python.

Pull request process
- Open a PR against `master` with a clear description and link to any related issues.
- Include tests and a short description of the impact on PoR scoring if applicable.
- At least one maintainer review required; major changes may require a security review and audit.

Roles & pathways
- PoRE Evidence Provider: telemetry data integrator (Python/IoT)
- PoREF Validator: validator operator (Go + governance)
- PoREX Market Maker: contract & market operator (Rust)

Security & audits
- All smart contracts must include unit tests and integration test coverage.
- Major contract changes require a formal audit before deployment to mainnet.

Thank you for helping build a regenerative future.