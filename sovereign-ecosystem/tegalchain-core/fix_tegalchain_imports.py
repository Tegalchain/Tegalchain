#!/usr/bin/env python3
"""
Tegalchain Import Path Fix Script
================================

This script fixes common import path issues in Tegalchain Go modules:
1. Removes incorrect AccAddress import paths
2. Fixes AddressCodec imports
3. Consolidates import blocks
4. Validates go.mod replace directives

Usage:
    python fix_tegalchain_imports.py [--project-root /path/to/tegalchain]
"""

import os
import re
import sys
import shutil
from pathlib import Path
from typing import List, Set, Tuple


class TegalchainImportFixer:
    """Fixes import path issues in Tegalchain modules."""
    
    def __init__(self, project_root: str = '/content/tegalchain'):
        self.project_root = Path(project_root)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.files_modified = 0
        
        if not self.project_root.exists():
            raise ValueError(f"Project root not found: {self.project_root}")
    
    def log_section(self, title: str):
        """Log a section header."""
        print(f"\n{'='*80}")
        print(f"{title}")
        print(f"{'='*80}")
    
    def log_success(self, msg: str):
        """Log a success message."""
        print(f"✓ {msg}")
    
    def log_warning(self, msg: str):
        """Log a warning message."""
        print(f"⚠ {msg}")
        self.warnings.append(msg)
    
    def log_error(self, msg: str):
        """Log an error message."""
        print(f"✗ {msg}")
        self.errors.append(msg)
    
    def fix_incorrect_accaddress_imports(self) -> int:
        """
        Remove incorrect AccAddress import paths.
        
        Incorrect: import \"github.com/cosmos/cosmos-sdk/types/sdk.AccAddress\"
        These should be handled by proper sdk import instead.
        """
        self.log_section("STEP 1: Fix Incorrect AccAddress Imports")
        
        modules = ['telemetry', 'txassets']
        pattern = re.compile(r'\"github\.com/cosmos/cosmos-sdk/types/sdk\.AccAddress\"')
        fixed_count = 0
        
        for module in modules:
            types_dir = self.project_root / 'x' / module / 'types'
            
            if not types_dir.exists():
                self.log_warning(f"Directory not found: {types_dir}")
                continue
            
            go_files = list(types_dir.glob('**/*.go'))
            self.log_success(f"Scanning {len(go_files)} files in {module}/types")
            
            for go_file in go_files:
                with open(go_file, 'r') as f:
                    content = f.read()
                
                original_content = content
                
                # Find and remove the incorrect import line
                lines = content.split('\n')
                new_lines = []
                line_removed = False
                
                for line in lines:
                    if pattern.search(line):
                        self.log_success(f"Removed incorrect import from {go_file.name}")
                        self.log_success(f"  Line: {line.strip()}")
                        line_removed = True
                    else:
                        new_lines.append(line)
                
                if line_removed:
                    content = '\n'.join(new_lines)
                    with open(go_file, 'w') as f:
                        f.write(content)
                    self.files_modified += 1
                    fixed_count += 1
        
        self.log_success(f"Fixed {fixed_count} incorrect imports")
        return fixed_count
    
    def _collect_imports(self, lines: List[str]) -> Tuple[Set[str], List[str]]:
        """
        Collect all imports from Go file lines and return non-import lines.
        
        Returns:
            Tuple of (collected_imports_set, non_import_lines_list)
        """
        collected_imports: Set[str] = set()
        new_lines: List[str] = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Multi-line import block
            if stripped == 'import (':
                i += 1
                while i < len(lines):
                    block_line = lines[i].strip()
                    if block_line == ')':
                        i += 1
                        break
                    
                    if block_line and not block_line.startswith('//') and not block_line.startswith('/*'):
                        # Parse: alias "path" or "path"
                        match = re.match(r'^(?:(\S+)\s+)?\"([^\"]+)\"', block_line)
                        if match:
                            alias = match.group(1) or ''
                            path = match.group(2)
                            import_str = f'{alias} "{path}"'.strip()
                            collected_imports.add(import_str)
                    i += 1
            
            # Single-line import
            elif re.match(r'^import\s+(?:(\S+)\s+)?\"([^\"]+)\"', line):
                match = re.match(r'^import\s+(?:(\S+)\s+)?\"([^\"]+)\"', line)
                if match:
                    alias = match.group(1) or ''
                    path = match.group(2)
                    import_str = f'{alias} "{path}"'.strip()
                    collected_imports.add(import_str)
                new_lines.append('')  # Placeholder for imports section
                i += 1
            else:
                new_lines.append(line)
                i += 1
        
        return collected_imports, new_lines
    
    def fix_expected_keepers(self) -> int:
        """
        Fix expected_keepers.go files in each module.
        
        Ensures proper imports for:
        - sdk \"github.com/cosmos/cosmos-sdk/types\"
        - address \"cosmossdk.io/core/address\"
        """
        self.log_section("STEP 2: Fix expected_keepers.go Files")
        
        modules = ['telemetry', 'txassets']
        fixed_count = 0
        
        required_imports = [
            'sdk "github.com/cosmos/cosmos-sdk/types"',
            'address "cosmossdk.io/core/address"',
        ]
        
        for module in modules:
            file_path = self.project_root / 'x' / module / 'types' / 'expected_keepers.go'
            
            if not file_path.exists():
                self.log_warning(f"File not found: {file_path}")
                continue
            
            self.log_success(f"Processing {module}/types/expected_keepers.go")
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                lines = content.split('\n')
                collected_imports, new_lines = self._collect_imports(lines)
                
                # Remove old/conflicting address imports
                filtered_imports = set()
                for imp in collected_imports:
                    if 'cosmos-sdk/types/address' not in imp and 'core/address' not in imp:
                        filtered_imports.add(imp)
                
                # Add required imports
                for req_imp in required_imports:
                    req_path = req_imp.split('"')[1]
                    found = any(req_path in imp for imp in filtered_imports)
                    if not found:
                        filtered_imports.add(req_imp)
                
                # Rebuild file with sorted imports
                import_lines = sorted(list(filtered_imports))
                import_block = "import (\n" + "\n".join(f"    {imp}" for imp in import_lines) + "\n)"
                
                # Find package declaration and insert imports after it
                package_idx = -1
                for idx, line in enumerate(new_lines):
                    if line.strip().startswith('package '):
                        package_idx = idx
                        break
                
                if package_idx >= 0:
                    # Find first non-empty line after package
                    insert_idx = package_idx + 1
                    while insert_idx < len(new_lines) and not new_lines[insert_idx].strip():
                        insert_idx += 1
                    
                    new_lines.insert(insert_idx, '\n' + import_block + '\n')
                
                # Remove placeholder empty lines
                new_lines = [l for l in new_lines if l != '']
                
                with open(file_path, 'w') as f:
                    f.write('\n'.join(new_lines))
                
                self.files_modified += 1
                fixed_count += 1
                self.log_success(f"  Updated imports in {file_path.name}")
            
            except Exception as e:
                self.log_error(f"Error processing {file_path}: {e}")
        
        self.log_success(f"Fixed {fixed_count} expected_keepers.go files")
        return fixed_count
    
    def validate_gomod(self) -> bool:
        """
        Validate go.mod for common issues.
        """
        self.log_section("STEP 3: Validate go.mod")
        
        gomod_path = self.project_root / 'go.mod'
        
        if not gomod_path.exists():
            self.log_error(f"go.mod not found at {gomod_path}")
            return False
        
        with open(gomod_path, 'r') as f:
            content = f.read()
        
        self.log_success(f"go.mod found at {gomod_path}")
        
        # Check Go version
        go_match = re.search(r'^go\s+([\d.]+)', content, re.MULTILINE)
        if go_match:
            go_version = go_match.group(1)
            self.log_success(f"Go version: {go_version}")
        
        # Check Cosmos SDK version
        cosmos_match = re.search(r'github\.com/cosmos/cosmos-sdk\s+v([\d.]+)', content)
        if cosmos_match:
            cosmos_version = cosmos_match.group(1)
            self.log_success(f"Cosmos SDK version: v{cosmos_version}")
            
            if cosmos_version != '0.53.6':
                self.log_warning(f"Expected Cosmos SDK v0.53.6, found v{cosmos_version}")
        
        # Check replace directives
        replace_pattern = re.compile(r'^replace\s+([^\s]+)\s+=>\s+(.+)$', re.MULTILINE)
        replaces = replace_pattern.findall(content)
        
        self.log_success(f"Found {len(replaces)} replace directives:")
        for src, dst in replaces:
            print(f"  {src} => {dst}")
        
        # Check for cosmos duplicates
        cosmos_replaces = [r for r in replaces if 'cosmos' in r[0]]
        if len(cosmos_replaces) > 1:
            self.log_warning(f"Multiple cosmos replace directives found ({len(cosmos_replaces)})")
            self.log_warning("This may cause module conflicts")
            return False
        
        self.log_success("go.mod validation passed")
        return True
    
    def fix_all(self) -> bool:
        """
        Run all fixes in order.
        """
        print(f"\n{'='*80}")
        print("TEGALCHAIN IMPORT PATH FIXER")
        print(f"{'='*80}")
        print(f"Project root: {self.project_root}\n")
        
        try:
            self.fix_incorrect_accaddress_imports()
            self.fix_expected_keepers()
            self.validate_gomod()
            
            # Summary
            self.log_section("SUMMARY")
            self.log_success(f"Total files modified: {self.files_modified}")
            
            if self.warnings:
                print(f"\nWarnings ({len(self.warnings)}):")
                for w in self.warnings:
                    print(f"  ⚠ {w}")
            
            if self.errors:
                print(f"\nErrors ({len(self.errors)}):")
                for e in self.errors:
                    print(f"  ✗ {e}")
                return False
            
            print(f"\n{'='*80}")
            print("✓ ALL FIXES COMPLETED SUCCESSFULLY")
            print(f"{'='*80}")
            return True
        
        except Exception as e:
            self.log_error(f"Unexpected error: {e}")
            return False


if __name__ == '__main__':
    project_root = sys.argv[1] if len(sys.argv) > 1 else '/content/tegalchain'
    
    fixer = TegalchainImportFixer(project_root)
    success = fixer.fix_all()
    
    sys.exit(0 if success else 1)
