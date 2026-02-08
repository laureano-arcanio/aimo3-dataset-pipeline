#!/usr/bin/env python
"""Verify AIMO3 Pipeline Installation

Run this script to check if all required dependencies are installed correctly.

Usage:
    python verify_install.py
"""

import sys
from pathlib import Path


def check_import(module_name, package_name=None, optional=False):
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        symbol = "✓" if not optional else "✓"
        print(f"{symbol} {package_name or module_name}")
        return True
    except ImportError:
        symbol = "✗" if not optional else "⚠"
        status = "NOT INSTALLED" if not optional else "OPTIONAL"
        print(f"{symbol} {package_name or module_name} - {status}")
        return False


def main():
    """Run installation verification."""
    print("AIMO3 Dataset Pipeline - Installation Verification")
    print("=" * 60)
    
    # Check Python version
    print(f"\nPython version: {sys.version}")
    if sys.version_info < (3, 10):
        print("⚠ Warning: Python 3.10+ is recommended")
    else:
        print("✓ Python version OK")
    
    # Core dependencies
    print("\n" + "=" * 60)
    print("Checking core dependencies...")
    print("-" * 60)
    core_deps = [
        ("pandas", None, False),
        ("numpy", None, False),
        ("tqdm", None, False),
        ("anyio", None, False),
        ("httpx", None, False),
        ("tenacity", None, False),
        ("jupyter", None, False),
        ("sklearn", "scikit-learn", False),
    ]
    
    core_ok = all(check_import(*dep) for dep in core_deps)
    
    # Visualization dependencies
    print("\n" + "=" * 60)
    print("Checking visualization dependencies...")
    print("-" * 60)
    viz_deps = [
        ("matplotlib", None, True),
        ("seaborn", None, True),
        ("IPython", "ipywidgets", True),
    ]
    
    viz_ok = all(check_import(*dep) for dep in viz_deps)
    
    # Training dependencies
    print("\n" + "=" * 60)
    print("Checking training dependencies (optional)...")
    print("-" * 60)
    train_deps = [
        ("torch", None, True),
        ("transformers", None, True),
        ("datasets", None, True),
        ("accelerate", None, True),
        ("peft", None, True),
    ]
    
    train_ok = all(check_import(*dep) for dep in train_deps)
    
    # Check pipeline utilities
    print("\n" + "=" * 60)
    print("Checking pipeline utilities...")
    print("-" * 60)
    
    utils_ok = False
    try:
        # Try to import from utils package
        sys.path.insert(0, str(Path(__file__).parent / "pipeline"))
        from utils import LLMPool, RuntimeConfig
        print("✓ Pipeline utils (LLMPool, RuntimeConfig)")
        utils_ok = True
    except ImportError as e:
        print(f"✗ Pipeline utils - {e}")
        print("  Make sure you're running this from the project root directory")
    
    # Summary
    print("\n" + "=" * 60)
    print("INSTALLATION SUMMARY")
    print("=" * 60)
    
    if core_ok:
        print("✓ Core dependencies: READY")
    else:
        print("✗ Core dependencies: INCOMPLETE")
        print("  Install with: pip install -r requirements.txt")
    
    if viz_ok:
        print("✓ Visualization: READY")
    else:
        print("⚠ Visualization: OPTIONAL")
        print("  Install with: pip install matplotlib seaborn ipywidgets")
    
    if train_ok:
        print("✓ Training: READY")
    else:
        print("⚠ Training: OPTIONAL (only needed for notebook 11)")
        print("  Install with: pip install -r requirements-training.txt")
    
    if utils_ok:
        print("✓ Pipeline utilities: READY")
    else:
        print("✗ Pipeline utilities: CHECK FAILED")
    
    print("\n" + "=" * 60)
    
    if core_ok and utils_ok:
        print("✓ INSTALLATION SUCCESSFUL!")
        print("\nYou can start using the pipeline.")
        print("Next steps:")
        print("  1. Review README.md for pipeline overview")
        print("  2. Start Jupyter: jupyter notebook")
        print("  3. Open notebook 0 for data extraction")
        return 0
    else:
        print("✗ INSTALLATION INCOMPLETE")
        print("\nPlease install missing dependencies:")
        if not core_ok:
            print("  pip install -r requirements.txt")
        if not utils_ok:
            print("  Make sure you're in the project root directory")
        return 1


if __name__ == "__main__":
    sys.exit(main())
