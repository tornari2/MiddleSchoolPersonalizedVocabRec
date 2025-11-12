# 🚀 OpenAI Integration Setup for Dev Environment

## Prerequisites

1. **Get OpenAI API Key**: Visit [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. **Copy your key** (starts with `sk-`)
3. **Install dependencies**: `pip install openai python-dotenv`

## Quick Setup (3 Steps)

### Step 1: Configure Environment
```bash
# Your .env file has been created with the template
# Edit it with your API key:
nano .env

# Replace this line:
OPENAI_API_KEY=your_openai_api_key_here

# With your actual key:
OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 2: Test Integration
```bash
# Test that OpenAI integration works
python test_openai_integration.py
```

### Step 3: Enable Enhanced Recommendations
```bash
# Edit .env to enable OpenAI recommendations:
nano .env

# Change this line:
USE_OPENAI_RECOMMENDATIONS=false

# To:
USE_OPENAI_RECOMMENDATIONS=true
```

## Configuration Options

### Model Settings
```bash
# Model (gpt-3.5-turbo is cost-effective, gpt-4 is more accurate)
OPENAI_MODEL=gpt-3.5-turbo

# Temperature (0.0 = consistent, 1.0 = creative)
OPENAI_TEMPERATURE=0.2

# Max tokens per recommendation generation
OPENAI_MAX_TOKENS=500
```

### Recommendation Engine Integration
```bash
# Enable/disable AI-enhanced recommendations
USE_OPENAI_RECOMMENDATIONS=true
```

## Testing Commands

### Test OpenAI Service
```bash
python test_openai_integration.py
```

### Test Enhanced Recommendations
```bash
# Enable OpenAI in .env first, then:
python -c "
from recommendation_engine import RecommendationEngine
engine = RecommendationEngine(use_openai_enhancement=True)
print('✅ OpenAI-enhanced recommendation engine ready')
"
```

### Generate Sample Recommendations
```bash
python -c "
from recommendation_engine import RecommendationEngine
from test_openai_integration import create_sample_recommendation_data
import json

# Create sample data
create_sample_recommendation_data()

# Load sample data
with open('test_recommendation_data.json') as f:
    data = json.load(f)

# Generate recommendations
engine = RecommendationEngine(use_openai_enhancement=True)
result = engine.generate_recommendations(
    'TEST001',
    data['student_profile'],
    {'writing_samples': data['writing_samples']}
)

print(f'Generated {len(result[\"recommendations\"])} recommendations')
for rec in result['recommendations'][:3]:
    print(f'- {rec[\"word\"]}: {rec[\"definition\"]}')
"
```

## Production Deployment

### AWS Lambda Setup
For production, use AWS Secrets Manager instead of `.env` files:

1. **Store secret in AWS**:
```bash
aws secretsmanager create-secret \
    --name "vocab-rec-engine/openai-api-key-dev" \
    --secret-string "your_api_key_here"
```

2. **Update Lambda environment**:
```terraform
resource "aws_lambda_function" "recommendation_engine" {
  environment {
    variables = {
      OPENAI_API_KEY_SECRET = aws_secretsmanager_secret.openai_api_key.name
    }
  }
}
```

3. **Lambda code updates** (automatic via OpenAI service)

## Cost Estimation

### API Usage Costs
- **gpt-3.5-turbo**: ~$0.002 per 1K tokens
- **gpt-4**: ~$0.03 per 1K tokens

### Typical Usage per Student
- **Vocabulary analysis**: 200-500 tokens
- **Recommendation generation**: 300-600 tokens
- **Cost per student**: $0.001 - $0.005

### Monthly Estimate (100 students)
- **Low usage**: $0.10 - $0.50/month
- **High usage**: $1.00 - $5.00/month

## Troubleshooting

### Common Issues

**"OpenAI API key not provided"**
```bash
# Check .env file
cat .env | grep OPENAI_API_KEY

# Make sure it's loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OPENAI_API_KEY')[:10] + '...')"
```

**"Rate limit exceeded"**
- Wait a few minutes
- Reduce request frequency
- Consider upgrading OpenAI plan

**"Invalid API key"**
- Verify key starts with `sk-`
- Check for extra spaces/characters
- Regenerate key if needed

### Debug Commands
```bash
# Check environment loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('Key loaded:', bool(os.getenv('OPENAI_API_KEY')))"

# Test API connectivity
python -c "from openai_service import OpenAIService; service = OpenAIService(); print('API available:', service.is_available())"
```

## Security Notes

- ✅ `.env` files are gitignored
- ✅ Never commit API keys
- ✅ Use Secrets Manager for production
- ✅ Rotate keys regularly
- ✅ Monitor API usage

## Next Steps

1. **Test locally** with sample data
2. **Deploy to dev environment** with Secrets Manager
3. **Monitor performance** and costs
4. **Scale to staging/production** when ready

Your OpenAI integration is ready! 🎉

Need help with any of these steps?
