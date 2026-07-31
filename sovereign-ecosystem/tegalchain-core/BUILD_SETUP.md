# Tegalchain Build Setup - Complete Guide

## Quick Links

- 📓 **Setup Notebook**: [Tegalchain_Blockchain_Genesis_FIXED.ipynb](Tegalchain_Blockchain_Genesis_FIXED.ipynb)
- 🔧 **Import Fixer**: [fix_tegalchain_imports.py](fix_tegalchain_imports.py)
- 📚 **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## Overview

This guide helps you set up and build Tegalchain in Google Colab with the correct environment specifications.

### Environment Specifications

| Tool | Version | Status |
|------|---------|--------|
| Go | 1.26.3 | ✓ Required |
| Ignite CLI | v0.29.10 | ✓ Required |
| Rust | 1.96.0 | ✓ Required |
| Cosmos SDK | v0.53.6 | ✓ Required |
| Buf | v1.70.0 | ✓ Required |

---

## 🚀 Quick Start (5 minutes)

### Option 1: Use the Fixed Notebook (Recommended)

1. **Open in Google Colab:**
   ```
   https://colab.research.google.com/github/Tegalchain/Tegalchain/blob/master/Tegalchain_Blockchain_Genesis_FIXED.ipynb
   ```

2. **Run the sections in order:**
   - Section 1: Initial verification
   - Section 2: Install Go, Rust, Ignite, Buf
   - Section 3: Configure environment
   - Section 4: Verify installation
   - Section 5: Download Tegalchain
   - Section 6: Fix imports
   - Section 7: Verify go.mod
   - Section 8: Build
   - Section 9: Diagnostics

### Option 2: Manual Setup

```bash
# In Colab cell:

# Install Go 1.26.3
cd ~
curl -L https://go.dev/dl/go1.26.3.linux-amd64.tar.gz | tar xz

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
rustup target add wasm32-unknown-unknown

# Install Ignite CLI v0.29.10
mkdir -p ~/.ignite/bin
curl -L https://github.com/ignite/cli/releases/download/v0.29.10/ignite_0.29.10_linux_amd64.tar.gz | tar xz -C ~/.ignite/bin

# Setup PATH
export PATH=~/go/bin:~/.ignite/bin:~/.cargo/bin:/usr/local/bin:$PATH
export GOROOT=~/go
export GOPATH=~/go

# Verify
go version      # Should be: go1.26.3
ignite version  # Should be: v0.29.10
rustc --version # Should be: 1.96.0
```

---

## 📋 Build Process

### Step 1: Verify Environment
```bash
go version
ignite version
rustc --version
buf --version
```

✓ All should match the versions above.

### Step 2: Fix Import Paths
```bash
cd /content/tegalchain
python fix_tegalchain_imports.py
```

This automatically:
- Removes incorrect `AccAddress` imports
- Consolidates import blocks
- Validates `go.mod`

### Step 3: Verify Go Modules
```bash
cd /content/tegalchain
go mod verify  # Should pass without errors
go mod tidy    # Should complete cleanly
```

### Step 4: Build
```bash
cd /content/tegalchain
ignite chain build
```

✓ Build completes successfully if all previous steps passed.

---

## 🔍 Troubleshooting

### Common Issues & Fixes

#### ❌ "go: command not found"
```bash
export PATH=~/go/bin:$PATH
go version
```

#### ❌ "undefined: AccAddress"
```bash
cd /content/tegalchain
python fix_tegalchain_imports.py
```

#### ❌ "module conflicts in go.mod"
```bash
cd /content/tegalchain
go mod tidy
go mod verify
```

#### ❌ "ignite: command not found"
```bash
export PATH=~/.ignite/bin:$PATH
ignite version
```

**For detailed solutions, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

---

## 📊 What Each File Does

### Tegalchain_Blockchain_Genesis_FIXED.ipynb
9-section Jupyter notebook that:
- ✓ Installs all tools with correct versions
- ✓ Configures environment variables properly
- ✓ Fixes import path issues
- ✓ Validates go.mod
- ✓ Builds Tegalchain
- ✓ Runs diagnostics

**Use this if:**
- You're new to Tegalchain
- You want automated setup
- You're in Google Colab

### fix_tegalchain_imports.py
Standalone Python script that:
- ✓ Removes incorrect `AccAddress` imports
- ✓ Consolidates import blocks
- ✓ Adds correct imports
- ✓ Validates go.mod replace directives

**Use this if:**
- You already have tools installed
- You need to fix import issues
- You want to run it separately

### TROUBLESHOOTING.md
Comprehensive reference guide with:
- ✓ Common error messages
- ✓ Specific fixes for each error
- ✓ Diagnostic commands
- ✓ Success indicators
- ✓ Detailed PATH configuration

**Use this if:**
- You encounter errors
- You need to debug issues
- You want detailed explanations

---

## ✅ Success Checklist

Before running `ignite chain build`, verify:

- [ ] `go version` shows go1.26.3
- [ ] `ignite version` shows v0.29.10
- [ ] `rustc --version` shows 1.96.0
- [ ] `buf --version` shows 1.70.0
- [ ] `go mod verify` passes
- [ ] `go mod tidy` completes without errors
- [ ] No import errors when scanning files
- [ ] go.mod has only ONE cosmos-sdk replace directive

---

## 🔧 Environment Variables (Critical!)

Make sure these are set in Colab:

```python
import os

HOME = os.path.expanduser("~")

# Set these variables
os.environ['PATH'] = f"{HOME}/go/bin:{HOME}/.ignite/bin:{HOME}/.cargo/bin:/usr/local/bin:/usr/bin:/bin"
os.environ['GOROOT'] = f"{HOME}/go"
os.environ['GOPATH'] = f"{HOME}/go"
os.environ['CARGO_HOME'] = f"{HOME}/.cargo"
os.environ['GO111MODULE'] = 'on'
os.environ['CGO_ENABLED'] = '0'
```

**Critical:** PATH order must prioritize `~/go/bin` BEFORE system paths to avoid conflicts.

---

## 📝 Typical Colab Workflow

### In Google Colab:

**Cell 1:** Clone/update repo
```python
import subprocess
import os

os.chdir('/content')
if not os.path.exists('tegalchain'):
    subprocess.run(['git', 'clone', 'https://github.com/Tegalchain/Tegalchain.git', 'tegalchain'])
```

**Cell 2:** Set up environment (copy from notebook Section 3)

**Cell 3:** Install tools (copy from notebook Sections 2)

**Cell 4:** Fix imports
```python
os.chdir('/content/tegalchain')
subprocess.run(['python', 'fix_tegalchain_imports.py'])
```

**Cell 5:** Verify and build
```python
os.chdir('/content/tegalchain')
result = subprocess.run(['ignite', 'chain', 'build'], env=os.environ.copy())
print(f"Build {'succeeded' if result.returncode == 0 else 'failed'}")
```

---

## 🎯 Key Improvements Over Original Setup

| Issue | Original | Fixed |
|-------|----------|-------|
| PATH conflicts | ✗ Mixed system/custom Go | ✓ Prioritizes custom Go |
| Import errors | ✗ Not addressed | ✓ Auto-fixed |
| go.mod validation | ✗ Limited | ✓ Comprehensive |
| Error messages | ✗ Generic | ✓ Specific with fixes |
| Environment setup | ✗ Manual | ✓ Automated |
| Build reliability | ✗ Often fails | ✓ Consistent success |

---

## 📞 Support

### If you encounter issues:

1. **Check TROUBLESHOOTING.md** for your specific error
2. **Run diagnostics:**
   ```bash
   python diagnose_tegalchain.py
   ```
3. **Verify all versions:** Follow the "Success Checklist" above
4. **Share error output:** Include full error message + `go version` + `ignite version`

---

## 📚 Additional Resources

- [Ignite CLI Documentation](https://docs.ignite.com/)
- [Cosmos SDK v0.53.6 Docs](https://docs.cosmos.network/v0.53/)
- [Go 1.26.3 Release Notes](https://go.dev/doc/go1.26)
- [Rust WebAssembly Guide](https://www.rust-lang.org/what/wasm/)

---

## 🏁 What's Next?

After successful build:

1. **Explore Tegalchain modules:**
   ```bash
   ls -la /content/tegalchain/x/
   ```

2. **Review smart contracts:**
   ```bash
   ls -la /content/tegalchain/contracts/
   ```

3. **Start local testnet:**
   ```bash
   ignite chain serve
   ```

4. **Read documentation:**
   - [CONTRIBUTING.md](CONTRIBUTING.md)
   - [docs/](docs/)
   - [contracts/DEVELOPMENT.md](contracts/DEVELOPMENT.md)

---

**Happy building! 🚀**

For questions or issues, refer to [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or check the [GitHub Issues](https://github.com/Tegalchain/Tegalchain/issues).
