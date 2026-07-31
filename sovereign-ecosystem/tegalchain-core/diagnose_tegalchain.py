#!/usr/bin/env python3
"""
Tegalchain Comprehensive Diagnostics Script
==========================================

Performs detailed diagnostics on Tegalchain setup and provides specific recommendations.

Usage:
    python diagnose_tegalchain.py [--project-root /path/to/tegalchain]
"""

import subprocess
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple


class TegalchainDiagnostics:
    """Comprehensive diagnostics for Tegalchain setup."""
    
    REQUIRED_VERSIONS = {
        'go': '1.26.3',
        'ignite': '0.29.10',
        'rust': '1.96.0',
        'cosmos_sdk': '0.53.6',
        'buf': '1.70.0'
    }
    
    def __init__(self, project_root: str = '/content/tegalchain'):
        self.project_root = Path(project_root)
        self.results: Dict[str, Dict] = {}
        self.issues: List[Dict] = []
        
    def run_command(self, cmd: str, timeout: int = 30) -> Tuple[int, str, str]:
        """Run command and return (return_code, stdout, stderr)."""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, '', 'Command timeout'
        except Exception as e:
            return -1, '', str(e)
    
    def check_tool_version(self, tool_name: str, cmd: str, version_key: str) -> Dict:
        """Check if tool is installed and correct version."""
        expected = self.REQUIRED_VERSIONS.get(version_key)
        returncode, stdout, stderr = self.run_command(cmd)
        
        output = stdout + stderr
        installed = returncode == 0
        correct_version = installed and (expected in output if expected else True)
        
        result = {
            'tool': tool_name,
            'installed': installed,
            'expected_version': expected,
            'actual_output': output.split('\n')[0][:100] if output else 'N/A',
            'correct_version': correct_version,
            'status': 'OK' if correct_version else ('WRONG_VERSION' if installed else 'MISSING')
        }
        
        return result
    
    def check_environment(self) -> Dict:
        """Check environment variables."""
        result = {
            'goroot': os.environ.get('GOROOT', 'NOT_SET'),
            'gopath': os.environ.get('GOPATH', 'NOT_SET'),
            'cargo_home': os.environ.get('CARGO_HOME', 'NOT_SET'),
            'go111module': os.environ.get('GO111MODULE', 'NOT_SET'),
            'cgo_enabled': os.environ.get('CGO_ENABLED', 'NOT_SET'),
        }
        
        # Check PATH
        path = os.environ.get('PATH', '').split(os.pathsep)
        result['path_entries'] = len(path)
        result['has_go_bin'] = any('go/bin' in p for p in path)
        result['has_ignite_bin'] = any('ignite' in p for p in path)
        result['has_local_go'] = any('/usr/local/go/bin' in p for p in path)
        result['path_priority'] = self._check_path_order(path)
        
        return result
    
    def _check_path_order(self, paths: List[str]) -> str:
        """Check if custom tools are prioritized over system tools."""
        go_custom_idx = next((i for i, p in enumerate(paths) if 'go/bin' in p and 'local' not in p), -1)
        go_system_idx = next((i for i, p in enumerate(paths) if '/usr/local/go/bin' in p), -1)
        
        if go_custom_idx >= 0 and (go_system_idx < 0 or go_custom_idx < go_system_idx):
            return "✓ Custom Go prioritized"
        elif go_system_idx >= 0:
            return "⚠ System Go prioritized (conflict risk)"
        return "OK"
    
    def check_gomod(self) -> Dict:
        """Analyze go.mod file."""
        gomod_path = self.project_root / 'go.mod'
        result = {
            'exists': gomod_path.exists(),
            'path': str(gomod_path),
            'issues': []
        }
        
        if not gomod_path.exists():
            return result
        
        try:
            with open(gomod_path, 'r') as f:
                content = f.read()
            
            # Check go version
            go_match = re.search(r'^go\s+([\d.]+)', content, re.MULTILINE)
            if go_match:
                result['go_version'] = go_match.group(1)
            
            # Check cosmos SDK version
            cosmos_match = re.search(r'github\.com/cosmos/cosmos-sdk\s+v([\d.]+)', content)
            if cosmos_match:
                result['cosmos_sdk_version'] = cosmos_match.group(1)
                if cosmos_match.group(1) != '0.53.6':
                    result['issues'].append('COSMOS_SDK_VERSION_MISMATCH')
            
            # Check replace directives
            replace_pattern = re.compile(r'^replace\s+([^\s]+)\s+=>\s+(.+)$', re.MULTILINE)
            replaces = replace_pattern.findall(content)
            result['replace_directives'] = len(replaces)
            
            cosmos_replaces = [r for r in replaces if 'cosmos' in r[0]]
            if len(cosmos_replaces) > 1:
                result['issues'].append('MULTIPLE_COSMOS_REPLACES')
            
            if 'module ' not in content:
                result['issues'].append('NO_MODULE_DECLARATION')
            
        except Exception as e:
            result['errors'] = str(e)
        
        return result
    
    def check_imports(self) -> Dict:
        """Check for import path issues."""
        issues_found = []
        files_scanned = 0
        
        bad_pattern = re.compile(r'"github\.com/cosmos/cosmos-sdk/types/sdk\.AccAddress"')
        
        try:
            x_dir = self.project_root / 'x'
            if x_dir.exists():
                for go_file in x_dir.rglob('*.go'):
                    files_scanned += 1
                    with open(go_file, 'r') as f:
                        content = f.read()
                        if bad_pattern.search(content):
                            issues_found.append({
                                'file': str(go_file.relative_to(self.project_root)),
                                'issue': 'INCORRECT_ACCADDRESS_IMPORT'
                            })
        except Exception as e:
            return {'error': str(e)}
        
        return {
            'files_scanned': files_scanned,
            'issues': issues_found,
            'has_import_issues': len(issues_found) > 0
        }
    
    def verify_go_modules(self) -> Dict:
        """Run go mod verify."""
        if not os.path.exists(self.project_root):
            return {'error': f'Project root not found: {self.project_root}'}
        
        os.chdir(self.project_root)
        returncode, stdout, stderr = self.run_command('go mod verify')
        
        return {
            'returncode': returncode,
            'status': 'OK' if returncode == 0 else 'FAILED',
            'output': (stdout + stderr).strip()[:500]
        }
    
    def run_diagnostics(self) -> bool:
        """Run all diagnostics."""
        print(f"\n{'='*80}")
        print("TEGALCHAIN BUILD DIAGNOSTICS")
        print(f"{'='*80}\n")
        
        # 1. Tool versions
        print("1. TOOL VERSIONS")
        print("-" * 80)
        tools = [
            ('Go', 'go version', 'go'),
            ('Ignite CLI', 'ignite version', 'ignite'),
            ('Rust', 'rustc --version', 'rust'),
            ('Buf', 'buf --version', 'buf'),
        ]
        
        for tool_name, cmd, version_key in tools:
            result = self.check_tool_version(tool_name, cmd, version_key)
            self.results[tool_name] = result
            
            status_icon = '✓' if result['correct_version'] else '✗' if not result['installed'] else '⚠'
            print(f"{status_icon} {tool_name}: {result['actual_output']}  [{result['status']}]")
            
            if not result['correct_version']:
                expected = result['expected_version']
                severity = 'ERROR' if not result['installed'] else 'WARNING'
                self.issues.append({
                    'severity': severity,
                    'component': tool_name,
                    'issue': f"Expected {expected}",
                    'resolution': f"Install {tool_name} version {expected}"
                })
        
        # 2. Environment
        print(f"\n2. ENVIRONMENT VARIABLES")
        print("-" * 80)
        env = self.check_environment()
        self.results['environment'] = env
        
        print(f"GOROOT: {env['goroot']}")
        print(f"GOPATH: {env['gopath']}")
        print(f"GO111MODULE: {env['go111module']}")
        print(f"CGO_ENABLED: {env['cgo_enabled']}")
        print(f"PATH entries: {env['path_entries']}")
        print(f"  {env['path_priority']}")
        print(f"  - Has /usr/local/go/bin: {env['has_local_go']}")
        
        if env['has_local_go'] and env['has_go_bin']:
            self.issues.append({
                'severity': 'WARNING',
                'component': 'PATH',
                'issue': 'Conflicting Go installations',
                'resolution': 'Ensure custom ~/go/bin is prioritized in PATH'
            })
        
        # 3. go.mod Analysis
        print(f"\n3. GO.MOD ANALYSIS")
        print("-" * 80)
        gomod = self.check_gomod()
        self.results['go.mod'] = gomod
        
        if gomod['exists']:
            print(f"✓ go.mod exists")
            print(f"  Go version: {gomod.get('go_version', 'N/A')}")
            print(f"  Cosmos SDK: {gomod.get('cosmos_sdk_version', 'N/A')}")
            print(f"  Replace directives: {gomod['replace_directives']}")
            
            for issue in gomod['issues']:
                print(f"  ⚠ {issue}")
                self.issues.append({
                    'severity': 'ERROR',
                    'component': 'go.mod',
                    'issue': issue,
                    'resolution': 'Run: go mod tidy && go mod verify'
                })
        else:
            print(f"✗ go.mod not found")
            self.issues.append({
                'severity': 'ERROR',
                'component': 'go.mod',
                'issue': 'Missing go.mod',
                'resolution': 'Clone Tegalchain repository'
            })
        
        # 4. Import Issues
        print(f"\n4. IMPORT ANALYSIS")
        print("-" * 80)
        imports = self.check_imports()
        self.results['imports'] = imports
        
        if 'error' not in imports:
            print(f"Files scanned: {imports['files_scanned']}")
            if imports['has_import_issues']:
                print(f"⚠ Found {len(imports['issues'])} files with import issues")
                for issue in imports['issues'][:3]:
                    print(f"  - {issue['file']}")
                
                self.issues.append({
                    'severity': 'ERROR',
                    'component': 'Imports',
                    'issue': f"{len(imports['issues'])} incorrect AccAddress imports",
                    'resolution': 'Run: python fix_tegalchain_imports.py'
                })
            else:
                print("✓ No import issues found")
        
        # 5. Go Modules
        print(f"\n5. GO MODULES VERIFICATION")
        print("-" * 80)
        if os.path.exists(self.project_root):
            verify = self.verify_go_modules()
            self.results['go_mod_verify'] = verify
            
            if verify['returncode'] == 0:
                print(f"✓ Go modules verified")
            else:
                print(f"✗ Go module verification failed")
                self.issues.append({
                    'severity': 'ERROR',
                    'component': 'Go Modules',
                    'issue': 'go mod verify failed',
                    'resolution': 'Run: go mod tidy && go mod verify'
                })
        
        # Summary
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}\n")
        
        errors = [i for i in self.issues if i['severity'] == 'ERROR']
        warnings = [i for i in self.issues if i['severity'] == 'WARNING']
        
        if not self.issues:
            print("✓✓✓ ALL CHECKS PASSED! ✓✓✓")
            print("\nYour environment is ready for building Tegalchain:")
            print("  cd /content/tegalchain")
            print("  ignite chain build")
        else:
            if errors:
                print(f"ERRORS ({len(errors)}):\n")
                for i, issue in enumerate(errors, 1):
                    print(f"{i}. [{issue['component']}] {issue['issue']}")
                    print(f"   → {issue['resolution']}\n")
            
            if warnings:
                print(f"WARNINGS ({len(warnings)}):\n")
                for i, issue in enumerate(warnings, 1):
                    print(f"{i}. [{issue['component']}] {issue['issue']}")
                    print(f"   → {issue['resolution']}\n")
        
        print(f"{'='*80}")
        
        return len(errors) == 0


if __name__ == '__main__':
    project_root = '/content/tegalchain' if len(sys.argv) < 2 else sys.argv[1]
    diagnostics = TegalchainDiagnostics(project_root)
    success = diagnostics.run_diagnostics()
    sys.exit(0 if success else 1)
