#!/usr/bin/env python3
"""
System Verification Script
Verifies that all components of the Camel Migration Agent are working
"""
import os
import sys

# Disable display warnings
os.environ.pop('DISPLAY', None)
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

def verify_imports():
    """Verify all imports work"""
    print("Verifying imports...")
    
    try:
        # Config imports
        from config.llm_config import get_llm, get_llm_config
        print("  ✅ Config imports OK")
        
        # Agent imports
        from agents.config_agent import ConfigAgent
        from agents.git_agent import GitAgent
        from agents.dependency_agent import DependencyAgent
        from agents.dsl_conversion_agent import DSLConversionAgent
        from agents.service_refactor_agent import ServiceRefactorAgent
        from agents.containerization_agent import ContainerizationAgent
        from agents.test_agent import TestAgent
        print("  ✅ All agent imports OK")
        
        # Workflow imports
        from orchestration.workflow import CamelMigrationWorkflow
        print("  ✅ Workflow imports OK")
        
        return True
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False

def verify_agent_creation():
    """Verify all agents can be created"""
    print("\nVerifying agent creation...")
    
    try:
        from agents.config_agent import ConfigAgent
        from agents.git_agent import GitAgent
        from agents.dependency_agent import DependencyAgent
        from agents.dsl_conversion_agent import DSLConversionAgent
        from agents.service_refactor_agent import ServiceRefactorAgent
        from agents.containerization_agent import ContainerizationAgent
        from agents.test_agent import TestAgent
        
        agents = [
            ("ConfigAgent", ConfigAgent),
            ("GitAgent", GitAgent),
            ("DependencyAgent", DependencyAgent),
            ("DSLConversionAgent", DSLConversionAgent),
            ("ServiceRefactorAgent", ServiceRefactorAgent),
            ("ContainerizationAgent", ContainerizationAgent),
            ("TestAgent", TestAgent),
        ]
        
        for name, agent_class in agents:
            agent = agent_class()
            print(f"  ✅ {name} created")
        
        return True
    except Exception as e:
        print(f"  ❌ Agent creation error: {e}")
        return False

def verify_workflow():
    """Verify workflow can be created"""
    print("\nVerifying workflow...")
    
    try:
        from orchestration.workflow import CamelMigrationWorkflow
        
        workflow = CamelMigrationWorkflow()
        print("  ✅ Workflow created successfully")
        return True
    except Exception as e:
        print(f"  ❌ Workflow error: {e}")
        return False

def verify_llm_config():
    """Verify LLM configuration"""
    print("\nVerifying LLM configuration...")
    
    try:
        from config.llm_config import get_llm, get_llm_config
        
        # Test both functions
        llm1 = get_llm()
        llm2 = get_llm_config()
        
        print(f"  ✅ LLM configured with model: {llm1.model_name}")
        return True
    except Exception as e:
        print(f"  ❌ LLM config error: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("CAMEL MIGRATION AGENT - SYSTEM VERIFICATION")
    print("=" * 60)
    
    results = []
    
    # Run verifications
    results.append(("Imports", verify_imports()))
    results.append(("LLM Config", verify_llm_config()))
    results.append(("Agent Creation", verify_agent_creation()))
    results.append(("Workflow", verify_workflow()))
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for check, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ SYSTEM VERIFICATION COMPLETE - ALL CHECKS PASSED")
        print("\nThe Camel Migration Agent is ready to use!")
        print("\nRun the migration with:")
        print("  python main.py --repo <repository-url>")
    else:
        print("❌ SYSTEM VERIFICATION FAILED")
        print("\nPlease fix the issues above before using the system.")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())