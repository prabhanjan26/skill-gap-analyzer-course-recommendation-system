"""Seed a set of realistic default roles into MongoDB (competency_matrix).

Idempotent: a role is only inserted if neither its name nor slug already exists,
so re-running setup.sh will not create duplicates or overwrite edited roles.

Run:  python scripts/seed_roles.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _skill(name, level, category):
    return {"skill_name": name, "required_level": level, "category": category}


SEED_ROLES = [
    {
        "role_name": "Senior Backend Developer",
        "description": "Leads backend system design and mentors junior engineers.",
        "skills": [
            _skill("Python", 4, "programming_languages"),
            _skill("REST API Design", 4, "backend"),
            _skill("FastAPI", 3, "backend"),
            _skill("PostgreSQL", 3, "databases"),
            _skill("Microservices", 3, "architecture"),
            _skill("System Design", 4, "architecture"),
            _skill("Docker", 3, "devops"),
            _skill("Unit Testing", 3, "quality"),
            _skill("Authentication", 3, "security"),
            _skill("Mentoring", 3, "soft_skills"),
        ],
    },
    {
        "role_name": "Frontend Engineer",
        "description": "Builds performant, accessible user interfaces.",
        "skills": [
            _skill("JavaScript", 4, "programming_languages"),
            _skill("TypeScript", 3, "programming_languages"),
            _skill("React", 4, "frontend"),
            _skill("CSS", 3, "frontend"),
            _skill("Responsive Design", 3, "frontend"),
            _skill("Web Accessibility", 3, "ui_ux"),
            _skill("Design Systems", 2, "ui_ux"),
            _skill("Jest", 3, "quality"),
            _skill("REST API Design", 2, "backend"),
            _skill("Communication", 3, "soft_skills"),
        ],
    },
    {
        "role_name": "DevOps Engineer",
        "description": "Owns CI/CD, infrastructure, and reliability.",
        "skills": [
            _skill("Docker", 4, "devops"),
            _skill("Kubernetes", 4, "devops"),
            _skill("Terraform", 3, "devops"),
            _skill("CI/CD Pipelines", 4, "devops"),
            _skill("AWS", 3, "cloud"),
            _skill("Prometheus", 3, "devops"),
            _skill("Bash Scripting", 3, "programming_languages"),
            _skill("Network Security", 3, "security"),
            _skill("Load Balancing", 3, "networking"),
            _skill("Incident Response", 3, "devops"),
        ],
    },
    {
        "role_name": "Data Scientist",
        "description": "Delivers ML models and data-driven insights.",
        "skills": [
            _skill("Python", 4, "programming_languages"),
            _skill("Machine Learning", 4, "data_science"),
            _skill("Deep Learning", 3, "data_science"),
            _skill("Statistics", 3, "data_science"),
            _skill("Pandas", 4, "data_science"),
            _skill("Data Visualization", 3, "data_science"),
            _skill("SQL Programming", 3, "programming_languages"),
            _skill("Model Deployment", 2, "ai_ml"),
            _skill("Feature Engineering", 3, "data_science"),
            _skill("Communication", 3, "soft_skills"),
        ],
    },
    {
        "role_name": "AI/ML Engineer",
        "description": "Builds and ships LLM and ML systems to production.",
        "skills": [
            _skill("Python", 4, "programming_languages"),
            _skill("Large Language Models", 3, "ai_ml"),
            _skill("RAG Pipelines", 3, "ai_ml"),
            _skill("Prompt Engineering", 3, "ai_ml"),
            _skill("Vector Databases", 3, "databases"),
            _skill("MLOps", 3, "ai_ml"),
            _skill("Model Deployment", 3, "ai_ml"),
            _skill("PyTorch", 3, "data_science"),
            _skill("Docker", 3, "devops"),
            _skill("System Design", 3, "architecture"),
        ],
    },
    {
        "role_name": "Mobile Developer",
        "description": "Develops cross-platform mobile applications.",
        "skills": [
            _skill("React Native", 4, "mobile"),
            _skill("JavaScript", 3, "programming_languages"),
            _skill("Mobile State Management", 3, "mobile"),
            _skill("Mobile UI Design", 3, "mobile"),
            _skill("REST API Design", 3, "backend"),
            _skill("Mobile Testing", 2, "quality"),
            _skill("App Store Deployment", 2, "mobile"),
            _skill("Mobile Security", 2, "security"),
            _skill("Firebase Mobile", 2, "mobile"),
            _skill("Communication", 3, "soft_skills"),
        ],
    },
    {
        "role_name": "Product Manager",
        "description": "Owns product strategy, roadmap, and delivery.",
        "skills": [
            _skill("Product Strategy", 4, "product_management"),
            _skill("Roadmapping", 4, "product_management"),
            _skill("User Research", 3, "product_management"),
            _skill("Prioritization Frameworks", 3, "product_management"),
            _skill("Product Analytics", 3, "product_management"),
            _skill("Agile", 3, "soft_skills"),
            _skill("Stakeholder Management", 4, "soft_skills"),
            _skill("Wireframing", 2, "ui_ux"),
            _skill("Go-to-Market Strategy", 3, "product_management"),
            _skill("Communication", 4, "soft_skills"),
        ],
    },
]


def main() -> None:
    from pymongo import MongoClient
    from slugify import slugify

    from app.config import get_settings

    settings = get_settings()
    if settings.mongodb_uri.startswith("your-mongodb"):
        print("ERROR: MONGODB_URI is not configured in backend/.env")
        sys.exit(1)

    client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=10000)
    db = client[settings.mongodb_db_name]
    collection = db["competency_matrix"]
    collection.create_index("role_slug", unique=True)
    collection.create_index("role_name", unique=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    created, skipped = 0, 0

    for role in SEED_ROLES:
        slug = slugify(role["role_name"])
        exists = collection.find_one(
            {"$or": [{"role_name": role["role_name"]}, {"role_slug": slug}]}
        )
        if exists:
            skipped += 1
            print(f"  skip (exists): {role['role_name']}")
            continue
        document = {
            "role_name": role["role_name"],
            "role_slug": slug,
            "description": role["description"],
            "skills": role["skills"],
            "created_at": now,
            "updated_at": now,
        }
        collection.insert_one(document)
        created += 1
        print(f"  created: {role['role_name']} ({len(role['skills'])} skills)")

    total = collection.count_documents({})
    print(f"Done. Seeded {created} new roles, skipped {skipped}. Total roles: {total}.")
    client.close()


if __name__ == "__main__":
    main()
