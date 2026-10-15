import hashlib
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.auth import current_profile
from app.config import get_settings
from app.database import get_db
from app.models import Profile, Resume
from app.resume_parser import extract_text, parse_resume
from app.schemas import ResumeOut

router = APIRouter(prefix="/api/resumes", tags=["Resume parsing"])
settings = get_settings()
ALLOWED_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


@router.post("/parse", response_model=ResumeOut, status_code=201)
async def upload_and_parse_resume(
    file: UploadFile = File(...),
    profile: Profile = Depends(current_profile),
    db: Session = Depends(get_db),
):
    filename = (file.filename or "").replace("\\", "/").split("/")[-1]
    if not filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=415, detail="Upload a PDF or DOCX resume.")
    content = await file.read(settings.max_resume_size_mb * 1024 * 1024 + 1)
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(content) > settings.max_resume_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Resume exceeds {settings.max_resume_size_mb} MB.")
    try:
        text = extract_text(filename, content)
    except (ValueError, Exception) as exc:
        # Do not expose parser internals or file paths to clients.
        raise HTTPException(status_code=422, detail=str(exc) if isinstance(exc, ValueError) else "Could not read this resume.") from exc

    parsed = parse_resume(text)
    digest = hashlib.sha256(content).hexdigest()
    resume = Resume(
        profile_id=profile.id,
        filename=filename[:255],
        content_type=file.content_type or "application/octet-stream",
        content_sha256=digest,
        extracted_text=text,
        **parsed,
    )
    db.add(resume)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This exact resume has already been uploaded to your profile.")
    db.refresh(resume)

    # Merge extracted skills into the user's editable profile without duplicates.
    profile.skills = sorted(set((profile.skills or []) + parsed["skills"]))
    db.add(profile)
    db.commit()
    return resume


@router.get("", response_model=list[ResumeOut])
def list_resumes(profile: Profile = Depends(current_profile), db: Session = Depends(get_db)):
    return db.query(Resume).filter_by(profile_id=profile.id).order_by(Resume.created_at.desc()).all()
