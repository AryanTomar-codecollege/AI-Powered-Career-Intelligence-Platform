from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=160)
    headline: str | None = Field(default=None, max_length=240)
    location: str | None = Field(default=None, max_length=160)
    education: list[dict] | None = None
    skills: list[str] | None = None
    certifications: list[str] | None = None
    work_experience: list[dict] | None = None


class ProfileOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None
    headline: str | None
    location: str | None
    education: list
    skills: list
    certifications: list
    work_experience: list
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ResumeOut(BaseModel):
    id: int
    filename: str
    skills: list[str]
    job_titles: list[str]
    institutions: list[str]
    duration_markers: list[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
