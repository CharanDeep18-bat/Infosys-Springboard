from fastapi import APIRouter, Depends
from app.api.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    metadata = user.get("user_metadata") or {}

    return {
        "id": user["id"],
        "email": user.get("email"),
        "name": metadata.get("full_name"),
        "avatar_url": metadata.get("avatar_url")
    }