#!/usr/bin/env python3
"""Script to run tests with various configurations."""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"❌ {description} failed with exit code {result.returncode}")
        return False
    else:
        print(f"✅ {description} passed")
        return True


def main():
    parser = argparse.ArgumentParser(description="Run tests and quality checks")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--lint", action="store_true", help="Run linting checks")
    parser.add_argument("--format", action="store_true", help="Run code formatting")
    parser.add_argument("--all", action="store_true", help="Run all checks")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    
    args = parser.parse_args()
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    subprocess.run(["cd", str(project_root)], shell=True)
    
    success = True
    
    if args.format or args.all:
        # Format code with black
        success &= run_command(
            ["black", "visey_recommender", "tests", "scripts"],
            "Code formatting (black)"
        )
        
        # Sort imports with isort
        success &= run_command(
            ["isort", "visey_recommender", "tests", "scripts"],
            "Import sorting (isort)"
        )
    
    if args.lint or args.all:
        # Run flake8 linting
        success &= run_command(
            ["flake8", "visey_recommender", "tests"],
            "Linting (flake8)"
        )
    
    if args.unit or args.all:
        # Run unit tests
        cmd = ["pytest", "-m", "unit or not integration"]
        if args.fast:
            cmd.extend(["-m", "not slow"])
        if args.coverage:
            cmd.extend(["--cov=visey_recommender", "--cov-report=term-missing"])
        
        success &= run_command(cmd, "Unit tests")
    
    if args.integration or args.all:
        # Run integration tests
        cmd = ["pytest", "-m", "integration"]
        if args.fast:
            cmd.extend(["-m", "not slow"])
        
        success &= run_command(cmd, "Integration tests")
    
    if not any([args.unit, args.integration, args.lint, args.format, args.all]):
        # Default: run all tests
        cmd = ["pytest"]
        if args.fast:
            cmd.extend(["-m", "not slow"])
        if args.coverage:
            cmd.extend(["--cov=visey_recommender", "--cov-report=term-missing"])
        
        success &= run_command(cmd, "All tests")
    
    if success:
        print("\n🎉 All checks passed!")
        sys.exit(0)
    else:
        print("\n💥 Some checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()