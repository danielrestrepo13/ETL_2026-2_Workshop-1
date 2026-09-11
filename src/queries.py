"""
Task 6: Analytical Queries and KPIs
"""

import pandas as pd
from sqlalchemy import text

from db_config import get_engine

QUERIES = {
    "R1": {
        "question": "How have hiring outcomes changed over time (by month)?",
        "sql": """
            SELECT d.year, d.month, d.month_name,
                   COUNT(*) AS total_applications,
                   SUM(f.is_hired) AS total_hired,
                   ROUND(100.0 * SUM(f.is_hired) / COUNT(*), 2) AS hire_rate_pct
            FROM fact_applications f
            JOIN dim_date d ON f.date_key = d.date_key
            GROUP BY d.year, d.month, d.month_name
            ORDER BY d.year, d.month;
        """,
    },
    "R2": {
        "question": "Which technologies generate the largest number and proportion of hired candidates?",
        "sql": """
            SELECT t.technology_name,
                   COUNT(*) AS total_applications,
                   SUM(f.is_hired) AS total_hired,
                   ROUND(100.0 * SUM(f.is_hired) / COUNT(*), 2) AS hire_rate_pct
            FROM fact_applications f
            JOIN dim_technology t ON f.technology_key = t.technology_key
            GROUP BY t.technology_name
            ORDER BY total_hired DESC, hire_rate_pct DESC;
        """,
    },
    "R3": {
        "question": "How do hiring outcomes vary by seniority and years of professional experience?",
        "sql": """
            SELECT p.seniority, p.yoe_band,
                   COUNT(*) AS total_applications,
                   SUM(f.is_hired) AS total_hired,
                   ROUND(100.0 * SUM(f.is_hired) / COUNT(*), 2) AS hire_rate_pct
            FROM fact_applications f
            JOIN dim_candidate_profile p ON f.profile_key = p.profile_key
            GROUP BY p.seniority, p.yoe_band
            ORDER BY hire_rate_pct DESC;
        """,
    },
    "R4": {
        "question": "Which countries generate the highest recruitment activity and what are their hiring outcomes?",
        "sql": """
            SELECT c.country_name,
                   COUNT(*) AS total_applications,
                   SUM(f.is_hired) AS total_hired,
                   ROUND(100.0 * SUM(f.is_hired) / COUNT(*), 2) AS hire_rate_pct
            FROM fact_applications f
            JOIN dim_country c ON f.country_key = c.country_key
            GROUP BY c.country_name
            HAVING COUNT(*) >= 50
            ORDER BY total_applications DESC
            LIMIT 20;
        """,
    },
    "R5": {
        "question": "Is there a gap between Code Challenge Score and Technical Interview Score, and which one is more often the reason a candidate is NOT hired?",
        "sql": """
            SELECT
                ROUND(AVG(f.score_gap), 2) AS avg_score_gap,
                SUM(CASE WHEN f.code_challenge_score < 7 AND f.technical_interview_score >= 7
                         THEN 1 ELSE 0 END) AS failed_by_code_challenge_only,
                SUM(CASE WHEN f.technical_interview_score < 7 AND f.code_challenge_score >= 7
                         THEN 1 ELSE 0 END) AS failed_by_interview_only,
                SUM(CASE WHEN f.code_challenge_score < 7 AND f.technical_interview_score < 7
                         THEN 1 ELSE 0 END) AS failed_both,
                SUM(f.is_hired) AS passed_both
            FROM fact_applications f;
        """,
    },
}


def run_all_queries() -> dict:
    """Executes R1-R5 against the MySQL DW and prints question, result, and a short interpretation."""
    engine = get_engine()
    results = {}
    try:
        with engine.connect() as conn:
            for req_id, spec in QUERIES.items():
                df = pd.read_sql_query(text(spec["sql"]), conn)
                results[req_id] = df

                print(f"\n{'=' * 70}")
                print(f"{req_id} - {spec['question']}")
                print("=" * 70)
                print(df.to_string(index=False))
                print(f"\nInterpretation: {interpret(req_id, df)}")
    finally:
        engine.dispose()
    return results


def interpret(req_id: str, df: pd.DataFrame) -> str:
    """Short, data-driven interpretation for each requirement's result."""
    if req_id == "R1":
        peak = df.loc[df["hire_rate_pct"].idxmax()]
        return (f"Hire rate is fairly stable month to month, with the best month at "
                f"{peak['hire_rate_pct']}% ({peak['month_name']} {int(peak['year'])}).")
    if req_id == "R2":
        top = df.iloc[0]
        return (f"'{top['technology_name']}' produced the most hires overall "
                f"({int(top['total_hired'])}), at a {top['hire_rate_pct']}% hire rate.")
    if req_id == "R3":
        top = df.iloc[0]
        return (f"The best-converting profile is {top['seniority']} / {top['yoe_band']} "
                f"at a {top['hire_rate_pct']}% hire rate.")
    if req_id == "R4":
        top = df.iloc[0]
        return (f"'{top['country_name']}' has the highest application volume "
                f"({int(top['total_applications'])}) at a {top['hire_rate_pct']}% hire rate.")
    if req_id == "R5":
        row = df.iloc[0]
        code_only = int(row["failed_by_code_challenge_only"])
        interview_only = int(row["failed_by_interview_only"])
        bottleneck = "The Technical Interview" if interview_only > code_only else "The Code Challenge"
        return (f"Average score gap is {row['avg_score_gap']} points (interview - code challenge). "
                f"{bottleneck} is the more common single point of failure "
                f"({interview_only} vs {code_only} candidates who passed only the other test).")
    return ""


if __name__ == "__main__":
    run_all_queries()