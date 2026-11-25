"""Skill taxonomy and extraction.

Each canonical skill maps to the different ways people write it in CVs and job adverts
("Power BI", "PowerBI", "power-bi" -> "Power BI"). Matching is case-insensitive and uses
word boundaries, so "R" only matches the standalone letter, not every word containing r.
"""
import re

SKILLS: dict[str, list[str]] = {
    # Programming & query languages
    "Python": ["python"],
    "SQL": ["sql", "t-sql", "tsql", "pl/sql", "postgresql", "mysql", "sql server"],
    "R": [r"\br\b(?!&)", "rstudio"],
    "JavaScript": ["javascript", "js", "typescript"],
    "VBA": ["vba", "excel macros"],
    "HTML/CSS": ["html", "css"],
    # Data & analysis
    "pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Excel": ["excel", "spreadsheets", "pivot tables", "vlookup", "xlookup"],
    "Statistics": ["statistics", "statistical analysis", "hypothesis testing", "a/b testing", "regression analysis"],
    "Data cleaning": ["data cleaning", "data cleansing", "data wrangling", "data preparation", "data quality",
                      "cleaned", "clean data", "cleaning"],
    "EDA": ["exploratory data analysis", "eda", "explored", "data exploration"],
    "ETL": ["etl", "elt", "data pipelines", "data pipeline"],
    "Data modelling": ["data modelling", "data modeling", "star schema", "dimensional model"],
    "Forecasting": ["forecasting", "time series", "time-series"],
    "Segmentation": ["segmentation", "rfm", "clustering"],
    "KPI reporting": ["kpi", "kpis", "reporting", "reports", "metrics"],
    # BI & visualisation
    "Power BI": ["power bi", "powerbi", "power-bi", "dax", "power query"],
    "Tableau": ["tableau"],
    "Looker": ["looker", "looker studio", "data studio"],
    "Data visualisation": ["data visualisation", "data visualization", "dashboards", "dashboard", "matplotlib",
                           "seaborn", "plotly"],
    # Machine learning & AI
    "Machine learning": ["machine learning", "ml models", "predictive modelling", "predictive modeling"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "Deep learning": ["deep learning", "neural networks", "pytorch", "tensorflow", "keras"],
    "NLP": ["nlp", "natural language processing", "text analytics", "sentiment analysis"],
    "Computer vision": ["computer vision", "image classification", "opencv"],
    "LLMs / Generative AI": ["llm", "llms", "large language models", "generative ai", "genai", "gpt",
                             "chatgpt", "claude", "gemini", "prompt engineering", "rag"],
    "Model evaluation": ["model evaluation", "cross-validation", "cross validation", "roc", "precision", "recall"],
    "MLOps": ["mlops", "model deployment", "mlflow"],
    # Cloud & engineering
    "Cloud": ["aws", "azure", "gcp", "google cloud", "cloud platforms"],
    "BigQuery": ["bigquery"],
    "Snowflake": ["snowflake"],
    "Databricks": ["databricks", "spark", "pyspark"],
    "Git": ["git", "github", "version control"],
    "Docker": ["docker", "containers"],
    "APIs": ["api", "apis", "rest"],
    # Analytics platforms
    "Google Analytics": ["google analytics", "ga4"],
    "Tag management": ["google tag manager", "gtm", "tagging", "adobe launch"],
    # Ways of working
    "Stakeholder management": ["stakeholder", "stakeholders", "business partners", "clients"],
    "Communication": ["communication", "communicate", "presenting", "presentation", "storytelling"],
    "Agile": ["agile", "scrum", "sprint", "jira"],
    "Problem solving": ["problem-solving", "problem solving", "analytical skills", "analytical"],
    "Documentation": ["documentation", "document processes"],
}

_PATTERNS = {
    skill: [re.compile(alias if alias.startswith(r"\b") else rf"(?<![\w/]){re.escape(alias)}(?![\w])",
                       re.IGNORECASE)
            for alias in aliases]
    for skill, aliases in SKILLS.items()
}


def extract_skills(text: str) -> set[str]:
    """Return the canonical skills mentioned anywhere in the text."""
    return {skill for skill, pats in _PATTERNS.items() if any(p.search(text) for p in pats)}


_DESIRABLE = re.compile(
    r"^\s*#*\s*\**\s*(desirable|nice[- ]to[- ]have|bonus|preferred|beneficial|a plus|plus)\b",
    re.IGNORECASE)
_ESSENTIAL = re.compile(
    r"^\s*#*\s*\**\s*(essential|requirements?|required|must[- ]have|what you('ll)? need|you have|"
    r"skills|qualifications|about you|responsibilities|the role)\b",
    re.IGNORECASE)


def split_requirements(job_text: str) -> tuple[set[str], set[str]]:
    """Split a job advert into (essential, desirable) skills using its section headings.

    Lines after a heading such as "Desirable" or "Nice to have" count as desirable until
    the next essential-type heading. Anything not under a desirable heading is treated as
    essential, because recruiters screen on the core list first.
    """
    essential_text, desirable_text, mode = [], [], "essential"
    for line in job_text.splitlines():
        if _DESIRABLE.search(line):
            mode = "desirable"
        elif _ESSENTIAL.search(line):
            mode = "essential"
        (desirable_text if mode == "desirable" else essential_text).append(line)
    essential = extract_skills("\n".join(essential_text))
    desirable = extract_skills("\n".join(desirable_text)) - essential
    return essential, desirable
