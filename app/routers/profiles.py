from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth import current_profile
from app.database import get_db
from app.models import Profile
from app.schemas import ProfileOut, ProfileUpdate

router = APIRouter(prefix="/api/profile", tags=["Profile"])


@router.get("", response_model=ProfileOut)
def read_profile(profile: Profile = Depends(current_profile)):
    return profile


@router.put("", response_model=ProfileOut)
def update_profile(
    payload: ProfileUpdate,
    profile: Profile = Depends(current_profile),
    db: Session = Depends(get_db),
):
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
