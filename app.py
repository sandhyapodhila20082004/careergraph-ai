import logging
import os
from flask import Flask, render_template, jsonify, request
from config import Config
from database.connection import close_db
from database import queries

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Register database teardown callback
app.teardown_appcontext(close_db)

# Helper for graceful error responses
def handle_db_error(e):
    logger.error(f"Database operation failed: {e}")
    return render_template(
        "base.html", 
        db_error="Database unavailable. Please verify connection credentials in .env and try again later."
    ), 500

# ==========================================
# WEB PAGE ROUTES
# ==========================================

@app.route("/")
def index():
    try:
        metrics = queries.get_dashboard_metrics()
        candidates = queries.get_all_candidates()
        # Default top candidate for featured graph preview
        sandhya = queries.get_candidate_details("cand_1")
        sandhya_projects = queries.get_candidate_projects("cand_1")
        sandhya_recs = queries.get_recommended_job_roles("cand_1")
        
        return render_template(
            "index.html", 
            metrics=metrics, 
            candidates=candidates,
            featured_candidate=sandhya,
            featured_projects=sandhya_projects,
            featured_recs=sandhya_recs[:3] if sandhya_recs else []
        )
    except Exception as e:
        logger.error(f"Error loading index route: {e}")
        return render_template("index.html", db_error="Database unavailable. Please try again later.", metrics={"candidates": 0, "skills": 0, "roles": 0, "companies": 0})

@app.route("/candidates")
def candidates_page():
    try:
        candidates_list = queries.get_all_candidates()
        return render_template("candidates.html", candidates=candidates_list)
    except Exception as e:
        return render_template("candidates.html", candidates=[], db_error="Database unavailable. Please try again later.")

@app.route("/candidate/<candidate_id>")
def candidate_detail_page(candidate_id):
    try:
        candidate = queries.get_candidate_details(candidate_id)
        if not candidate or not candidate.get("id"):
            return render_template("base.html", db_error="Candidate not found."), 404
            
        projects = queries.get_candidate_projects(candidate_id)
        recommendations = queries.get_recommended_job_roles(candidate_id)
        companies_multihop = queries.get_candidate_companies_multi_hop(candidate_id)
        graph_data = queries.get_candidate_graph_visualization(candidate_id)

        return render_template(
            "candidate.html",
            candidate=candidate,
            projects=projects,
            recommendations=recommendations,
            companies_multihop=companies_multihop,
            graph_data=graph_data
        )
    except Exception as e:
        return handle_db_error(e)

@app.route("/jobs")
def jobs_page():
    try:
        roles = queries.get_all_job_roles()
        selected_role_id = request.args.get("role_id")
        selected_role = None
        if selected_role_id:
            selected_role = queries.get_job_role_details(selected_role_id)
        elif roles:
            selected_role = queries.get_job_role_details(roles[0]["id"])

        return render_template("jobs.html", roles=roles, selected_role=selected_role)
    except Exception as e:
        return render_template("jobs.html", roles=[], selected_role=None, db_error="Database unavailable. Please try again later.")

@app.route("/skill-gap")
def skill_gap_page():
    try:
        all_candidates = queries.get_all_candidates()
        all_roles = queries.get_all_job_roles()

        cand_id = request.args.get("candidate_id", "cand_1")  # Default to Sandhya
        role_id = request.args.get("role_id", "role_5")        # Default to AI Engineer

        gap_data = queries.get_skill_gap_analysis(cand_id, role_id)
        related_projects = queries.get_projects_for_role_skills(role_id)

        return render_template(
            "skill_gap.html",
            candidates=all_candidates,
            roles=all_roles,
            selected_cand_id=cand_id,
            selected_role_id=role_id,
            gap_data=gap_data,
            related_projects=related_projects
        )
    except Exception as e:
        return render_template("skill_gap.html", candidates=[], roles=[], db_error="Database unavailable. Please try again later.")

@app.route("/companies")
def companies_page():
    try:
        companies_list = queries.get_all_companies()
        selected_company_id = request.args.get("company_id")
        selected_company = None
        if selected_company_id:
            selected_company = queries.get_company_details(selected_company_id)
        elif companies_list:
            selected_company = queries.get_company_details(companies_list[0]["id"])

        return render_template("companies.html", companies=companies_list, selected_company=selected_company)
    except Exception as e:
        return render_template("companies.html", companies=[], selected_company=None, db_error="Database unavailable. Please try again later.")

# ==========================================
# JSON API ROUTES
# ==========================================

@app.route("/api/candidate/<candidate_id>")
def api_candidate(candidate_id):
    try:
        candidate = queries.get_candidate_details(candidate_id)
        if not candidate:
            return jsonify({"error": "Candidate not found"}), 404
        projects = queries.get_candidate_projects(candidate_id)
        return jsonify({"candidate": candidate, "projects": projects})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/recommendations/<candidate_id>")
def api_recommendations(candidate_id):
    try:
        recommendations = queries.get_recommended_job_roles(candidate_id)
        return jsonify({"candidate_id": candidate_id, "recommendations": recommendations})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/skill-gap/<candidate_id>/<role_id>")
def api_skill_gap(candidate_id, role_id):
    try:
        analysis = queries.get_skill_gap_analysis(candidate_id, role_id)
        projects = queries.get_projects_for_role_skills(role_id)
        return jsonify({"analysis": analysis, "suggested_projects": projects})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)