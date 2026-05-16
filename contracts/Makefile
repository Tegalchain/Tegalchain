.PHONY: build test optimize deploy

build:
	for d in $(shell ls -d ./*/ | grep -v scripts | sed 's/^\.\///' | sed 's/\///g'); do \
		cd $$d && if [ -f Cargo.toml ]; then cargo wasm || true; fi; cd - >/dev/null; \
	done

test:
	for d in $(shell ls -d ./*/ | grep -v scripts | sed 's/^\.\///' | sed 's/\///g'); do \
		cd $$d && if [ -f Cargo.toml ]; then cargo test || true; fi; cd - >/dev/null; \
	done

optimize:
	# Requires cosmwasm-optimize in PATH
	for d in $(shell ls -d ./*/ | grep -v scripts | sed 's/^\.\///' | sed 's/\///g'); do \
		cd $$d && if [ -f Cargo.toml ]; then cosmwasm-optimize || true; fi; cd - >/dev/null; \
	done

deploy:
	./scripts/deploy-contracts.sh
