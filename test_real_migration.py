#!/usr/bin/env python3
"""
Test Real Migration
Performs an actual migration test with a sample repository
"""
import os
import sys
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Disable display warnings
os.environ.pop('DISPLAY', None)
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from orchestration.langgraph_workflow import CamelMigrationLangGraphWorkflow


def test_real_migration():
    """Test with a real sample repository"""
    print("\n" + "="*70)
    print("TESTING REAL MIGRATION WITH SAMPLE REPOSITORY")
    print("="*70)
    
    # Use a small sample Camel project
    # This is a simple public example that should work
    repository_url = "https://github.com/apache/camel-examples.git"
    
    # Output directory in ~/neo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    workspace_dir = os.path.expanduser(f"~/neo/camel-migration-{timestamp}")
    
    print(f"\nRepository: {repository_url}")
    print(f"Output Directory: {workspace_dir}")
    print(f"Branch: feature/camel4-migration")
    print("\nStarting migration workflow...")
    print("-"*70)
    
    try:
        # Create workflow
        workflow = CamelMigrationLangGraphWorkflow(checkpoint=False)
        
        # Run migration
        result = workflow.run_migration(
            repository_url=repository_url,
            branch_name="feature/camel4-migration",
            workspace_dir=workspace_dir,
            java_version=17
        )
        
        print("\n" + "="*70)
        print("MIGRATION RESULTS")
        print("="*70)
        
        print(f"Success: {result.get('success', False)}")
        print(f"Workspace: {result.get('workspace', 'N/A')}")
        print(f"Branch: {result.get('branch', 'N/A')}")
        print(f"Stages Completed: {len(result.get('stages_completed', []))}")
        
        if result.get('stages_completed'):
            print("\nCompleted Stages:")
            for stage in result['stages_completed']:
                print(f"  ✓ {stage}")
        
        if result.get('errors'):
            print("\nErrors Encountered:")
            for error in result['errors'][:5]:  # Show first 5 errors
                print(f"  ✗ {error[:100]}...")  # Truncate long errors
        
        # Check what was created
        if os.path.exists(workspace_dir):
            print(f"\n✅ Output directory created: {workspace_dir}")
            
            # List contents
            print("\nDirectory contents:")
            for root, dirs, files in os.walk(workspace_dir):
                level = root.replace(workspace_dir, '').count(os.sep)
                indent = ' ' * 2 * level
                print(f'{indent}{os.path.basename(root)}/')
                
                # Only show first few files per directory
                subindent = ' ' * 2 * (level + 1)
                for file in files[:5]:
                    print(f'{subindent}{file}')
                if len(files) > 5:
                    print(f'{subindent}... and {len(files)-5} more files')
                
                # Only show first level of subdirectories
                if level < 2:
                    for d in dirs[:5]:
                        pass  # Directories are shown in the walk
                if len(dirs) > 5 and level < 2:
                    print(f'{subindent}... and {len(dirs)-5} more directories')
                    
                # Don't go too deep
                if level >= 2:
                    dirs.clear()
        else:
            print(f"\n⚠️ Output directory was not created: {workspace_dir}")
        
        # Check for migration report
        report_path = os.path.join(workspace_dir, "migration-report.txt")
        if os.path.exists(report_path):
            print(f"\n📄 Migration report found: {report_path}")
            with open(report_path, 'r') as f:
                report_content = f.read()
                print("\nReport Preview:")
                print("-"*50)
                print(report_content[:500])  # Show first 500 chars
                if len(report_content) > 500:
                    print("... [truncated]")
                print("-"*50)
        
        # Save result summary
        summary_path = os.path.expanduser("~/neo/migration-test-summary.json")
        with open(summary_path, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'repository': repository_url,
                'workspace': workspace_dir,
                'success': result.get('success', False),
                'stages_completed': result.get('stages_completed', []),
                'error_count': len(result.get('errors', []))
            }, f, indent=2)
        print(f"\n📊 Test summary saved to: {summary_path}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_real_migration()
    print("\n" + "="*70)
    if success:
        print("✅ MIGRATION TEST COMPLETED SUCCESSFULLY")
    else:
        print("⚠️ MIGRATION TEST COMPLETED WITH ISSUES")
    print("="*70)
    sys.exit(0 if success else 1)