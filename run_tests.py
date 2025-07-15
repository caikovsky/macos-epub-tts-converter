#!/usr/bin/env python3
"""
Test runner for the TTS application.

This script provides convenient commands for running different types of tests.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> int:
    """Run a command and return the exit code."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user.")
        return 1
    except Exception as e:
        print(f"Error running command: {e}")
        return 1


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Run tests for the TTS application",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Test type selection
    parser.add_argument(
        "test_type",
        choices=["all", "unit", "integration", "security", "performance", "fast", "slow"],
        help="""Test type to run:
  all         - Run all tests
  unit        - Run only unit tests
  integration - Run only integration tests
  security    - Run only security tests
  performance - Run only performance tests
  fast        - Run fast tests (excludes slow tests)
  slow        - Run slow tests only
        """
    )
    
    # Test execution options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "-x", "--exitfirst",
        action="store_true",
        help="Exit on first test failure"
    )
    
    parser.add_argument(
        "-n", "--numprocesses",
        type=int,
        default=1,
        help="Number of parallel processes (default: 1)"
    )
    
    parser.add_argument(
        "--cov",
        action="store_true",
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "--no-cov",
        action="store_true",
        help="Disable coverage reporting"
    )
    
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML coverage report"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Test timeout in seconds (default: 300)"
    )
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test selection based on type
    if args.test_type == "unit":
        cmd.extend(["-m", "unit", "tests/unit/"])
    elif args.test_type == "integration":
        cmd.extend(["-m", "integration", "tests/integration/"])
    elif args.test_type == "security":
        cmd.extend(["-m", "security"])
    elif args.test_type == "performance":
        cmd.extend(["-m", "performance"])
    elif args.test_type == "fast":
        cmd.extend(["-m", "not slow"])
    elif args.test_type == "slow":
        cmd.extend(["-m", "slow"])
    else:  # all
        cmd.append("tests/")
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    
    # Add exit on first failure
    if args.exitfirst:
        cmd.append("-x")
    
    # Add parallel processing
    if args.numprocesses > 1:
        cmd.extend(["-n", str(args.numprocesses)])
    
    # Add timeout
    cmd.extend(["--timeout", str(args.timeout)])
    
    # Coverage options
    if args.cov or not args.no_cov:
        cmd.extend([
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
        
        if args.html:
            cmd.append("--cov-report=html")
    
    # Run the tests
    exit_code = run_command(cmd, f"Running {args.test_type} tests")
    
    if exit_code == 0:
        print(f"\n✅ {args.test_type.capitalize()} tests passed!")
        
        if args.html and (args.cov or not args.no_cov):
            print("\n📊 Coverage report available at: htmlcov/index.html")
            
    else:
        print(f"\n❌ {args.test_type.capitalize()} tests failed!")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main()) 