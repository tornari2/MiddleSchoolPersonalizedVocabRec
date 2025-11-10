# Middle School Personalized Vocabulary Recommendation

## Setup

### API Key Configuration

This project requires an OpenAI API key. Follow these steps to set it up securely:

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Add your OpenAI API key to `.env`:**
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

3. **Important Security Notes:**
   - ⚠️ **NEVER commit your `.env` file to git**
   - The `.env` file is already in `.gitignore`
   - Never share your API key publicly
   - If you accidentally expose your key, rotate it immediately at https://platform.openai.com/api-keys

### Getting an OpenAI API Key

If you don't have an OpenAI API key yet:
1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Create a new API key
4. Copy it to your `.env` file

## Usage

[Add project usage instructions here]
