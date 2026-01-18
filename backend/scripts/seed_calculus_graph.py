"""
Seed script for Calculus knowledge graph and sample questions.

Run this to populate MongoDB with an initial Calculus curriculum.

Usage:
    python -m scripts.seed_calculus_graph
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports and change to backend dir for .env
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))
os.chdir(backend_dir)

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from app.config import get_settings


async def seed_calculus_graph():
    """Seed Calculus knowledge graph and questions."""
    
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    
    print("🌱 Seeding Calculus knowledge graph...")
    
    # Define Calculus knowledge graph
    calculus_graph = {
        "_id": "calculus_graph_v1",
        "subject_id": "calculus_1",
        "created_by": "system",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "nodes": {
            "functions": {
                "concept_id": "functions",
                "name": "Functions",
                "description": "Understanding function notation, domain, and range",
                "parents": [],
                "children": ["limits"],
                "default_params": {
                    "P_L0": 0.10,
                    "P_T": 0.10,
                    "P_G": 0.25,
                    "P_S": 0.10
                },
                "depth": 0
            },
            "limits": {
                "concept_id": "limits",
                "name": "Limits",
                "description": "Computing limits and understanding continuity",
                "parents": ["functions"],
                "children": ["derivatives", "continuity"],
                "default_params": {
                    "P_L0": 0.10,
                    "P_T": 0.10,
                    "P_G": 0.25,
                    "P_S": 0.10
                },
                "depth": 1
            },
            "continuity": {
                "concept_id": "continuity",
                "name": "Continuity",
                "description": "Determining where functions are continuous",
                "parents": ["limits"],
                "children": [],
                "default_params": {
                    "P_L0": 0.10,
                    "P_T": 0.10,
                    "P_G": 0.25,
                    "P_S": 0.10
                },
                "depth": 2
            },
            "derivatives": {
                "concept_id": "derivatives",
                "name": "Derivatives",
                "description": "Basic derivative rules and computing derivatives",
                "parents": ["limits"],
                "children": ["chain_rule", "product_rule"],
                "default_params": {
                    "P_L0": 0.10,
                    "P_T": 0.08,
                    "P_G": 0.20,
                    "P_S": 0.10
                },
                "depth": 2
            },
            "chain_rule": {
                "concept_id": "chain_rule",
                "name": "Chain Rule",
                "description": "Applying the chain rule to composite functions",
                "parents": ["derivatives"],
                "children": ["implicit_differentiation"],
                "default_params": {
                    "P_L0": 0.10,
                    "P_T": 0.08,
                    "P_G": 0.15,
                    "P_S": 0.12
                },
                "depth": 3
            },
            "product_rule": {
                "concept_id": "product_rule",
                "name": "Product Rule",
                "description": "Differentiating products of functions",
                "parents": ["derivatives"],
                "children": ["implicit_differentiation"],
                "default_params": {
                    "P_L0": 0.10,
                    "P_T": 0.10,
                    "P_G": 0.20,
                    "P_S": 0.10
                },
                "depth": 3
            },
            "implicit_differentiation": {
                "concept_id": "implicit_differentiation",
                "name": "Implicit Differentiation",
                "description": "Finding derivatives of implicitly defined functions",
                "parents": ["chain_rule", "product_rule"],
                "children": ["related_rates"],
                "default_params": {
                    "P_L0": 0.10,
                    "P_T": 0.08,
                    "P_G": 0.15,
                    "P_S": 0.15
                },
                "depth": 4
            },
            "related_rates": {
                "concept_id": "related_rates",
                "name": "Related Rates",
                "description": "Solving problems involving rates of change",
                "parents": ["implicit_differentiation"],
                "children": [],
                "default_params": {
                    "P_L0": 0.10,
                    "P_T": 0.08,
                    "P_G": 0.10,
                    "P_S": 0.15
                },
                "depth": 5
            }
        },
        "root_concepts": ["functions"]
    }
    
    # Insert or replace graph
    await db["knowledge_graphs"].replace_one(
        {"_id": calculus_graph["_id"]},
        calculus_graph,
        upsert=True
    )
    print(f"✅ Created knowledge graph with {len(calculus_graph['nodes'])} concepts")
    
    # Define sample questions
    questions = [
        # Functions
        {
            "_id": str(ObjectId()),
            "subject_id": "calculus_1",
            "concept_id": "functions",
            "related_concepts": [],
            "question_text": "What is the domain of f(x) = 1/(x-2)?",
            "answer_key": "All real numbers except x=2",
            "elo_rating": 1150,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "easy",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        {
            "_id": str(ObjectId()),
            "subject_id": "calculus_1",
            "concept_id": "functions",
            "related_concepts": [],
            "question_text": "Evaluate f(3) if f(x) = x² - 4x + 1",
            "answer_key": "-2",
            "elo_rating": 1120,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "easy",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        
        # Limits
        {
            "_id": str(ObjectId()),
            "subject_id": "calculus_1",
            "concept_id": "limits",
            "related_concepts": ["functions"],
            "question_text": "Find lim(x→2) of (x² - 4)/(x - 2)",
            "answer_key": "4",
            "elo_rating": 1200,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "medium",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        {
            "_id": str(ObjectId()),
            "subject_id": "calculus_1",
            "concept_id": "limits",
            "related_concepts": [],
            "question_text": "Find lim(x→3) of (2x + 1)",
            "answer_key": "7",
            "elo_rating": 1150,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "easy",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        {
            "_id": str(ObjectId()),
            "subject_id": "calculus_1",
            "concept_id": "limits",
            "related_concepts": [],
            "question_text": "Find lim(x→0) of sin(x)/x",
            "answer_key": "1",
            "elo_rating": 1280,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "hard",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        
        # Derivatives
        {
            "_id": str(ObjectId()),
            "subject_id": "calculus_1",
            "concept_id": "derivatives",
            "related_concepts": ["limits"],
            "question_text": "Find the derivative of f(x) = 3x² + 2x - 5",
            "answer_key": "6x + 2",
            "elo_rating": 1180,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "easy",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        {
            "_id": str(ObjectId()),
            "subject_id": "calculus_1",
            "concept_id": "derivatives",
            "related_concepts": [],
            "question_text": "Find f'(x) if f(x) = x³ - 4x",
            "answer_key": "3x² - 4",
            "elo_rating": 1190,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "easy",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        {
            "_id": str(ObjectId()),
            "subject_id": "calculus_1",
            "concept_id": "derivatives",
            "related_concepts": [],
            "question_text": "Find the derivative of f(x) = sin(x) + cos(x)",
            "answer_key": "cos(x) - sin(x)",
            "elo_rating": 1220,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "medium",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        
        # Chain Rule
        {
            "_id": str(ObjectId()),
            "subject_id": "calculus_1",
            "concept_id": "chain_rule",
            "related_concepts": ["derivatives"],
            "question_text": "Find the derivative of f(x) = (3x + 1)⁴",
            "answer_key": "12(3x + 1)³",
            "elo_rating": 1240,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "medium",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        {
            "_id": str(ObjectId()),
            "subject_id": "calculus_1",
            "concept_id": "chain_rule",
            "related_concepts": ["derivatives"],
            "question_text": "Find f'(x) if f(x) = sin(2x)",
            "answer_key": "2cos(2x)",
            "elo_rating": 1230,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "medium",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        
        # Product Rule
        {
            "_id": str(ObjectId()),
            "subject_id": "calculus_1",
            "concept_id": "product_rule",
            "related_concepts": ["derivatives"],
            "question_text": "Find the derivative of f(x) = x²·sin(x)",
            "answer_key": "2x·sin(x) + x²·cos(x)",
            "elo_rating": 1250,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "medium",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
        {
            "_id": str(ObjectId()),
            "subject_id": "calculus_1",
            "concept_id": "product_rule",
            "related_concepts": ["derivatives"],
            "question_text": "Find f'(x) if f(x) = (x³)(e^x)",
            "answer_key": "3x²·e^x + x³·e^x",
            "elo_rating": 1270,
            "times_attempted": 0,
            "times_correct": 0,
            "difficulty_label": "hard",
            "created_by": "system",
            "created_at": datetime.utcnow()
        },
    ]
    
    # Insert questions
    await db["questions"].insert_many(questions)
    print(f"✅ Created {len(questions)} sample questions")
    
    # Create subject if it doesn't exist
    subject = {
        "_id": "calculus_1",
        "name": "Calculus I",
        "description": "Introduction to differential calculus",
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
    print(f"1. Initialize mastery: POST /api/bkt/initialize?user_id=test_user&subject_id=calculus_1")
    print(f"2. Get recommendation: GET /api/bkt/recommend/test_user/calculus_1")
    print(f"3. Submit answer: POST /api/bkt/submit?user_id=test_user&subject_id=calculus_1")
    print(f"4. View progress: GET /api/bkt/progress/test_user/calculus_1")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_calculus_graph())
