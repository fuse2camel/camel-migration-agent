#!/usr/bin/env python3
"""
Simple test to verify Docker tools work without K8s/Helm
"""

import os
import sys
import tempfile

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import only the docker tools, not the agents
import importlib.util

# Load docker_tools module directly
spec = importlib.util.spec_from_file_location("docker_tools", "tools/docker_tools.py")
docker_tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(docker_tools)

def test_dockerfile_content():
    """Test the Dockerfile template content"""
    print("Testing Dockerfile template...")
    
    # Check that the template exists and has expected content
    if hasattr(docker_tools, 'DOCKERFILE_TEMPLATE'):
        template = docker_tools.DOCKERFILE_TEMPLATE
        
        # Verify key Docker best practices are in template
        checks = [
            ('Multi-stage build', 'AS builder' in template),
            ('Non-root user', 'USER camel' in template),
            ('Health check', 'HEALTHCHECK' in template),
            ('JVM options', 'JAVA_OPTS' in template),
            ('Alpine base', 'alpine' in template)
        ]
        
        for name, passed in checks:
            if passed:
                print(f"  ✓ {name}")
            else:
                print(f"  ✗ {name}")
        
        return all(check[1] for check in checks)
    else:
        print("  ✗ DOCKERFILE_TEMPLATE not found")
        return False

def test_generate_dockerfile():
    """Test Dockerfile generation function"""
    print("\nTesting generate_dockerfile function...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        result = docker_tools.generate_dockerfile(temp_dir, java_version=17)
        
        if result['status'] == 'Success':
            print("  ✓ Function executed successfully")
            
            # Check generated files
            dockerfile_path = result.get('dockerfile_path')
            dockerignore_path = result.get('dockerignore_path')
            
            if dockerfile_path and os.path.exists(dockerfile_path):
                print(f"  ✓ Dockerfile created at: {dockerfile_path}")
                
                # Read and verify content
                with open(dockerfile_path, 'r') as f:
                    content = f.read()
                    if 'eclipse-temurin:17' in content:
                        print("  ✓ Correct Java version in Dockerfile")
            
            if dockerignore_path and os.path.exists(dockerignore_path):
                print(f"  ✓ .dockerignore created at: {dockerignore_path}")
            
            return True
        else:
            print(f"  ✗ Function failed: {result.get('message')}")
            return False

def check_removed_functions():
    """Verify K8s and Helm functions are removed"""
    print("\nVerifying K8s/Helm functions are removed...")
    
    removed_functions = [
        'generate_k8s_manifests',
        'generate_helm_chart',
        'DEPLOYMENT_TEMPLATE',
        'SERVICE_TEMPLATE',
        'CONFIGMAP_TEMPLATE',
        'HPA_TEMPLATE'
    ]
    
    all_removed = True
    for func_name in removed_functions:
        if hasattr(docker_tools, func_name):
            print(f"  ✗ {func_name} still exists (should be removed)")
            all_removed = False
        else:
            print(f"  ✓ {func_name} removed")
    
    return all_removed

def main():
    """Run all tests"""
    print("=" * 60)
    print("Docker Tools Test (K8s/Helm Removed)")
    print("=" * 60)
    
    results = []
    
    # Test 1: Dockerfile template
    results.append(("Dockerfile Template", test_dockerfile_content()))
    
    # Test 2: Generate Dockerfile
    results.append(("Generate Dockerfile", test_generate_dockerfile()))
    
    # Test 3: Verify removals
    results.append(("K8s/Helm Removal", check_removed_functions()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("-" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed! Docker-only configuration is working correctly.")
        print("   K8s and Helm configurations have been successfully removed.")
    else:
        print("❌ Some tests failed. Please check the output above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
