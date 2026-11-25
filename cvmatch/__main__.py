"""Command line: python -m cvmatch CV_FILE JOB_FILE [--out report.md] [--no-ai]"""
import argparse
from pathlib import Path

from .llm import tailor
from .score import match


def render(result, ai_text: str | None) -> str:
    def bullets(items):
        return "\n".join(f"- {i}" for i in items) if items else "- none"

    verdict = ("Strong match — apply" if result.score >= 65 else
               "Reasonable match — tailor the CV first" if result.score >= 45 else
               "Weak match — only apply if you can close the gaps")
    out = f"""# CV vs job match report

**Match score: {result.score}/100** — {verdict}
(skill coverage {result.coverage}/100 · keyword similarity {result.similarity}/100)

## Essential skills
**You show:**
{bullets(result.matched_essential)}

**Missing:**
{bullets(result.missing_essential)}

## Desirable skills
**You show:** {', '.join(result.matched_desirable) or 'none'}
**Missing:** {', '.join(result.missing_desirable) or 'none'}

## Recruiter keywords not yet in your CV
{', '.join(result.missing_job_terms) or 'none'}
"""
    if ai_text:
        out += "\n## AI tailoring suggestions (Claude)\n\n" + ai_text + "\n"
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Score a CV against a job advert and show the gaps.")
    p.add_argument("cv")
    p.add_argument("job")
    p.add_argument("--out", help="write the report to this Markdown file")
    p.add_argument("--no-ai", action="store_true", help="skip the optional Claude step")
    a = p.parse_args()

    cv_text, job_text = Path(a.cv).read_text(), Path(a.job).read_text()
    result = match(cv_text, job_text)
    ai_text = None if a.no_ai else tailor(cv_text, job_text, result)
    report = render(result, ai_text)
    if a.out:
        Path(a.out).write_text(report)
        print(f"report written to {a.out}")
    print(report)


if __name__ == "__main__":
    main()
