#!/usr/bin/env python3
"""
Full Migration Test - Runs complete migration on sample app
"""
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

# Disable display
os.environ.pop('DISPLAY', None)
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

def main():
    print("\n" + "=" * 70)
    print("CAMEL MIGRATION AGENT - FULL MIGRATION TEST")
    print("=" * 70)
    
    # Create test workspace
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_workspace = Path(tempfile.gettempdir()) / f"camel_full_test_{timestamp}"
    test_workspace.mkdir(exist_ok=True)
    
    print(f"\nTest Workspace: {test_workspace}")
    
    # Run the migration using main.py
    print("\n" + "=" * 70)
    print("RUNNING FULL MIGRATION")
    print("=" * 70)
    
    cmd = [
        sys.executable,
        "main.py",
        "--repo", "https://github.com/fuse2camel/sample-fuse6-app.git",
        "--workspace", str(test_workspace),
        "--branch", "camel4-migration",
        "--skip-tests"  # Skip tests for faster execution
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print("\nExecuting migration...")
    print("(This may take a few minutes...)\n")
    
    try:
        # Run migration
        result = subprocess.run(
            cmd,
            cwd="/home/neox/PycharmProjects/camel-migration-agent",
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Parse output
        output_lines = result.stdout.split('\n')
        for line in output_lines:
            if any(keyword in line.lower() for keyword in ['error', 'success', 'complete', 'fail', '✓', '✗']):
                print(line)
        
        # Check results
        print("\n" + "=" * 70)
        print("MIGRATION RESULTS")
        print("=" * 70)
        
        # Check what was created
        checks = {
            "Repository Cloned": (test_workspace / ".git").exists(),
            "POM Updated": (test_workspace / "pom.xml").exists(),
            "Dockerfile Created": (test_workspace / "Dockerfile").exists(),
            "K8s Manifests": (test_workspace / "k8s").exists(),
        }
        
        passed = 0
        failed = 0
        
        for check_name, check_result in checks.items():
            if check_result:
                print(f"✅ {check_name}")
                passed += 1
            else:
                print(f"❌ {check_name}")
                failed += 1
        
        # Check if POM was actually updated
        pom_file = test_workspace / "pom.xml"
        if pom_file.exists():
            pom_content = pom_file.read_text()
            if "4.8" in pom_content or "camel-core-model" in pom_content:
                print("✅ POM contains Camel 4 dependencies")
                passed += 1
            else:
                print("❌ POM still has Camel 2 dependencies")
                failed += 1
        
        # Final summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Migration successful!")
        else:
            print(f"\n⚠️  Some tests failed. Check {test_workspace} for details.")
        
        print(f"\nMigrated project location: {test_workspace}")
        print("You can inspect the migrated code at this location.")
        
        return 0 if failed == 0 else 1
        
    except subprocess.TimeoutExpired:
        print("\n✗ Migration timed out after 5 minutes")
        return 1
    except Exception as e:
        print(f"\n✗ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())