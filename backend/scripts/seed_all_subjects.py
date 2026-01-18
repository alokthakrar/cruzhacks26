"""
Seed knowledge graphs for all existing subjects
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import get_settings

settings = get_settings()

async def seed_all_graphs():
    """Create knowledge graphs for all subjects"""
    client = AsyncIOMotorClient(settings.mongodb_uri, tlsAllowInvalidCertificates=True)
    db = client[settings.database_name]
    graphs_collection = db["knowledge_graphs"]

    # Define all knowledge graphs
    graphs = [
        # Calculus I
        {
            "subject_id": "696b5cd7f2697fc102b0c7a5",
            "name": "Calculus I",
            "description": "Fundamental calculus concepts: limits, derivatives, and integrals",
            "created_at": datetime.utcnow(),
            "nodes": [
                {
                    "id": "limits",
                    "name": "Limits",
                    "description": "Understanding limits and continuity",
                    "prerequisites": [],
                    "depth": 0,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.15, "P_G": 0.2, "P_S": 0.1}
                },
                {
                    "id": "derivatives_basic",
                    "name": "Basic Derivatives",
                    "description": "Power rule, sum rule, constant rule",
                    "prerequisites": ["limits"],
                    "depth": 1,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.15, "P_G": 0.15, "P_S": 0.1}
                },
                {
                    "id": "chain_rule",
                    "name": "Chain Rule",
                    "description": "Derivatives of composite functions",
                    "prerequisites": ["derivatives_basic"],
                    "depth": 2,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.12, "P_G": 0.12, "P_S": 0.12}
                },
                {
                    "id": "integrals_basic",
                    "name": "Basic Integration",
                    "description": "Antiderivatives and indefinite integrals",
                    "prerequisites": ["derivatives_basic"],
                    "depth": 2,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.12, "P_G": 0.15, "P_S": 0.1}
                },
                {
                    "id": "definite_integrals",
                    "name": "Definite Integrals",
                    "description": "Fundamental theorem of calculus",
                    "prerequisites": ["integrals_basic"],
                    "depth": 3,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.1, "P_G": 0.1, "P_S": 0.12}
                },
                {
                    "id": "applications",
                    "name": "Applications",
                    "description": "Area, volume, optimization problems",
                    "prerequisites": ["chain_rule", "definite_integrals"],
                    "depth": 4,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.1, "P_G": 0.08, "P_S": 0.15}
                }
            ],
            "root_concepts": ["limits"]
        },

        # Algebra 2
        {
            "subject_id": "696c3594d6f0b2831db1cdae",
            "name": "Algebra 2",
            "description": "Advanced algebra: polynomials, rational expressions, exponentials",
            "created_at": datetime.utcnow(),
            "nodes": [
                {
                    "id": "polynomials",
                    "name": "Polynomials",
                    "description": "Operations with polynomials, factoring",
                    "prerequisites": [],
                    "depth": 0,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.15, "P_G": 0.2, "P_S": 0.1}
                },
                {
                    "id": "quadratics",
                    "name": "Quadratic Equations",
                    "description": "Solving quadratics, completing the square",
                    "prerequisites": ["polynomials"],
                    "depth": 1,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.15, "P_G": 0.15, "P_S": 0.1}
                },
                {
                    "id": "rational_expressions",
                    "name": "Rational Expressions",
                    "description": "Simplifying and solving rational equations",
                    "prerequisites": ["polynomials"],
                    "depth": 1,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.12, "P_G": 0.15, "P_S": 0.12}
                },
                {
                    "id": "exponentials",
                    "name": "Exponential Functions",
                    "description": "Properties and graphs of exponential functions",
                    "prerequisites": ["quadratics"],
                    "depth": 2,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.12, "P_G": 0.12, "P_S": 0.1}
                },
                {
                    "id": "logarithms",
                    "name": "Logarithms",
                    "description": "Logarithmic functions and properties",
                    "prerequisites": ["exponentials"],
                    "depth": 3,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.1, "P_G": 0.1, "P_S": 0.12}
                }
            ],
            "root_concepts": ["polynomials"]
        },

        # Quadratic Equations (original)
        {
            "subject_id": "696c5c5f80ac0ec6262336a2",
            "name": "Quadratic Equations",
            "description": "Mastering quadratic equations and their applications",
            "created_at": datetime.utcnow(),
            "nodes": [
                {
                    "id": "factoring",
                    "name": "Factoring",
                    "description": "Factor quadratics to find solutions",
                    "prerequisites": [],
                    "depth": 0,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.15, "P_G": 0.2, "P_S": 0.1}
                },
                {
                    "id": "quadratic_formula",
                    "name": "Quadratic Formula",
                    "description": "Using the quadratic formula to solve equations",
                    "prerequisites": ["factoring"],
                    "depth": 1,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.15, "P_G": 0.15, "P_S": 0.1}
                },
                {
                    "id": "completing_square",
                    "name": "Completing the Square",
                    "description": "Alternative method for solving quadratics",
                    "prerequisites": ["factoring"],
                    "depth": 1,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.12, "P_G": 0.15, "P_S": 0.12}
                },
                {
                    "id": "graphing",
                    "name": "Graphing Parabolas",
                    "description": "Vertex form, axis of symmetry, transformations",
                    "prerequisites": ["completing_square"],
                    "depth": 2,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.12, "P_G": 0.12, "P_S": 0.1}
                },
                {
                    "id": "applications",
                    "name": "Applications",
                    "description": "Word problems and real-world applications",
                    "prerequisites": ["quadratic_formula", "graphing"],
                    "depth": 3,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.1, "P_G": 0.08, "P_S": 0.15}
                }
            ],
            "root_concepts": ["factoring"]
        },

        # Quadratic Equations 2
        {
            "subject_id": "696c5d749c86374616901c32",
            "name": "Quadratic Equations 2",
            "description": "Advanced quadratic concepts and applications",
            "created_at": datetime.utcnow(),
            "nodes": [
                {
                    "id": "standard_form",
                    "name": "Standard Form",
                    "description": "Working with ax² + bx + c = 0",
                    "prerequisites": [],
                    "depth": 0,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.15, "P_G": 0.2, "P_S": 0.1}
                },
                {
                    "id": "discriminant",
                    "name": "Discriminant",
                    "description": "Using b² - 4ac to determine solution types",
                    "prerequisites": ["standard_form"],
                    "depth": 1,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.15, "P_G": 0.15, "P_S": 0.1}
                },
                {
                    "id": "complex_solutions",
                    "name": "Complex Solutions",
                    "description": "Solving quadratics with imaginary roots",
                    "prerequisites": ["discriminant"],
                    "depth": 2,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.12, "P_G": 0.12, "P_S": 0.12}
                },
                {
                    "id": "systems",
                    "name": "Quadratic Systems",
                    "description": "Systems involving quadratic equations",
                    "prerequisites": ["complex_solutions"],
                    "depth": 3,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.1, "P_G": 0.1, "P_S": 0.15}
                }
            ],
            "root_concepts": ["standard_form"]
        },

        # Quadratic Equations 3
        {
            "subject_id": "696c5e1ebff4c295b77d5761",
            "name": "Quadratic Equations 3",
            "description": "Quadratic inequalities and optimization",
            "created_at": datetime.utcnow(),
            "nodes": [
                {
                    "id": "inequalities_basic",
                    "name": "Quadratic Inequalities",
                    "description": "Solving and graphing quadratic inequalities",
                    "prerequisites": [],
                    "depth": 0,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.15, "P_G": 0.2, "P_S": 0.1}
                },
                {
                    "id": "sign_analysis",
                    "name": "Sign Analysis",
                    "description": "Test points and interval notation",
                    "prerequisites": ["inequalities_basic"],
                    "depth": 1,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.15, "P_G": 0.15, "P_S": 0.1}
                },
                {
                    "id": "optimization",
                    "name": "Optimization",
                    "description": "Finding maximum and minimum values",
                    "prerequisites": ["sign_analysis"],
                    "depth": 2,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.12, "P_G": 0.12, "P_S": 0.12}
                },
                {
                    "id": "real_world",
                    "name": "Real-World Problems",
                    "description": "Physics, business, and geometry applications",
                    "prerequisites": ["optimization"],
                    "depth": 3,
                    "bkt_params": {"P_L0": 0.1, "P_T": 0.1, "P_G": 0.08, "P_S": 0.15}
                }
            ],
            "root_concepts": ["inequalities_basic"]
        }
    ]

    # Insert all graphs
    for graph in graphs:
        # Delete existing graph for this subject (if any)
        await graphs_collection.delete_many({"subject_id": graph["subject_id"]})

        # Insert the new graph
        result = await graphs_collection.insert_one(graph)
        print(f"✅ Seeded '{graph['name']}' with {len(graph['nodes'])} concepts")

    client.close()
    print(f"\n🎉 Successfully seeded {len(graphs)} knowledge graphs!")

if __name__ == "__main__":
    asyncio.run(seed_all_graphs())
