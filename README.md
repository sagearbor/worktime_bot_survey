DCRI Activity Logging Tool

This project is a web-based application for logging time and activities at the Duke Clinical Research Institute (DCRI). It is designed to be configured via a central JSON file and provide simple, clear data entry for users.



Core Features

Configurable Dropdowns: User-selectable groups and activities are dynamically populated from config/dcri\_config.json.example.



Hierarchical Data: The configuration supports hierarchical relationships to enable powerful, aggregated reporting.



Simple UI: A clean, straightforward interface for quick data entry.



Free-Text Feedback Collection: Allows users to provide optional, open-ended feedback, controlled via a flag in the configuration file.



Reporting Dashboard: A visualization of logged activities to identify trends and opportunities.



Development Plan \& Checklist

This plan outlines the major phases and tasks for building the application. Developers will update the checklist as they complete each task.



Phase 1: Backend API and Database Setup

Goal: Build the core Flask server, database models, and API endpoints for managing the configuration and survey submissions.



\[x] Task BE-01: Set up the basic Flask project structure.



Dependencies: None



Status: Critical Path



\[x] Task BE-02: Define database models using SQLAlchemy for ActivityLog.



Dependencies: BE-01



Status: Critical Path



\[x] Task BE-03: Implement Alembic for managing database migrations.



Dependencies: BE-02



Status: Critical Path



\[x] Task BE-04: Create an API endpoint (GET /api/config) to serve the dcri\_config.json file.



Dependencies: BE-01



Status: Critical Path



\[x] Task BE-05: Create a secure API endpoint (POST /api/submit) to receive and validate activity log submissions.



Dependencies: BE-02



Status: Critical Path



\[x] Task BE-06: Implement logic in the submission endpoint to handle the optional feedback text field.



Dependencies: BE-05



Status: Critical Path



\[x] Task BE-07: Create an API endpoint (GET /api/results) to retrieve aggregated submission data.



Dependencies: BE-05



Status: Critical Path



Phase 2: Interactive Frontend Survey UI

Goal: Develop the user-facing survey UI as a static HTML/CSS/JS application.



\[x] Task FE-01: Create the main index.html file with the basic form structure and styling.



Dependencies: None



Status: Critical Path



\[x] Task FE-02: Write JavaScript to fetch configuration from /api/config.



Dependencies: BE-04



Status: Critical Path



\[x] Task FE-03: Implement logic to dynamically populate the "Group" and "Activity" dropdowns.



Dependencies: FE-02



Status: Critical Path



\[x] Task FE-04: Implement logic to read the enableFreeTextFeedback flag and conditionally display the feedback <textarea>.



Dependencies: FE-02



Status: Critical Path



\[x] Task FE-05: Implement form submission logic to POST data to /api/submit.



Dependencies: BE-05, FE-03, FE-04



Status: Critical Path



\[x] Task FE-06: Ensure the UI is clean, responsive, and easy to use on both desktop and mobile devices.



Dependencies: FE-01



Status: Critical Path



Phase 3: Reporting Dashboard

Goal: Create a simple web page to visualize the collected data.



\[x] Task DB-01: Create a new HTML page/template for the dashboard (dashboard.html).



Dependencies: FE-01 (to share structure/styling)



Status: Critical Path



\[x] Task DB-02: Write JavaScript to fetch aggregated data from the /api/results endpoint.



Dependencies: BE-07



Status: Critical Path



\[x] Task DB-03: Use a charting library (e.g., Chart.js) to display time allocation by group and activity.



Dependencies: DB-02



Status: Critical Path



\[ ] Task DB-04: Add filters to the dashboard (e.g., filter by group, date range).



Dependencies: DB-03



Status: Optional (Enhancement)



Phase 4: Deployment and Documentation

Goal: Package the application and provide clear instructions for deployment.



\[x] Task DEP-01: Create a Dockerfile to containerize the Flask backend for easy deployment.



Dependencies: BE-01



Status: Critical Path



\[x] Task DEP-02: Write clear deployment instructions for setting up the database and running the application.



Dependencies: All previous phases



Status: Critical Path



\[x] Task DEP-03: Finalize all documentation, ensuring the config.json structure and all API endpoints are clearly described.



Dependencies: All previous phases



Status: Critical Path


## Deployment Instructions

### Local Setup
1. Install Python 3.9 or newer.
2. Install dependencies:
   ```bash
   pip install .
   ```
3. Run the database migrations:
   ```bash
   alembic upgrade head
   ```
4. Start the application:
   ```bash
   uvicorn src.time_profiler.main:app --host 0.0.0.0 --port 8000
   ```

### Docker Compose
The project includes a `docker-compose.yml` file for running the API with a PostgreSQL
container.

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

## Configuration Reference
All runtime options are stored in `config/dcri_config.json.example`. Copy this file to
`config/dcri_config.json` and modify as needed. The structure is:

```json
{
  "groups": [
    { "displayName": "<name>", "id": "<id>", "parent": "<parent>" }
  ],
  "activities": [
    {
      "category": "<category>",
      "sub_activities": ["<sub activity>"]
    }
  ],
  "enableFreeTextFeedback": true
}
```

* `groups` – list of group objects with a display name, unique id and optional parent group.
* `activities` – list of activity categories each with optional `sub_activities`.
* `enableFreeTextFeedback` – when `true`, users may submit optional text feedback.

## API Endpoints

| Method | Endpoint       | Description                                          |
| ------ | -------------- | ---------------------------------------------------- |
| GET    | `/api/config`  | Returns the configuration JSON described above.      |
| POST   | `/api/submit`  | Submit a log entry. Body requires `group_id`, `activity`, and `sub_activity` with optional `feedback`. |
| GET    | `/api/results` | Aggregated counts of submissions grouped by `group_id` and `activity`. |
| GET    | `/health`      | Simple health check returning `{"status": "ok"}`.   |

