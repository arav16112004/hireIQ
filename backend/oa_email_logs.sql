-- ============================================================
-- OA Email Logs Table
-- Tracks all OA invitation emails sent to candidates
-- ============================================================

CREATE OR REPLACE TABLE oa_email_logs (
    id INT AUTOINCREMENT PRIMARY KEY,
    candidate_id INT NOT NULL,
    email STRING NOT NULL,
    oa_link STRING,
    status STRING NOT NULL,  -- 'sent', 'failed', 'bounced'
    sendgrid_message_id STRING,
    error_message STRING,
    sent_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP,
    opened_at TIMESTAMP_LTZ,
    clicked_at TIMESTAMP_LTZ
);

-- Create index for faster candidate lookups
CREATE INDEX IF NOT EXISTS idx_oa_email_logs_candidate 
ON oa_email_logs(candidate_id);

-- Create index for status lookups
CREATE INDEX IF NOT EXISTS idx_oa_email_logs_status 
ON oa_email_logs(status);

-- Sample query to check email logs
-- SELECT * FROM oa_email_logs ORDER BY sent_at DESC LIMIT 10;

-- Query to get all emails for a candidate
-- SELECT * FROM oa_email_logs WHERE candidate_id = 1 ORDER BY sent_at DESC;

-- Query to check delivery rates
-- SELECT 
--     status,
--     COUNT(*) as count,
--     ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
-- FROM oa_email_logs
-- GROUP BY status;

