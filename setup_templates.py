#!/usr/bin/env python
"""
Template Setup Script

This script sets up the template database by running population and verification scripts.
It also checks for required dependencies.

Usage:
    python setup_templates.py

Author: GitHub Copilot
Date: July 2, 2025
"""

import os
import sys
import subprocess

def check_requirements():
    """Check if required packages are installed"""
    try:
        import django
        import requests
        import tabulate
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("Installing required dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tabulate", "requests", "django"])
    print("Dependencies installed successfully.")

def run_population_script():
    """Run the template population script"""
    print("\nRunning template population script...")
    subprocess.call([sys.executable, "populate_templates.py"])

def run_verification_script():
    """Run the template verification script"""
    print("\nRunning template verification script...")
    subprocess.call([sys.executable, "verify_templates.py"])

def main():
    """Main function to setup templates"""
    print("Template Setup")
    print("==============\n")
    
    # Check and install dependencies
    if not check_requirements():
        install_dependencies()
    
    # Run population script
    run_population_script()
    
    # Ask to run verification script
    verify = input("\nRun verification script? (y/n): ").lower().strip() == 'y'
    if verify:
        run_verification_script()
    
    print("\nTemplate setup complete!")

if __name__ == "__main__":
    main()
