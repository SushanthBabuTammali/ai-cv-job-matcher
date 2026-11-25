"""cvmatch: score a CV against a job advert, show the skill gaps, and optionally ask Claude for honest tailoring tips."""
from .score import MatchResult, match
from .skills import extract_skills, split_requirements

__all__ = ["match", "MatchResult", "extract_skills", "split_requirements"]
