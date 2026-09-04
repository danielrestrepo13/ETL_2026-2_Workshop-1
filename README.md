# Taller 1: ETL - De Requisitos de Negocio a DW Dimensional

# Workshop 1: From Business Requirements to a Dimensional Data Warehouse

## Project Objective
The objective of this project is to simulate a real-world Data Engineering technical challenge by transforming raw operational candidate recruitment data into an analytical Dimensional Data Warehouse that directly supports specific business requirements and analytical decisions.

## Business Context
A technology recruitment company receives thousands of applications from candidates with diverse professional backgrounds, experience levels, countries, seniorities, and technology profiles. Candidate performance is evaluated through two technical assessments: a **Code Challenge Score** and a **Technical Interview Score**[cite: 3]. This system aims to provide decision-makers with insights into hiring patterns and recruitment performance[cite: 3].

## Five Business Requirements
* **R1 — Hiring Trends:** Monitor hiring trends over time to identify changes in recruitment outcomes across different periods[cite: 3].
* **R2 — Technology Analysis:** Compare hiring results across technologies to identify which technical profiles generate the largest number and proportion of hired candidates[cite: 3].
* **R3 — Candidate Profile Analysis:** Analyze hiring outcomes according to candidate seniority and years of professional experience (YOE)[cite: 3].
* **R4 — Country Analysis:** Evaluate recruitment activity and hiring effectiveness by candidate country of origin to optimize sourcing investments[cite: 3].
* **R5 — Technical Evaluation:** Analyze the efficiency and consistency of technical evaluations by comparing Code Challenge Scores against Technical Interview Scores to identify primary bottlenecks[cite: 3].

## Requirements Traceability
| Requirement | Business Question | Data Required | Expected Analytical Output |
| :--- | :--- | :--- | :--- |
| **R1** | How have hiring results changed over time[cite: 3]? | Application Date, Scores[cite: 3] | Monthly time series of applications, hires, and hire rate (%)[cite: 3] |
| **R2** | Which technologies generate the highest number and proportion of hired candidates[cite: 3]? | Technology, Scores[cite: 3] | Ranking of technologies by number of hires and hire rate (%)[cite: 3] |
| **R3** | How do hiring results change by seniority and experience[cite: 3]? | Seniority, YOE, Scores[cite: 3] | Hire rate by seniority level and experience range[cite: 3] |
| **R4** | Which countries generate the highest volume of applications and hire rates[cite: 3]? | Country, Scores[cite: 3] | Ranking of countries by application volume vs hire rate[cite: 3] |
| **R5** | Is there a gap between test scores and which is the main bottleneck[cite: 3]? | Code Challenge Score, Technical Interview Score[cite: 3] | Average score gap + breakdown of candidates failing by test[cite: 3] |

## Dataset Description
The source dataset contains approximately **50,000 candidate applications**[cite: 3]. Attributes include First Name, Last Name, Email, Country, Application Date, YOE, Seniority, Technology, Code Challenge Score, and Technical Interview Score[cite: 3].

## Main Profiling Findings
* Dataset contains 50,000 rows and 10 columns with no critical missing values in core analytical fields.
* Application dates span from 2018 to 2022.
* Scores range continuously from 0 to 10 for both technical evaluations.

## Business Process
* **Business Process:** Technical candidate recruitment and selection process, where each application is evaluated through two technical tests resulting in a binary hiring decision[cite: 3].

## Grain Definition
* **Grain:** One row in `FactApplications` represents a single candidate application to the selection process, evaluated with a specific Code Challenge Score and Technical Interview Score, resulting in a single hiring outcome (hired / not hired)[cite: 3].

## Star Schema Diagram
*(Refer to `diagrams/star_schema.png` in the repository)*[cite: 3]

## Explanation of Dimensions and Facts
* **`DimDate`:** Analyzes hiring trends over time (`date_key`, `full_date`, `year`, `quarter`, `month`, `month_name`, `day`)[cite: 3].
* **`DimTechnology`:** Compares hiring outcomes by technical profile (`technology_key`, `technology_name`)[cite: 3].
* **`DimCandidateProfile`:** Groups candidates by seniority and experience bands (`profile_key`, `seniority`, `yoe_band`, `yoe_min`, `yoe_max`)[cite: 3].
* **`DimCountry`:** Compares recruitment volume and effectiveness by country (`country_key`, `country_name`)[cite: 3].
* **`FactApplications`:** Stores foreign keys to dimensions along with core measures (`code_challenge_score`, `technical_interview_score`, `score_gap`, `is_hired`)[cite: 3].

## ETL Architecture & Main Transformation Decisions
1. **Extract:** Read raw data from `data/raw/candidates.csv` into a Pandas DataFrame without business transformations[cite: 3].
2. **Transform (Data Preparation & Business Rule):** 
   * Clean formats and handle data types.
   * Apply the core hiring rule: A candidate is **HIRED** when `Code Challenge Score >= 7` AND `Technical Interview Score >= 7`; otherwise, **NOT HIRED**[cite: 3].
3. **Dimensional Transformation:** Map prepared records to dimension surrogate keys.
4. **Load:** Create schema tables in MySQL and load dimensions followed by the fact table while preserving referential integrity[cite: 3].

## Technologies Used
* Python, Pandas[cite: 3]
* MySQL & SQLAlchemy[cite: 3]
* Git & GitHub[cite: 3]

## Instructions to Run the Project
1. Clone the repository and navigate to the project root.
2. Set up and activate a Python virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate   # On Windows

3. Install dependencies
```bash
pip install -r requirements.txt


4. Configure your .env file based on .env.example with your local MySQL credentials.

5. Run the complete ETL pipeline and generate analytical outputs:
```bash
python src/main.py
```

## Analytical Queries and KPIs

All analytical outputs are generated directly from queries executed against the MySQL Data Warehouse (`recruitment_dw`), covering monthly time series, technology rankings, profile conversions, country metrics, and score gap evaluations.

## Main Business Findings

* **R1 — Hiring Trends:** Hire rates remain stable month-to-month, peaking at **16.96% in July 2022**.

* **R2 — Technology Analysis:** **Game Development** generated the highest volume of hires (**519**) with a **13.59% success rate**.

* **R3 — Candidate Profile Analysis:** **Interns with Entry-level experience (0–2 YOE)** achieved the highest conversion rate (**17.11%**).

* **R4 — Country Analysis:** **Malawi** presented the highest application volume (**242**) with a **9.50% hire rate**.

* **R5 — Technical Evaluation:** The **Code Challenge** is a slightly more common single failure point (**11,571 failures**) compared to the **Technical Interview** (**11,534 failures**).

## Final Requirements Validation

All five business requirements (**R1–R5**) have been fully implemented, verified through referential integrity checks, and successfully answered using the dimensional Data Warehouse schema.
