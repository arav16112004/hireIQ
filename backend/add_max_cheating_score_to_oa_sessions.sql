-- Add max_cheating_score column to oa_sessions table
-- This column stores the highest integrity/cheating score recorded during an OA session
-- Higher scores indicate higher risk of cheating

USE DATABASE TEAM_SERO;
USE SCHEMA PUBLIC;

-- Add the column (will fail if column already exists - that's okay, just means it's already added)
ALTER TABLE oa_sessions 
ADD COLUMN max_cheating_score FLOAT;

-- Add a comment to the column
COMMENT ON COLUMN oa_sessions.max_cheating_score IS 'Highest integrity/cheating score recorded during the OA session. Higher scores indicate higher risk of cheating.';

