#!/usr/bin/env python3
"""
Main execution script for Camel Migration Agent
Migrates Apache Camel 2 Spring Boot applications to Apache Camel 4
Now uses LangGraph for orchestration instead of direct Crew execution
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

from orchestration.langgraph_workflow import CamelMigrationLangGraphWorkflow
from agents.config_agent import ConfigAgent
from crewai import Crew


def validate_environment():
    """Quick environment validation before starting"""
    print("🔍 Performing quick environment check...")
    config_agent = ConfigAgent()
    
    # Create and execute validation task using a temporary crew
    task = config_agent.create_validation_task()
    crew = Crew(
        agents=[config_agent.agent],
        tasks=[task],
        verbose=False
    )
    
    try:
        result = crew.kickoff()
        validation = result if isinstance(result, dict) else {"overall_status": "Unknown", "result": str(result)}
        
        if validation.get("overall_status") != "Success":
            print("\n❌ Environment validation failed!")
            print(config_agent.get_validation_summary(validation))
            return False
        
        print("✅ Environment validation passed!")
        return True
    except Exception as e:
        print(f"\n❌ Environment validation error: {str(e)}")
        return False


def run_individual_agent(agent_name: str, **kwargs):
    """Run a specific agent individually for testing"""
    print(f"\n🚀 Running {agent_name} agent...")
    
    if agent_name == "config":
        from agents.config_agent import ConfigAgent
        agent = ConfigAgent()
        task = agent.create_validation_task()
        crew = Crew(agents=[agent.agent], tasks=[task], verbose=True)
        result = crew.kickoff()
        print(f"Result: {result}")
        
    elif agent_name == "git":
        from agents.git_agent import GitAgent
        agent = GitAgent()
        if kwargs.get("action") == "clone":
            task = agent.create_initiate_task(
                repository_url=kwargs.get("repo_url"),
                branch_name=kwargs.get("branch", "feature/camel4-migration"),
                workspace_dir=kwargs.get("workspace", "/tmp/camel-migration")
            )
        else:
            task = agent.create_finalize_task(
                source_code_path=kwargs.get("workspace", "/tmp/camel-migration"),
                commit_message=kwargs.get("message", "Camel 4 migration")
            )
        crew = Crew(agents=[agent.agent], tasks=[task], verbose=True)
        result = crew.kickoff()
        print(f"Result: {result}")
        
    elif agent_name == "dependency":
        from agents.dependency_agent import DependencyAgent
        agent = DependencyAgent()
        pom_path = os.path.join(kwargs.get("workspace", "."), "pom.xml")
        task = agent.create_update_task(pom_path)
        crew = Crew(agents=[agent.agent], tasks=[task], verbose=True)
        result = crew.kickoff()
        print(f"Result: {result}")
        
    elif agent_name == "dsl":
        from agents.dsl_conversion_agent import DSLConversionAgent
        agent = DSLConversionAgent()
        task = agent.create_conversion_task(
            source_code_path=kwargs.get("workspace", "."),
            package_name=kwargs.get("package", "com.example.routes.migrated")
        )
        crew = Crew(agents=[agent.agent], tasks=[task], verbose=True)
        result = crew.kickoff()
        print(f"Result: {result}")
        
    elif agent_name == "service":
        from agents.service_refactor_agent import ServiceRefactorAgent
        agent = ServiceRefactorAgent()
        task = agent.create_refactor_task(
            source_code_path=kwargs.get("workspace", ".")
        )
        crew = Crew(agents=[agent.agent], tasks=[task], verbose=True)
        result = crew.kickoff()
        print(f"Result: {result}")
        
    elif agent_name == "test":
        from agents.test_agent import TestAgent
        agent = TestAgent()
        task = agent.create_test_task(
            project_root_path=kwargs.get("workspace", "."),
            run_full_tests=kwargs.get("full_tests", False)
        )
        crew = Crew(agents=[agent.agent], tasks=[task], verbose=True)
        result = crew.kickoff()
        print(f"Result: {result}")
        
    elif agent_name == "container":
        from agents.containerization_agent import ContainerizationAgent
        agent = ContainerizationAgent()
        task = agent.create_containerization_task(
            project_root_path=kwargs.get("workspace", "."),
            app_name=kwargs.get("app_name", "camel-app"),
            java_version=kwargs.get("java_version", 17)
        )
        crew = Crew(agents=[agent.agent], tasks=[task], verbose=True)
        result = crew.kickoff()
        print(f"Result: {result}")
        
    else:
        print(f"❌ Unknown agent: {agent_name}")
        print("Available agents: config, git, dependency, dsl, service, test, container")


def run_full_migration(
    repository_url: str,
    branch_name: str = "feature/camel4-migration",
    workspace: str = "/tmp/camel-migration",
    java_version: int = 17,
    skip_validation: bool = False,
    checkpoint: bool = False
):
    """
    Run the complete migration workflow using LangGraph
    """
    # Validate environment first
    if not skip_validation:
        if not validate_environment():
            print("\n⚠️  Environment validation failed. Use --skip-validation to bypass.")
            return
    
    print("\n" + "="*60)
    print("🚀 STARTING CAMEL 2 TO CAMEL 4 MIGRATION")
    print("="*60)
    print(f"Repository: {repository_url}")
    print(f"Branch: {branch_name}")
    print(f"Workspace: {workspace}")
    print(f"Java Version: {java_version}")
    print(f"Checkpointing: {'Enabled' if checkpoint else 'Disabled'}")
    print("="*60 + "\n")
    
    # Initialize the LangGraph workflow
    workflow = CamelMigrationLangGraphWorkflow(checkpoint=checkpoint)
    
    # Run the migration
    result = workflow.run_migration(
        repository_url=repository_url,
        branch_name=branch_name,
        workspace_dir=workspace,
        java_version=java_version
    )
    
    # Display results
    print("\n" + "="*60)
    print("📊 MIGRATION RESULTS")
    print("="*60)
    
    if result.get("success"):
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed or partially completed")
    
    if result.get("report"):
        print("\n" + result["report"])
    
    if result.get("errors"):
        print("\n⚠️  Errors encountered:")
        for error in result["errors"]:
            print(f"  - {error}")
    
    print("\n" + "="*60)
    print("Migration process finished")
    print("="*60)
    
    return result


def main():
    """Main entry point for the Camel Migration Agent"""
    parser = argparse.ArgumentParser(
        description="Camel Migration Agent - Migrate Apache Camel 2 to Camel 4 with LangGraph orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full migration
  python main.py --repo https://github.com/user/camel-app.git
  
  # Run with custom workspace
  python main.py --repo https://github.com/user/camel-app.git --workspace /path/to/workspace
  
  # Test individual agent
  python main.py --test-agent config
  python main.py --test-agent git --repo-url https://github.com/user/app.git
  
  # Validate environment only
  python main.py --validate-only
  
  # Enable checkpointing for resumable workflows
  python main.py --repo https://github.com/user/app.git --checkpoint
        """
    )
    
    # Main arguments
    parser.add_argument('--repo', '--repository', 
                        help='Git repository URL to migrate')
    parser.add_argument('--branch', 
                        default='feature/camel4-migration',
                        help='Branch name for migration (default: feature/camel4-migration)')
    parser.add_argument('--workspace', 
                        default='/tmp/camel-migration',
                        help='Local workspace directory (default: /tmp/camel-migration)')
    parser.add_argument('--java-version', 
                        type=int,
                        default=17,
                        choices=[11, 17, 21],
                        help='Target Java version (default: 17)')
    
    # Workflow options
    parser.add_argument('--checkpoint',
                        action='store_true',
                        help='Enable checkpointing for resumable workflows')
    parser.add_argument('--skip-validation',
                        action='store_true',
                        help='Skip environment validation')
    
    # Testing options
    parser.add_argument('--test-agent',
                        choices=['config', 'git', 'dependency', 'dsl', 'service', 'test', 'container'],
                        help='Test a specific agent')
    parser.add_argument('--validate-only',
                        action='store_true',
                        help='Only validate the environment')
    
    # Agent-specific options
    parser.add_argument('--action',
                        help='Action for agent testing (e.g., clone, push for git agent)')
    parser.add_argument('--repo-url',
                        help='Repository URL for agent testing')
    parser.add_argument('--package',
                        default='com.example.routes.migrated',
                        help='Java package name for converted routes')
    parser.add_argument('--app-name',
                        default='camel-app',
                        help='Application name for containerization')
    parser.add_argument('--full-tests',
                        action='store_true',
                        help='Run full test suite')
    parser.add_argument('--message',
                        default='Migrate from Apache Camel 2 to Camel 4',
                        help='Commit message for git operations')
    
    args = parser.parse_args()
    
    # Handle different execution modes
    if args.validate_only:
        # Only validate environment
        success = validate_environment()
        sys.exit(0 if success else 1)
        
    elif args.test_agent:
        # Test individual agent
        run_individual_agent(
            args.test_agent,
            action=args.action,
            repo_url=args.repo_url or args.repo,
            workspace=args.workspace,
            branch=args.branch,
            package=args.package,
            app_name=args.app_name,
            java_version=args.java_version,
            full_tests=args.full_tests,
            message=args.message
        )
        
    elif args.repo:
        # Run full migration workflow
        result = run_full_migration(
            repository_url=args.repo,
            branch_name=args.branch,
            workspace=args.workspace,
            java_version=args.java_version,
            skip_validation=args.skip_validation,
            checkpoint=args.checkpoint
        )
        sys.exit(0 if result.get("success") else 1)
        
    else:
        # No valid action specified
        parser.print_help()
        print("\n❌ Error: Please specify either --repo for full migration or --test-agent for testing")
        sys.exit(1)


if __name__ == "__main__":
    main()