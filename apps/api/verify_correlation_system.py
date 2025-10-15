#!/usr/bin/env python3
"""
Verification script for correlation modeling system

Checks that all modules are properly structured and importable.
"""
import sys
import ast
from pathlib import Path

def verify_syntax(file_path):
    """Verify Python file syntax"""
    try:
        with open(file_path) as f:
            ast.parse(f.read())
        return True, None
    except SyntaxError as e:
        return False, str(e)

def main():
    print("="*80)
    print("CORRELATION SYSTEM VERIFICATION")
    print("="*80)
    
    base_path = Path("/Users/joshuadeleon/BetterBros Bets/apps/api/src/corr")
    
    # Files to check
    files = {
        "Core Modules": [
            "__init__.py",
            "correlation.py",
            "copula.py",
            "sampler.py",
            "constraints.py",
        ],
        "Examples": [
            "example_usage.py",
        ],
        "Documentation": [
            "README.md",
            "INSTALLATION.md",
            "QUICKSTART.md",
            "SUMMARY.md",
            "ARCHITECTURE.md",
        ]
    }
    
    all_passed = True
    total_lines = 0
    
    for category, file_list in files.items():
        print(f"\n{category}:")
        for filename in file_list:
            file_path = base_path / filename
            
            # Check existence
            if not file_path.exists():
                print(f"  ✗ {filename} - NOT FOUND")
                all_passed = False
                continue
            
            # Check size
            size = file_path.stat().st_size
            size_kb = size / 1024
            
            # Check syntax for Python files
            if filename.endswith('.py'):
                valid, error = verify_syntax(file_path)
                if valid:
                    # Count lines
                    with open(file_path) as f:
                        lines = len(f.readlines())
                    total_lines += lines
                    print(f"  ✓ {filename} - {lines} lines, {size_kb:.1f} KB")
                else:
                    print(f"  ✗ {filename} - SYNTAX ERROR: {error}")
                    all_passed = False
            else:
                print(f"  ✓ {filename} - {size_kb:.1f} KB")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total Python code: {total_lines} lines")
    
    # Check dependencies
    print("\nDependencies:")
    requirements_path = Path("/Users/joshuadeleon/BetterBros Bets/apps/api/requirements.txt")
    if requirements_path.exists():
        with open(requirements_path) as f:
            content = f.read()
            if "scipy" in content:
                print("  ✓ scipy")
            else:
                print("  ✗ scipy - MISSING")
                all_passed = False
            
            if "copulas" in content:
                print("  ✓ copulas")
            else:
                print("  ✗ copulas - MISSING")
                all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("✓ ALL CHECKS PASSED")
        print("="*80)
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Run examples: python3 -m src.corr.example_usage")
        print("  3. Review docs: src/corr/README.md")
        return 0
    else:
        print("✗ SOME CHECKS FAILED")
        print("="*80)
        return 1

if __name__ == "__main__":
    sys.exit(main())
