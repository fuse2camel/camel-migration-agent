#!/usr/bin/env python3
"""
LangGraph Workflow Testing
Tests the complete migration workflow using LangGraph orchestration
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable display warnings
os.environ.pop('DISPLAY', None)
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from orchestration.langgraph_workflow import CamelMigrationLangGraphWorkflow


class TestLangGraphWorkflow:
    """Test the complete LangGraph workflow"""
    
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="workflow_test_")
        print(f"Test directory: {self.test_dir}")
    
    def cleanup(self):
        """Clean up test directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_workflow_initialization(self):
        """Test workflow initialization"""
        print("\n" + "="*60)
        print("Testing Workflow Initialization")
        print("="*60)
        
        try:
            workflow = CamelMigrationLangGraphWorkflow(checkpoint=False)
            print("✅ Workflow initialized without checkpointing")
            
            workflow_with_checkpoint = CamelMigrationLangGraphWorkflow(checkpoint=True)
            print("✅ Workflow initialized with checkpointing")
            
            return True
        except Exception as e:
            print(f"❌ Workflow initialization failed: {e}")
            return False
    
    def test_workflow_visualization(self):
        """Test workflow visualization"""
        print("\n" + "="*60)
        print("Testing Workflow Visualization")
        print("="*60)
        
        try:
            workflow = CamelMigrationLangGraphWorkflow()
            visualization = workflow.visualize_workflow()
            
            if "Camel Migration Workflow" in visualization:
                print("✅ Workflow visualization generated")
                print("\nVisualization preview:")
                lines = visualization.split("\n")[:10]
                for line in lines:
                    print(f"  {line}")
                print("  ...")
                return True
            else:
                print("❌ Workflow visualization incomplete")
                return False
        except Exception as e:
            print(f"❌ Workflow visualization failed: {e}")
            return False
    
    def test_workflow_state_management(self):
        """Test workflow state management"""
        print("\n" + "="*60)
        print("Testing Workflow State Management")
        print("="*60)
        
        try:
            workflow = CamelMigrationLangGraphWorkflow(checkpoint=True)
            
            # Test state retrieval for non-existent thread
            state = workflow.get_workflow_state("test-thread-123")
            if state is None:
                print("✅ Correctly returns None for non-existent thread")
            else:
                print("⚠️ Unexpected state returned for non-existent thread")
            
            return True
        except Exception as e:
            print(f"❌ State management test failed: {e}")
            return False
    
    def test_minimal_workflow_execution(self):
        """Test minimal workflow execution (validation only)"""
        print("\n" + "="*60)
        print("Testing Minimal Workflow Execution")
        print("="*60)
        
        try:
            workflow = CamelMigrationLangGraphWorkflow()
            
            # Create a test workspace
            workspace = os.path.join(self.test_dir, "test_migration")
            os.makedirs(workspace, exist_ok=True)
            
            # We'll test with a minimal execution that should fail early
            # This tests the workflow mechanics without actual migration
            result = workflow.run_migration(
                repository_url="https://github.com/nonexistent/repo.git",
                branch_name="test-branch",
                workspace_dir=workspace,
                java_version=17
            )
            
            # Check that result has expected structure
            expected_keys = ["success", "report", "stages_completed", "errors", "workspace", "branch"]
            missing_keys = [key for key in expected_keys if key not in result]
            
            if not missing_keys:
                print("✅ Workflow execution returned expected structure")
                print(f"   Success: {result['success']}")
                print(f"   Stages completed: {len(result['stages_completed'])}")
                print(f"   Errors: {len(result['errors'])}")
                return True
            else:
                print(f"❌ Missing keys in result: {missing_keys}")
                return False
                
        except Exception as e:
            print(f"❌ Workflow execution failed: {e}")
            return False
    
    def test_workflow_graph_structure(self):
        """Test workflow graph structure"""
        print("\n" + "="*60)
        print("Testing Workflow Graph Structure")
        print("="*60)
        
        try:
            workflow = CamelMigrationLangGraphWorkflow()
            
            # Check that workflow has been compiled
            if workflow.workflow:
                print("✅ Workflow graph compiled successfully")
                
                # Check for expected nodes (by trying to access methods)
                expected_nodes = [
                    "validate_config_node",
                    "clone_repository_node",
                    "update_dependencies_node",
                    "convert_routes_node",
                    "refactor_services_node",
                    "run_tests_node",
                    "containerize_node",
                    "push_changes_node",
                    "generate_report_node"
                ]
                
                missing_nodes = []
                for node in expected_nodes:
                    if not hasattr(workflow, node):
                        missing_nodes.append(node)
                
                if not missing_nodes:
                    print(f"✅ All {len(expected_nodes)} expected nodes present")
                    return True
                else:
                    print(f"❌ Missing nodes: {missing_nodes}")
                    return False
            else:
                print("❌ Workflow graph not compiled")
                return False
                
        except Exception as e:
            print(f"❌ Graph structure test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all workflow tests"""
        print("\n" + "="*60)
        print("LANGGRAPH WORKFLOW TESTING")
        print("="*60)
        
        results = []
        
        # Run tests
        results.append(("Workflow Initialization", self.test_workflow_initialization()))
        results.append(("Workflow Visualization", self.test_workflow_visualization()))
        results.append(("State Management", self.test_workflow_state_management()))
        results.append(("Graph Structure", self.test_workflow_graph_structure()))
        results.append(("Minimal Execution", self.test_minimal_workflow_execution()))
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        all_passed = True
        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name}: {status}")
            if not passed:
                all_passed = False
        
        print("\n" + "="*60)
        if all_passed:
            print("✅ ALL WORKFLOW TESTS PASSED")
        else:
            print("❌ SOME WORKFLOW TESTS FAILED")
        print("="*60)
        
        return all_passed


def main():
    """Main test runner"""
    tester = TestLangGraphWorkflow()
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    sys.exit(main())