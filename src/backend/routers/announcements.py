"""
Announcement endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)

def require_auth(username: Optional[str]):
    if not username:
        raise HTTPException(status_code=401, detail="Authentication required")
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return teacher

@router.get("", response_model=List[dict])
def get_announcements():
    """Get all current (not expired) announcements"""
    now = datetime.utcnow().isoformat()
    anns = list(announcements_collection.find({"expiration": {"$gt": now}}))
    for ann in anns:
        ann["id"] = str(ann["_id"])
        ann.pop("_id", None)
    return anns

@router.post("", response_model=dict)
def create_announcement(
    message: str,
    expiration: str,
    start: Optional[str] = None,
    username: Optional[str] = None
):
    require_auth(username)
    if not message or not expiration:
        raise HTTPException(status_code=400, detail="Message and expiration required")
    ann = {
        "message": message,
        "expiration": expiration,
        "start": start
    }
    result = announcements_collection.insert_one(ann)
    ann["id"] = str(result.inserted_id)
    return ann

@router.put("/{announcement_id}", response_model=dict)
def update_announcement(
    announcement_id: str,
    message: Optional[str] = None,
    expiration: Optional[str] = None,
    start: Optional[str] = None,
    username: Optional[str] = None
):
    require_auth(username)
    update = {}
    if message is not None:
        update["message"] = message
    if expiration is not None:
        update["expiration"] = expiration
    if start is not None:
        update["start"] = start
    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = announcements_collection.update_one({"_id": announcement_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    ann = announcements_collection.find_one({"_id": announcement_id})
    ann["id"] = str(ann["_id"])
    ann.pop("_id", None)
    return ann

@router.delete("/{announcement_id}", response_model=dict)
def delete_announcement(announcement_id: str, username: Optional[str] = None):
    require_auth(username)
    result = announcements_collection.delete_one({"_id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"id": announcement_id, "deleted": True}
