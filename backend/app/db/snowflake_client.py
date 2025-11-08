import snowflake.connector
from typing import Optional, Dict, List, Any
from contextlib import contextmanager

from app.core.config import settings


@contextmanager
def get_connection():
    """Context manager for Snowflake connections"""
    conn = snowflake.connector.connect(
        user=settings.snowflake_user,
        password=settings.snowflake_password,
        account=settings.snowflake_account,
        warehouse=settings.snowflake_warehouse,
        database=settings.snowflake_database,
        schema=settings.snowflake_schema
    )
    try:
        yield conn
    finally:
        conn.close()


def _execute_query(query: str, params: Optional[tuple] = None) -> List[tuple]:
    """Execute a query and return results"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
            return results
        finally:
            cursor.close()


def _execute_update(query: str, params: Optional[tuple] = None) -> int:
    """Execute an UPDATE/INSERT/DELETE and return affected rows"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount
        finally:
            cursor.close()


def _row_to_dict(cursor_description: tuple, row: tuple) -> Dict[str, Any]:
    """Convert a row tuple to a dictionary"""
    if not cursor_description:
        return {}
    columns = [desc[0] for desc in cursor_description]
    return dict(zip(columns, row))


# ============================================================
# JOBS TABLE FUNCTIONS
# ============================================================

def get_job(job_id: int) -> Optional[Dict[str, Any]]:
    """Get a job by ID"""
    query = "SELECT * FROM jobs WHERE id = %s"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (job_id,))
        results = cursor.fetchall()
        if results:
            desc = cursor.description
            return _row_to_dict(desc, results[0])
        cursor.close()
    return None


def create_job(title: str, description: str, department: str) -> int:
    """Create a new job and return its ID"""
    query = "INSERT INTO jobs (title, description, department) VALUES (%s, %s, %s)"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (title, description, department))
        # Get the last inserted ID using Snowflake's IDENT_CURRENT equivalent
        cursor.execute("SELECT MAX(id) FROM jobs")
        job_id = cursor.fetchone()[0]
        cursor.close()
        return job_id


def get_all_jobs() -> List[Dict[str, Any]]:
    """Get all jobs"""
    query = "SELECT * FROM jobs ORDER BY created_at DESC"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        if not results:
            cursor.close()
            return []
        desc = cursor.description
        cursor.close()
        return [_row_to_dict(desc, row) for row in results]


# ============================================================
# CANDIDATES TABLE FUNCTIONS
# ============================================================

def get_candidate(candidate_id: int) -> Optional[Dict[str, Any]]:
    """Get a candidate by ID"""
    query = "SELECT * FROM candidates WHERE id = %s"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (candidate_id,))
        results = cursor.fetchall()
        if results:
            desc = cursor.description
            cursor.close()
            return _row_to_dict(desc, results[0])
        cursor.close()
    return None


def get_candidate_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get a candidate by email"""
    query = "SELECT * FROM candidates WHERE email = %s"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (email,))
        results = cursor.fetchall()
        if results:
            desc = cursor.description
            cursor.close()
            return _row_to_dict(desc, results[0])
        cursor.close()
    return None


def create_candidate(name: str, email: str, resume_url: str, job_id: int) -> int:
    """Create a new candidate and return its ID"""
    query = """
        INSERT INTO candidates (name, email, resume_url, job_id)
        VALUES (%s, %s, %s, %s)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (name, email, resume_url, job_id))
        cursor.execute("SELECT MAX(id) FROM candidates")
        candidate_id = cursor.fetchone()[0]
        cursor.close()
        return candidate_id


def save_fit_score(candidate_id: int, fit_score: float, summary: Optional[str] = None) -> bool:
    """Update candidate's fit score and optionally stage"""
    query = "UPDATE candidates SET fit_score = %s WHERE id = %s"
    rows_affected = _execute_update(query, (fit_score, candidate_id))
    return rows_affected > 0


def update_candidate_stage(candidate_id: int, stage: str) -> bool:
    """Update candidate's stage in the pipeline"""
    query = "UPDATE candidates SET stage = %s WHERE id = %s"
    rows_affected = _execute_update(query, (stage, candidate_id))
    return rows_affected > 0


def get_candidates_by_job(job_id: int) -> List[Dict[str, Any]]:
    """Get all candidates for a specific job"""
    query = "SELECT * FROM candidates WHERE job_id = %s ORDER BY created_at DESC"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (job_id,))
        results = cursor.fetchall()
        if not results:
            cursor.close()
            return []
        desc = cursor.description
        cursor.close()
        return [_row_to_dict(desc, row) for row in results]


# ============================================================
# OA_RESULTS TABLE FUNCTIONS
# ============================================================

def create_oa_result(candidate_id: int, status: str = "pending") -> int:
    """Create a new OA result entry"""
    query = "INSERT INTO oa_results (candidate_id, status) VALUES (%s, %s)"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (candidate_id, status))
        cursor.execute("SELECT MAX(id) FROM oa_results")
        oa_id = cursor.fetchone()[0]
        cursor.close()
        return oa_id


def update_oa_result(oa_id: int, score: float, status: str, completed_at: Optional[str] = None) -> bool:
    """Update OA result with score and completion status"""
    query = """
        UPDATE oa_results 
        SET score = %s, status = %s, completed_at = %s
        WHERE id = %s
    """
    rows_affected = _execute_update(query, (score, status, completed_at, oa_id))
    return rows_affected > 0


def get_oa_result(candidate_id: int) -> Optional[Dict[str, Any]]:
    """Get OA result for a candidate"""
    query = "SELECT * FROM oa_results WHERE candidate_id = %s ORDER BY sent_at DESC LIMIT 1"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (candidate_id,))
        results = cursor.fetchall()
        if results:
            desc = cursor.description
            cursor.close()
            return _row_to_dict(desc, results[0])
        cursor.close()
    return None


# ============================================================
# INTERVIEWS TABLE FUNCTIONS
# ============================================================

def create_interview(
    candidate_id: int,
    transcript: str,
    engagement_score: float,
    ai_score: float,
    notes: Optional[str] = None
) -> int:
    """Create a new interview record"""
    query = """
        INSERT INTO interviews (candidate_id, transcript, engagement_score, ai_score, notes)
        VALUES (%s, %s, %s, %s, %s)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (candidate_id, transcript, engagement_score, ai_score, notes))
        cursor.execute("SELECT MAX(id) FROM interviews")
        interview_id = cursor.fetchone()[0]
        cursor.close()
        return interview_id


def get_interview(interview_id: int) -> Optional[Dict[str, Any]]:
    """Get an interview by ID"""
    query = "SELECT * FROM interviews WHERE id = %s"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (interview_id,))
        results = cursor.fetchall()
        if results:
            desc = cursor.description
            cursor.close()
            return _row_to_dict(desc, results[0])
        cursor.close()
    return None


def get_interviews_by_candidate(candidate_id: int) -> List[Dict[str, Any]]:
    """Get all interviews for a candidate"""
    query = "SELECT * FROM interviews WHERE candidate_id = %s ORDER BY created_at DESC"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (candidate_id,))
        results = cursor.fetchall()
        if not results:
            cursor.close()
            return []
        desc = cursor.description
        cursor.close()
        return [_row_to_dict(desc, row) for row in results]


# ============================================================
# FINAL_INTERVIEWS TABLE FUNCTIONS
# ============================================================

def create_final_interview(
    candidate_id: int,
    recruiter_name: str,
    recruiter_email: str,
    scheduled_date: str,
    decision: str = "pending"
) -> int:
    """Create a final interview record"""
    query = """
        INSERT INTO final_interviews (candidate_id, recruiter_name, recruiter_email, scheduled_date, decision)
        VALUES (%s, %s, %s, %s, %s)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (candidate_id, recruiter_name, recruiter_email, scheduled_date, decision))
        cursor.execute("SELECT MAX(id) FROM final_interviews")
        interview_id = cursor.fetchone()[0]
        cursor.close()
        return interview_id


def update_final_interview(interview_id: int, decision: str, feedback: Optional[str] = None) -> bool:
    """Update final interview decision and feedback"""
    query = "UPDATE final_interviews SET decision = %s, feedback = %s WHERE id = %s"
    rows_affected = _execute_update(query, (decision, feedback, interview_id))
    return rows_affected > 0


def get_final_interview(candidate_id: int) -> Optional[Dict[str, Any]]:
    """Get final interview for a candidate"""
    query = "SELECT * FROM final_interviews WHERE candidate_id = %s ORDER BY created_at DESC LIMIT 1"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (candidate_id,))
        results = cursor.fetchall()
        if results:
            desc = cursor.description
            cursor.close()
            return _row_to_dict(desc, results[0])
        cursor.close()
    return None


# ============================================================
# OA Email Logs Functions
# ============================================================

def log_oa_email_sent(
    candidate_id: int,
    email: str,
    oa_link: str,
    status: str = 'sent',
    sendgrid_message_id: str = None,
    error_message: str = None
) -> Optional[int]:
    """
    Log an OA email sent to a candidate
    
    Args:
        candidate_id: ID of the candidate
        email: Email address
        oa_link: OA invitation link
        status: 'sent', 'failed', 'bounced'
        sendgrid_message_id: SendGrid message ID
        error_message: Error message if failed
    
    Returns:
        Log ID if successful, None otherwise
    """
    query = """
        INSERT INTO oa_email_logs 
        (candidate_id, email, oa_link, status, sendgrid_message_id, error_message)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    return _execute_update(
        query,
        (candidate_id, email, oa_link, status, sendgrid_message_id, error_message)
    )


def get_email_logs_for_candidate(candidate_id: int) -> list:
    """
    Get all email logs for a candidate
    
    Args:
        candidate_id: ID of the candidate
    
    Returns:
        List of email log dictionaries
    """
    query = """
        SELECT * FROM oa_email_logs
        WHERE candidate_id = %s
        ORDER BY sent_at DESC
    """
    return _execute_query(query, (candidate_id,))


def update_email_log_status(
    log_id: int,
    status: str,
    opened_at: str = None,
    clicked_at: str = None
) -> bool:
    """
    Update email log status (for tracking opens/clicks)
    
    Args:
        log_id: Email log ID
        status: New status
        opened_at: Timestamp when email was opened
        clicked_at: Timestamp when link was clicked
    
    Returns:
        True if successful
    """
    query = """
        UPDATE oa_email_logs
        SET status = %s, opened_at = %s, clicked_at = %s
        WHERE id = %s
    """
    return _execute_update(query, (status, opened_at, clicked_at, log_id)) is not None

