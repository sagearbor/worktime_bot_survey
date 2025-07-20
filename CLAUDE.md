# Claude Code Development Notes

This file contains important information for Claude Code sessions to avoid common setup issues.

## Quick Startup Commands

To start the development server without issues:

```bash
# Recommended: Use the startup script
python start_dev.py

# Alternative: Shell script (Linux/Mac/WSL)
./dev.sh

# Manual startup if needed
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
python -m src.time_profiler.main
```

## Common Issues & Solutions

### 1. Migration Errors
- The database migrations may show errors but often still work
- If migrations fail, run: `alembic stamp head` to mark DB as current
- The startup scripts handle this automatically

### 2. Import Path Issues
- Always set `PYTHONPATH` to include the `src` directory
- The `migrations/env.py` file has been fixed to handle imports correctly

### 3. Dependencies
- Required packages: `flask flask-cors sqlalchemy alembic python-dotenv psycopg2-binary pytest black`
- The startup scripts install these automatically if missing

### 4. Database Location
- SQLite database: `dcri_logger.db` in project root
- Migrations are in: `src/time_profiler/migrations/versions/`

## Development Server
- Runs on: http://127.0.0.1:8000
- Survey page: http://127.0.0.1:8000
- Dashboard: http://127.0.0.1:8000/dashboard

## Testing
```bash
python -m pytest tests/ -v
```

## Current Architecture

### Core Models
- `ActivityLog` - Individual activity entries (legacy)
- `TimeAllocation` - Complete time allocation per user (new format)
- `UserSubmissionHistory` - Version tracking for submissions
- `ChatbotFeedback` - Chatbot interactions
- `ProblemIdentification` - AI-identified problems
- `SolutionSuggestion` - AI solution recommendations
- `JiraTicketLifecycle` - Jira integration tracking

### API Endpoints
- `/api/config` - Get configuration
- `/api/submit` - Submit activity log
- `/api/submit-allocation` - Submit time allocation
- `/api/results` - Get aggregated results
- `/api/chatbot-feedback` - Process chatbot messages
- `/api/problems` - Manage identified problems
- `/api/solutions` - Handle solution suggestions
- `/api/insights` - Dashboard analytics

### Chatbot Framework
- Base chatbot service with platform abstraction
- Adapters for Web, Teams, Slack
- Conversation state management
- Message classification and routing

## Project Status
Currently in Phase 5: AI Chatbot Integration & Feedback Analysis
Core infrastructure complete, ready for advanced AI features and platform integrations.