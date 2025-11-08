-- ============================================================
-- Users Table - Authentication & Authorization
-- Supports multiple user roles: candidate, recruiter, admin
-- ============================================================

USE DATABASE TEAM_SERO;
USE SCHEMA PUBLIC;

CREATE OR REPLACE TABLE users (
    id INT AUTOINCREMENT PRIMARY KEY,
    email STRING UNIQUE NOT NULL,
    password STRING NOT NULL,  -- Hashed password
    name STRING NOT NULL,
    role STRING DEFAULT 'candidate',  -- 'candidate', 'recruiter', 'admin'
    company_name STRING,  -- For recruiters/employers
    phone STRING,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP_LTZ
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Comments
COMMENT ON TABLE users IS 'User accounts with role-based access control';
COMMENT ON COLUMN users.role IS 'User role: candidate, recruiter, or admin';

-- ============================================================
-- Sample Data (for testing)
-- ============================================================

-- Admin user (password: admin123)
INSERT INTO users (email, password, name, role)
VALUES (
    'admin@serohire.tech',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eSfpK1VVVgXe',  -- hashed: admin123
    'Admin User',
    'admin'
);

-- Recruiter user (password: recruiter123)
INSERT INTO users (email, password, name, role, company_name)
VALUES (
    'recruiter@example.com',
    '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',  -- hashed: recruiter123
    'Jane Recruiter',
    'recruiter',
    'TechCorp Inc'
);

-- ============================================================
-- Queries for verification
-- ============================================================

-- Check all users
SELECT id, email, name, role, company_name, is_active, created_at FROM users;

-- Check role distribution
SELECT role, COUNT(*) as count FROM users GROUP BY role;

-- ============================================================
-- ✅ Done! Run this in Snowflake to create the users table
-- ============================================================

