-- ============================================================
-- Candidate Profiles Table
-- Stores persistent candidate information (resume, skills, etc.)
-- Separate from job applications
-- ============================================================

USE DATABASE TEAM_SERO;
USE SCHEMA PUBLIC;

CREATE OR REPLACE TABLE candidate_profiles (
    id INT AUTOINCREMENT PRIMARY KEY,
    user_id INT NOT NULL,  -- Links to users table
    resume_url STRING,
    phone STRING,
    location STRING,
    linkedin_url STRING,
    portfolio_url STRING,
    skills STRING,  -- Comma-separated or JSON
    experience_years INT,
    education STRING,
    bio STRING,
    is_profile_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure one profile per user
    CONSTRAINT unique_user_profile UNIQUE (user_id)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_candidate_profiles_user ON candidate_profiles(user_id);

COMMENT ON TABLE candidate_profiles IS 'Persistent candidate profiles - resumes and info stored here';

-- ============================================================
-- ✅ Now candidates have a permanent profile!
-- ============================================================

