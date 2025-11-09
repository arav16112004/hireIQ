-- Add company_name column to JOBS table if it doesn't exist
-- This allows recruiters to associate jobs with their company

ALTER TABLE TEAM_SERO.PUBLIC.JOBS 
ADD COLUMN IF NOT EXISTS company_name VARCHAR(16777216);

-- Add comment to column
COMMENT ON COLUMN TEAM_SERO.PUBLIC.JOBS.company_name IS 'Company name associated with this job (for recruiters)';

-- Verify the column was added
SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    IS_NULLABLE,
    COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'PUBLIC' 
  AND TABLE_NAME = 'JOBS' 
  AND COLUMN_NAME = 'COMPANY_NAME';

