"""Optional AI step: ask Claude to suggest honest, tailored CV wording.

Runs only when the ANTHROPIC_API_KEY environment variable is set. The prompt gives the model
the CV, the advert and the gap analysis, and tells it never to invent experience: it may only
reword or re-order what the CV already shows, and must flag gaps as things to learn instead.
"""
import os

from .score import MatchResult

MODEL = os.environ.get("CVMATCH_MODEL", "claude-sonnet-5-5")

SYSTEM = (
    "You are an experienced UK tech recruiter helping a candidate tailor their CV to one job. "
    "Rules: never invent jobs, employers, dates, numbers, tools or achievements. Only reword, "
    "re-order or emphasise what the CV already contains. Use the advert's own keywords where the "
    "CV genuinely supports them. Write in natural, first-person-free CV style with UK spelling. "
    "If an essential skill is missing, say so plainly and suggest a quick way to learn or "
    "evidence it; do not hide it."
)


def build_prompt(cv_text: str, job_text: str, result: MatchResult) -> str:
    return f"""<job_advert>
{job_text}
</job_advert>

<cv>
{cv_text}
</cv>

<gap_analysis>
Match score: {result.score}/100
Essential skills shown: {', '.join(result.matched_essential) or 'none'}
Essential skills missing: {', '.join(result.missing_essential) or 'none'}
Desirable skills missing: {', '.join(result.missing_desirable) or 'none'}
Advert keywords not in CV: {', '.join(result.missing_job_terms) or 'none'}
</gap_analysis>

Please return, in Markdown:
1. A 3-sentence profile tailored to this advert.
2. Up to 5 rewritten CV bullets (show "Before" and "After" for each), using the advert's keywords only where the CV supports them.
3. The gaps that remain, each with one practical way to close it in under a week."""


def tailor(cv_text: str, job_text: str, result: MatchResult) -> str | None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    import anthropic

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM,
        messages=[{"role": "user", "content": build_prompt(cv_text, job_text, result)}],
    )
    return "".join(block.text for block in msg.content if block.type == "text")
