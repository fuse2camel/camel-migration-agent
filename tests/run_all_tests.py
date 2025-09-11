#!/usr/bin/env python3
"""
Master Test Runner
Runs all test suites in sequence
"""
import os
import sys
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable display warnings
os.environ.pop('DISPLAY', None)
os.environ['QT_QPA_PLATFORM'] = 'offscreen'


def run_test(test_file, description):
    """Run a single test file"""
    print("\n" + "="*70)
    print(f"Running: {description}")
    print("="*70)
    
    test_path = os.path.join(os.path.dirname(__file__), test_file)
    
    try:
        result = subprocess.run(
            [sys.executable, test_path],
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {test_file}: {e}")
        return False


def main():
    """Main test runner"""
    print("\n" + "="*70)
    print("CAMEL MIGRATION AGENT - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print("\nThis will run all test suites to verify the system is working correctly.")
    
    # Define test suites
    test_suites = [
        ("verify_system.py", "System Verification"),
        ("test_individual_agents.py", "Individual Agent Tests"),
        ("test_langgraph_workflow.py", "LangGraph Workflow Tests"),
    ]
    
    results = []
    
    # Run each test suite
    for test_file, description in test_suites:
        success = run_test(test_file, description)
        results.append((description, success))
    
    # Print summary
    print("\n" + "="*70)
    print("OVERALL TEST SUMMARY")
    print("="*70)
    
    all_passed = True
    for suite_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{suite_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL TEST SUITES PASSED")
        print("\nThe Camel Migration Agent is fully functional!")
        print("\nYou can now run migrations with:")
        print("  python main.py --repo <repository-url>")
        print("\nOr use the GUI:")
        print("  python -m tasks.run_coordinator --source-path /path/to/repo --branch feature/fuse2camel --port 8000")
    else:
        print("❌ SOME TEST SUITES FAILED")
        print("\nPlease review the failures above and fix any issues.")
        print("\nNote: Some failures may be due to external dependencies (e.g., Git, Maven, Docker)")
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())