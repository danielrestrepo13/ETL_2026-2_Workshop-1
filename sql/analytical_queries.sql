
-- R1 - Hiring Trends
-- Business question: how have hiring outcomes changed over time?

SELECT
    d.year,
    d.month,
    d.month_name,
    COUNT(*)                                            AS total_applications,
    SUM(f.is_hired)                                      AS total_hired,
    ROUND(100.0 * SUM(f.is_hired) / COUNT(*), 2)         AS hire_rate_pct
FROM fact_applications f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;



-- R2 - Technology Analysis
-- Business question: which technologies generate the largest number and proportion of hired candidates?

SELECT
    t.technology_name,
    COUNT(*)                                            AS total_applications,
    SUM(f.is_hired)                                      AS total_hired,
    ROUND(100.0 * SUM(f.is_hired) / COUNT(*), 2)         AS hire_rate_pct
FROM fact_applications f
JOIN dim_technology t ON f.technology_key = t.technology_key
GROUP BY t.technology_name
ORDER BY total_hired DESC, hire_rate_pct DESC;


-- R3 - Candidate Profile Analysis
-- Business question: how do hiring outcomes vary by seniority and years of professional experience?

SELECT
    p.seniority,
    p.yoe_band,
    COUNT(*)                                            AS total_applications,
    SUM(f.is_hired)                                      AS total_hired,
    ROUND(100.0 * SUM(f.is_hired) / COUNT(*), 2)         AS hire_rate_pct
FROM fact_applications f
JOIN dim_candidate_profile p ON f.profile_key = p.profile_key
GROUP BY p.seniority, p.yoe_band
ORDER BY hire_rate_pct DESC;



-- R4 - Geographic Recruitment Analysis
-- Business question: which countries generate the highest recruitment activity and what are their hiring outcomes?

SELECT
    c.country_name,
    COUNT(*)                                            AS total_applications,
    SUM(f.is_hired)                                      AS total_hired,
    ROUND(100.0 * SUM(f.is_hired) / COUNT(*), 2)         AS hire_rate_pct
FROM fact_applications f
JOIN dim_country c ON f.country_key = c.country_key
GROUP BY c.country_name
HAVING COUNT(*) >= 50 
ORDER BY total_applications DESC
LIMIT 20;


-- R5 - Score Efficiency / Assessment Bottleneck Analysis
-- Business question: is there a systematic gap between the Code Challenge Score and the Technical Interview Score, and which assessment is more often the reason a candidate is NOT hired?

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
