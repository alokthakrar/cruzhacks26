from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from ..auth import get_current_user_id
from ..database import get_user_collection, get_sessions_collection
from ..models.user import (
    UserState,
    UserCreate,
    UserUpdate,
    WeaknessRecord,
    Weakness,
    Session,
    SessionCreate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserState)
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """Get the current user's profile."""
    collection = get_user_collection()
    user = await collection.find_one({"_id": user_id})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Create a profile first with POST /api/users/me",
        )

    return UserState(**user)


@router.post("/me", response_model=UserState, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    user_id: str = Depends(get_current_user_id),
):
    """Create or initialize a user profile on first login."""
    collection = get_user_collection()

    # Check if user already exists
    existing = await collection.find_one({"_id": user_id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    user_doc = {
        "_id": user_id,
        "name": user_data.name,
        "email": user_data.email,
        "weaknesses": {},
        "created_at": datetime.utcnow(),
    }

    await collection.insert_one(user_doc)
    return UserState(**user_doc)


@router.patch("/me", response_model=UserState)
async def update_user(
    user_data: UserUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """Update the current user's profile."""
    collection = get_user_collection()

    # Build update document with only provided fields
    update_fields = {k: v for k, v in user_data.model_dump().items() if v is not None}

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    result = await collection.find_one_and_update(
        {"_id": user_id},
        {"$set": update_fields},
        return_document=True,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserState(**result)


@router.post("/me/weaknesses", response_model=UserState)
async def record_weakness(
    weakness_data: WeaknessRecord,
    user_id: str = Depends(get_current_user_id),
):
    """Record or update a weakness for the current user."""
    collection = get_user_collection()

    weakness_key = f"weaknesses.{weakness_data.weakness_type}"

    # Increment error count and update last_seen
    # Calculate confidence based on error count (simple formula: min(count/10, 1.0))
    result = await collection.find_one_and_update(
        {"_id": user_id},
        {
            "$inc": {f"{weakness_key}.error_count": 1},
            "$set": {f"{weakness_key}.last_seen": datetime.utcnow()},
        },
        return_document=True,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update confidence score based on new error count
    weakness = result.get("weaknesses", {}).get(weakness_data.weakness_type, {})
    error_count = weakness.get("error_count", 1)
    confidence = min(error_count / 10.0, 1.0)

    await collection.update_one(
        {"_id": user_id},
        {"$set": {f"{weakness_key}.confidence": confidence}},
    )

    # Fetch updated document
    updated = await collection.find_one({"_id": user_id})
    return UserState(**updated)


@router.get("/me/sessions", response_model=list[Session])
async def get_user_sessions(
    user_id: str = Depends(get_current_user_id),
    limit: int = 50,
    skip: int = 0,
):
    """Get the current user's session history."""
    collection = get_sessions_collection()

    cursor = (
        collection.find({"user_id": user_id})
        .sort("timestamp", -1)
        .skip(skip)
        .limit(limit)
    )

    sessions = await cursor.to_list(length=limit)
    return [Session(**s) for s in sessions]


@router.post("/me/sessions", response_model=Session, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    user_id: str = Depends(get_current_user_id),
):
    """Log a new learning session."""
    collection = get_sessions_collection()

    session_doc = {
        "_id": str(ObjectId()),
        "user_id": user_id,
        "problem_id": session_data.problem_id,
        "timestamp": datetime.utcnow(),
        "status": session_data.status,
        "error_type": session_data.error_type,
        "steps_attempted": session_data.steps_attempted,
    }

    await collection.insert_one(session_doc)

    # If session failed and has an error type, record the weakness
    if session_data.status == "failed" and session_data.error_type:
        user_collection = get_user_collection()
        weakness_key = f"weaknesses.{session_data.error_type}"

        await user_collection.update_one(
            {"_id": user_id},
            {
                "$inc": {f"{weakness_key}.error_count": 1},
                "$set": {f"{weakness_key}.last_seen": datetime.utcnow()},
            },
        )

        # Update confidence
        user = await user_collection.find_one({"_id": user_id})
        if user:
            weakness = user.get("weaknesses", {}).get(session_data.error_type, {})
            error_count = weakness.get("error_count", 1)
            confidence = min(error_count / 10.0, 1.0)
            await user_collection.update_one(
                {"_id": user_id},
                {"$set": {f"{weakness_key}.confidence": confidence}},
            )

    return Session(**session_doc)
