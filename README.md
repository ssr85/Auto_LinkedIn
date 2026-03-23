# LinkedIn Content Automation System

An intelligent, AI-powered system that automates the entire LinkedIn content creation workflow—from research to publication—with human approval gates using Trello.

## 🌟 Features

- **🔍 AI-Powered Research**: Automatically discovers trending topics based on your target URL and industry
- **📝 Content Generation**: Uses CrewAI agents to create engaging, professional LinkedIn posts
- **✅ Approval Workflow**: Integration with Trello for manual review and approval at each stage
- **🤖 Automated Scheduling**: Daily research and periodic checking for approvals
- **📊 Smart Orchestration**: Seamlessly manages the entire workflow from research to publication
- **🎯 Industry-Specific**: Tailored content for your specific industry and audience

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- OpenAI API key
- Trello account with API access
- LinkedIn Developer App

### Installation

1. **Clone the repository**
2. **Setup venv**: `python -m venv venv && source venv/bin/activate`
3. **Install deps**: `pip install -r requirements.txt`
4. **Setup config**: `cp .env.example .env` and edit your keys.

### 🔑 LinkedIn Configuration & Token Refresh

This project supports **automated token refreshing**. To set it up:

1. Create a LinkedIn App and enable 'Share on LinkedIn' and 'Sign In with LinkedIn'.
2. Add `http://localhost:8000/callback` to your authorized redirect URLs.
3. Run the helper to generate your tokens:
   ```bash
   python get_linkedin_token.py
   ```
4. Copy the `ACCESS_TOKEN` and `REFRESH_TOKEN` into your `.env` file.

The system will now automatically refresh your access token whenever it expires.

## 🏗️ Project Architecture

```
Auto LinkedIN/
├── agents/             # AI CrewAI Agents
├── integrations/       # API Clients (LinkedIn, Trello)
├── utils/              # Helper utilities
├── orchestrator.py     # Main Workflow Logic
├── main.py             # CLI Entry Point
└── get_linkedin_token.py # Auth Helper
```

## 📖 Usage

- **Validate**: `python main.py validate`
- **Full Run**: `python main.py full`
- **Scheduler**: `python main.py schedule`

---
**Built with ❤️ for LinkedIn Automation**
