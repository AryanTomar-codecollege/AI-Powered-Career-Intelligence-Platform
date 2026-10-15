from app.resume_parser import parse_resume


def test_extracts_common_skills_titles_and_dates():
    parsed = parse_resume(
        "Software Developer with Python, FastAPI, SQL and Machine Learning. "
        "B.Tech Computer Science. Jan 2023 - Present"
    )
    assert {"python", "fastapi", "sql", "machine learning"}.issubset(set(parsed["skills"]))
    assert "software developer" in parsed["job_titles"]
    assert "jan 2023 - Present" in [x.lower() for x in parsed["duration_markers"]]
