# DeepSeek API Integration Guide

## Overview
DeepSeek is a cost-effective alternative to OpenAI that provides excellent AI capabilities at a fraction of the cost. This guide will help you set up DeepSeek API integration for your PromptCraft application.

## Why DeepSeek?

### Cost Comparison (Approximate)
- **OpenAI GPT-4**: $30-60 per 1M tokens
- **DeepSeek**: $0.14-0.28 per 1M tokens (up to 200x cheaper!)
- **Quality**: Comparable performance for most use cases

### Key Benefits
- 🎯 **Budget Friendly**: Dramatically lower costs
- 🚀 **High Performance**: Fast response times
- 🔧 **Easy Integration**: OpenAI-compatible API
- 📊 **Reliable**: Professional service with good uptime

## Getting Started

### 1. Sign Up for DeepSeek API

1. Visit [DeepSeek Platform](https://platform.deepseek.com)
2. Create an account
3. Navigate to API Keys section
4. Generate a new API key
5. Copy your API key (starts with `sk-`)

### 2. Environment Setup

Create a `.env` file in your project root:

```bash
# Copy from .env.example and configure:
cp .env.example .env
```

Edit `.env` and add your DeepSeek API key:

```env
# DeepSeek Configuration (Primary - Budget Friendly)
DEEPSEEK_API_KEY=sk-your-actual-deepseek-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_DEFAULT_MODEL=deepseek-chat
DEEPSEEK_CODER_MODEL=deepseek-coder

# Provider Priority (DeepSeek first)
AI_PROVIDER_PRIORITY=deepseek,openai,anthropic
ENABLE_AI_FALLBACK=True
```

### 3. Install Dependencies

Run the following command to ensure all required packages are installed:

```bash
pip install -r requirements.txt
```

Key packages for DeepSeek integration:
- `openai>=1.0.0` (for API compatibility)
- `httpx>=0.24.0` (for async HTTP requests)
- `langchain-openai` (for LangChain integration)

### 4. Test the Integration

Run our comprehensive test suite:

```bash
python test_deepseek_integration.py
```

This will test:
- DeepSeek client initialization
- API connectivity (if key is configured)
- LangChain integration
- WebSocket functionality
- Database connections

### 5. Start the Application

```bash
# Development
python manage.py runserver

# Production with Daphne (WebSocket support)
daphne -b 0.0.0.0 -p 8000 promptcraft.asgi:application
```

## Configuration Details

### Available Models

DeepSeek offers several models optimized for different use cases:

- **deepseek-chat**: General conversation and text generation
- **deepseek-coder**: Code generation and programming tasks
- **deepseek-math**: Mathematical reasoning and calculations

### Configuration Options

In your settings, you can configure:

```python
LANGCHAIN_SETTINGS = {
    # Provider priority - DeepSeek first for cost savings
    'AI_PROVIDER_PRIORITY': ['deepseek', 'openai', 'anthropic'],
    
    # DeepSeek specific settings
    'DEEPSEEK_SETTINGS': {
        'api_key': os.getenv('DEEPSEEK_API_KEY'),
        'base_url': 'https://api.deepseek.com/v1',
        'default_model': 'deepseek-chat',
        'coder_model': 'deepseek-coder',
        'max_tokens': 4000,
        'temperature': 0.7,
        'timeout': 30,
        'max_retries': 3,
    },
    
    # Fallback behavior
    'ENABLE_AI_FALLBACK': True,
    'FALLBACK_TO_MOCK': True,  # If no API keys work
}
```

## Usage Examples

### Basic Chat Completion

```python
from apps.templates.deepseek_integration import DeepSeekClient

client = DeepSeekClient()

response = await client.create_completion(
    messages=[
        {"role": "user", "content": "Optimize this marketing prompt for better engagement"}
    ],
    model="deepseek-chat",
    max_tokens=500
)

print(response['choices'][0]['message']['content'])
```

### LangChain Integration

```python
from apps.templates.langchain_services import LangChainOptimizationService

service = LangChainOptimizationService()

# Will automatically use DeepSeek if configured
optimized_prompt = service.optimize_prompt(
    prompt="Write a marketing email",
    context="E-commerce product launch",
    optimization_type="engagement"
)
```

### WebSocket Integration

The WebSocket consumers automatically use the configured AI provider:

```javascript
// Frontend WebSocket usage
const ws = new WebSocket('ws://localhost:8000/ws/chat/');

// Send optimization request
ws.send(JSON.stringify({
    type: 'optimization_request',
    prompt: 'Create a social media post',
    context: 'Tech startup product launch',
    optimization_type: 'viral'
}));

// Receive optimized result
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'optimization_result') {
        console.log('Optimized prompt:', data.result);
    }
};
```

## Cost Optimization Tips

### 1. Smart Token Management
- Use `max_tokens` parameter to limit response length
- Implement request batching for multiple prompts
- Cache frequently requested optimizations

### 2. Model Selection
- Use `deepseek-chat` for general prompts
- Use `deepseek-coder` only for code-related tasks
- Adjust temperature based on creativity needs

### 3. Request Optimization
```python
# Example: Batch multiple prompts
prompts_to_optimize = [
    "Write a sales email",
    "Create a product description", 
    "Generate a blog title"
]

# Process in single request
batch_request = "Optimize these prompts:\n" + "\n".join(
    f"{i+1}. {prompt}" for i, prompt in enumerate(prompts_to_optimize)
)
```

## Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   Error: Invalid API key
   ```
   - Verify your API key is correct
   - Check if key has sufficient credits
   - Ensure key is properly set in environment

2. **Rate Limiting**
   ```
   Error: Rate limit exceeded
   ```
   - Implement exponential backoff
   - Reduce request frequency
   - Consider upgrading your plan

3. **Connection Timeout**
   ```
   Error: Request timeout
   ```
   - Increase timeout in settings
   - Check network connectivity
   - Verify DeepSeek service status

### Debug Mode

Enable debug logging in your `.env`:

```env
LOG_LEVEL=DEBUG
DJANGO_LOG_LEVEL=DEBUG
```

This will show detailed API request/response logs.

### Fallback Behavior

If DeepSeek API fails, the system will:
1. Try OpenAI (if configured)
2. Try Anthropic (if configured)  
3. Fall back to mock responses
4. Log the failure for debugging

## Monitoring and Analytics

### API Usage Tracking

Monitor your DeepSeek usage:

```python
# Check API usage (implement in your admin panel)
from apps.analytics.models import APIUsageLog

daily_usage = APIUsageLog.objects.filter(
    provider='deepseek',
    date=today()
).aggregate(
    total_requests=Count('id'),
    total_tokens=Sum('tokens_used')
)
```

### Cost Calculation

```python
# Estimate costs
DEEPSEEK_COST_PER_1K_TOKENS = 0.00014  # $0.14 per 1M tokens

def calculate_cost(tokens_used):
    return (tokens_used / 1000) * DEEPSEEK_COST_PER_1K_TOKENS

monthly_cost = calculate_cost(monthly_token_usage)
print(f"Estimated monthly cost: ${monthly_cost:.2f}")
```

## Performance Optimization

### 1. Connection Pooling
The DeepSeek client uses connection pooling for better performance:

```python
# Configured automatically in DeepSeekClient
import httpx

client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    timeout=30.0
)
```

### 2. Caching
Implement caching for frequently used prompts:

```python
from django.core.cache import cache

def get_cached_optimization(prompt_hash):
    return cache.get(f"optimization:{prompt_hash}")

def cache_optimization(prompt_hash, result):
    cache.set(f"optimization:{prompt_hash}", result, 3600)  # 1 hour
```

### 3. Async Processing
All DeepSeek integration is async-ready:

```python
import asyncio

async def optimize_multiple_prompts(prompts):
    tasks = [
        service.optimize_prompt(prompt) 
        for prompt in prompts
    ]
    return await asyncio.gather(*tasks)
```

## Security Best Practices

### 1. API Key Management
- Never commit API keys to version control
- Use environment variables
- Rotate keys regularly
- Monitor for unauthorized usage

### 2. Request Validation
- Validate all user inputs
- Implement rate limiting
- Log suspicious activity
- Use HTTPS only

### 3. Data Privacy
- Don't send sensitive data to AI APIs
- Implement data anonymization
- Follow GDPR/privacy regulations
- Provide opt-out options

## Production Deployment

### 1. Environment Variables
Set these in your production environment:

```bash
export DEEPSEEK_API_KEY="sk-your-production-key"
export AI_PROVIDER_PRIORITY="deepseek,openai"
export ENABLE_AI_FALLBACK="True"
export LOG_LEVEL="INFO"
```

### 2. Health Checks
Implement health checks for the AI service:

```python
# Add to your health check endpoint
async def check_ai_service():
    try:
        client = DeepSeekClient()
        response = await client.create_completion(
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
        return "healthy"
    except Exception:
        return "unhealthy"
```

### 3. Monitoring
Set up monitoring for:
- API response times
- Error rates
- Token usage
- Cost tracking

## Support and Resources

### Documentation
- [DeepSeek API Documentation](https://platform.deepseek.com/api-docs)
- [LangChain Integration Guide](https://python.langchain.com/docs/)
- [Django Channels WebSocket Guide](https://channels.readthedocs.io/)

### Community
- [DeepSeek Discord](https://discord.gg/deepseek)
- [GitHub Issues](https://github.com/your-repo/issues)

### Getting Help
If you encounter issues:
1. Check the troubleshooting section above
2. Run the test suite: `python test_deepseek_integration.py`
3. Enable debug logging
4. Check DeepSeek service status
5. Contact support with error logs

## Conclusion

DeepSeek integration provides a cost-effective solution for AI-powered prompt optimization. With proper setup and configuration, you can achieve excellent results at a fraction of the cost of other providers.

The integration includes:
- ✅ OpenAI-compatible API
- ✅ LangChain integration
- ✅ WebSocket real-time support
- ✅ Automatic fallback mechanisms
- ✅ Comprehensive error handling
- ✅ Performance optimization
- ✅ Cost monitoring tools

Start with the basic setup and gradually explore advanced features as your application grows.