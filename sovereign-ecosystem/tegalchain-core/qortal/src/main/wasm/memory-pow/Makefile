# Use GNU make

# For FreeBSD 12. Probably comment these out for Linux, MacOS, etc.
CLANG=/usr/local/llvm-devel/bin/clang
LLVM_DWARFDUMP=/usr/local/llvm-devel/bin/llvm-dwarfdump
WASM_SOURCEMAP_PY=/usr/local/lib/emscripten/tools/wasm-sourcemap.py


.PHONY: all
all: memory-pow memory-pow.wasm test.wasm

clean:
	rm -f memory-pow *.wasm*

%.wasm.full: %.c Makefile
	${CLANG} -g -Os --target=wasm32 --no-standard-libraries -Wl,--export-all -Wl,--no-entry -Wl,--import-memory -o $@ $<

%.wasm.dwarf: %.wasm.full
	${LLVM_DWARFDUMP} $< > $@

%.wasm: %.wasm.full %.wasm.dwarf
	${WASM_SOURCEMAP_PY} -w $@ --sources --prefix $(CURDIR) --source-map-url http://localhost:8080/$(@:.wasm=.wasm.map) --output $(@:.wasm=.wasm.map) --dwarfdump-output $(@:.wasm=.wasm.dwarf) $<

memory-pow: memory-pow-main.c memory-pow.c
	cc -Os -g -L/usr/local/lib -o memory-pow memory-pow-main.c -lssl -lcrypto

emrun:
	emrun  --no_browser --port 8080 .
