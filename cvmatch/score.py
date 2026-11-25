"""Scoring a CV against a job description.

Two signals are combined:
* Skill coverage (70%): how many of the advert's essential and desirable skills the CV shows.
  Essential skills count twice as much as desirable ones.
* Text similarity (30%): TF-IDF cosine similarity between the CV and the advert, which rewards
  using the same vocabulary as the recruiter (ATS systems often work this way).
"""
from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .skills import extract_skills, split_requirements

ESSENTIAL_WEIGHT = 2.0
DESIRABLE_WEIGHT = 1.0
COVERAGE_SHARE = 0.7


@dataclass
class MatchResult:
    score: float                       # 0-100 overall match
    coverage: float                    # 0-100 weighted skill coverage
    similarity: float                  # 0-100 TF-IDF cosine similarity (rescaled)
    matched_essential: list[str] = field(default_factory=list)
    missing_essential: list[str] = field(default_factory=list)
    matched_desirable: list[str] = field(default_factory=list)
    missing_desirable: list[str] = field(default_factory=list)
    top_job_terms: list[str] = field(default_factory=list)
    missing_job_terms: list[str] = field(default_factory=list)


# Words that carry no skill signal; terms containing them are not suggested as keywords.
GENERIC = {"good", "strong", "clear", "help", "make", "better", "role", "will", "work", "team", "demo",
           "advert", "fictional", "purposes", "example", "location", "hybrid", "spot", "carry", "support",
           "experience", "skills", "subject", "degree", "knowledge", "familiarity", "exposure", "group"}


def _useful(term: str) -> bool:
    words = term.split()
    return all(len(w) > 2 and w not in GENERIC for w in words)


def tfidf_similarity(cv_text: str, job_text: str, top_n: int = 15) -> tuple[float, list[str], list[str]]:
    job_lower = " ".join(job_text.lower().split())
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True, min_df=1)
    m = vec.fit_transform([cv_text, job_text])
    sim = float(cosine_similarity(m[0], m[1])[0, 0])
    terms = vec.get_feature_names_out()
    job_weights = m[1].toarray()[0]
    cv_vector = m[0].toarray()[0]
    order = job_weights.argsort()[::-1]
    top = [terms[i] for i in order if job_weights[i] > 0 and _useful(terms[i])][:top_n]
    missing = [terms[i] for i in order if job_weights[i] > 0 and cv_vector[i] == 0 and _useful(terms[i])
               and terms[i] in job_lower][:top_n]  # phrase must really appear in the advert
    return sim, top, missing


def match(cv_text: str, job_text: str) -> MatchResult:
    cv_skills = extract_skills(cv_text)
    essential, desirable = split_requirements(job_text)

    got_e, got_d = sorted(essential & cv_skills), sorted(desirable & cv_skills)
    total = ESSENTIAL_WEIGHT * len(essential) + DESIRABLE_WEIGHT * len(desirable)
    earned = ESSENTIAL_WEIGHT * len(got_e) + DESIRABLE_WEIGHT * len(got_d)
    coverage = 100 * earned / total if total else 0.0

    sim, top_terms, missing_terms = tfidf_similarity(cv_text, job_text)
    # Raw cosine similarity between a CV and an advert rarely exceeds ~0.5, so rescale to 0-100.
    similarity = min(100.0, sim * 200)

    return MatchResult(
        score=round(COVERAGE_SHARE * coverage + (1 - COVERAGE_SHARE) * similarity, 1),
        coverage=round(coverage, 1),
        similarity=round(similarity, 1),
        matched_essential=got_e,
        missing_essential=sorted(essential - cv_skills),
        matched_desirable=got_d,
        missing_desirable=sorted(desirable - cv_skills),
        top_job_terms=top_terms,
        missing_job_terms=missing_terms,
    )
