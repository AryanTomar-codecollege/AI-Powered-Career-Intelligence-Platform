import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database import get_db
from app.models import Profile

bearer = HTTPBearer(auto_error=False)
settings = get_settings()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                settings.supabase_user_url,
                headers={
                    "Authorization": f"Bearer {credentials.credentials}",
                    "apikey": settings.supabase_anon_key,
                },
            )
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Session is invalid or expired. Please sign in again.")
        user = response.json()
        if not user.get("id") or not user.get("email"):
            raise HTTPException(status_code=401, detail="Supabase did not return a valid user.")
        return {"id": user["id"], "email": user["email"]}
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Authentication service is temporarily unavailable.")


def get_or_create_profile(user: dict, db: Session) -> Profile:
    profile = db.query(Profile).filter_by(supabase_user_id=user["id"]).first()
    if profile:
        if profile.email != user["email"]:
            profile.email = user["email"]
            db.commit()
            db.refresh(profile)
        return profile
    profile = Profile(supabase_user_id=user["id"], email=user["email"])
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def current_profile(user: dict = Depends(get_current_user), db: Session = Depends(get_db)) -> Profile:
    return get_or_create_profile(user, db)
