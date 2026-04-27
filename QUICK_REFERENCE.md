# Quick Reference Card

## 🚀 Quick Start Commands

```bash
# Setup
./setup.sh                    # Initial setup
python main.py validate       # Check configuration

# Run Workflows
python main.py research       # Research topics
python main.py process        # Generate content
python main.py publish        # Post to LinkedIn
python main.py full          # Run all workflows

# Automation
python main.py schedule       # Start scheduler (runs continuously)
```

## 📋 Trello Board Lists (Required)

1. **Pending Topics** - New research results
2. **Approved Topics** - Move here → generates content
3. **Rejected** - Skip these topics
4. **Pending Content** - Generated content
5. **Approved Content** - Move here → posts to LinkedIn
6. **Needs Revision** - Content needing edits
7. **Published** - Auto-archived after posting

## 🔑 Required API Keys

```env
# .env file
OPENAI_API_KEY=sk-...                    # From platform.openai.com
TRELLO_API_KEY=...                       # From trello.com/app-key
TRELLO_TOKEN=...                         # Generated with API key
TRELLO_BOARD_ID=...                      # From board URL or .json
TRELLO_TOPICS_LIST_ID=...                # "Pending Topics" list
TRELLO_CONTENT_LIST_ID=...               # "Pending Content" list
LINKEDIN_ACCESS_TOKEN=...                # OAuth token
LINKEDIN_USER_ID=...                     # Person ID from API
TARGET_URL=https://example.com           # Site to research
TARGET_INDUSTRY=Technology               # Your industry
```

## 🔗 Getting API Credentials

### OpenAI
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy to `.env` as `OPENAI_API_KEY`

### Trello
1. API Key: https://trello.com/app-key
2. Token: Click "Token" link on same page
3. Board ID: Add `.json` to board URL
4. List IDs: Look for "lists" in JSON

### LinkedIn
```bash
python get_linkedin_token.py
# Follow prompts to get token
```

## 🏗️ Project Structure

```
Auto LinkedIN/
├── main.py                 # CLI entry point ⭐
├── config.py              # Configuration
├── orchestrator.py        # Workflow coordination
├── scheduler.py           # Automation
├── agents/
│   ├── research_agent.py  # Topic discovery
│   └── content_agent.py   # Content generation
├── integrations/
│   ├── trello_client.py   # Trello API
│   └── linkedin_client.py # LinkedIn API
├── utils/
│   └── logger.py          # Logging
└── logs/                  # Log files
    ├── app.log           # All logs
    └── error.log         # Errors only
```

## 🔄 Workflow

```
Daily (9 AM)
  └─> Research topics
      └─> Create Trello cards in "Pending Topics"
          └─> [YOU REVIEW & APPROVE]

Every 2 Hours
  └─> Check "Approved Topics"
      └─> Generate content
          └─> Create Trello cards in "Pending Content"
              └─> [YOU REVIEW & APPROVE]

Every Hour
  └─> Check "Approved Content"
      └─> Post to LinkedIn
          └─> Archive Trello card
```

## 🐛 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "Token validation failed" | Regenerate LinkedIn token |
| "No topics generated" | Check TARGET_URL is accessible |
| "Trello list not found" | Verify list IDs in .env |
| "OpenAI rate limit" | Wait or upgrade plan |
| "Module not found" | Run `pip install -r requirements.txt` |

## 📊 Monitoring

```bash
# View logs
tail -f logs/app.log        # All activity
tail -f logs/error.log      # Errors only
grep "ERROR" logs/app.log   # Search errors

# Check status
python main.py config       # Show configuration
python main.py validate     # Test all integrations
```

## ⚙️ Configuration Options

```env
# Content Settings
CONTENT_MIN_LENGTH=500              # Min characters
CONTENT_MAX_LENGTH=3000             # Max characters
MAX_TOPICS_PER_RESEARCH=5           # Topics per day

# Scheduling
RESEARCH_FREQUENCY_HOURS=24         # How often to research

# AI Model
AI_MODEL=gpt-4o        # OpenAI model
# or
AI_MODEL=gpt-3.5-turbo             # Cheaper option
```

## 🎯 Typical Daily Flow

**9:00 AM** - System researches 5 topics → Trello

**10:00 AM** - You review, approve 2 topics in Trello

**11:00 AM** - System generates content for 2 topics

**12:00 PM** - You review content, approve 1

**1:00 PM** - System posts to LinkedIn

**Done!** One quality post with minimal effort

## 💰 Cost Estimates

| Component | Daily Cost | Monthly Cost |
|-----------|-----------|--------------|
| OpenAI API | $0.50-2.00 | $15-60 |
| Trello | Free | Free |
| LinkedIn | Free | Free |
| **Total** | **$0.50-2.00** | **$15-60** |

*Costs vary based on usage and AI model*

## 🔐 Security Checklist

- [ ] `.env` file not in git
- [ ] API keys kept secret
- [ ] Tokens rotated regularly
- [ ] Review content before posting
- [ ] Monitor API usage
- [ ] Use separate keys for test/prod

## 📞 Quick Help

```bash
# Show all commands
python main.py --help

# Show configuration
python main.py config

# Test everything
python main.py validate

# View recent logs
tail -n 50 logs/app.log
```

## 🎓 Learning Resources

- **CrewAI**: https://docs.crewai.com
- **LinkedIn API**: https://learn.microsoft.com/en-us/linkedin/
- **Trello API**: https://developer.atlassian.com/cloud/trello/
- **OpenAI API**: https://platform.openai.com/docs

## 🚨 Emergency Commands

```bash
# Stop scheduler
Ctrl+C (in terminal)

# Clear logs
rm logs/*.log

# Reset everything
rm -rf venv
rm .env
./setup.sh

# Test one workflow
python main.py research --no-banner
```

## 📝 Tips & Tricks

1. **Better Topics**: Use industry-specific news sites for TARGET_URL
2. **Brand Voice**: Edit agent prompts in `agents/*.py`
3. **Scheduling**: Adjust times in `scheduler.py`
4. **Cost Saving**: Use `gpt-3.5-turbo` instead of `gpt-4`
5. **Testing**: Run workflows manually before scheduling

## 🎉 Success Metrics

Track these to measure effectiveness:
- Topics generated per week
- Approval rate (topics → content)
- Posts published per week
- LinkedIn engagement
- Time saved vs manual creation

---

**Need More Help?**
- 📖 Full docs: `README.md`
- 🏗️ Architecture: `ARCHITECTURE.md`
- 🔧 Setup guide: `SETUP_GUIDE.md`
