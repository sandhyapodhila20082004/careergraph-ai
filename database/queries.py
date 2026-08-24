import logging
from database.connection import get_db

logger = logging.getLogger(__name__)

# ==========================================
# 1. DASHBOARD / METRICS QUERIES
# ==========================================

def get_dashboard_metrics():
    """Returns overview count metrics for dashboard."""
    cypher = """
    MATCH (c:Candidate) WITH count(c) AS candidates
    MATCH (s:Skill) WITH candidates, count(s) AS skills
    MATCH (r:JobRole) WITH candidates, skills, count(r) AS roles
    MATCH (comp:Company) WITH candidates, skills, roles, count(comp) AS companies
    RETURN candidates, skills, roles, companies
    """
    db = get_db()
    res = db.execute_query(cypher)
    if res:
        return res[0]
    return {"candidates": 0, "skills": 0, "roles": 0, "companies": 0}

# ==========================================
# 2. CANDIDATE QUERIES
# ==========================================

def get_all_candidates():
    """1. Get all candidates with their skill count."""
    cypher = """
    MATCH (c:Candidate)
    OPTIONAL MATCH (c)-[:HAS_SKILL]->(s:Skill)
    RETURN c.id AS id, c.name AS name, c.email AS email, 
           c.experience AS experience, c.education AS education,
           count(s) AS skill_count
    ORDER BY c.name ASC
    """
    db = get_db()
    return db.execute_query(cypher)

def get_candidate_details(candidate_id):
    """2. Get candidate profile along with their skills."""
    cypher = """
    MATCH (c:Candidate {id: $candidate_id})
    OPTIONAL MATCH (c)-[:HAS_SKILL]->(s:Skill)
    RETURN c.id AS id, c.name AS name, c.email AS email, 
           c.experience AS experience, c.education AS education,
           collect(s { .id, .name, .category }) AS skills
    """
    db = get_db()
    res = db.execute_query(cypher, {"candidate_id": candidate_id})
    return res[0] if res else None

def get_candidate_projects(candidate_id):
    """3. Get candidate projects and skills utilized in those projects."""
    cypher = """
    MATCH (c:Candidate {id: $candidate_id})-[:WORKED_ON]->(p:Project)
    OPTIONAL MATCH (p)-[:USES_SKILL]->(s:Skill)
    RETURN p.id AS id, p.name AS name, p.description AS description, 
           p.difficulty AS difficulty, collect(s.name) AS skills_used
    ORDER BY p.name ASC
    """
    db = get_db()
    return db.execute_query(cypher, {"candidate_id": candidate_id})

def get_recommended_job_roles(candidate_id):
    """
    4. Recommend job roles based on candidate skills.
    Calculates match percentage dynamically based on role requirement coverage.
    """
    cypher = """
    MATCH (c:Candidate {id: $candidate_id})
    MATCH (r:JobRole)-[:REQUIRES]->(req_skill:Skill)
    WITH c, r, collect(req_skill) AS required_skills, count(req_skill) AS total_required
    MATCH (c)-[:HAS_SKILL]->(cand_skill:Skill) WHERE cand_skill IN required_skills
    WITH r, required_skills, total_required, collect(cand_skill) AS matched_skills, count(cand_skill) AS matching_count
    OPTIONAL MATCH (r)-[:AVAILABLE_AT]->(comp:Company)
    WITH r, total_required, matching_count, matched_skills, count(DISTINCT comp) AS connected_companies,
         round((toFloat(matching_count) / toFloat(total_required)) * 100) AS match_percentage
    RETURN r.id AS id, r.name AS name, r.description AS description, r.level AS level,
           matching_count, total_required, match_percentage, connected_companies,
           [s IN matched_skills | s.name] AS matched_skill_names
    ORDER BY match_percentage DESC, matching_count DESC
    """
    db = get_db()
    return db.execute_query(cypher, {"candidate_id": candidate_id})

def get_candidate_companies_multi_hop(candidate_id):
    """
    5. Multi-hop traversal demonstrating Graph strength:
    Candidate -> HAS_SKILL -> Skill <- REQUIRES <- JobRole -> AVAILABLE_AT -> Company
    """
    cypher = """
    MATCH (c:Candidate {id: $candidate_id})-[:HAS_SKILL]->(s:Skill)<-[:REQUIRES]-(r:JobRole)-[:AVAILABLE_AT]->(comp:Company)
    RETURN comp.id AS company_id, comp.name AS company_name, comp.industry AS industry, comp.location AS location,
           r.name AS via_role, collect(DISTINCT s.name) AS matching_skills, count(DISTINCT s) AS skill_overlap
    ORDER BY skill_overlap DESC, company_name ASC
    """
    db = get_db()
    return db.execute_query(cypher, {"candidate_id": candidate_id})

# ==========================================
# 3. SKILL GAP ANALYSIS & CAREER PATH QUERIES
# ==========================================

def get_skill_gap_analysis(candidate_id, role_id):
    """
    6. Skill gap analysis:
    Calculates candidate skills vs required skills for target role,
    missing skills, and match percentage.
    """
    cypher = """
    MATCH (c:Candidate {id: $candidate_id})
    MATCH (r:JobRole {id: $role_id})
    
    // Get all required skills for role
    MATCH (r)-[:REQUIRES]->(req:Skill)
    WITH c, r, collect(req) AS required_skills
    
    // Get candidate skills
    OPTIONAL MATCH (c)-[:HAS_SKILL]->(cand_skill:Skill)
    WITH c, r, required_skills, collect(cand_skill) AS candidate_skills
    
    WITH c, r, required_skills, candidate_skills,
         [s IN required_skills WHERE s IN candidate_skills] AS matching_skills,
         [s IN required_skills WHERE NOT s IN candidate_skills] AS missing_skills
         
    WITH c.name AS candidate_name, r.name AS role_name,
         [s IN matching_skills | s.name] AS skills_have,
         [s IN missing_skills | s.name] AS skills_need,
         size(required_skills) AS total_required,
         size(matching_skills) AS total_matched,
         CASE WHEN size(required_skills) > 0 
              THEN round((toFloat(size(matching_skills)) / toFloat(size(required_skills))) * 100)
              ELSE 0 END AS match_percentage
              
    RETURN candidate_name, role_name, skills_have, skills_need, total_required, total_matched, match_percentage
    """
    db = get_db()
    res = db.execute_query(cypher, {"candidate_id": candidate_id, "role_id": role_id})
    return res[0] if res else None

def get_projects_for_role_skills(role_id):
    """
    7. Find projects related to skills required by a role.
    Role -> REQUIRES -> Skill <- USES_SKILL <- Project
    """
    cypher = """
    MATCH (r:JobRole {id: $role_id})-[:REQUIRES]->(s:Skill)<-[:USES_SKILL]-(p:Project)
    RETURN p.id AS project_id, p.name AS project_name, p.description AS description, p.difficulty AS difficulty,
           collect(DISTINCT s.name) AS skills_addressed
    ORDER BY size(skills_addressed) DESC
    """
    db = get_db()
    return db.execute_query(cypher, {"role_id": role_id})

def get_candidate_graph_visualization(candidate_id):
    """
    8. Career path graph exploration query for visual UI graphs.
    Fetches 2+ hop subgraph around a candidate.
    """
    cypher = """
    MATCH (c:Candidate {id: $candidate_id})
    OPTIONAL MATCH (c)-[:HAS_SKILL]->(s:Skill)
    OPTIONAL MATCH (s)<-[:REQUIRES]-(r:JobRole)
    OPTIONAL MATCH (r)-[:AVAILABLE_AT]->(comp:Company)
    OPTIONAL MATCH (c)-[:WORKED_ON]->(p:Project)
    RETURN c.id AS candidate_id, c.name AS candidate_name,
           collect(DISTINCT {id: s.id, name: s.name, type: 'Skill'}) AS skills,
           collect(DISTINCT {id: p.id, name: p.name, type: 'Project'}) AS projects,
           collect(DISTINCT {id: r.id, name: r.name, type: 'JobRole'}) AS roles,
           collect(DISTINCT {id: comp.id, name: comp.name, type: 'Company'}) AS companies
    """
    db = get_db()
    res = db.execute_query(cypher, {"candidate_id": candidate_id})
    return res[0] if res else {}

# ==========================================
# 4. JOB ROLES QUERIES
# ==========================================

def get_all_job_roles():
    """Get all job roles with count of required skills and hiring companies."""
    cypher = """
    MATCH (r:JobRole)
    OPTIONAL MATCH (r)-[:REQUIRES]->(s:Skill)
    OPTIONAL MATCH (r)-[:AVAILABLE_AT]->(c:Company)
    RETURN r.id AS id, r.name AS name, r.description AS description, r.level AS level,
           count(DISTINCT s) AS skill_count, collect(DISTINCT s.name) AS required_skills,
           count(DISTINCT c) AS company_count, collect(DISTINCT c.name) AS companies
    ORDER BY r.name ASC
    """
    db = get_db()
    return db.execute_query(cypher)

def get_job_role_details(role_id):
    """Get detailed information for a job role including candidates interested."""
    cypher = """
    MATCH (r:JobRole {id: $role_id})
    OPTIONAL MATCH (r)-[:REQUIRES]->(s:Skill)
    OPTIONAL MATCH (r)-[:AVAILABLE_AT]->(comp:Company)
    OPTIONAL MATCH (c:Candidate)-[:INTERESTED_IN]->(r)
    RETURN r.id AS id, r.name AS name, r.description AS description, r.level AS level,
           collect(DISTINCT s { .id, .name, .category }) AS skills,
           collect(DISTINCT comp { .id, .name, .location, .industry }) AS companies,
           collect(DISTINCT c { .id, .name, .experience }) AS interested_candidates
    """
    db = get_db()
    res = db.execute_query(cypher, {"role_id": role_id})
    return res[0] if res else None

# ==========================================
# 5. COMPANIES QUERIES
# ==========================================

def get_all_companies():
    """Get all companies with available roles."""
    cypher = """
    MATCH (comp:Company)
    OPTIONAL MATCH (comp)<-[:AVAILABLE_AT]-(r:JobRole)
    RETURN comp.id AS id, comp.name AS name, comp.industry AS industry, comp.location AS location,
           count(DISTINCT r) AS open_roles_count, collect(DISTINCT r.name) AS roles
    ORDER BY comp.name ASC
    """
    db = get_db()
    return db.execute_query(cypher)

def get_company_details(company_id):
    """Get company details along with required skills and potential qualified candidates."""
    cypher = """
    MATCH (comp:Company {id: $company_id})
    OPTIONAL MATCH (r:JobRole)-[:AVAILABLE_AT]->(comp)
    OPTIONAL MATCH (r)-[:REQUIRES]->(s:Skill)
    OPTIONAL MATCH (c:Candidate)-[:HAS_SKILL]->(s)
    RETURN comp.id AS id, comp.name AS name, comp.industry AS industry, comp.location AS location,
           collect(DISTINCT r { .id, .name, .level }) AS roles,
           collect(DISTINCT s.name) AS required_skills,
           collect(DISTINCT c { .id, .name, .experience }) AS qualified_candidates
    """
    db = get_db()
    res = db.execute_query(cypher, {"company_id": company_id})
    return res[0] if res else None