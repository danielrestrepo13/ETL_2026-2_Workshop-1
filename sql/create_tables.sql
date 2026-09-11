DROP TABLE IF EXISTS fact_applications;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_technology;
DROP TABLE IF EXISTS dim_candidate_profile;
DROP TABLE IF EXISTS dim_country;

-- DIMENSION: dim_date
-- Purpose: enables time-based / trend analysis (R1).

CREATE TABLE dim_date (
    date_key    INT          NOT NULL,
    full_date   DATE         NOT NULL,
    day         SMALLINT     NOT NULL,
    month       SMALLINT     NOT NULL,
    month_name  VARCHAR(20)  NOT NULL,
    quarter     SMALLINT     NOT NULL,
    year        SMALLINT     NOT NULL,
    PRIMARY KEY (date_key)
);

-- DIMENSION: dim_technology
-- Purpose: compares hiring outcomes across technical profiles (R2).

CREATE TABLE dim_technology (
    technology_key   INT          NOT NULL AUTO_INCREMENT,
    technology_name  VARCHAR(100) NOT NULL,
    PRIMARY KEY (technology_key),
    UNIQUE KEY uq_technology_name (technology_name)
);

-- DIMENSION: dim_candidate_profile
-- Purpose: groups candidates by seniority + years-of-experience band to compare hiring outcomes across profiles (R3).

CREATE TABLE dim_candidate_profile (
    profile_key  INT          NOT NULL AUTO_INCREMENT,
    seniority    VARCHAR(50)  NOT NULL,
    yoe_band     VARCHAR(30)  NOT NULL,
    yoe_min      SMALLINT     NOT NULL,
    yoe_max      SMALLINT     NOT NULL,
    PRIMARY KEY (profile_key),
    UNIQUE KEY uq_seniority_yoe_band (seniority, yoe_band)
);

-- DIMENSION: dim_country
-- Purpose: compares recruitment volume/effectiveness by country (R4).

CREATE TABLE dim_country (
    country_key   INT          NOT NULL AUTO_INCREMENT,
    country_name  VARCHAR(100) NOT NULL,
    PRIMARY KEY (country_key),
    UNIQUE KEY uq_country_name (country_name)
);

-- FACT: fact_applications
-- Grain: one row = one candidate application, evaluated with one Code Challenge Score and one Technical Interview Score, resulting in one hiring outcome.

CREATE TABLE fact_applications (
    application_id              INT      NOT NULL,
    date_key                    INT      NOT NULL,
    technology_key              INT      NOT NULL,
    profile_key                 INT      NOT NULL,
    country_key                 INT      NOT NULL,
    code_challenge_score        TINYINT  NOT NULL,
    technical_interview_score   TINYINT  NOT NULL,
    score_gap                   SMALLINT NOT NULL,
    is_hired                    TINYINT  NOT NULL,
    PRIMARY KEY (application_id),
    CONSTRAINT fk_fact_date
        FOREIGN KEY (date_key) REFERENCES dim_date (date_key),
    CONSTRAINT fk_fact_technology
        FOREIGN KEY (technology_key) REFERENCES dim_technology (technology_key),
    CONSTRAINT fk_fact_profile
        FOREIGN KEY (profile_key) REFERENCES dim_candidate_profile (profile_key),
    CONSTRAINT fk_fact_country
        FOREIGN KEY (country_key) REFERENCES dim_country (country_key),
    CONSTRAINT chk_code_challenge_score
        CHECK (code_challenge_score BETWEEN 0 AND 10),
    CONSTRAINT chk_technical_interview_score
        CHECK (technical_interview_score BETWEEN 0 AND 10),
    CONSTRAINT chk_is_hired
        CHECK (is_hired IN (0, 1)),
    KEY idx_fact_date       (date_key),
    KEY idx_fact_technology (technology_key),
    KEY idx_fact_profile    (profile_key),
    KEY idx_fact_country    (country_key)
);