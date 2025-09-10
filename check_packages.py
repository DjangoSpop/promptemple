#!/usr/bin/env python
"""
Check installed LangChain packages
"""

import subprocess
import sys

def check_langchain_packages():
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True)
        
        langchain_packages = []
        for line in result.stdout.split('\n'):
            if 'langchain' in line.lower():
                langchain_packages.append(line.strip())
        
        print("=== Installed LangChain Packages ===")
        for pkg in langchain_packages:
            print(pkg)
            
        if not langchain_packages:
            print("No LangChain packages found")
            
    except Exception as e:
        print(f"Error checking packages: {e}")

if __name__ == "__main__":
    check_langchain_packages()