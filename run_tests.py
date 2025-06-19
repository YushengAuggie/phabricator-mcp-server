#!/usr/bin/env python3
"""Test runner for MCP tool completeness tests."""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Run all tests and display results."""
    print("🧪 Running MCP Tool Completeness Tests")
    print("=" * 60)

    # Change to the project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # Add src to Python path
    sys.path.insert(0, str(project_root / "src"))

    # Test commands to run
    test_commands = [["python", "-m", "pytest", "src/tests/", "-v", "--tb=short"]]

    all_passed = True

    for i, cmd in enumerate(test_commands, 1):
        print(f"\n📋 Running Test Suite {i}: {' '.join(cmd)}")
        print("-" * 40)

        try:
            result = subprocess.run(
                cmd, cwd=project_root, capture_output=False, text=True  # Show output in real time
            )

            if result.returncode == 0:
                print(f"✅ Test Suite {i} PASSED")
            else:
                print(f"❌ Test Suite {i} FAILED (exit code: {result.returncode})")
                all_passed = False

        except subprocess.CalledProcessError as e:
            print(f"❌ Test Suite {i} FAILED: {e}")
            all_passed = False
        except FileNotFoundError:
            print(f"❌ Test Suite {i} FAILED: pytest not found. Install with: pip install pytest")
            all_passed = False

    # Final summary
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ All MCP tools are properly configured and working")
    else:
        print("💥 SOME TESTS FAILED!")
        print("❌ Please fix the issues above")
        sys.exit(1)


if __name__ == "__main__":
    main()
