import json
import os
import sys
import logging

# Ensure project root is on Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db, close_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEED_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "seed_data.json")

def load_seed_json():
    with open(SEED_FILE_PATH, "r") as f:
        return json.load(f)

def seed_database():
    data = load_seed_json()
    db = get_db()
    
    logger.info("Starting CognoDB seeding process using MERGE statements...")
    
    # 1. Seed Candidate Nodes
    logger.info(f"Seeding {len(data['candidates'])} Candidate nodes...")
    cypher_cand = """
    UNWIND $candidates AS item
    MERGE (c:Candidate {id: item.id})
    SET c.name = item.name,
        c.email = item.email,
        c.experience = item.experience,
        c.education = item.education
    """
    db.execute_query(cypher_cand, {"candidates": data["candidates"]})

    # 2. Seed Skill Nodes
    logger.info(f"Seeding {len(data['skills'])} Skill nodes...")
    cypher_skill = """
    UNWIND $skills AS item
    MERGE (s:Skill {id: item.id})
    SET s.name = item.name,
        s.category = item.category
    """
    db.execute_query(cypher_skill, {"skills": data["skills"]})

    # 3. Seed Project Nodes
    logger.info(f"Seeding {len(data['projects'])} Project nodes...")
    cypher_proj = """
    UNWIND $projects AS item
    MERGE (p:Project {id: item.id})
    SET p.name = item.name,
        p.description = item.description,
        p.difficulty = item.difficulty
    """
    db.execute_query(cypher_proj, {"projects": data["projects"]})

    # 4. Seed JobRole Nodes
    logger.info(f"Seeding {len(data['job_roles'])} JobRole nodes...")
    cypher_role = """
    UNWIND $job_roles AS item
    MERGE (r:JobRole {id: item.id})
    SET r.name = item.name,
        r.description = item.description,
        r.level = item.level
    """
    db.execute_query(cypher_role, {"job_roles": data["job_roles"]})

    # 5. Seed Company Nodes
    logger.info(f"Seeding {len(data['companies'])} Company nodes...")
    cypher_comp = """
    UNWIND $companies AS item
    MERGE (comp:Company {id: item.id})
    SET comp.name = item.name,
        comp.industry = item.industry,
        comp.location = item.location
    """
    db.execute_query(cypher_comp, {"companies": data["companies"]})

    # 6. Seed Relationship: (:Candidate)-[:HAS_SKILL]->(:Skill)
    logger.info("Seeding HAS_SKILL relationships...")
    cypher_has_skill = """
    UNWIND $candidate_skills AS item
    MATCH (c:Candidate {id: item.candidate_id})
    UNWIND item.skill_ids AS skill_id
    MATCH (s:Skill {id: skill_id})
    MERGE (c)-[:HAS_SKILL]->(s)
    """
    db.execute_query(cypher_has_skill, {"candidate_skills": data["candidate_skills"]})

    # 7. Seed Relationship: (:Candidate)-[:WORKED_ON]->(:Project)
    logger.info("Seeding WORKED_ON relationships...")
    cypher_worked_on = """
    UNWIND $candidate_projects AS item
    MATCH (c:Candidate {id: item.candidate_id})
    UNWIND item.project_ids AS proj_id
    MATCH (p:Project {id: proj_id})
    MERGE (c)-[:WORKED_ON]->(p)
    """
    db.execute_query(cypher_worked_on, {"candidate_projects": data["candidate_projects"]})

    # 8. Seed Relationship: (:Project)-[:USES_SKILL]->(:Skill)
    logger.info("Seeding USES_SKILL relationships...")
    cypher_uses_skill = """
    UNWIND $project_skills AS item
    MATCH (p:Project {id: item.project_id})
    UNWIND item.skill_ids AS skill_id
    MATCH (s:Skill {id: skill_id})
    MERGE (p)-[:USES_SKILL]->(s)
    """
    db.execute_query(cypher_uses_skill, {"project_skills": data["project_skills"]})

    # 9. Seed Relationship: (:Candidate)-[:INTERESTED_IN]->(:JobRole)
    logger.info("Seeding INTERESTED_IN relationships...")
    cypher_interested_in = """
    UNWIND $candidate_roles_interested AS item
    MATCH (c:Candidate {id: item.candidate_id})
    UNWIND item.role_ids AS role_id
    MATCH (r:JobRole {id: role_id})
    MERGE (c)-[:INTERESTED_IN]->(r)
    """
    db.execute_query(cypher_interested_in, {"candidate_roles_interested": data["candidate_roles_interested"]})

    # 10. Seed Relationship: (:JobRole)-[:REQUIRES]->(:Skill)
    logger.info("Seeding REQUIRES relationships...")
    cypher_requires = """
    UNWIND $role_skills_required AS item
    MATCH (r:JobRole {id: item.role_id})
    UNWIND item.skill_ids AS skill_id
    MATCH (s:Skill {id: skill_id})
    MERGE (r)-[:REQUIRES]->(s)
    """
    db.execute_query(cypher_requires, {"role_skills_required": data["role_skills_required"]})

    # 11. Seed Relationship: (:JobRole)-[:AVAILABLE_AT]->(:Company)
    logger.info("Seeding AVAILABLE_AT relationships...")
    cypher_available_at = """
    UNWIND $role_companies AS item
    MATCH (r:JobRole {id: item.role_id})
    UNWIND item.company_ids AS comp_id
    MATCH (comp:Company {id: comp_id})
    MERGE (r)-[:AVAILABLE_AT]->(comp)
    """
    db.execute_query(cypher_available_at, {"role_companies": data["role_companies"]})

    logger.info("✅ Database seeding completed successfully!")
    close_db()

if __name__ == "__main__":
    try:
        seed_database()
    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        sys.exit(1)