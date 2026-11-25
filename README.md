# AI CV ↔ Job Matcher

A Python tool I built for my own job search. Give it a CV and a job advert, and it:

1. **Scores the match (0–100)**: how many of the advert's skills the CV shows, and how closely the CV uses the recruiter's own vocabulary.
2. **Lists the gaps**: essential and desirable skills you're missing, plus advert keywords that never appear in your CV.
3. **(Optional) asks Claude, an LLM, for tailoring suggestions**: a tailored profile, before/after bullet rewrites and a plan to close each gap. Claude is told **never to invent experience**; it can only reword what the CV already proves.

**Tech:** Python, scikit-learn (TF-IDF, cosine similarity), regular expressions, Anthropic Claude API, pytest

---

## Example

```bash
python -m cvmatch examples/sample_cv.txt examples/job_junior_data_analyst.txt --no-ai
```

```
Match score: 57.9/100 — Reasonable match — tailor the CV first
(skill coverage 69.7/100 · keyword similarity 30.4/100)

Essential skills missing: Forecasting, Problem solving, Stakeholder management
Desirable skills missing: Cloud, Looker, Statistics, Tableau
Recruiter keywords not yet in your CV: dashboards, sales, warehouse, clean data, write sql, weekly kpi ...
```

Full output: [`examples/sample_report.md`](examples/sample_report.md). The example CV and advert are fictional.

## How the score works

**Skill coverage (70% of the score)**
- A taxonomy of about 45 data and AI skills, each with its common spellings, so *"PowerBI"*, *"Power BI"* and *"DAX"* all count as **Power BI**, and *"T-SQL"* and *"PostgreSQL"* count as **SQL**.
- Word-boundary regex, so the language **R** is only found as a standalone letter, not inside every word that contains an r. A unit test covers this.
- The advert is split into **essential** and **desirable** sections using its headings ("Essential", "Desirable", "Nice to have" …). Essential skills are weighted 2×, because recruiters screen on those first.

**Keyword similarity (30% of the score)**
- **TF-IDF** turns the CV and the advert into vectors of word importance (single words and two-word phrases, with stop words removed). **Cosine similarity** measures how closely they point in the same direction.
- This mimics how many applicant tracking systems (ATS) rank CVs, which is why using the advert's own wording matters.
- Suggested missing keywords are filtered so only phrases that literally appear in the advert are shown, not noise.

**AI step (optional)**
- Runs only if `ANTHROPIC_API_KEY` is set. The CV, the advert and the gap analysis go into a structured prompt, and a system prompt sets the rules: UK spelling, use advert keywords only where the CV supports them, and flag real gaps honestly instead of hiding them.

## Run it

```bash
pip install -r requirements.txt
python -m pytest                      # 6 tests
python -m cvmatch my_cv.txt job.txt --out report.md
export ANTHROPIC_API_KEY=...          # optional: adds Claude's tailoring suggestions
```

## Project structure

```
cvmatch/skills.py    skill taxonomy, alias matching, essential/desirable split
cvmatch/score.py     coverage + TF-IDF similarity -> MatchResult
cvmatch/llm.py       optional Claude prompt (honesty rules in the system prompt)
cvmatch/__main__.py  command-line interface and Markdown report
tests/               pytest unit tests
examples/            fictional CV, advert and generated report
```

## What I'd add next

- Sentence embeddings instead of TF-IDF, so "built dashboards" also matches "created reports".
- PDF and DOCX input.
- A small Streamlit web page so non-technical users can paste a CV and an advert.
