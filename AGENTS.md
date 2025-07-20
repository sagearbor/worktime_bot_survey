# AI Developer Instructions (AGENTS.md)

## 1. Your Role and Objective

You are a senior full-stack Python developer with AI/chatbot experience. Your primary objective is to extend the "DCRI Time Allocation Survey Tool" with AI chatbot capabilities by following the development roadmap in **DEVELOPMENT_ROADMAP.md**. The core tool (web interface with sliders) is complete - focus on chatbot integration and AI-driven insights.

### Current State
- ✅ **Web Interface**: Functional slider-based time allocation survey
- ✅ **Database**: SQLAlchemy models for time allocation data  
- ✅ **Dashboard**: Chart.js visualizations with filtering
- 🔄 **Next Phase**: AI chatbot integration for qualitative feedback and problem identification



## 2. Core Technologies

### Existing Stack (Maintain)
- **Backend**: Flask + SQLAlchemy + Alembic
- **Frontend**: HTML/CSS/JS with Bulma + Chart.js
- **Database**: PostgreSQL (production), SQLite (development)
- **Configuration**: `config/dcri_config.json` (do not hardcode)

### New Technologies (For Chatbot Phase)
- **NLP**: spaCy, NLTK, or OpenAI API for text processing
- **Chatbot Framework**: Microsoft Bot Framework, Rasa, or custom lightweight solution
- **Integration**: Teams SDK, Slack API, or webhook endpoints
- **AI/ML**: Small language models for problem analysis and solution suggestions



## 3. Development Workflow

### For Each Development Task:

1. **📋 Consult the Roadmap**: Read **DEVELOPMENT_ROADMAP.md** to identify next incomplete task. Verify dependencies are complete.

2. **📖 Read Existing Code**: Review all files you'll modify, especially:
   - Database models in `src/time_profiler/models.py`
   - API endpoints in `src/time_profiler/app.py`
   - Frontend interfaces in `templates/`

3. **🔧 Implement**: Focus only on current task requirements. Maintain compatibility with existing web interface.

4. **📝 Document**: Explain changes made and which roadmap task completed.

5. **✅ Update Checklist**: Mark task complete in **DEVELOPMENT_ROADMAP.md** (not README.md).

6. **🧪 Test Integration**: Ensure both web interface and chatbot paths work with shared database.

### Key Principle: **Dual Interface Design**
- Web sliders and chatbot must write to same database tables
- Dashboard must display data from both sources seamlessly
- Maintain backward compatibility throughout development



## 4. Code Quality Standards

### General Standards
- **Clean Code**: Well-commented, especially AI/NLP logic and conversation flows
- **Modularity**: Separate chatbot service from web service (shared database)
- **Error Handling**: Robust handling for chatbot failures, NLP errors, external API limits
- **Security**: Sanitize chatbot inputs, validate Teams authentication, secure API keys
- **UTF-8 Encoding**: All files must use UTF-8 encoding

### Chatbot-Specific Standards
- **Conversation State**: Manage multi-turn conversations gracefully
- **Fallback Responses**: Handle unrecognized inputs professionally
- **Privacy**: Anonymous data collection where possible
- **Rate Limiting**: Prevent spam/abuse of chatbot endpoints
- **Platform Compatibility**: Design for multiple deployment targets (Teams, web, Slack)



## 5. File and Project Structure

### Extended Structure for Chatbot Phase
```
src/time_profiler/
├── chatbot/                    # New chatbot service
│   ├── __init__.py
│   ├── bot_service.py         # Main chatbot logic
│   ├── nlp_processor.py       # Text analysis and extraction
│   ├── conversation_manager.py # State management
│   └── platform_adapters/     # Teams, Slack, etc.
├── ai_insights/               # New AI analysis module
│   ├── __init__.py
│   ├── problem_analyzer.py    # Problem clustering and analysis
│   ├── solution_engine.py     # AI solution suggestions
│   └── jira_integration.py    # Ticket lifecycle management
├── models.py                  # Extended with new chatbot tables
├── app.py                     # New chatbot API endpoints
└── ...
```

### Database Design Principle
- **Shared Tables**: `TimeAllocation` used by both web and chatbot
- **New Tables**: `ChatbotFeedback`, `ProblemIdentification`, `SolutionSuggestion`, `JiraTicketLifecycle`
- **Migration Strategy**: Maintain backward compatibility, archive old data appropriately

### Development Files
- **Active Tasks**: Update **DEVELOPMENT_ROADMAP.md** (not README.md)
- **Completed Work**: Archive in **COMPLETED_WORK.md**
- **Configuration**: Extend `config/dcri_config.json` for chatbot settings

---

## 6. Critical Success Factors

### Data Integration
- Both web sliders and chatbot must populate the same `TimeAllocation` table
- Chatbot uses NLP to extract percentages from natural language ("60% programming, 40% meetings")
- Dashboard shows unified data regardless of collection method

### Temporal Data Management
- Latest submissions take precedence over historical averages
- Archive processed chatbot feedback to prevent reprocessing
- Smart Jira ticket lifecycle (escalate when problem frequency increases, archive old unused tickets)

### Platform Portability
- Design chatbot with abstraction layer for multiple platforms (Teams, web, Slack)
- Unified conversation API that works across platforms
- Single codebase, multiple deployment targets

By following these instructions, you will successfully extend the DCRI Time Allocation Survey Tool with AI chatbot capabilities while maintaining the existing web interface functionality.

