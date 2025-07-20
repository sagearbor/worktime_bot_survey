"""Flask application factory and database setup."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timedelta

from flask import Flask, jsonify, request, render_template
import asyncio
from flask_cors import CORS
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session

# SQLAlchemy setup
engine = None
SessionLocal = scoped_session(sessionmaker())
Base = declarative_base()

# Import models so they are registered with SQLAlchemy's metadata
from . import models  # noqa: F401


def load_config(config_path: Path) -> dict:
    """Load the DCRI configuration from a JSON file."""
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def init_db(database_url: str):
    """Initialize the database engine and session factory."""
    global engine
    engine = create_engine(database_url)
    SessionLocal.remove()
    SessionLocal.configure(bind=engine)
    # Ensure tables are created when running without migrations
    Base.metadata.create_all(bind=engine)


def create_app(config_object: dict | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder='../../templates')
    
    # Enable CORS for all routes
    CORS(app)

    # Default configuration
    app.config.setdefault("DATABASE_URL", "sqlite:///dcri_logger.db")
    default_config_path = (
        Path(__file__).resolve().parents[2] / "config" / "dcri_config.json.example"
    )
    app.config.setdefault("DCRI_CONFIG_PATH", default_config_path)

    if config_object:
        app.config.update(config_object)

    init_db(app.config["DATABASE_URL"])

    # Initialize chatbot service with platform adapters
    from .chatbot.base import BaseChatbotService
    from .chatbot.adapters import TeamsAdapter, WebChatAdapter

    chatbot_service = BaseChatbotService()
    chatbot_service.register_adapter("teams", TeamsAdapter())
    chatbot_service.register_adapter("web", WebChatAdapter())

    @app.route("/api/config", methods=["GET"])
    def get_config() -> jsonify:
        """Return configuration data loaded from the JSON file."""
        config_data = load_config(Path(app.config["DCRI_CONFIG_PATH"]))
        return jsonify(config_data)

    @app.route("/api/submit", methods=["POST"])
    def submit_activity() -> jsonify:
        """Receive and validate an activity log submission."""
        data = request.get_json(silent=True) or {}

        required = ["group_id", "activity", "sub_activity"]
        if not all(data.get(f) for f in required):
            return jsonify({"error": "Missing required fields"}), 400

        config = load_config(Path(app.config["DCRI_CONFIG_PATH"]))
        valid_groups = {g["id"] for g in config.get("groups", [])}
        if data["group_id"] not in valid_groups:
            return jsonify({"error": "Invalid group_id"}), 400

        activity_map = {
            a["category"]: set(a.get("sub_activities", []))
            for a in config.get("activities", [])
        }
        if data["activity"] not in activity_map:
            return jsonify({"error": "Invalid activity"}), 400

        sub_acts = activity_map[data["activity"]]
        if sub_acts and data["sub_activity"] not in sub_acts:
            return jsonify({"error": "Invalid sub_activity"}), 400

        session = SessionLocal()
        try:
            feedback_text = None
            if config.get("enableFreeTextFeedback"):
                feedback_text = data.get("feedback")

            log_entry = models.ActivityLog(
                group_id=data["group_id"],
                activity=data["activity"],
                sub_activity=data["sub_activity"],
                hours_work=data.get("hours_work"),
                feedback=feedback_text,
            )
            session.add(log_entry)
            session.commit()
            return jsonify({"status": "success", "id": log_entry.id})
        except Exception:  # pragma: no cover - unexpected DB errors
            session.rollback()
            return jsonify({"error": "Server error"}), 500
        finally:
            session.close()

    @app.route("/api/results", methods=["GET"])
    def get_results() -> jsonify:
        """Return aggregated activity data by group and activity."""
        session = SessionLocal()
        try:
            # First try TimeAllocation entries (new format)
            time_query = session.query(models.TimeAllocation)
            
            # Optional filters
            group_id = request.args.get("group_id")
            start_date = request.args.get("start_date")
            end_date = request.args.get("end_date")

            if group_id:
                time_query = time_query.filter(models.TimeAllocation.group_id == group_id)

            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date)
                    time_query = time_query.filter(models.TimeAllocation.timestamp >= start_dt)
                except ValueError:
                    return jsonify({"error": "Invalid start_date"}), 400

            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date)
                    time_query = time_query.filter(models.TimeAllocation.timestamp <= end_dt)
                except ValueError:
                    return jsonify({"error": "Invalid end_date"}), 400

            time_allocations = time_query.all()
            
            if time_allocations:
                # Handle TimeAllocation format (hours-based)
                group_activity_totals = {}
                group_totals = {}
                
                for allocation in time_allocations:
                    group_id_val = allocation.group_id
                    activities = allocation.activities
                    
                    # Track total hours per group for percentage calculation
                    if group_id_val not in group_totals:
                        group_totals[group_id_val] = 0
                    group_totals[group_id_val] += sum(activities.values())
                        
                    for activity, hours in activities.items():
                        key = (group_id_val, activity)
                        if key not in group_activity_totals:
                            group_activity_totals[key] = 0
                        group_activity_totals[key] += hours

                # Convert to percentages for dashboard display
                results = []
                for (group_id_val, activity), total_hours in group_activity_totals.items():
                    group_total_hours = group_totals[group_id_val]
                    percentage = (total_hours / group_total_hours * 100) if group_total_hours > 0 else 0
                    results.append({
                        "group_id": group_id_val,
                        "activity": activity,
                        "count": percentage,  # Convert hours to percentage for display
                        "total_hours": total_hours,  # Include raw hours for reference
                    })
                    
                return jsonify(results)
            
            else:
                # Fall back to ActivityLog entries (legacy format)
                activity_query = session.query(models.ActivityLog)
                
                if group_id:
                    activity_query = activity_query.filter(models.ActivityLog.group_id == group_id)

                if start_date:
                    try:
                        start_dt = datetime.fromisoformat(start_date)
                        activity_query = activity_query.filter(models.ActivityLog.timestamp >= start_dt)
                    except ValueError:
                        return jsonify({"error": "Invalid start_date"}), 400

                if end_date:
                    try:
                        end_dt = datetime.fromisoformat(end_date)
                        activity_query = activity_query.filter(models.ActivityLog.timestamp <= end_dt)
                    except ValueError:
                        return jsonify({"error": "Invalid end_date"}), 400

                activity_logs = activity_query.all()
                
                # Aggregate activity logs by group and activity
                group_activity_counts = {}
                for log in activity_logs:
                    key = (log.group_id, log.activity)
                    if key not in group_activity_counts:
                        group_activity_counts[key] = 0
                    group_activity_counts[key] += 1

                # Format results
                results = []
                for (group_id_val, activity), count in group_activity_counts.items():
                    results.append({
                        "group_id": group_id_val,
                        "activity": activity,
                        "count": count
                    })

                return jsonify(results)
                
        except Exception as e:  # pragma: no cover - unexpected DB errors
            print(f"Error in get_results: {e}")
            return jsonify({"error": "Server error"}), 500
        finally:
            session.close()

    @app.route("/api/submit-allocation", methods=["POST"])
    def submit_time_allocation() -> jsonify:
        """Receive and validate a comprehensive time allocation submission."""
        data = request.get_json(silent=True) or {}

        # Validate required fields
        if not data.get("group_id") or not data.get("activities"):
            return jsonify({"error": "Missing required fields: group_id, activities"}), 400

        # Validate group_id
        config = load_config(Path(app.config["DCRI_CONFIG_PATH"]))
        valid_groups = {g["id"] for g in config.get("groups", [])}
        if data["group_id"] not in valid_groups:
            return jsonify({"error": "Invalid group_id"}), 400

        # Validate activities exist in config
        valid_activities = {a["category"] for a in config.get("activities", [])}
        for activity in data["activities"].keys():
            if activity not in valid_activities:
                return jsonify({"error": f"Invalid activity: {activity}"}), 400

        # Validate that hours are positive numbers
        for activity, hours in data["activities"].items():
            if not isinstance(hours, (int, float)) or hours < 0:
                return jsonify({"error": f"Invalid hours for {activity}: must be a positive number"}), 400

        session = SessionLocal()
        try:
            allocation_entry = models.TimeAllocation(
                group_id=data["group_id"],
                activities=data["activities"],
                feedback=data.get("feedback"),
            )
            session.add(allocation_entry)
            session.commit()
            return jsonify({"status": "success", "id": allocation_entry.id})
        except Exception as e:  # pragma: no cover
            session.rollback()
            print(f"Database error: {e}")
            return jsonify({"error": "Server error"}), 500
        finally:
            session.close()

    @app.route("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.route("/")
    def index():
        """Serve the main survey page."""
        return render_template("index.html")
    
    @app.route("/dashboard")
    def dashboard():
        """Serve the dashboard page."""
        return render_template("dashboard.html")

    @app.route("/admin")
    def admin_page():
        """Serve the admin problem management page."""
        return render_template("admin.html")

    @app.route("/api/chatbot-feedback", methods=["POST"])
    def submit_chatbot_feedback() -> jsonify:
        """Process chatbot message and return response."""
        data = request.get_json(silent=True) or {}
        
        # Validate required fields
        if not data.get("user_id") or not data.get("message"):
            return jsonify({"error": "Missing required fields: user_id, message"}), 400
        
        session = SessionLocal()
        try:
            # Store the feedback
            feedback = models.ChatbotFeedback(
                user_id=data["user_id"],
                message_text=data["message"],
                message_type=data.get("message_type", "general")
            )
            session.add(feedback)
            session.commit()
            
            # Simple response generation (can be enhanced with chatbot service)
            response_text = "Thank you for your feedback. I've recorded your message and will analyze it for insights."
            
            return jsonify({
                "status": "success",
                "response": response_text,
                "feedback_id": feedback.id
            })
        except Exception as e:
            session.rollback()
            print(f"Error processing chatbot feedback: {e}")
            return jsonify({"error": "Server error"}), 500
        finally:
            session.close()

    @app.route("/api/teams/messages", methods=["POST"])
    def teams_messages() -> jsonify:
        """Endpoint for Microsoft Teams bot messages."""
        raw = request.get_json(silent=True) or {}
        response = asyncio.run(chatbot_service.process_message("teams", raw))
        return jsonify({"text": response.text})

    @app.route("/api/problems", methods=["GET"])
    def get_problems() -> jsonify:
        """Return identified problems with optional filters."""
        session = SessionLocal()
        try:
            query = session.query(models.ProblemIdentification)
            
            # Optional filters
            status = request.args.get("status")
            category = request.args.get("category")
            limit = request.args.get("limit", type=int)
            
            if status:
                query = query.filter(models.ProblemIdentification.status == status)
            if category:
                query = query.filter(models.ProblemIdentification.category == category)
            
            if limit:
                query = query.limit(limit)
            
            problems = query.all()
            
            results = []
            for problem in problems:
                results.append({
                    "id": problem.id,
                    "description": problem.description,
                    "category": problem.category,
                    "frequency_count": problem.frequency_count,
                    "first_reported": problem.first_reported.isoformat(),
                    "last_reported": problem.last_reported.isoformat(),
                    "status": problem.status
                })
            
            return jsonify(results)
        except Exception as e:
            print(f"Error retrieving problems: {e}")
            return jsonify({"error": "Server error"}), 500
        finally:
            session.close()

    @app.route("/api/problems", methods=["POST"])
    def create_problem() -> jsonify:
        """Create a new identified problem."""
        data = request.get_json(silent=True) or {}
        
        if not data.get("description"):
            return jsonify({"error": "Missing required field: description"}), 400
        
        session = SessionLocal()
        try:
            problem = models.ProblemIdentification(
                description=data["description"],
                category=data.get("category"),
                frequency_count=data.get("frequency_count", 1),
                status=data.get("status", "identified")
            )
            session.add(problem)
            session.commit()
            
            return jsonify({
                "status": "success",
                "problem_id": problem.id,
                "description": problem.description
            })
        except Exception as e:
            session.rollback()
            print(f"Error creating problem: {e}")
            return jsonify({"error": "Server error"}), 500
        finally:
            session.close()

    @app.route("/api/problems/<int:problem_id>", methods=["PATCH"])
    def update_problem(problem_id: int) -> jsonify:
        """Update problem fields such as status or category."""
        data = request.get_json(silent=True) or {}
        session = SessionLocal()
        try:
            problem = session.query(models.ProblemIdentification).filter_by(id=problem_id).first()
            if not problem:
                return jsonify({"error": "Problem not found"}), 404

            if "status" in data:
                problem.status = data["status"]
            if "category" in data:
                problem.category = data["category"]
            if "description" in data:
                problem.description = data["description"]

            session.commit()
            return jsonify({"status": "success"})
        except Exception as e:  # pragma: no cover
            session.rollback()
            print(f"Error updating problem: {e}")
            return jsonify({"error": "Server error"}), 500
        finally:
            session.close()

    @app.route("/api/solutions", methods=["GET"])
    def get_solutions() -> jsonify:
        """Return solution suggestions with optional filters."""
        session = SessionLocal()
        try:
            query = session.query(models.SolutionSuggestion)
            
            # Optional filters
            problem_id = request.args.get("problem_id", type=int)
            status = request.args.get("status")
            limit = request.args.get("limit", type=int)
            
            if problem_id:
                query = query.filter(models.SolutionSuggestion.problem_id == problem_id)
            if status:
                query = query.filter(models.SolutionSuggestion.status == status)
            
            if limit:
                query = query.limit(limit)
            
            solutions = query.all()
            
            results = []
            for solution in solutions:
                results.append({
                    "id": solution.id,
                    "problem_id": solution.problem_id,
                    "description": solution.description,
                    "estimated_effort": solution.estimated_effort,
                    "estimated_savings": solution.estimated_savings,
                    "roi_score": solution.roi_score,
                    "status": solution.status,
                    "created_at": solution.created_at.isoformat()
                })
            
            return jsonify(results)
        except Exception as e:
            print(f"Error retrieving solutions: {e}")
            return jsonify({"error": "Server error"}), 500
        finally:
            session.close()

    @app.route("/api/solutions", methods=["POST"])
    def create_solution() -> jsonify:
        """Create a new solution suggestion."""
        data = request.get_json(silent=True) or {}
        
        required = ["problem_id", "description"]
        if not all(data.get(f) for f in required):
            return jsonify({"error": "Missing required fields: problem_id, description"}), 400
        
        session = SessionLocal()
        try:
            # Verify problem exists
            problem = session.query(models.ProblemIdentification).filter_by(id=data["problem_id"]).first()
            if not problem:
                return jsonify({"error": "Invalid problem_id"}), 400
            
            solution = models.SolutionSuggestion(
                problem_id=data["problem_id"],
                description=data["description"],
                estimated_effort=data.get("estimated_effort"),
                estimated_savings=data.get("estimated_savings"),
                roi_score=data.get("roi_score"),
                status=data.get("status", "suggested")
            )
            session.add(solution)
            session.commit()
            
            return jsonify({
                "status": "success",
                "solution_id": solution.id,
                "problem_id": solution.problem_id
            })
        except Exception as e:
            session.rollback()
            print(f"Error creating solution: {e}")
            return jsonify({"error": "Server error"}), 500
        finally:
            session.close()

    @app.route("/api/solutions/<int:solution_id>", methods=["PATCH"])
    def update_solution(solution_id: int) -> jsonify:
        """Update solution information such as status or savings."""
        data = request.get_json(silent=True) or {}
        session = SessionLocal()
        try:
            solution = session.query(models.SolutionSuggestion).filter_by(id=solution_id).first()
            if not solution:
                return jsonify({"error": "Solution not found"}), 404

            if "status" in data:
                solution.status = data["status"]
            if "actual_savings" in data:
                solution.actual_savings = data["actual_savings"]
            if "roi_score" in data:
                solution.roi_score = data["roi_score"]

            session.commit()
            return jsonify({"status": "success"})
        except Exception as e:  # pragma: no cover
            session.rollback()
            print(f"Error updating solution: {e}")
            return jsonify({"error": "Server error"}), 500
        finally:
            session.close()

    @app.route("/api/insights", methods=["GET"])
    def get_insights() -> jsonify:
        """Return dashboard insights and analytics."""
        session = SessionLocal()
        try:
            # Get problem statistics
            total_problems = session.query(models.ProblemIdentification).count()
            active_problems = session.query(models.ProblemIdentification).filter_by(status="identified").count()
            resolved_problems = session.query(models.ProblemIdentification).filter_by(status="resolved").count()

            # Get solution statistics
            total_solutions = session.query(models.SolutionSuggestion).count()
            implemented_solutions = session.query(models.SolutionSuggestion).filter_by(status="implemented").count()

            # Solution pipeline counts
            pipeline_counts = dict(
                session.query(models.SolutionSuggestion.status, func.count(models.SolutionSuggestion.id))
                .group_by(models.SolutionSuggestion.status)
                .all()
            )

            # Get recent feedback count
            recent_feedback = session.query(models.ChatbotFeedback).filter(
                models.ChatbotFeedback.processed == False
            ).count()

            # Get top problems by frequency
            top_problems = session.query(models.ProblemIdentification).order_by(
                models.ProblemIdentification.frequency_count.desc()
            ).limit(5).all()

            # Trending problems (last 7 days, min 2 reports)
            from .ai_insights import ProblemAggregator, analyze_sentiment

            aggregator = ProblemAggregator()
            trending = aggregator.trending_problems(within_days=7, min_reports=2)

            # Champion counts from success stories
            champion_rows = (
                session.query(models.ChatbotFeedback.user_id, func.count(models.ChatbotFeedback.id))
                .filter(models.ChatbotFeedback.message_type == "success_story")
                .group_by(models.ChatbotFeedback.user_id)
                .order_by(func.count(models.ChatbotFeedback.id).desc())
                .limit(5)
                .all()
            )
            champions = [
                {"user_id": uid, "count": cnt}
                for uid, cnt in champion_rows
            ]

            # ROI statistics for implemented solutions
            implemented = session.query(models.SolutionSuggestion).filter_by(status="implemented").all()
            total_savings = sum(s.actual_savings or 0 for s in implemented)
            avg_roi = 0.0
            if implemented:
                roi_values = [s.roi_score for s in implemented if s.roi_score is not None]
                if roi_values:
                    avg_roi = sum(roi_values) / len(roi_values)

            # Sentiment analysis for recent feedback (7 days)
            cutoff = datetime.utcnow() - timedelta(days=7)
            recent_messages = (
                session.query(models.ChatbotFeedback.message_text)
                .filter(models.ChatbotFeedback.timestamp >= cutoff)
                .all()
            )
            sentiments = [analyze_sentiment(m[0]) for m in recent_messages]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

            return jsonify({
                "problem_stats": {
                    "total": total_problems,
                    "active": active_problems,
                    "resolved": resolved_problems,
                },
                "solution_stats": {
                    "total": total_solutions,
                    "implemented": implemented_solutions,
                    "pipeline": pipeline_counts,
                },
                "feedback_stats": {
                    "unprocessed": recent_feedback,
                    "sentiment": avg_sentiment,
                },
                "top_problems": [
                    {
                        "id": p.id,
                        "description": p.description[:100] + "..." if len(p.description) > 100 else p.description,
                        "frequency": p.frequency_count,
                    }
                    for p in top_problems
                ],
                "trending_problems": [
                    {
                        "id": pid,
                        "description": desc,
                        "frequency": freq,
                    }
                    for pid, desc, freq in trending
                ],
                "champions": champions,
                "roi": {
                    "total_savings": total_savings,
                    "average_roi": avg_roi,
                },
            })
        except Exception as e:
            print(f"Error retrieving insights: {e}")
            return jsonify({"error": "Server error"}), 500
        finally:
            session.close()

    @app.route("/api/jira-tickets", methods=["GET"])
    def get_jira_tickets() -> jsonify:
        """Return Jira ticket lifecycle records."""
        session = SessionLocal()
        try:
            tickets = session.query(models.JiraTicketLifecycle).all()
            results = []
            for t in tickets:
                results.append({
                    "id": t.id,
                    "ticket_key": t.ticket_key,
                    "status": t.status,
                    "priority": t.priority,
                    "problem_id": t.problem_id,
                    "solution_id": t.solution_id,
                })
            return jsonify(results)
        except Exception as e:  # pragma: no cover
            print(f"Error retrieving Jira tickets: {e}")
            return jsonify({"error": "Server error"}), 500
        finally:
            session.close()

    @app.route("/api/jira-tickets/<int:ticket_id>", methods=["PATCH"])
    def update_jira_ticket(ticket_id: int) -> jsonify:
        """Update Jira ticket status or priority."""
        data = request.get_json(silent=True) or {}
        session = SessionLocal()
        try:
            ticket = session.query(models.JiraTicketLifecycle).filter_by(id=ticket_id).first()
            if not ticket:
                return jsonify({"error": "Ticket not found"}), 404

            if "status" in data:
                ticket.status = data["status"]
            if "priority" in data:
                ticket.priority = data["priority"]
            if data.get("escalate"):
                ticket.escalation_count += 1
            ticket.last_updated = datetime.utcnow()

            session.commit()
            return jsonify({"status": "success"})
        except Exception as e:  # pragma: no cover
            session.rollback()
            print(f"Error updating Jira ticket: {e}")
            return jsonify({"error": "Server error"}), 500
        finally:
            session.close()

    @app.route("/api/admin/archive", methods=["POST"])
    def archive_data() -> jsonify:
        """Archive processed feedback and resolved problems."""
        days = request.args.get("days", default=30, type=int)
        cutoff = datetime.utcnow() - timedelta(days=days)
        session = SessionLocal()
        try:
            fb_q = session.query(models.ChatbotFeedback).filter(
                models.ChatbotFeedback.processed == True,
                models.ChatbotFeedback.archived == False,
                models.ChatbotFeedback.timestamp < cutoff,
            )
            fb_count = fb_q.update({models.ChatbotFeedback.archived: True}, synchronize_session=False)

            prob_q = session.query(models.ProblemIdentification).filter(
                models.ProblemIdentification.status == "resolved",
                models.ProblemIdentification.last_reported < cutoff,
            )
            prob_count = prob_q.update({models.ProblemIdentification.status: "archived"}, synchronize_session=False)

            session.commit()
            return jsonify({"status": "success", "feedback_archived": fb_count, "problems_archived": prob_count})
        except Exception as e:  # pragma: no cover
            session.rollback()
            print(f"Error archiving data: {e}")
            return jsonify({"error": "Server error"}), 500
        finally:
            session.close()

    @app.route("/api/jira-webhook", methods=["POST"])
    def jira_webhook() -> jsonify:
        """Receive Jira status updates via webhook."""
        data = request.get_json(silent=True) or {}

        ticket_key = data.get("ticket_key")
        status = data.get("status")
        if not ticket_key or not status:
            return jsonify({"error": "Missing required fields: ticket_key, status"}), 400

        session = SessionLocal()
        try:
            ticket = session.query(models.JiraTicketLifecycle).filter_by(ticket_key=ticket_key).first()
            if not ticket:
                return jsonify({"error": "Ticket not found"}), 404
            ticket.status = status
            ticket.last_updated = datetime.utcnow()
            session.commit()
            return jsonify({"status": "success"})
        except Exception as e:  # pragma: no cover
            session.rollback()
            print(f"Error updating Jira ticket: {e}")
            return jsonify({"error": "Server error"}), 500
        finally:
            session.close()

    return app
