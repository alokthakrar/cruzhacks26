from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from ..auth import get_current_user_id
from ..database import get_subjects_collection, get_sessions_collection
from ..models.subject import Subject, SubjectCreate, SubjectUpdate
from ..models.session import Session, SessionCreate
from ..services.knowledge_graph_generator import knowledge_graph_generator

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("")
async def list_subjects(user_id: str = Depends(get_current_user_id)):
    """List all subjects for the current user."""
    collection = get_subjects_collection()
    cursor = collection.find({"user_id": user_id}).sort("last_accessed", -1)
    subjects = await cursor.to_list(length=100)
    # Convert _id to id for frontend and return as plain dicts
    result = []
    for s in subjects:
        s['id'] = s.pop('_id')  # Rename _id to id
        s['created_at'] = s['created_at'].isoformat()
        s['last_accessed'] = s['last_accessed'].isoformat()
        result.append(s)
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject_data: SubjectCreate,
    user_id: str = Depends(get_current_user_id),
):
    """Create a new subject and auto-generate a knowledge graph."""
    collection = get_subjects_collection()

    now = datetime.utcnow()
    subject_doc = {
        "_id": str(ObjectId()),
        "user_id": user_id,
        "name": subject_data.name,
        "created_at": now,
        "last_accessed": now,
    }

    await collection.insert_one(subject_doc)

    # Auto-generate knowledge graph based on subject name
    print(f"\nCreating subject '{subject_data.name}' with ID: {subject_doc['_id']}")
    graph = await knowledge_graph_generator.generate_graph(
        subject_name=subject_data.name,
        subject_id=subject_doc["_id"],
        user_id=user_id
    )

    if graph:
        print(f"Knowledge graph linked to subject {subject_doc['_id']}")
    else:
        print(f"WARNING: No knowledge graph created for subject {subject_doc['_id']}")

    # Return as plain dict with id instead of _id
    return {
        "id": subject_doc["_id"],
        "user_id": subject_doc["user_id"],
        "name": subject_doc["name"],
        "created_at": subject_doc["created_at"].isoformat(),
        "last_accessed": subject_doc["last_accessed"].isoformat(),
        "knowledge_graph_created": graph is not None,
    }


@router.get("/{subject_id}", response_model=Subject)
async def get_subject(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get a specific subject."""
    collection = get_subjects_collection()
    subject = await collection.find_one({"_id": subject_id, "user_id": user_id})

    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    # Update last_accessed
    await collection.update_one(
        {"_id": subject_id},
        {"$set": {"last_accessed": datetime.utcnow()}},
    )

    return Subject(**subject)


@router.patch("/{subject_id}", response_model=Subject)
async def update_subject(
    subject_id: str,
    subject_data: SubjectUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """Update a subject."""
    collection = get_subjects_collection()

    # Build update document with only provided fields
    update_fields = {k: v for k, v in subject_data.model_dump().items() if v is not None}
    update_fields["last_accessed"] = datetime.utcnow()

    result = await collection.find_one_and_update(
        {"_id": subject_id, "user_id": user_id},
        {"$set": update_fields},
        return_document=True,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    return Subject(**result)


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Delete a subject and all its sessions."""
    subjects_collection = get_subjects_collection()
    sessions_collection = get_sessions_collection()

    # Check subject exists and belongs to user
    subject = await subjects_collection.find_one({"_id": subject_id, "user_id": user_id})
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    # Delete all sessions for this subject
    await sessions_collection.delete_many({"subject_id": subject_id})

    # Delete the subject
    await subjects_collection.delete_one({"_id": subject_id})

    return None


# --- Session endpoints (nested under subjects) ---

@router.get("/{subject_id}/sessions", response_model=List[Session])
async def list_sessions(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """List all sessions for a subject."""
    # Verify subject exists and belongs to user
    subjects_collection = get_subjects_collection()
    subject = await subjects_collection.find_one({"_id": subject_id, "user_id": user_id})
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    sessions_collection = get_sessions_collection()
    cursor = sessions_collection.find({"subject_id": subject_id}).sort("timestamp", -1)
    sessions = await cursor.to_list(length=100)
    return [Session(**s) for s in sessions]


@router.post("/{subject_id}/sessions", response_model=Session, status_code=status.HTTP_201_CREATED)
async def create_session(
    subject_id: str,
    session_data: SessionCreate,
    user_id: str = Depends(get_current_user_id),
):
    """Start a new canvas session with an optional problem image."""
    # Verify subject exists and belongs to user
    subjects_collection = get_subjects_collection()
    subject = await subjects_collection.find_one({"_id": subject_id, "user_id": user_id})
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    # Update subject's last_accessed
    await subjects_collection.update_one(
        {"_id": subject_id},
        {"$set": {"last_accessed": datetime.utcnow()}},
    )

    sessions_collection = get_sessions_collection()
    session_doc = {
        "_id": str(ObjectId()),
        "user_id": user_id,
        "subject_id": subject_id,
        "problem_image": session_data.problem_image,
        "timestamp": datetime.utcnow(),
        "status": "in_progress",
        "error_types": [],
        "steps_attempted": 0,
    }

    await sessions_collection.insert_one(session_doc)
    return Session(**session_doc)


@router.get("/{subject_id}/sessions/{session_id}", response_model=Session)
async def get_session(
    subject_id: str,
    session_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get a specific session."""
    sessions_collection = get_sessions_collection()
    session = await sessions_collection.find_one({
        "_id": session_id,
        "subject_id": subject_id,
        "user_id": user_id,
    })

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return Session(**session)
