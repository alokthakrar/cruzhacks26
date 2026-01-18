"""
Seed script for Quadratic Equations knowledge graph and sample questions.

Run this to populate MongoDB with a Quadratic Equations curriculum.

Usage:
    python scripts/seed_quadratics_graph.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from app.config import get_settings


async def seed_quadratics_graph():
    """Seed Quadratic Equations knowledge graph and questions."""
    
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    
    print("🌱 Seeding Quadratic Equations knowledge graph...")
    
    # Define Quadratic Equations knowledge graph
    quadratics_graph = {
        "_id": "quadratics_graph_v1",
        "subject_id": "quadratic_equations",
        "created_by": "system",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "nodes": {
            "linear_equations": {
                "concept_id": "linear_equations",
                "name": "Linear Equations",
                "description": "Solving equations of the form ax + b = 0",
                "parents": [],
                "children": ["standard_form", "factoring_basics"],
                "default_params": {
                    "P_L0": 0.15,
                    "P_T": 0.12,
                    "P_G": 0.25,
                    "P_S": 0.10
                },
                "depth": 0
            },
            "factoring_basics": {
                "concept_id": "factoring_basics",
                "name": "Basic Factoring",
                "description": "Factoring expressions like x² + bx + c",
                "parents": ["linear_equations"],
                "children": ["factoring_quadratics"],
                "default_params": {
                    "P_L0": 0.10,
                    "P_T": 0.10,
                    "P_G": 0.20,
                    "P_S": 0.12
                },
                "depth": 1
            },
            "standard_form": {
                "concept_id": "standard_form",
                "name": "Quadratic Standard Form",
                "description": "Understanding ax² + bx + c = 0",
                "parents": ["linear_equations"],
                "children": ["factoring_quadratics", "quadratic_formula"],
                "default_params": {
                    "P_L0": 0.12,
                    "P_T": 0.10,
                    "P_G": 0.25,
                    "P_S": 0.10
                },
                "depth": 1
            },
            "factoring_quadratics": {
                "concept_id": "factoring_quadratics",
                "name": "Factoring Quadratics",
                "description": "Factoring quadratic equations to find roots",
                "parents": ["standard_form", "factoring_basics"],
                "children": ["vertex_form", "graphing"],
                "default_params": {
                    "P_L0": 0.10,
                    "P_T": 0.08,
                    "P_G": 0.18,
                    "P_S": 0.12
                },
                "depth": 2
            },
            "quadratic_formula": {
                "concept_id": "quadratic_formula",
                "name": "Quadratic Formula",
                "description": "Using x = (-b ± √(b²-4ac)) / 2a",
                "parents": ["standard_form"],
                "children": ["completing_square", "discriminant"],
                "default_params": {
                    "P_L0": 0.10,
                    "P_T": 0.10,
                    "P_G": 0.20,
                    "P_S": 0.10
                },
                "depth": 2
            },
            "completing_square": {
                "concept_id": "completing_square",
                "name": "Completing the Square",
                "description": "Rewriting quadratics by completing the square",
                "parents": ["quadratic_formula"],
                "children": ["vertex_form"],
                "default_params": {
                    "P_L0": 0.10,
                    "P_T": 0.08,
                    "P_G": 0.15,
                    "P_S": 0.15
                },
                "depth": 3
            },
            "discriminant": {
                "concept_id": "discriminant",
                "name": "Discriminant",
                "description": "Understanding b² - 4ac and number of solutions",
                "parents": ["quadratic_formula"],
                "children": ["graphing"],
                "default_params": {
                    "P_L0": 0.10,
                    "P_T": 0.10,
                    "P_G": 0.22,
                    "P_S": 0.10
                },
                "depth": 3
            },
            "vertex_form": {
                "concept_id": "vertex_form",
                "name": "Vertex Form",
                "description": "Understanding a(x-h)² + k form",
                "parents": ["completing_square", "factoring_quadratics"],
                "children": ["graphing"],
                "default_params": {
                    "P_L0": 0.10,
                    "P_T": 0.10,
                    "P_G": 0.20,
                    "P_S": 0.12
                },
                "depth": 4
            },
            "graphing": {
                "concept_id": "graphing",
                "name": "Graphing Parabolas",
                "description": "Graphing quadratic functions and finding key features",
                "parents": ["vertex_form", "factoring_quadratics", "discriminant"],
                "children": ["applications"],
                "default_params": {
                    "P_L0": 0.10,
                    "P_T": 0.08,
                    "P_G": 0.18,
                    "P_S": 0.12
                },
                "depth": 5
            },
            "applications": {
                "concept_id": "applications",
                "name": "Word Problems",
                "description": "Applying quadratics to real-world scenarios",
                "parents": ["graphing"],
                "children": [],
                "default_params": {
                    "P_L0": 0.08,
                    "P_T": 0.08,
                    "P_G": 0.12,
                    "P_S": 0.15
                },
                "depth": 6
            }
        },
        "root_concepts": ["linear_equations"]
    }
    
    # Insert or replace graph
    await db["knowledge_graphs"].replace_one(
        {"_id": quadratics_graph["_id"]},
        quadratics_graph,
        upsert=True
    )
    print(f"✅ Created knowledge graph with {len(quadratics_graph['nodes'])} concepts")
    
    # Define sample questions
    questions = [
        # Linear Equations
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "linear_equations",
            "related_concepts": [],
            "question_text": "Solve for x: 3x + 7 = 22",
            "answer_key": "x = 5",
            "elo_rating": 1100,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "easy",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "linear_equations",
            "related_concepts": [],
            "question_text": "Solve: 2x - 5 = 11",
            "answer_key": "x = 8",
            "elo_rating": 1120,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "easy",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        
        # Factoring Basics
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "factoring_basics",
            "related_concepts": ["linear_equations"],
            "question_text": "Factor: x² + 5x + 6",
            "answer_key": "(x + 2)(x + 3)",
            "elo_rating": 1180,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "medium",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "factoring_basics",
            "related_concepts": [],
            "question_text": "Factor: x² - 7x + 12",
            "answer_key": "(x - 3)(x - 4)",
            "elo_rating": 1200,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "medium",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        
        # Standard Form
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "standard_form",
            "related_concepts": [],
            "question_text": "Identify a, b, and c in: 2x² - 3x + 5 = 0",
            "answer_key": "a=2, b=-3, c=5",
            "elo_rating": 1150,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "easy",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "standard_form",
            "related_concepts": [],
            "question_text": "Rewrite in standard form: (x + 2)² = 9",
            "answer_key": "x² + 4x - 5 = 0",
            "elo_rating": 1220,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "medium",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        
        # Factoring Quadratics
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "factoring_quadratics",
            "related_concepts": ["factoring_basics", "standard_form"],
            "question_text": "Solve by factoring: x² + 6x + 8 = 0",
            "answer_key": "x = -2 or x = -4",
            "elo_rating": 1210,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "medium",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "factoring_quadratics",
            "related_concepts": ["factoring_basics"],
            "question_text": "Solve: x² - 9 = 0",
            "answer_key": "x = 3 or x = -3",
            "elo_rating": 1190,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "easy",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "factoring_quadratics",
            "related_concepts": [],
            "question_text": "Factor and solve: 2x² + 7x + 3 = 0",
            "answer_key": "x = -1/2 or x = -3",
            "elo_rating": 1260,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "hard",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        
        # Quadratic Formula
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "quadratic_formula",
            "related_concepts": ["standard_form"],
            "question_text": "Use the quadratic formula to solve: x² + 4x + 1 = 0",
            "answer_key": "x = -2 ± √3",
            "elo_rating": 1240,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "medium",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "quadratic_formula",
            "related_concepts": [],
            "question_text": "Solve using the quadratic formula: 2x² - 5x - 3 = 0",
            "answer_key": "x = 3 or x = -1/2",
            "elo_rating": 1250,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "medium",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        
        # Discriminant
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "discriminant",
            "related_concepts": ["quadratic_formula"],
            "question_text": "Find the discriminant of x² + 2x + 5 = 0. How many real solutions?",
            "answer_key": "b² - 4ac = -16, no real solutions",
            "elo_rating": 1230,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "medium",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "discriminant",
            "related_concepts": [],
            "question_text": "For what value of k does x² + kx + 4 = 0 have exactly one solution?",
            "answer_key": "k = 4 or k = -4",
            "elo_rating": 1280,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "hard",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        
        # Vertex Form
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "vertex_form",
            "related_concepts": ["completing_square"],
            "question_text": "Find the vertex of y = 2(x - 3)² + 5",
            "answer_key": "(3, 5)",
            "elo_rating": 1210,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "medium",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "vertex_form",
            "related_concepts": [],
            "question_text": "Convert to vertex form: y = x² + 6x + 5",
            "answer_key": "y = (x + 3)² - 4",
            "elo_rating": 1270,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "hard",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        
        # Graphing
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "graphing",
            "related_concepts": ["vertex_form"],
            "question_text": "What is the axis of symmetry for y = x² - 4x + 3?",
            "answer_key": "x = 2",
            "elo_rating": 1220,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "medium",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "graphing",
            "related_concepts": ["factoring_quadratics"],
            "question_text": "Find the x-intercepts of y = x² - 5x + 6",
            "answer_key": "x = 2 and x = 3",
            "elo_rating": 1200,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "medium",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        
        # Applications
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "applications",
            "related_concepts": ["graphing", "quadratic_formula"],
            "question_text": "A ball is thrown upward with initial velocity 20 m/s. Height h(t) = -5t² + 20t. When does it hit the ground?",
            "answer_key": "t = 4 seconds",
            "elo_rating": 1290,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "hard",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        {
            "_id": str(ObjectId()),
            "subject_id": "quadratic_equations",
            "concept_id": "applications",
            "related_concepts": [],
            "question_text": "The area of a rectangle is 48 sq ft. Length is 4 ft more than width. Find dimensions.",
            "answer_key": "Width = 4 ft, Length = 8 ft",
            "elo_rating": 1310,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "hard",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
    ]
    
    # Clear existing quadratics questions
    await db["questions"].delete_many({"subject_id": "quadratic_equations"})
    
    # Insert questions
    await db["questions"].insert_many(questions)
    print(f"✅ Created {len(questions)} sample questions")
    
    # Create subject if it doesn't exist
    subject = {
        "_id": "quadratic_equations",
        "name": "Quadratic Equations",
        "description": "Complete guide to solving and graphing quadratic equations",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db["subjects"].replace_one(
        {"_id": subject["_id"]},
        subject,
        upsert=True
    )
    print(f"✅ Created subject: {subject['name']}")
    
    print("\n🎉 Seeding complete!")
    print(f"\nTo test the system:")
    print(f"1. Initialize mastery: POST /api/bkt/initialize?user_id=test_user&subject_id=quadratic_equations")
    print(f"2. Get recommendation: GET /api/bkt/recommend/test_user/quadratic_equations")
    print(f"3. Submit answer: POST /api/bkt/submit?user_id=test_user&subject_id=quadratic_equations")
    print(f"4. View progress: GET /api/bkt/progress/test_user/quadratic_equations")
    print(f"\nOr open the demo frontend and change subject_id to 'quadratic_equations'")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_quadratics_graph())
