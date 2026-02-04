from careeros.parsing.service import build_profile_from_text

def test_profile_extracts_skills():
    txt = "Experienced in Python, Docker, Kubernetes, MLflow, DVC, FastAPI and Streamlit."
    p = build_profile_from_text(txt, candidate_name="Ganesh")
    assert p.candidate_name == "Ganesh"
    assert "python" in p.skills
    assert "docker" in p.skills
