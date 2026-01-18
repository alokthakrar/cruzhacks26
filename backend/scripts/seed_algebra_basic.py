"""
Seed a basic Algebra knowledge graph for high school level
Simple tree structure: 5 concepts with clear progression
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import get_settings

settings = get_settings()

async def seed_algebra_graph():
    """Create a basic Algebra knowledge graph"""
    client = AsyncIOMotorClient(settings.mongodb_uri, tlsAllowInvalidCertificates=True)
    db = client[settings.database_name]
    graphs_collection = db["knowledge_graphs"]

    # Define the knowledge graph
    graph = {
        "subject_id": "algebra_basics",  # This should match a subject in your subjects collection
        "name": "Basic Algebra",
        "description": "Foundational algebra concepts for high school",
        "created_at": datetime.utcnow(),
        "nodes": [
            {
                "id": "basic_operations",
                "name": "Basic Operations",
                "description": "Addition, subtraction, multiplication, division with variables",
                "prerequisites": [],  # Root concept - no prerequisites
                "depth": 0,
                "bkt_params": {
                    "P_L0": 0.1,  # Initial mastery probability
                    "P_T": 0.15,  # Probability of learning
                    "P_G": 0.2,   # Probability of guessing
                    "P_S": 0.1    # Probability of slipping
                }
            },
            {
                "id": "solving_equations",
                "name": "Solving Simple Equations",
                "description": "Solve equations like x + 5 = 12, 3x = 15",
                "prerequisites": ["basic_operations"],
                "depth": 1,
                "bkt_params": {
                    "P_L0": 0.1,
                    "P_T": 0.15,
                    "P_G": 0.15,
                    "P_S": 0.1
                }
            },
            {
                "id": "two_step_equations",
                "name": "Two-Step Equations",
                "description": "Equations like 2x + 3 = 11, requiring multiple operations",
                "prerequisites": ["solving_equations"],
                "depth": 2,
                "bkt_params": {
                    "P_L0": 0.1,
                    "P_T": 0.12,
                    "P_G": 0.12,
                    "P_S": 0.1
                }
            },
            {
                "id": "linear_equations",
                "name": "Linear Equations",
                "description": "More complex equations like 3(x - 2) = 2x + 5",
                "prerequisites": ["two_step_equations"],
                "depth": 3,
                "bkt_params": {
                    "P_L0": 0.1,
                    "P_T": 0.12,
                    "P_G": 0.1,
                    "P_S": 0.12
                }
            },
            {
                "id": "word_problems",
                "name": "Algebraic Word Problems",
                "description": "Apply algebra to solve real-world problems",
                "prerequisites": ["linear_equations"],
                "depth": 4,
                "bkt_params": {
                    "P_L0": 0.1,
                    "P_T": 0.1,
                    "P_G": 0.08,
                    "P_S": 0.15
                }
            }
        ],
        "root_concepts": ["basic_operations"]  # Starting points
    }

    # Delete existing graph for this subject (if any)
    await graphs_collection.delete_many({"subject_id": "algebra_basics"})

    # Insert the new graph
    result = await graphs_collection.insert_one(graph)
    print(f"✅ Seeded Algebra graph with ID: {result.inserted_id}")
    print(f"   - Total concepts: {len(graph['nodes'])}")
    print(f"   - Root concepts: {graph['root_concepts']}")
    print(f"   - Max depth: {max(node['depth'] for node in graph['nodes'])}")

    # Also create a matching subject if it doesn't exist
    subjects_collection = db["subjects"]
    existing_subject = await subjects_collection.find_one({"_id": "algebra_basics"})

    if not existing_subject:
        subject = {
            "_id": "algebra_basics",
            "name": "Basic Algebra",
            "user_id": "dev_user_123",  # Default dev user
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow()
        }
        await subjects_collection.insert_one(subject)
        print(f"✅ Created matching subject: Basic Algebra")
    else:
        print(f"ℹ️  Subject 'Basic Algebra' already exists")

    client.close()
    print("\n🎉 Knowledge graph seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_algebra_graph())
