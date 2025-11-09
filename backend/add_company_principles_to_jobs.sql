-- Add company_principles column to jobs table
-- This column stores company principles/values that the AI will emphasize during AI avatar video interviews

USE DATABASE TEAM_SERO;
USE SCHEMA PUBLIC;

-- Add the column (will fail if column already exists - that's okay, just means it's already added)
ALTER TABLE jobs 
ADD COLUMN company_principles STRING;

-- Add a comment to the column
COMMENT ON COLUMN jobs.company_principles IS 'Company principles, values, or culture that the AI avatar should emphasize during video interviews. Used to assess candidate fit and ask relevant questions.';

