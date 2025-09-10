#!/usr/bin/env python3
"""
Test DeepSeek API integration
"""

import os
import requests
import json

def test_deepseek_api():
    print('Testing DeepSeek API configuration...')
    
    api_key = os.environ.get('DEEPSEEK_API_KEY', 'NOT SET')
    base_url = os.environ.get('DEEPSEEK_BASE_URL', 'NOT SET')
    
    print(f'DEEPSEEK_API_KEY: {api_key[:20]}...' if api_key != 'NOT SET' else 'DEEPSEEK_API_KEY: NOT SET')
    print(f'DEEPSEEK_BASE_URL: {base_url}')
    
    if api_key == 'NOT SET':
        print('❌ DeepSeek API key not found in environment')
        return False
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'user', 'content': 'Hello! Can you help me optimize prompts?'}
            ],
            'max_tokens': 50
        }
        
        print('\nTesting DeepSeek API connection...')
        response = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print('✅ DeepSeek API test successful!')
            print(f'Response: {result["choices"][0]["message"]["content"]}')
            return True
        else:
            print(f'❌ API Error: {response.status_code} - {response.text}')
            return False
            
    except Exception as e:
        print(f'❌ Connection error: {e}')
        return False

if __name__ == "__main__":
    test_deepseek_api()