"""Check knowledge graph in database"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import get_settings

settings = get_settings()

async def check_graph():
    client = AsyncIOMotorClient(settings.mongodb_uri, tlsAllowInvalidCertificates=True)
    db = client[settings.database_name]

    graph = await db["knowledge_graphs"].find_one({"subject_id": "algebra_basics"})

    if graph:
        print("✅ Found knowledge graph!")
        print(f"Subject ID: {graph['subject_id']}")
        print(f"Name: {graph['name']}")
        print(f"Number of nodes: {len(graph['nodes'])}")
        print(f"Root concepts: {graph['root_concepts']}")
        print("\nFull document structure:")
        # Remove _id for cleaner output
        if '_id' in graph:
            graph['_id'] = str(graph['_id'])
        print(json.dumps(graph, indent=2, default=str))
    else:
        print("❌ No knowledge graph found for algebra_basics")

    client.close()

if __name__ == "__main__":
    asyncio.run(check_graph())
