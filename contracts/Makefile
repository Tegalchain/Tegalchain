.PHONY: build test optimize deploy install-rust

install-rust:
	./scripts/install-rust.sh

build:
	@if [ ! -f Cargo.toml ]; then echo "ERROR: run from contracts/"; exit 1; fi
	CARGO_TARGET_DIR=$${CARGO_TARGET_DIR:-$(CURDIR)/target} \
		cargo build --release --target wasm32-unknown-unknown -p tx-tel

test:
	@if [ ! -f Cargo.toml ]; then echo "ERROR: run from contracts/"; exit 1; fi
	CARGO_TARGET_DIR=$${CARGO_TARGET_DIR:-$(CURDIR)/target} \
		cargo test -p tx-tel

optimize:
	@echo "Requires docker + cosmwasm/optimizer (optional for lab)"
	@echo "  docker run --rm -v \"\$$(pwd)\":/code cosmwasm/optimizer:0.16.0"
	@false

deploy:
	./scripts/deploy-contracts.sh
