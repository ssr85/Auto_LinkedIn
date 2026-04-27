# Setup Guide - LinkedIn Content Automation System

This guide will walk you through the complete setup process.

## 📋 Prerequisites Checklist

Before you begin, ensure you have:

- [ ] Python 3.9+ installed
- [ ] A Trello account
- [ ] A LinkedIn account
- [ ] An OpenAI API key (with GPT-4 access)
- [ ] Basic familiarity with command line

## 🔧 Step-by-Step Setup

### Step 1: Install Python Dependencies

```bash
# Navigate to project directory
cd "Auto LinkedIN"

# Run setup script (Mac/Linux)
chmod +x setup.sh
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
mkdir logs
```

### Step 2: Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-`)
4. Save it - you won't be able to see it again!

**Cost Estimate**: ~$0.50-2.00 per day for research + content generation

### Step 3: Set Up Trello

#### 3.1: Create API Credentials

1. **Get API Key**:
   - Go to https://trello.com/app-key
   - Copy your API Key

2. **Generate Token**:
   - On the same page, click "Token" link
   - Or visit: `https://trello.com/1/authorize?expiration=never&scope=read,write&response_type=token&key=YOUR_API_KEY`
   - Replace `YOUR_API_KEY` with your actual key
   - Click "Allow"
   - Copy the token

#### 3.2: Create Your Board

1. Create a new Trello board: "LinkedIn Content Automation"
2. Create these lists (in this order):
   - **Pending Topics** (for new research)
   - **Approved Topics** (move here to generate content)
   - **Rejected** (topics you don't want)
   - **Pending Content** (generated content)
   - **Approved Content** (move here to publish)
   - **Needs Revision** (content requiring edits)
   - **Published** (archived after posting)

#### 3.3: Get Board and List IDs

**Method 1: Using JSON Export**
```bash
# Open your board in browser
# Add .json to the end of URL
https://trello.com/b/XXXXXXXX.json

# Look for:
{
  "id": "BOARD_ID",
  "lists": [
    {"id": "LIST_ID_1", "name": "Pending Topics"},
    {"id": "LIST_ID_2", "name": "Approved Topics"},
    ...
  ]
}
```

**Method 2: Using Browser Console**
```javascript
// Open your board
// Press F12 (Developer Tools)
// Run in console:
TrelloPowerUp.util.board.lists()
```

### Step 4: Set Up LinkedIn API Access

LinkedIn API access requires a registered application.

#### 4.1: Create LinkedIn App

1. Go to https://www.linkedin.com/developers/apps
2. Click "Create app"
3. Fill in required information:
   - App name: "Content Automation"
   - LinkedIn Page: Your company page (or create one)
   - Privacy policy URL: (your website or use a free one)
   - App logo: Upload any logo

4. Click "Create app"

#### 4.2: Get OAuth Credentials

1. In your app, go to "Auth" tab
2. Note your Client ID and Client Secret
3. Add redirect URL: `http://localhost:8000/callback`

#### 4.3: Request API Access

1. Go to "Products" tab
2. Request access to:
   - "Share on LinkedIn"
   - "Sign In with LinkedIn"

3. Wait for approval (usually instant for personal use)

#### 4.4: Generate Access Token

**Option 1: Use LinkedIn OAuth Playground**
1. Go to https://www.linkedin.com/developers/tools/oauth
2. Follow the OAuth flow
3. Copy the access token

**Option 2: Manual OAuth Flow**
```bash
# Install a simple HTTP server for callback
pip install oauth2-client

# Use the LinkedIn OAuth helper script
python get_linkedin_token.py
```

#### 4.5: Get Your User ID

```bash
# Using curl with your access token
curl -X GET \
  'https://api.linkedin.com/v2/me' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'

# Look for: "id": "YOUR_USER_ID"
```

### Step 5: Configure Environment Variables

Edit your `.env` file:

```env
# OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
AI_MODEL=gpt-4o

# Trello
TRELLO_API_KEY=your_32_char_api_key
TRELLO_TOKEN=your_64_char_token
TRELLO_BOARD_ID=your_board_id
TRELLO_TOPICS_LIST_ID=your_pending_topics_list_id
TRELLO_CONTENT_LIST_ID=your_pending_content_list_id

# LinkedIn
LINKEDIN_ACCESS_TOKEN=your_access_token
LINKEDIN_USER_ID=your_person_id

# Research Configuration
TARGET_URL=https://techcrunch.com
TARGET_INDUSTRY=Technology
RESEARCH_FREQUENCY_HOURS=24

# Content Settings
CONTENT_MIN_LENGTH=500
CONTENT_MAX_LENGTH=3000
MAX_TOPICS_PER_RESEARCH=5
```

### Step 6: Validate Setup

```bash
python main.py validate
```

You should see:
```
✓ LinkedIn integration validated
✓ Trello integration validated
✓ All systems validated successfully
```

### Step 7: Test the System

#### Test 1: Research
```bash
python main.py research
```

Check your Trello board - you should see new cards in "Pending Topics"

#### Test 2: Content Generation
1. Move a topic card to "Approved Topics"
2. Run:
```bash
python main.py process
```

Check your Trello - you should see new content card in "Pending Content"

#### Test 3: Publishing
1. Move a content card to "Approved Content"
2. Run:
```bash
python main.py publish
```

Check your LinkedIn profile - you should see the new post!

### Step 8: Start Automation

```bash
python main.py schedule
```

This runs continuously and:
- Researches topics daily at 9 AM
- Checks for approvals every 2 hours
- Publishes approved content every hour

## 🔒 Security Best Practices

1. **Never commit `.env` file**
   ```bash
   # Verify it's in .gitignore
   cat .gitignore | grep .env
   ```

2. **Rotate tokens regularly**
   - LinkedIn tokens: Every 60 days
   - OpenAI keys: Every 90 days
   - Trello tokens: Annually

3. **Monitor API usage**
   - OpenAI: https://platform.openai.com/usage
   - LinkedIn: Check developer app dashboard

4. **Use environment-specific configs**
   - Production: `.env`
   - Testing: `.env.test`
   - Development: `.env.dev`

## 🐛 Troubleshooting

### Issue: "Failed to validate LinkedIn token"

**Solutions**:
1. Token expired - generate new one
2. Wrong permissions - ensure "Share on LinkedIn" is enabled
3. Wrong user ID - verify with API call

### Issue: "Trello list not found"

**Solutions**:
1. Verify list IDs are correct
2. Ensure list names match exactly
3. Check token has write permissions

### Issue: "OpenAI rate limit error"

**Solutions**:
1. You've hit rate limits - wait and retry
2. Reduce `MAX_TOPICS_PER_RESEARCH`
3. Upgrade OpenAI plan for higher limits

### Issue: "No topics generated"

**Solutions**:
1. Check TARGET_URL is accessible
2. Try a different, more content-rich URL
3. Be more specific with INDUSTRY
4. Check OpenAI API logs for errors

## 📊 Monitoring

### Check Logs
```bash
# View all logs
tail -f logs/app.log

# View errors only
tail -f logs/error.log

# Search for specific issues
grep "ERROR" logs/app.log
```

### View System Status
```bash
# Show configuration
python main.py config

# Validate all systems
python main.py validate
```

## 🎯 Next Steps

Once setup is complete:

1. **Customize Agent Prompts**
   - Edit `agents/research_agent.py` for better research
   - Edit `agents/content_agent.py` for your brand voice

2. **Adjust Scheduling**
   - Edit `scheduler.py` for your timezone
   - Change frequency of checks

3. **Monitor Performance**
   - Track which topics get most engagement
   - Refine your TARGET_URL and INDUSTRY

4. **Scale Up**
   - Increase `MAX_TOPICS_PER_RESEARCH`
   - Add multiple target URLs
   - Create content variations

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `logs/app.log`
2. Review this guide
3. Verify all API keys are valid
4. Test each component individually
5. Check API service status pages

## ✅ Setup Complete!

You now have a fully automated LinkedIn content system! 🎉

Remember to:
- Review generated content before approving
- Monitor API costs
- Adjust prompts to match your voice
- Engage with comments on your posts

Happy automating! 🚀
