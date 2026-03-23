# LinkedIn Content Automation System

An intelligent, AI-powered system that automates the entire LinkedIn content creation workflow—from research to publication—with human approval gates using Trello.

## 🌟 Features

- **🔍 AI-Powered Research**: Automatically discovers trending topics based on your target URL and industry
- **📝 Content Generation**: Uses CrewAI agents to create engaging, professional LinkedIn posts
- **✅ Approval Workflow**: Integration with Trello for manual review and approval at each stage
- **🤖 Automated Scheduling**: Daily research and periodic checking for approvals
- **📊 Smart Orchestration**: Seamlessly manages the entire workflow from research to publication
- **🎯 Industry-Specific**: Tailored content for your specific industry and audience

## 📋 Workflow

```
1. Daily Research
   └─> AI researches topics based on URL + Industry
       └─> Creates Trello cards with topic outlines
           └─> Waits for manual approval

2. Content Generation
   └─> Monitors Trello for approved topics
       └─> AI generates LinkedIn content
           └─> Creates Trello cards with content
               └─> Waits for manual approval

3. Publishing
   └─> Monitors Trello for approved content
       └─> Posts to LinkedIn
           └─> Archives Trello cards
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- OpenAI API key (for GPT-4)
- Trello account with API access
- LinkedIn account with API access

### Installation

1. **Clone the repository**
```bash
cd "Auto LinkedIN"
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. **Create necessary directories**
```bash
mkdir logs
```

### Configuration

Edit your `.env` file with the following:

#### OpenAI Configuration
```env
OPENAI_API_KEY=sk-...
AI_MODEL=gpt-4-turbo-preview
```

#### Trello Configuration

1. Get your API key: https://trello.com/app-key
2. Generate a token: https://trello.com/1/authorize?expiration=never&scope=read,write&response_type=token&key=YOUR_API_KEY
3. Get Board and List IDs:
   - Open your Trello board
   - Add `.json` to the URL: `https://trello.com/b/BOARD_ID.json`
   - Find the IDs for your lists

```env
TRELLO_API_KEY=your_api_key
TRELLO_TOKEN=your_token
TRELLO_BOARD_ID=board_id
TRELLO_TOPICS_LIST_ID=list_id_for_topics
TRELLO_CONTENT_LIST_ID=list_id_for_content
```

#### LinkedIn Configuration

1. Create a LinkedIn App: https://www.linkedin.com/developers/apps
2. Get your Access Token using OAuth 2.0
3. Get your User ID (Person ID)

```env
LINKEDIN_ACCESS_TOKEN=your_access_token
LINKEDIN_USER_ID=your_user_id
```

#### Research Configuration
```env
TARGET_URL=https://example.com
TARGET_INDUSTRY=Technology
RESEARCH_FREQUENCY_HOURS=24
```

### Setting Up Trello Board

Create a Trello board with the following lists:

1. **Pending Topics** - For new topic proposals
2. **Approved Topics** - Move cards here to generate content
3. **Rejected** - For topics you don't want
4. **Pending Content** - Generated content awaiting approval
5. **Approved Content** - Move cards here to publish
6. **Needs Revision** - Content that needs changes
7. **Published** - Archived after posting

## 📖 Usage

### Validate Setup
```bash
python main.py validate
```

### View Configuration
```bash
python main.py config
```

### Run Individual Workflows

**Research Topics:**
```bash
python main.py research
```

**Process Approved Topics:**
```bash
python main.py process
```

**Publish Approved Content:**
```bash
python main.py publish
```

**Run Complete Workflow:**
```bash
python main.py full
```

### Start Automated Scheduler

```bash
python main.py schedule
```

This will:
- Run research daily at 9 AM
- Check for approved topics every 2 hours
- Check for approved content every hour

## 🏗️ Project Structure

```
Auto LinkedIN/
├── agents/
│   ├── research_agent.py      # AI agent for topic research
│   └── content_agent.py       # AI agent for content generation
├── integrations/
│   ├── trello_client.py       # Trello API integration
│   └── linkedin_client.py     # LinkedIn API integration
├── utils/
│   └── logger.py              # Logging configuration
├── config.py                  # Configuration management
├── orchestrator.py            # Main workflow orchestration
├── scheduler.py               # Automated scheduling
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## 🤖 How It Works

### 1. Research Agent

The Research Agent uses CrewAI to:
- Analyze your target URL and industry
- Search for trending topics using SerperDevTool
- Scrape relevant content
- Generate detailed outlines with:
  - Hook/opening
  - Key points to cover
  - Supporting details
  - Call-to-action suggestions
  - Relevant hashtags

### 2. Content Agent

The Content Agent creates LinkedIn-optimized posts:
- Follows LinkedIn best practices
- Uses appropriate tone and formatting
- Optimizes for engagement
- Includes hashtags and CTAs
- Validates length (500-3000 characters)

### 3. Trello Integration

Manages approval workflow:
- Creates cards with formatted descriptions
- Monitors card movements between lists
- Archives cards after processing
- Adds comments with status updates

### 4. LinkedIn Integration

Handles publication:
- Posts content using LinkedIn API
- Supports article links
- Tracks post statistics
- Validates access tokens

## ⚙️ Advanced Configuration

### Custom Scheduling

Edit `scheduler.py` to customize timing:

```python
# Daily research at 8 AM
scheduler.schedule_daily_research(hour=8, minute=0)

# Check approvals every 3 hours
scheduler.schedule_process_approvals(interval_hours=3)

# Publish every 30 minutes
scheduler.schedule_publish_content(interval_hours=0.5)
```

### AI Model Selection

In `.env`, you can use different models:

```env
# GPT-4 (recommended)
AI_MODEL=gpt-4-turbo-preview

# GPT-3.5 (faster, cheaper)
AI_MODEL=gpt-3.5-turbo

# Claude (requires ANTHROPIC_API_KEY)
AI_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=your_key
```

### Content Length

Adjust in `.env`:
```env
CONTENT_MIN_LENGTH=500
CONTENT_MAX_LENGTH=3000
MAX_TOPICS_PER_RESEARCH=5
```

## 🔧 Troubleshooting

### Common Issues

**"Setup validation failed"**
- Check all API keys are correct
- Ensure Trello board and list IDs are valid
- Verify LinkedIn token hasn't expired

**"No topics generated"**
- Check that TARGET_URL is accessible
- Verify OpenAI API key has credits
- Review logs in `logs/app.log`

**"Failed to post to LinkedIn"**
- LinkedIn tokens expire - generate a new one
- Check API rate limits
- Verify you have posting permissions

### Logs

Check logs for detailed information:
- `logs/app.log` - All application logs
- `logs/error.log` - Error logs only

## 🛡️ Security Notes

- Never commit your `.env` file
- Rotate API keys regularly
- Use environment-specific tokens for testing
- Review generated content before approval
- Monitor API usage and costs

## 📈 Best Practices

1. **Start Small**: Begin with 2-3 topics per research cycle
2. **Review Carefully**: Always review content before approving
3. **Customize Prompts**: Edit agent prompts to match your brand voice
4. **Monitor Engagement**: Track which topics perform best
5. **Iterate**: Refine your target URL and industry focus based on results

## 🔄 Workflow Example

1. **Morning (9 AM)**: System researches 5 new topics
2. **You Review**: Check Trello, move 2 topics to "Approved"
3. **System Generates**: Within 2 hours, content is generated
4. **You Review**: Edit if needed, approve for publishing
5. **System Publishes**: Content posted to LinkedIn within 1 hour
6. **Archive**: Trello cards archived, cycle complete

## 🚦 API Rate Limits

Be aware of rate limits:
- **OpenAI**: 3,500 requests/min (GPT-4)
- **Trello**: 300 requests/10 seconds/token
- **LinkedIn**: Varies by endpoint, typically 100 requests/day for posting

## 💡 Tips for Better Results

1. **Target URL**: Use industry news sites, blogs, or your own site
2. **Industry**: Be specific (e.g., "B2B SaaS" vs "Technology")
3. **Review Outlines**: Provide feedback in Trello comments
4. **Customize Templates**: Modify agent prompts in agent files
5. **Test First**: Run workflows manually before scheduling

## 📝 License

This project is provided as-is for educational and commercial use.

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional AI models (Anthropic Claude, Google Gemini)
- More social platforms (Twitter, Medium)
- Enhanced analytics and reporting
- A/B testing for content variations
- Image generation integration

## 📧 Support

For issues and questions:
1. Check logs in `logs/` directory
2. Review this README
3. Check API documentation for respective services
4. Create an issue with detailed error logs

## 🎯 Roadmap

- [ ] Support for multiple LinkedIn accounts
- [ ] Content calendar integration
- [ ] Analytics dashboard
- [ ] A/B testing framework
- [ ] Image/media generation
- [ ] Multi-language support
- [ ] Content performance tracking
- [ ] Advanced scheduling (specific dates/times)

---

## Running the System
# How to Start Your Automation:
Run Research:
bash
- python main.py research

# Approve Topics: Move cards to "Approved Topics" in Trello.
Process Drafts:
bash
- python main.py process

# Schedule Posts: Set a Due Date on any card in "Approved Content".
Publish (or Start Scheduler):
bash
- python main.py publish   # Manual publish
# OR 
- python main.py schedule  # Start the background automation

**Built with ❤️ using CrewAI, OpenAI, and Python**

*Automate your LinkedIn presence while maintaining quality and authenticity*
