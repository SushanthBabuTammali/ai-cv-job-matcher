from pathlib import Path

from cvmatch import extract_skills, match, split_requirements
from cvmatch.llm import build_prompt, tailor

EX = Path(__file__).resolve().parents[1] / "examples"


def test_aliases_map_to_one_skill():
    assert extract_skills("Built dashboards in PowerBI with DAX") >= {"Power BI", "Data visualisation"}
    assert "SQL" in extract_skills("Wrote T-SQL and PostgreSQL queries")


def test_single_letter_r_needs_word_boundary():
    assert "R" in extract_skills("Analysis in R and Python")
    assert "R" not in extract_skills("Strong reporting and research skills")


def test_desirable_section_is_split_out():
    job = "Essential\n- SQL and Python\n\nDesirable\n- Tableau\n- Git"
    essential, desirable = split_requirements(job)
    assert {"SQL", "Python"} <= essential
    assert {"Tableau", "Git"} <= desirable
    assert not essential & desirable


def test_example_match_finds_real_gaps():
    r = match((EX / "sample_cv.txt").read_text(), (EX / "job_junior_data_analyst.txt").read_text())
    assert 0 <= r.score <= 100
    assert "SQL" in r.matched_essential and "Power BI" in r.matched_essential
    assert "Tableau" in r.missing_desirable


def test_perfect_cv_scores_higher_than_unrelated_cv():
    job = (EX / "job_junior_data_analyst.txt").read_text()
    good = match((EX / "sample_cv.txt").read_text(), job).score
    bad = match("Experienced chef. Menu planning, food safety, team leadership.", job).score
    assert good > bad + 30


def test_ai_step_is_skipped_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = match("python sql", "Essential: python sql tableau")
    assert tailor("python sql", "Essential: python sql tableau", r) is None
    assert "never invent" not in build_prompt("cv", "job", r)  # rule lives in the system prompt
