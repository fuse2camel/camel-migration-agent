#!/usr/bin/env python3
"""
Main execution script for Camel Migration Agent
Migrates Apache Camel 2 Spring Boot applications to Apache Camel 4
"""

import argparse
import os
import sys
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestration.workflow import CamelMigrationWorkflow
from agents.config_agent import ConfigAgent


def validate_environment():
    """Quick environment validation before starting"""
    print("🔍 Performing quick environment check...")
    config_agent = ConfigAgent()
    validation = config_agent.validate()
    
    if validation.get("overall_status") != "Success":
        print("\n❌ Environment validation failed!")
        print(config_agent.get_validation_summary(validation))
        return False
    
    print("✅ Environment validation passed!")
    return True


def run_individual_agent(agent_name: str, **kwargs):
    """Run a specific agent individually for testing"""
    print(f"\n🚀 Running {agent_name} agent...")
    
    if agent_name == "config":
        from agents.config_agent import ConfigAgent
        agent = ConfigAgent()
        result = agent.validate()
        print(agent.get_validation_summary(result))
        
    elif agent_name == "git":
        from agents.git_agent import GitAgent
        agent = GitAgent()
        if kwargs.get("action") == "clone":
            result = agent.initiate_workflow(
                repository_url=kwargs.get("repo_url"),
                branch_name=kwargs.get("branch", "feature/camel4-migration"),
                workspace_dir=kwargs.get("workspace", "/tmp/camel-migration")
            )
        else:
            result = agent.finalize_workflow(
                source_code_path=kwargs.get("workspace", "/tmp/camel-migration"),
                commit_message=kwargs.get("message", "Camel 4 migration")
            )
        print(f"Result: {result}")
        
    elif agent_name == "dependency":
        from agents.dependency_agent import DependencyAgent
        agent = DependencyAgent()
        pom_path = os.path.join(kwargs.get("workspace", "."), "pom.xml")
        if kwargs.get("action") == "analyze":
            result = agent.analyze_dependencies(pom_path)
        else:
            result = agent.update_project_dependencies(pom_path)
        print(f"Result: {result.get('summary', result)}")
        
    elif agent_name == "dsl":
        from agents.dsl_conversion_agent import DSLConversionAgent
        agent = DSLConversionAgent()
        result = agent.convert_routes(
            source_code_path=kwargs.get("workspace", "."),
            package_name=kwargs.get("package", "com.example.routes.migrated")
        )
        print(agent.generate_conversion_report(result))
        
    elif agent_name == "service":
        from agents.service_refactor_agent import ServiceRefactorAgent
        agent = ServiceRefactorAgent()
        result = agent.refactor_business_logic(
            source_code_path=kwargs.get("workspace", ".")
        )
        print(f"Result: {result.get('summary', result)}")
        
    elif agent_name == "test":
        from agents.test_agent import TestAgent
        agent = TestAgent()
        result = agent.validate_migration(
            project_root_path=kwargs.get("workspace", "."),
            run_full_tests=kwargs.get("full_tests", False)
        )
        print(agent.generate_test_report(result))
        
    elif agent_name == "container":
        from agents.containerization_agent import ContainerizationAgent
        agent = ContainerizationAgent()
        result = agent.containerize_application(
            project_root_path=kwargs.get("workspace", "."),
            app_name=kwargs.get("app_name", "camel-app"),
            java_version=kwargs.get("java_version", 17),
            build_image=kwargs.get("build", False)
        )
        print(f"Result: {result.get('summary', result)}")
        
    else:
        print(f"Unknown agent: {agent_name}")
        print("Available agents: config, git, dependency, dsl, service, test, container")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Camel Migration Agent - Migrate Apache Camel 2 to Camel 4",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full migration workflow
  python main.py --repo https://github.com/user/camel-app.git

  # Run with custom settings
  python main.py --repo https://github.com/user/camel-app.git \\
                 --branch my-migration \\
                 --workspace /path/to/workspace \\
                 --java 17

  # Test individual agents
  python main.py --test-agent config
  python main.py --test-agent dependency --workspace /path/to/project

  # Use the sample Fuse 6 application
  python main.py --repo https://github.com/fuse2camel/sample-fuse6-app.git
        """
    )
    
    # Workflow arguments
    parser.add_argument(
        "--repo",
        type=str,
        help="Git repository URL to migrate"
    )
    parser.add_argument(
        "--branch",
        type=str,
        default="feature/camel4-migration",
        help="Branch name for migration (default: feature/camel4-migration)"
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default="/tmp/camel-migration",
        help="Local workspace directory (default: /tmp/camel-migration)"
    )
    parser.add_argument(
        "--java",
        type=int,
        default=17,
        choices=[11, 17, 21],
        help="Target Java version (default: 17)"
    )
    parser.add_argument(
        "--skip-container",
        action="store_true",
        help="Skip containerization step"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running tests"
    )
    
    # Testing arguments
    parser.add_argument(
        "--test-agent",
        type=str,
        choices=["config", "git", "dependency", "dsl", "service", "test", "container"],
        help="Test a specific agent individually"
    )
    parser.add_argument(
        "--action",
        type=str,
        help="Action for test agent (e.g., 'analyze' for dependency agent)"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate environment without running migration"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate environment first
    if not validate_environment():
        if not args.validate_only:
            print("\n⚠️  Environment validation failed. Fix the issues above before proceeding.")
            print("   You can run with --validate-only to see detailed validation results.")
            sys.exit(1)
    
    if args.validate_only:
        print("\n✅ Environment validation complete.")
        sys.exit(0)
    
    # Test individual agent if requested
    if args.test_agent:
        run_individual_agent(
            args.test_agent,
            repo_url=args.repo,
            branch=args.branch,
            workspace=args.workspace,
            java_version=args.java,
            action=args.action
        )
        sys.exit(0)
    
    # Check if repository URL is provided
    if not args.repo:
        print("\n❌ Error: Repository URL is required!")
        print("   Use --repo <url> to specify the repository to migrate")
        print("   Example: python main.py --repo https://github.com/fuse2camel/sample-fuse6-app.git")
        parser.print_help()
        sys.exit(1)
    
    # Run the full migration workflow
    print("\n" + "=" * 70)
    print("CAMEL MIGRATION AGENT")
    print("Apache Camel 2 to Camel 4 Migration Tool")
    print("=" * 70)
    
    workflow = CamelMigrationWorkflow()
    
    try:
        result = workflow.run(
            repository_url=args.repo,
            branch_name=args.branch,
            workspace_dir=args.workspace,
            java_version=args.java,
            skip_containerization=args.skip_container
        )
        
        if result.get("migration_complete"):
            print("\n✅ Migration completed successfully!")
            
            # Show important outputs
            if result.get("git_status", {}).get("pushed_branch_url"):
                print(f"\n📌 Migration branch: {result['git_status']['pushed_branch_url']}")
            
            print(f"\n📁 Workspace: {args.workspace}")
            print(f"📄 Report: {os.path.join(args.workspace, 'migration-report.txt')}")
            
            sys.exit(0)
        else:
            print("\n❌ Migration failed!")
            if result.get("error"):
                print(f"   Error: {result['error']}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
