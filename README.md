# DCRI Time Allocation Survey Tool

A modern, user-friendly web application for collecting time allocation data using intuitive sliders instead of manual percentage entry. Built for the Duke Clinical Research Institute (DCRI) with mobile-first design and real-time feedback.

## Key Features

- **Intuitive Slider Interface**: Simply move sliders for activities you do (leave at 0 for others)
- **Automatic Percentage Calculation**: No need to make numbers add up to 100%
- **Real-time Feedback**: See your time breakdown update as you adjust sliders
- **Mobile Optimized**: Touch-friendly interface works seamlessly on all devices
- **Configurable Activities**: Easily customize departments and activities via JSON configuration
- **Visual Dashboard**: Charts and filters to analyze time allocation trends
- **Portable Architecture**: Foundation for chatbot and Teams integration



## Quick Start

### Using Docker (Recommended)
```bash
docker compose up --build
```

### Local Development
```bash
# Install dependencies
pip install .

# Create database tables
python create_tables.py

# Start application
python -m src.time_profiler.main
```

Access the application at:
- **Survey**: http://localhost:8000
- **Dashboard**: http://localhost:8000/dashboard

## Development

- **Active Development**: See [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) for current tasks and AI chatbot integration plans
- **Completed Work**: See [COMPLETED_WORK.md](COMPLETED_WORK.md) for full development history


## Detailed Setup

### Environment Setup

1. **Prerequisites**: Python 3.9+ or Docker

2. **Local Development**:
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate (choose your platform)
   source venv/Scripts/activate      # Git Bash (Windows)
   venv\Scripts\activate            # Command Prompt (Windows)
   source venv/bin/activate         # macOS/Linux/WSL
   
   # Install and setup
   pip install .
   python create_tables.py
   python -m src.time_profiler.main
   ```

3. **Docker Deployment**:
   ```bash
   # Ensure .env file exists with database credentials
   docker compose up --build
   ```

4. **Optional**: Load test data
   ```bash
   python -m src.time_profiler.seed_allocation_data
   ```

## Configuration

Customize departments and activities by editing `config/dcri_config.json`:

```json
{
  "groups": [
    { "displayName": "Research", "id": "research", "parent": null },
    { "displayName": "Clinical", "id": "clinical", "parent": null }
  ],
  "activities": [
    {
      "category": "Programming",
      "sub_activities": ["Python", "R", "SQL"]
    },
    {
      "category": "Meetings",
      "sub_activities": ["Team meetings", "Client calls"]
    }
  ],
  "enableFreeTextFeedback": true
}
```

## API Endpoints

| Method | Endpoint       | Description                                          |
| ------ | -------------- | ---------------------------------------------------- |
| GET    | `/api/config`  | Returns the configuration JSON described above.      |
| POST   | `/api/submit`  | Submit a log entry. Body requires `group_id`, `activity`, and `sub_activity` with optional `feedback`. |
| GET    | `/api/results` | Aggregated counts of submissions grouped by `group_id` and `activity`. |
| GET    | `/health`      | Simple health check returning `{"status": "ok"}`.   |

