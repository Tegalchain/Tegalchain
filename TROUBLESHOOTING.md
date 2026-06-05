# Tegalchain Build Troubleshooting Guide

## Quick Reference

### Environment Specs
- **Go**: 1.26.3
- **Ignite CLI**: v0.29.10  
- **Rust**: 1.96.0
- **Cosmos SDK**: v0.53.6
- **Buf**: v1.70.0

### Common Error Messages & Fixes

#### ❌ "go: command not found"
**Solution:**
```bash
export PATH=~/go/bin:$PATH
export GOROOT=~/go
go version  # Should show: go version go1.26.3 linux/amd64
```

#### ❌ "ignite: command not found"
**Solution:**
```bash
export PATH=~/.ignite/bin:$PATH
ignite version  # Should show: v0.29.10
```

#### ❌ "undefined: AccAddress" or "undefined: sdk.AccAddress"
**Root Cause:** Incorrect import path in `.go` files

**Bad:**
```go
import "github.com/cosmos/cosmos-sdk/types/sdk.AccAddress"
```

**Good:**
```go
import sdk "github.com/cosmos/cosmos-sdk/types"
// Then use: sdk.AccAddress
```

**Auto-Fix:**
```bash
python fix_tegalchain_imports.py /content/tegalchain
```

#### ❌ "go: github.com/cosmos/cosmos-sdk@v0.53.6 used for two different module paths"
**Root Cause:** Multiple replace directives in go.mod

**Check:**
```bash
grep "^replace.*cosmos" /content/tegalchain/go.mod
```

**Fix:** Keep only ONE replace directive:
```go
replace (
    cosmossdk.io/cosmos-sdk => github.com/cosmos/cosmos-sdk v0.53.6
)
```

#### ❌ "conflicting imports" or "redeclared"
**Solution:** Consolidate import block - no duplicate imports

**Bad:**
```go
import (
    sdk "github.com/cosmos/cosmos-sdk/types"
    "github.com/cosmos/cosmos-sdk/types"  // DUPLICATE!
)
```

**Good:**
```go
import (
    sdk "github.com/cosmos/cosmos-sdk/types"
)
```

---

## Detailed Diagnostic Steps

### Step 1: Check All Tool Versions
```bash
#!/bin/bash
echo "=== Environment Check ==="
echo "Go: $(go version)"
echo "Rust: $(rustc --version)"
echo "Ignite: $(ignite version | head -1)"
echo "Buf: $(buf --version)"

echo -e "\n=== Environment Variables ==="
echo "GOROOT: $GOROOT"
echo "GOPATH: $GOPATH"
echo "Which go: $(which go)"
echo "Which ignite: $(which ignite)"
```

### Step 2: Verify Go Modules
```bash
cd /content/tegalchain

# Check module integrity
go mod verify

# Clean cache if issues exist
go clean -modcache

# Update dependencies
go mod tidy
```

### Step 3: Scan for Import Issues
```bash
# Find incorrect AccAddress imports
grep -r "types/sdk\.AccAddress" /content/tegalchain/x/

# Find all imports in a file
go list -f '{{join .Imports "\n"}}' ./x/telemetry/types
```

### Step 4: Check go.mod Configuration
```bash
cd /content/tegalchain

# Show module info
head -20 go.mod

# Check specific dependency
go list -m github.com/cosmos/cosmos-sdk

# Show why a module is included
go mod why github.com/cosmos/cosmos-sdk
```

---

## Build Process

### Clean Build
```bash
cd /content/tegalchain

# Clean everything
go clean -testcache
go clean -cache
go clean -modcache

# Tidy modules
go mod tidy

# Build
ignite chain build
```

### Verbose Build (for debugging)
```bash
cd /content/tegalchain
ignite chain build -v
```

### Build Single Module (to isolate errors)
```bash
cd /content/tegalchain
go build ./x/telemetry/types
go build ./x/txassets/types
```

---

## Specific Error Messages & Solutions

### Error: "cannot find package"
```
go: github.com/some/package: module github.com/some/package not found
```
**Fix:**
```bash
# Check if import path is correct in code
grep -r "github.com/some/package" /content/tegalchain/

# Add to go.mod if legitimate
go get github.com/some/package
```

### Error: "invalid version: unknown revision"
```
go: github.com/cosmos/cosmos-sdk@v0.53.6: invalid version: unknown revision
```
**Fix:**
```bash
# Clear mod cache
go clean -modcache

# Verify version exists
go list -m github.com/cosmos/cosmos-sdk@v0.53.6

# Update go.mod
go mod tidy
```

### Error: "compilation fails with cryptic message"
**Diagnostic:**
```bash
# Check specific file compilation
go build -v github.com/Tegalchain/tegalchain/x/telemetry/types 2>&1 | head -50

# Check all imports in file
go list -f '{{join .Imports "\n"}}' ./x/telemetry/types

# List files with issues
find ./x -name "*.go" -exec grep -l "AccAddress" {} \;
```

---

## Python Diagnostic Tools

### Run Comprehensive Diagnostics
```python
import subprocess
import os

os.chdir('/content/tegalchain')

# Verify all tools
tools = {
    'go': 'go version',
    'ignite': 'ignite version',
    'rust': 'rustc --version',
    'buf': 'buf --version'
}

for name, cmd in tools.items():
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"{name}: {result.stdout.strip()}")

# Check go.mod
with open('go.mod', 'r') as f:
    lines = f.readlines()
    print("\nFirst 30 lines of go.mod:")
    for line in lines[:30]:
        print(line.rstrip())
```

### Auto-Fix Imports
```python
import subprocess
result = subprocess.run(['python', 'fix_tegalchain_imports.py', '/content/tegalchain'])
print("Fix complete" if result.returncode == 0 else "Fix failed")
```

---

## PATH Prioritization (Critical!)

### Correct ORDER for Colab
```python
import os

custom_paths = [
    '/root/go/bin',              # Your Go (PRIORITY)
    '/root/.ignite/bin',         # Your Ignite
    '/root/.cargo/bin',          # Your Rust
    '/usr/local/bin',            # System tools (buf)
    # ... other paths
]

# EXCLUDE: /usr/local/go/bin (conflicts with custom Go)
os.environ['PATH'] = ':'.join(custom_paths) + ':' + os.environ.get('PATH', '')
```

---

## Success Indicators

✓ All tools show correct versions  
✓ `go mod verify` passes without errors  
✓ `go mod tidy` doesn't report issues  
✓ No "undefined: " compilation errors  
✓ No "conflicting imports" errors  
✓ Build completes: `ignite chain build`  
✓ Binary exists: `ls -la cmd/tegalchaind/`

---

## Need More Help?

1. **Run diagnostics script:**
   ```bash
   python diagnose_tegalchain.py
   ```

2. **Check the fixed notebook:**
   - Open `Tegalchain_Blockchain_Genesis_FIXED.ipynb` in Colab

3. **Run fix script:**
   ```bash
   python fix_tegalchain_imports.py /content/tegalchain
   ```

4. **Share your error output** with:
   - `go version`
   - `ignite version`
   - First 50 lines of `go.mod`
   - Error message from failed build
