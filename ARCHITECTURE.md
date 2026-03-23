# Architecture Documentation

## System Overview

The LinkedIn Content Automation System is built using a modular, agent-based architecture powered by CrewAI. It orchestrates multiple AI agents and integrations to automate the entire content lifecycle.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Scheduler (APScheduler)                  │
│  - Daily research triggers                                   │
│  - Periodic approval checks                                  │
│  - Publishing automation                                     │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Content Orchestrator                      │
│  - Workflow coordination                                     │
│  - State management                                          │
│  - Error handling & retry logic                              │
└─────┬──────────────┬──────────────┬─────────────────────────┘
      │              │              │
      ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌────────────┐
│ Research │  │ Content  │  │Integrations│
│  Agent   │  │  Agent   │  │   Layer    │
└──────────┘  └──────────┘  └────────────┘
      │              │              │
      ├─ OpenAI     ├─ OpenAI     ├─ Trello API
      ├─ SerperDev  ├─ LangChain  ├─ LinkedIn API
      └─ Scraping   └─ Validation └─ Webhooks (future)
```

## Component Architecture

### 1. Core Components

#### Orchestrator (`orchestrator.py`)
**Responsibility**: Main workflow coordination

```python
ContentOrchestrator
├── run_daily_research()        # Trigger research workflow
├── process_approved_topics()   # Generate content from approved topics
├── publish_approved_content()  # Post to LinkedIn
└── validate_setup()            # System health check
```

**Flow**:
1. Initializes all agents and integrations
2. Manages workflow state transitions
3. Handles errors and retries
4. Logs all operations

#### Scheduler (`scheduler.py`)
**Responsibility**: Automated task execution

```python
WorkflowScheduler
├── schedule_daily_research()      # Cron-based scheduling
├── schedule_process_approvals()   # Interval-based checks
├── schedule_publish_content()     # Continuous monitoring
└── BackgroundScheduler            # APScheduler instance
```

**Features**:
- Cron-based scheduling for daily tasks
- Interval-based scheduling for periodic checks
- Job management and monitoring
- Graceful shutdown handling

### 2. AI Agents Layer

Built using CrewAI framework for autonomous agent orchestration.

#### Research Agent (`agents/research_agent.py`)

**Purpose**: Discover and research content topics

**Tools**:
- `SerperDevTool`: Web search for trending topics
- `ScrapeWebsiteTool`: Extract content from target URLs

**Tasks**:
1. **Research Task**: Analyze URL + industry, identify trends
2. **Outline Task**: Create detailed content outlines

**Output**:
```python
{
    'title': str,
    'outline': str,
    'metadata': {
        'source_url': str,
        'industry': str,
        'research_date': ISO datetime,
        'keywords': list[str]
    }
}
```

#### Content Agent (`agents/content_agent.py`)

**Purpose**: Generate LinkedIn-optimized content

**Tasks**:
1. **Generation Task**: Create initial content
2. **Review Task**: Polish and optimize

**Validation**:
- Length checks (500-3000 chars)
- Formatting validation
- Engagement optimization
- Hashtag extraction

**Output**:
```python
{
    'content': str,
    'topic': str,
    'metadata': {
        'generated_date': ISO datetime,
        'word_count': int,
        'char_count': int,
        'hashtags': list[str]
    }
}
```

### 3. Integration Layer

#### Trello Client (`integrations/trello_client.py`)

**Purpose**: Approval workflow management

**Key Methods**:
```python
TrelloManager
├── create_topic_card()          # New research results
├── create_content_card()        # Generated content
├── get_approved_topics()        # Poll for approvals
├── get_approved_content()       # Poll for publish approval
├── archive_card()               # Cleanup after processing
└── add_comment()                # Status updates
```

**Board Structure**:
```
Trello Board: "LinkedIn Content Automation"
├── Pending Topics        # New research (system created)
├── Approved Topics       # Move here to generate content
├── Rejected             # Topics to skip
├── Pending Content      # Generated content (system created)
├── Approved Content     # Move here to publish
├── Needs Revision       # Content requiring edits
└── Published            # Archived after posting
```

#### LinkedIn Client (`integrations/linkedin_client.py`)

**Purpose**: Content publishing

**Key Methods**:
```python
LinkedInManager
├── post_content()               # Publish to LinkedIn
├── validate_token()             # Check authentication
├── get_post_stats()             # Analytics (future)
├── format_content_with_hashtags()
└── preview_post()               # Pre-publish preview
```

**API Usage**:
- `/v2/ugcPosts`: Create posts
- `/v2/me`: User info
- `/v2/socialActions`: Analytics

### 4. Configuration Layer

#### Config (`config.py`)
Uses Pydantic Settings for type-safe configuration:

```python
Settings (BaseSettings)
├── API Credentials
│   ├── openai_api_key
│   ├── anthropic_api_key (optional)
│   ├── trello_api_key, trello_token
│   └── linkedin_access_token
├── Service IDs
│   ├── trello_board_id
│   ├── trello_topics_list_id
│   └── linkedin_user_id
├── Research Config
│   ├── target_url
│   ├── target_industry
│   └── research_frequency_hours
└── System Config
    ├── ai_model
    ├── max_topics_per_research
    └── content_min/max_length
```

**Environment Loading**:
- Reads from `.env` file
- Type validation via Pydantic
- Default values for optional settings
- Case-insensitive keys

#### Logger (`utils/logger.py`)
Loguru-based structured logging:

```python
Logger Configuration
├── Console Output (colored, formatted)
├── Error Log (logs/error.log)
│   ├── Rotation: 10 MB
│   └── Retention: 30 days
└── Application Log (logs/app.log)
    ├── Rotation: 50 MB
    └── Retention: 7 days
```

## Data Flow

### Research Workflow

```
1. Scheduler Trigger
   └─> orchestrator.run_daily_research()
       └─> research_agent.research_topics(url, industry)
           ├─> SerperDevTool: Search trends
           ├─> ScrapeWebsiteTool: Extract content
           └─> CrewAI: Execute research task
               └─> Parse results into topic objects
                   └─> For each topic:
                       └─> trello.create_topic_card()
                           └─> Card created in "Pending Topics"
```

### Content Generation Workflow

```
2. Approval Check (every 2 hours)
   └─> orchestrator.process_approved_topics()
       └─> trello.get_approved_topics()
           └─> For each approved topic:
               └─> content_agent.generate_content(topic)
                   ├─> CrewAI: Generate task
                   ├─> CrewAI: Review task
                   └─> Validate output
                       └─> trello.create_content_card()
                           ├─> Card created in "Pending Content"
                           └─> Original topic card archived
```

### Publishing Workflow

```
3. Publish Check (every hour)
   └─> orchestrator.publish_approved_content()
       └─> trello.get_approved_content()
           └─> For each approved content:
               └─> linkedin.post_content()
                   ├─> Format content
                   ├─> API call to LinkedIn
                   ├─> Validate response
                   └─> On success:
                       ├─> trello.add_comment() (with post ID)
                       └─> trello.archive_card()
```

## Error Handling Strategy

### Retry Logic

```python
# Configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Implementation
for attempt in range(MAX_RETRIES):
    try:
        result = operation()
        break
    except RetryableError as e:
        if attempt < MAX_RETRIES - 1:
            log.warning(f"Retry {attempt + 1}/{MAX_RETRIES}")
            time.sleep(RETRY_DELAY)
        else:
            log.error("Max retries reached")
            raise
```

### Error Categories

1. **API Errors** (Retryable)
   - Rate limits → Exponential backoff
   - Timeouts → Retry with longer timeout
   - 5xx errors → Retry

2. **Validation Errors** (Non-retryable)
   - Invalid content length
   - Missing required fields
   - Configuration errors

3. **Auth Errors** (Alert)
   - Expired tokens
   - Invalid credentials
   - Permission issues

### Logging Strategy

```python
# All operations log:
log.info("Starting operation X")      # Start
log.debug("Intermediate step Y")      # Progress
log.info("✓ Operation X completed")   # Success
log.error("✗ Operation X failed: Z")  # Failure
```

## Security Considerations

### 1. Credential Management
- All secrets in `.env` (not in code)
- `.env` in `.gitignore`
- No hardcoded tokens
- Pydantic validation for presence

### 2. API Security
- HTTPS only
- Token rotation recommended
- Rate limit compliance
- Request timeout enforcement

### 3. Data Privacy
- No sensitive data in logs
- Trello cards can be made private
- LinkedIn posts are public by default

### 4. Access Control
- Trello: Token-based auth
- LinkedIn: OAuth 2.0
- OpenAI: API key auth

## Scalability Considerations

### Current Limits
- Research: 5 topics/day (configurable)
- Content: Unlimited (rate-limited by approvals)
- Publishing: Unlimited (rate-limited by LinkedIn API)

### Scaling Options

1. **Horizontal Scaling**
   - Multiple instances for different industries
   - Separate Trello boards per brand
   - Different LinkedIn accounts

2. **Performance Optimization**
   - Parallel API calls where possible
   - Content caching
   - Result memoization

3. **Database Addition** (Future)
   - Track all generated content
   - Analytics and metrics
   - A/B testing results

## Monitoring & Observability

### Current Monitoring

1. **Logs**
   - Application logs: `logs/app.log`
   - Error logs: `logs/error.log`
   - Real-time: `tail -f logs/app.log`

2. **Validation**
   - System check: `python main.py validate`
   - Configuration: `python main.py config`

3. **Scheduler Status**
   - Job listing in scheduler startup
   - Next run times displayed

### Metrics to Track (Future)

- Topics generated per day
- Approval rate (topics → content)
- Publishing rate (content → LinkedIn)
- Engagement per post
- Error rates by component
- API costs per workflow

## Testing Strategy

### Unit Testing (Recommended)
```python
tests/
├── test_research_agent.py
├── test_content_agent.py
├── test_trello_client.py
├── test_linkedin_client.py
└── test_orchestrator.py
```

### Integration Testing
```bash
# Test individual workflows
python main.py research   # Test research
python main.py process    # Test content gen
python main.py publish    # Test publishing
```

### Manual Testing Checklist
- [ ] Research generates valid topics
- [ ] Topics appear in Trello
- [ ] Moving to "Approved" triggers content gen
- [ ] Content appears in Trello
- [ ] Moving to "Approved Content" publishes
- [ ] Post appears on LinkedIn
- [ ] Cards are archived

## Deployment

### Local Deployment (Current)
```bash
# Run continuously
python main.py schedule

# Or use screen/tmux for persistence
screen -S linkedin-automation
python main.py schedule
# Ctrl+A, D to detach
```

### Production Deployment (Recommended)

#### Option 1: Systemd Service (Linux)
```ini
[Unit]
Description=LinkedIn Content Automation
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/Auto LinkedIN
ExecStart=/path/to/venv/bin/python main.py schedule
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Option 2: Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py", "schedule"]
```

#### Option 3: Cloud (AWS/GCP/Azure)
- AWS Lambda + EventBridge for scheduling
- GCP Cloud Functions + Scheduler
- Azure Functions + Timer triggers

## Future Enhancements

### Phase 1: Core Improvements
- [ ] Database for content tracking
- [ ] A/B testing framework
- [ ] Content calendar integration
- [ ] Image generation (DALL-E)
- [ ] Multi-language support

### Phase 2: Intelligence
- [ ] Engagement prediction
- [ ] Optimal posting time
- [ ] Audience analysis
- [ ] Trend forecasting
- [ ] Performance analytics

### Phase 3: Expansion
- [ ] Multi-platform (Twitter, Medium)
- [ ] Multi-account support
- [ ] Team collaboration features
- [ ] Web dashboard
- [ ] Mobile notifications

## Troubleshooting Guide

### Issue: Agent tasks failing
**Check**:
1. OpenAI API key valid
2. Model availability
3. Rate limits not exceeded
4. Internet connectivity

### Issue: Trello integration errors
**Check**:
1. API key and token valid
2. Board and list IDs correct
3. Token has write permissions
4. Board is accessible

### Issue: LinkedIn posting fails
**Check**:
1. Access token not expired
2. User ID is correct
3. App has "Share" permission
4. Rate limits not exceeded
5. Content meets LinkedIn guidelines

### Issue: Scheduler not running
**Check**:
1. Script running continuously
2. No exceptions in logs
3. System time correct
4. Jobs properly scheduled

## Performance Benchmarks

Typical execution times:
- Research workflow: 2-5 minutes
- Content generation: 1-3 minutes per topic
- Publishing: < 5 seconds per post

API costs (approximate):
- Research: $0.10-0.30 per run
- Content generation: $0.05-0.15 per piece
- Daily cost: $0.50-2.00

## Conclusion

This architecture provides:
- ✅ Modularity: Easy to extend/modify
- ✅ Reliability: Error handling and retries
- ✅ Observability: Comprehensive logging
- ✅ Scalability: Can handle multiple workflows
- ✅ Maintainability: Clear separation of concerns

The system is production-ready with room for enhancement.
