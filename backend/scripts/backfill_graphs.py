"""
Backfill knowledge graphs for existing subjects.

Usage:
  python backend/scripts/backfill_graphs.py
"""
import asyncio
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import (  # noqa: E402
    connect_to_mongo,
    close_mongo_connection,
    get_subjects_collection,
    get_knowledge_graphs_collection
)
from app.services.knowledge_graph_generator import knowledge_graph_generator  # noqa: E402


async def backfill_graphs() -> None:
    await connect_to_mongo()
    knowledge_graph_generator.load_model()

    subjects_collection = get_subjects_collection()
    graphs_collection = get_knowledge_graphs_collection()

    created = 0
    updated = 0
    skipped = 0

    cursor = subjects_collection.find({})
    subjects = await cursor.to_list(length=1000)

    for subject in subjects:
        subject_id = subject["_id"]
        subject_name = subject.get("name", subject_id)
        user_id = subject.get("user_id", "system")

        graph_doc = await graphs_collection.find_one({"subject_id": subject_id})
        if not graph_doc:
            result = await knowledge_graph_generator.generate_graph(
                subject_name=subject_name,
                subject_id=subject_id,
                user_id=user_id
            )
            if result:
                created += 1
            continue

        updates = {}
        if not graph_doc.get("name"):
            updates["name"] = subject_name
        if not graph_doc.get("description"):
            updates["description"] = f"Learning path for {subject_name}"
        if updates:
            updates["updated_at"] = datetime.utcnow()
            await graphs_collection.update_one({"_id": graph_doc["_id"]}, {"$set": updates})
            updated += 1
        else:
            skipped += 1

    await close_mongo_connection()
    print(f"Created: {created}, Updated: {updated}, Skipped: {skipped}")


if __name__ == "__main__":
    asyncio.run(backfill_graphs())
