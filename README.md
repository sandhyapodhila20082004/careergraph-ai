# CareerGraph AI

> **Tagline:** Discover career opportunities through skills, projects and connections.

CareerGraph AI is a graph-native career intelligence platform built for the Wexa AI take-home assignment. The application uses **CognoDB** (an openCypher-compliant graph database accessed via the official Neo4j Python driver) to map candidates, skills, projects, job roles, and companies into a interconnected graph.

---

## 💡 Why a Graph Database?

Traditional relational databases (RDBMS) model data in static tables using foreign key joins. In a career application involving multi-hop exploratory queries such as:
> *"Find companies hiring for job roles that require skills used in projects completed by candidate Sandhya"*

In SQL, this requires **5+ JOIN operations across multiple junction tables** (`candidates_skills`, `projects_skills`, `job_roles_skills`, `job_roles_companies`), leading to heavy query syntax and exponential join overhead as depth increases.

In **CognoDB (openCypher)**, relationships are first-class entities. A multi-hop graph traversal is written naturally as an intuitive path:

```cypher
MATCH (c:Candidate {id: $candidate_id})-[:HAS_SKILL]->(s:Skill)<-[:REQUIRES]-(r:JobRole)-[:AVAILABLE_AT]->(comp:Company)
RETURN comp.name, r.name, collect(s.name) AS matching_skills