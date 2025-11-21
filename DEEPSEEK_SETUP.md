# DeepSeek AI Integration Setup Guide

## Overview
This guide walks you through setting up DeepSeek AI as your primary AI provider for PromptCraft, offering a budget-friendly alternative to OpenAI with excellent performance.

## Prerequisites
- DeepSeek API account and API key
- Django project with WebSocket functionality configured
- Redis server running for caching

## Step 1: Get DeepSeek API Key

1. Visit [DeepSeek Platform](https://platform.deepseek.com/)
2. Create an account or log in
3. Navigate to API Keys section
4. Generate a new API key
5. Copy and securely store the API key

## Step 2: Environment Configuration

Add the following environment variables to your `.env` file or system environment:

```env
# DeepSeek Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_MAX_TOKENS=4000
DEEPSEEK_TEMPERATURE=0.7

# Optional: Fallback to OpenAI if needed
OPENAI_API_KEY=your_openai_key_here
```

## Step 3: Django Settings Configuration

Update your `settings.py` to include DeepSeek configuration:

```python
# AI Service Configuration
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
DEEPSEEK_MAX_TOKENS = int(os.getenv('DEEPSEEK_MAX_TOKENS', 4000))
DEEPSEEK_TEMPERATURE = float(os.getenv('DEEPSEEK_TEMPERATURE', 0.7))

# Service Priority (DeepSeek first, then OpenAI fallback)
AI_SERVICE_PRIORITY = ['deepseek', 'openai', 'mock']
```

## Step 4: Test DeepSeek Integration

Create a test script to verify the integration:

```python
import asyncio
import os
import sys
import django

# Add project root to path
sys.path.append('/path/to/your/project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from apps.templates.deepseek_service import DeepSeekService

async def test_deepseek():
    service = DeepSeekService()
    
    # Test intent processing
    print("Testing intent processing...")
    intent_result = await service.process_intent("Help me write a marketing email for a new product launch")
    print(f"Intent: {intent_result}")
    
    # Test prompt optimization
    print("\nTesting prompt optimization...")
    optimization_result = await service.optimize_prompt(
        "Write me something good",
        intent_result.get('processed_data', {})
    )
    print(f"Optimization: {optimization_result}")
    
    # Test content generation
    print("\nTesting content generation...")
    content_result = await service.generate_content(
        "Write a professional email subject line for a product launch"
    )
    print(f"Content: {content_result}")

if __name__ == "__main__":
    asyncio.run(test_deepseek())
```

## Step 5: WebSocket Consumer Updates

The WebSocket consumers have been updated to automatically use DeepSeek as the primary AI provider. No additional configuration needed.

## Step 6: Production Deployment

### For Heroku:
```bash
heroku config:set DEEPSEEK_API_KEY=your_api_key_here
heroku config:set DEEPSEEK_BASE_URL=https://api.deepseek.com
heroku config:set DEEPSEEK_MODEL=deepseek-chat
```

### For Docker:
Update your `docker-compose.yml`:
```yaml
environment:
  - DEEPSEEK_API_KEY=your_api_key_here
  - DEEPSEEK_BASE_URL=https://api.deepseek.com
  - DEEPSEEK_MODEL=deepseek-chat
```

## Cost Comparison

### DeepSeek Pricing (Approximate):
- Input: $0.14 per 1M tokens
- Output: $0.28 per 1M tokens
- **~95% cheaper than GPT-4**

### OpenAI GPT-4 Pricing:
- Input: $30.00 per 1M tokens  
- Output: $60.00 per 1M tokens

## Features Supported

✅ **Intent Classification**: Understands user intent for prompt optimization
✅ **Prompt Optimization**: AI-powered prompt enhancement and refinement  
✅ **Content Generation**: High-quality text generation for various use cases
✅ **Real-time Processing**: WebSocket integration for live optimization
✅ **Caching**: Redis-based caching for improved performance
✅ **Fallback Support**: Automatic fallback to OpenAI or mock services
✅ **Error Handling**: Comprehensive error handling and logging

## API Rate Limits

DeepSeek has generous rate limits:
- 30 requests per minute for free tier
- 180 requests per minute for paid tier
- Burst capacity available

## Monitoring and Logging

The integration includes comprehensive logging:
- API request/response logging
- Performance metrics
- Error tracking with Sentry
- Processing time measurements

## Troubleshooting

### Common Issues:

1. **API Key Invalid**
   - Verify your API key is correct
   - Check if key has necessary permissions

2. **Rate Limit Exceeded**
   - Implement exponential backoff
   - Consider upgrading your plan

3. **Network Timeouts**
   - Check internet connectivity
   - Verify DeepSeek API status

4. **Model Not Found**
   - Ensure you're using supported model names
   - Check DeepSeek documentation for available models

### Debug Mode:
Enable debug logging in Django settings:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/deepseek_debug.log',
        },
    },
    'loggers': {
        'apps.templates.deepseek_service': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Support

- DeepSeek Documentation: https://platform.deepseek.com/docs
- DeepSeek Community: https://github.com/deepseek-ai
- PromptCraft Issues: Create an issue in your project repository

## Security Best Practices

1. **Never commit API keys to version control**
2. **Use environment variables for all secrets**
3. **Rotate API keys regularly**
4. **Monitor API usage for unusual activity**
5. **Implement proper access controls**

## Performance Optimization

1. **Enable caching** for frequently used prompts
2. **Implement request batching** where possible
3. **Use appropriate temperature settings** (0.7 for balanced creativity/consistency)
4. **Monitor token usage** to optimize costs
5. **Implement circuit breakers** for resilience

---

Your DeepSeek integration is now complete! The system will automatically use DeepSeek as the primary AI provider with OpenAI as a fallback, giving you the best of both worlds while keeping costs low.