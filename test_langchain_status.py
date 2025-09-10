#!/usr/bin/env python
"""
Test script to check LangChain integration status
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.development')
django.setup()

from apps.templates.rag.services import get_langchain_service, langchain_status

print('=== LangChain Status ===')
status = langchain_status()
for key, value in status.items():
    print(f'{key}: {value}')

print('\n=== Testing LangChain Service ===')
service = get_langchain_service()
print(f'Service instance: {type(service).__name__ if service else "None"}')
print(f'Service available: {service is not None}')

if service:
    print(f'Available factories: {list(service.keys())}')
    print(f'Strategy: {service.get("strategy", "unknown")}')