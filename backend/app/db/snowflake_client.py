import snowflake.connector
from typing import Optional, Dict, List, Any
from contextlib import contextmanager

from app.core.config import settings
from app.core.logger import logger


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


def create_job(title: str, description: str, department: str, company_name: Optional[str] = None, company_principles: Optional[str] = None) -> int:
    """Create a new job and return its ID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            # Check if company_principles column exists
            column_exists = False
            try:
                check_query = """
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = UPPER('PUBLIC') 
                    AND TABLE_NAME = UPPER('JOBS') 
                    AND COLUMN_NAME = UPPER('COMPANY_PRINCIPLES')
                """
                cursor.execute(check_query)
                result = cursor.fetchone()
                column_exists = result[0] > 0 if result else False
            except Exception as e:
                logger.warning(f"Could not check for COMPANY_PRINCIPLES column: {str(e)}")
                column_exists = False
            
            # Build query based on whether column exists and value is provided
            if company_principles is not None and column_exists:
                if company_name:
                    query = "INSERT INTO jobs (title, description, department, company_name, company_principles) VALUES (%s, %s, %s, %s, %s)"
                    params = (title, description, department, company_name, company_principles)
                else:
                    query = "INSERT INTO jobs (title, description, department, company_principles) VALUES (%s, %s, %s, %s)"
                    params = (title, description, department, company_principles)
            else:
                if company_name:
                    query = "INSERT INTO jobs (title, description, department, company_name) VALUES (%s, %s, %s, %s)"
                    params = (title, description, department, company_name)
                else:
                    query = "INSERT INTO jobs (title, description, department) VALUES (%s, %s, %s)"
                    params = (title, description, department)
            
            cursor.execute(query, params)
            # Get the last inserted ID using Snowflake's IDENT_CURRENT equivalent
            cursor.execute("SELECT MAX(id) FROM jobs")
            job_id = cursor.fetchone()[0]
            logger.info(f"Job created: ID={job_id}, title={title}, company_name={company_name}, has_principles={company_principles is not None}")
            return job_id
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}", exc_info=True)
            # If error is about missing column, try without it
            if "COMPANY_PRINCIPLES" in str(e) or "company_principles" in str(e) or "invalid identifier" in str(e).lower():
                try:
                    logger.warning(f"Column COMPANY_PRINCIPLES doesn't exist, creating job without it")
                    if company_name:
                        query = "INSERT INTO jobs (title, description, department, company_name) VALUES (%s, %s, %s, %s)"
                        params = (title, description, department, company_name)
                    else:
                        query = "INSERT INTO jobs (title, description, department) VALUES (%s, %s, %s)"
                        params = (title, description, department)
                    cursor.execute(query, params)
                    cursor.execute("SELECT MAX(id) FROM jobs")
                    job_id = cursor.fetchone()[0]
                    logger.info(f"Job created (without company_principles): ID={job_id}, title={title}")
                    return job_id
                except Exception as e2:
                    logger.error(f"Error creating job (fallback): {str(e2)}")
                    raise
            raise
        finally:
            cursor.close()


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


def update_job(job_id: int, title: Optional[str] = None, description: Optional[str] = None, department: Optional[str] = None, company_principles: Optional[str] = None) -> bool:
    """Update a job"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            # Check if company_principles column exists
            column_exists = False
            try:
                check_query = """
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = UPPER('PUBLIC') 
                    AND TABLE_NAME = UPPER('JOBS') 
                    AND COLUMN_NAME = UPPER('COMPANY_PRINCIPLES')
                """
                cursor.execute(check_query)
                result = cursor.fetchone()
                column_exists = result[0] > 0 if result else False
            except Exception as e:
                logger.warning(f"Could not check for COMPANY_PRINCIPLES column: {str(e)}")
                column_exists = False
            
            updates = []
            params = []
            
            if title is not None:
                updates.append("title = %s")
                params.append(title)
            if description is not None:
                updates.append("description = %s")
                params.append(description)
            if department is not None:
                updates.append("department = %s")
                params.append(department)
            if company_principles is not None and column_exists:
                updates.append("company_principles = %s")
                params.append(company_principles)
            
            if not updates:
                return False
            
            params.append(job_id)
            query = f"UPDATE jobs SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, tuple(params))
            rowcount = cursor.rowcount
            return rowcount > 0
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {str(e)}")
            # If error is about missing column, try without it
            if "COMPANY_PRINCIPLES" in str(e) or "company_principles" in str(e) or "invalid identifier" in str(e).lower():
                try:
                    logger.warning(f"Column COMPANY_PRINCIPLES doesn't exist, updating without it")
                    updates = []
                    params = []
                    if title is not None:
                        updates.append("title = %s")
                        params.append(title)
                    if description is not None:
                        updates.append("description = %s")
                        params.append(description)
                    if department is not None:
                        updates.append("department = %s")
                        params.append(department)
                    if not updates:
                        return False
                    params.append(job_id)
                    query = f"UPDATE jobs SET {', '.join(updates)} WHERE id = %s"
                    cursor.execute(query, tuple(params))
                    rowcount = cursor.rowcount
                    return rowcount > 0
                except Exception as e2:
                    logger.error(f"Error updating job (fallback): {str(e2)}")
                    return False
            raise
        finally:
            cursor.close()


def delete_job(job_id: int) -> bool:
    """Delete a job"""
    query = "DELETE FROM jobs WHERE id = %s"
    rows_affected = _execute_update(query, (job_id,))
    return rows_affected > 0


# ============================================================
# CANDIDATES TABLE FUNCTIONS
# ============================================================

def get_candidate(candidate_id: int) -> Optional[Dict[str, Any]]:
    """Get a candidate by ID"""
    query = "SELECT * FROM candidates WHERE id = %s"
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
    query = "UPDATE candidates SET fit_score = %s WHERE id = %s"
    rows_affected = _execute_update(query, (fit_score, candidate_id))
    return rows_affected > 0


def update_candidate_stage(candidate_id: int, stage: str) -> bool:
    """Update candidate's stage in the pipeline"""
    query = "UPDATE candidates SET stage = %s WHERE id = %s"
    rows_affected = _execute_update(query, (stage, candidate_id))
    return rows_affected > 0


def get_all_candidates(job_id: Optional[int] = None, stage: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all candidates, optionally filtered by job_id and/or stage"""
    query = "SELECT * FROM candidates WHERE 1=1"
    params = []
    
    if job_id:
        query += " AND job_id = %s"
        params.append(job_id)
    
    if stage:
        query += " AND stage = %s"
        params.append(stage)
    
    query += " ORDER BY created_at DESC"
    
    with get_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, tuple(params))
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        if not results:
            cursor.close()
            return []
        desc = cursor.description
        cursor.close()
        return [_row_to_dict(desc, row) for row in results]


def get_candidates_by_job(job_id: int) -> List[Dict[str, Any]]:
    """Get all candidates for a specific job"""
    return get_all_candidates(job_id=job_id)


def get_candidates_by_company(company_name: str) -> List[Dict[str, Any]]:
    """Get all candidates for jobs under a specific company"""
    query = """
        SELECT 
            c.*,
            j.title AS job_title,
            j.company_name
        FROM candidates c
        JOIN jobs j ON c.job_id = j.id
        WHERE j.company_name = %s
        ORDER BY c.created_at DESC
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (company_name,))
        results = cursor.fetchall()
        if not results:
            cursor.close()
            return []
        desc = cursor.description
        cursor.close()
        return [_row_to_dict(desc, row) for row in results]


def delete_candidate(candidate_id: int) -> bool:
    """Delete a candidate by ID"""
    try:
        query = "DELETE FROM candidates WHERE id = %s"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (candidate_id,))
            cursor.close()
            logger.info(f"Candidate deleted: ID={candidate_id}")
            return True
    except Exception as e:
        logger.error(f"Error deleting candidate: {str(e)}", exc_info=True)
        return False


def get_jobs_by_company(company_name: str) -> List[Dict[str, Any]]:
    """Get all jobs for a specific company"""
    query = "SELECT * FROM jobs WHERE company_name = %s ORDER BY created_at DESC"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (company_name,))
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


def update_oa_result(oa_id: int, score: float, status: str, completed_at: Optional[str] = None, integrity_score: Optional[float] = None) -> bool:
    """Update OA result with score, completion status, and integrity score"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            # Check if integrity_score column exists
            column_exists = False
            try:
                check_query = """
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = UPPER('PUBLIC') 
                    AND TABLE_NAME = UPPER('OA_RESULTS') 
                    AND COLUMN_NAME = UPPER('INTEGRITY_SCORE')
                """
                cursor.execute(check_query)
                result = cursor.fetchone()
                column_exists = result[0] > 0 if result else False
            except Exception as e:
                logger.warning(f"Could not check for INTEGRITY_SCORE column: {str(e)}")
                column_exists = False
            
            # Build query based on whether column exists and value is provided
            if integrity_score is not None and column_exists:
                if completed_at is None:
                    query = """
                        UPDATE oa_results 
                        SET score = %s, status = %s, completed_at = CURRENT_TIMESTAMP(), integrity_score = %s
                        WHERE id = %s
                    """
                    params = (score, status, integrity_score, oa_id)
                else:
                    query = """
                        UPDATE oa_results 
                        SET score = %s, status = %s, completed_at = %s, integrity_score = %s
                        WHERE id = %s
                    """
                    params = (score, status, completed_at, integrity_score, oa_id)
            else:
                if completed_at is None:
                    query = """
                        UPDATE oa_results 
                        SET score = %s, status = %s, completed_at = CURRENT_TIMESTAMP()
                        WHERE id = %s
                    """
                    params = (score, status, oa_id)
                else:
                    query = """
                        UPDATE oa_results 
                        SET score = %s, status = %s, completed_at = %s
                        WHERE id = %s
                    """
                    params = (score, status, completed_at, oa_id)
            
            cursor.execute(query, params)
            rowcount = cursor.rowcount
            if rowcount > 0:
                logger.info(f"✅ Successfully updated OA result {oa_id} with integrity_score={integrity_score}, score={score}, status={status}")
            else:
                logger.warning(f"⚠️ No rows updated for OA result {oa_id}")
            return rowcount > 0
        except Exception as e:
            logger.error(f"Error updating OA result {oa_id}: {str(e)}")
            # If error is about missing column, try without it
            if "INTEGRITY_SCORE" in str(e) or "integrity_score" in str(e) or "invalid identifier" in str(e).lower():
                try:
                    logger.warning(f"Column INTEGRITY_SCORE doesn't exist, updating without it")
                    if completed_at is None:
                        query = """
                            UPDATE oa_results 
                            SET score = %s, status = %s, completed_at = CURRENT_TIMESTAMP()
                            WHERE id = %s
                        """
                        params = (score, status, oa_id)
                    else:
                        query = """
                            UPDATE oa_results 
                            SET score = %s, status = %s, completed_at = %s
                            WHERE id = %s
                        """
                        params = (score, status, completed_at, oa_id)
                    cursor.execute(query, params)
                    rowcount = cursor.rowcount
                    return rowcount > 0
                except Exception as e2:
                    logger.error(f"Error updating OA result (fallback): {str(e2)}")
                    return False
            raise
        finally:
            cursor.close()


def get_oa_result(candidate_id: int) -> Optional[Dict[str, Any]]:
    """Get OA result for a candidate"""
    query = "SELECT * FROM oa_results WHERE candidate_id = %s ORDER BY sent_at DESC LIMIT 1"
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, (candidate_id,))
            results = cursor.fetchall()
            if results:
                desc = cursor.description
                result = _row_to_dict(desc, results[0])
                # Log integrity_score for debugging
                integrity_score = result.get("INTEGRITY_SCORE") or result.get("integrity_score")
                logger.info(f"📊 Retrieved OA result for candidate {candidate_id}: integrity_score={integrity_score}, score={result.get('SCORE') or result.get('score')}")
                return result
            else:
                logger.info(f"📊 No OA result found for candidate {candidate_id}")
            cursor.close()
            return None
        except Exception as e:
            logger.error(f"Error getting OA result for candidate {candidate_id}: {str(e)}")
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
    query = "UPDATE final_interviews SET decision = %s, feedback = %s WHERE id = %s"
    rows_affected = _execute_update(query, (decision, feedback, interview_id))
    return rows_affected > 0


def get_final_interview(candidate_id: int) -> Optional[Dict[str, Any]]:
    """Get final interview for a candidate"""
    query = "SELECT * FROM final_interviews WHERE candidate_id = %s ORDER BY created_at DESC LIMIT 1"
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


# ============================================================
# USERS TABLE FUNCTIONS (Authentication)
# ============================================================

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Get a user by email address
    
    Args:
        email: User's email address
    
    Returns:
        User dictionary if found, None otherwise
    """
    query = "SELECT * FROM users WHERE email = %s"
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


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a user by ID
    
    Args:
        user_id: User's ID
    
    Returns:
        User dictionary if found, None otherwise
    """
    query = "SELECT * FROM users WHERE id = %s"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        if results:
            desc = cursor.description
            cursor.close()
            return _row_to_dict(desc, results[0])
        cursor.close()
    return None


def create_user(email: str, password_hash: str, name: str, role: str = "candidate", company_name: Optional[str] = None) -> int:
    """
    Create a new user account
    
    Args:
        email: User's email address
        password_hash: Hashed password
        name: User's full name
        role: User role (candidate, recruiter, admin)
        company_name: Company name (for recruiters)
    
    Returns:
        User ID of newly created user
    """
    query = """
        INSERT INTO users (email, password, name, role, company_name)
        VALUES (%s, %s, %s, %s, %s)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (email, password_hash, name, role, company_name))
        cursor.execute("SELECT MAX(id) FROM users")
        user_id = cursor.fetchone()[0]
        cursor.close()
        return user_id


def update_user_last_login(user_id: int) -> bool:
    """
    Update user's last login timestamp
    
    Args:
        user_id: User's ID
    
    Returns:
        True if successful
    """
    query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s"
    rows_affected = _execute_update(query, (user_id,))
    return rows_affected > 0


def update_user_profile(user_id: int, name: Optional[str] = None, company_name: Optional[str] = None, phone: Optional[str] = None) -> bool:
    """
    Update user profile information
    
    Args:
        user_id: User's ID
        name: New name (optional)
        company_name: New company name (optional)
        phone: New phone number (optional)
    
    Returns:
        True if successful
    """
    updates = {}
    if name is not None:
        updates['name'] = name
    if company_name is not None:
        updates['company_name'] = company_name
    if phone is not None:
        updates['phone'] = phone
    
    if not updates:
        return False
    
    set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
    query = f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
    
    rows_affected = _execute_update(query, (*updates.values(), user_id))
    return rows_affected > 0


def verify_user_email(user_id: int) -> bool:
    """
    Mark user's email as verified
    
    Args:
        user_id: User's ID
    
    Returns:
        True if successful
    """
    query = "UPDATE users SET email_verified = TRUE WHERE id = %s"
    rows_affected = _execute_update(query, (user_id,))
    return rows_affected > 0


def deactivate_user(user_id: int) -> bool:
    """
    Deactivate a user account
    
    Args:
        user_id: User's ID
    
    Returns:
        True if successful
    """
    query = "UPDATE users SET is_active = FALSE WHERE id = %s"
    rows_affected = _execute_update(query, (user_id,))
    return rows_affected > 0


def get_users_by_role(role: str) -> List[Dict[str, Any]]:
    """
    Get all users with a specific role
    
    Args:
        role: User role (candidate, recruiter, admin)
    
    Returns:
        List of user dictionaries
    """
    query = "SELECT * FROM users WHERE role = %s ORDER BY created_at DESC"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (role,))
        results = cursor.fetchall()
        if not results:
            cursor.close()
            return []
        desc = cursor.description
        cursor.close()
        return [_row_to_dict(desc, row) for row in results]


# ============================================================
# CANDIDATE PROFILES TABLE FUNCTIONS
# ============================================================

def create_candidate_profile(user_id: int) -> int:
    """
    Create a candidate record in CANDIDATES table and candidate_profiles record if they don't exist
    
    Args:
        user_id: User's ID (from users table)
    
    Returns:
        Candidate ID (from candidates table)
    """
    # Get user info
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    # Handle both uppercase and lowercase column names from Snowflake
    email = user.get("EMAIL") or user.get("email")
    name = user.get("NAME") or user.get("name")
    
    # First, check if candidate exists in CANDIDATES table
    candidate_query = "SELECT ID FROM CANDIDATES WHERE EMAIL = %s"
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(candidate_query, (email,))
            candidate_result = cursor.fetchone()
            
            if candidate_result:
                candidate_id = candidate_result[0]
            else:
                # Create candidate record in CANDIDATES table
                insert_candidate_query = """
                    INSERT INTO CANDIDATES (NAME, EMAIL, STAGE)
                    VALUES (%s, %s, 'applied')
                """
                cursor.execute(insert_candidate_query, (name, email))
                # Get the inserted ID
                cursor.execute("SELECT ID FROM CANDIDATES WHERE EMAIL = %s", (email,))
                candidate_id = cursor.fetchone()[0]
                logger.info(f"Created candidate record {candidate_id} for user {user_id}")
            
            # Now check if candidate_profiles record exists
            profile_query = "SELECT ID FROM CANDIDATE_PROFILES WHERE USER_ID = %s"
            cursor.execute(profile_query, (candidate_id,))
            profile_result = cursor.fetchone()
            
            if not profile_result:
                # Create candidate_profiles record
                insert_profile_query = """
                    INSERT INTO CANDIDATE_PROFILES (USER_ID)
                    VALUES (%s)
                """
                cursor.execute(insert_profile_query, (candidate_id,))
                logger.info(f"Created candidate_profiles record for candidate {candidate_id}")
            
            cursor.close()
            return candidate_id
        except Exception as e:
            logger.error(f"Error creating candidate profile: {str(e)}")
            cursor.close()
            raise


def get_candidate_profile_by_candidate_id(candidate_id: int) -> Optional[Dict[str, Any]]:
    """
    Get candidate profile by candidate ID (from candidate_profiles table)
    
    Args:
        candidate_id: Candidate's ID (from CANDIDATES table)
    
    Returns:
        Profile dictionary if found, None otherwise
    """
    # Get profile from candidate_profiles table
    # Note: USER_ID in candidate_profiles references CANDIDATES(id)
    profile_query = "SELECT * FROM CANDIDATE_PROFILES WHERE USER_ID = %s"
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(profile_query, (candidate_id,))
            results = cursor.fetchall()
            
            if results:
                desc = cursor.description
                profile = _row_to_dict(desc, results[0])
                # Also get candidate info and merge
                candidate_info_query = "SELECT * FROM CANDIDATES WHERE ID = %s"
                cursor.execute(candidate_info_query, (candidate_id,))
                candidate_results = cursor.fetchall()
                if candidate_results:
                    candidate_desc = cursor.description
                    candidate_data = _row_to_dict(candidate_desc, candidate_results[0])
                    # Merge candidate data into profile
                    profile.update(candidate_data)
                return profile
            
            return None
        finally:
            cursor.close()


def get_candidate_profile_by_user_id(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get candidate profile by user ID (from candidate_profiles table)
    
    Args:
        user_id: User's ID (from users table)
    
    Returns:
        Profile dictionary if found, None otherwise
    """
    # Get user email to find candidate record
    user = get_user_by_id(user_id)
    if not user:
        return None
    
    # Handle both uppercase and lowercase column names from Snowflake
    email = user.get("EMAIL") or user.get("email")
    if not email:
        return None
    
    # First get candidate ID from CANDIDATES table
    candidate_query = "SELECT ID FROM CANDIDATES WHERE EMAIL = %s"
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(candidate_query, (email,))
            candidate_result = cursor.fetchone()
            
            if not candidate_result:
                return None
            
            candidate_id = candidate_result[0]
            
            # Use the candidate_id-based function
            return get_candidate_profile_by_candidate_id(candidate_id)
        finally:
            cursor.close()


def update_candidate_profile(
    user_id: int,
    resume_url: Optional[str] = None,
    phone: Optional[str] = None,
    location: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    portfolio_url: Optional[str] = None,
    skills: Optional[str] = None,
    experience_years: Optional[int] = None,
    education: Optional[str] = None,
    bio: Optional[str] = None,
    description: Optional[str] = None
) -> bool:
    """
    Update candidate profile in candidate_profiles table
    
    Args:
        user_id: User's ID (from users table)
        resume_url: URL to resume
        phone: Phone number
        location: Location/city
        linkedin_url: LinkedIn profile URL
        portfolio_url: Portfolio website URL
        skills: Comma-separated skills (will be converted to ARRAY)
        experience_years: Years of experience
        education: Education details
        bio: Short bio
        description: Resume summary/description from Gemini
    
    Returns:
        True if successful
    """
    # Get user email to find candidate record
    user = get_user_by_id(user_id)
    if not user:
        logger.error(f"User {user_id} not found")
        return False
    
    # Handle both uppercase and lowercase column names from Snowflake
    email = user.get("EMAIL") or user.get("email")
    if not email:
        logger.error(f"User {user_id} has no email")
        return False
    
    # Ensure candidate and profile exist
    try:
        candidate_id = create_candidate_profile(user_id)
    except Exception as e:
        logger.error(f"Failed to create/get candidate profile for user {user_id}: {str(e)}")
        return False
    
    # Map to Snowflake column names (uppercase)
    updates = {}
    
    # Log all incoming parameters with their types
    logger.info(f"update_candidate_profile called with:")
    logger.info(f"  user_id: {user_id} (type: {type(user_id).__name__})")
    logger.info(f"  resume_url: {resume_url} (type: {type(resume_url).__name__})")
    logger.info(f"  phone: {repr(phone)} (type: {type(phone).__name__})")
    logger.info(f"  location: {repr(location)} (type: {type(location).__name__})")
    logger.info(f"  linkedin_url: {repr(linkedin_url)} (type: {type(linkedin_url).__name__})")
    logger.info(f"  portfolio_url: {repr(portfolio_url)} (type: {type(portfolio_url).__name__})")
    logger.info(f"  skills: {repr(skills)} (type: {type(skills).__name__})")
    logger.info(f"  experience_years: {experience_years} (type: {type(experience_years).__name__})")
    logger.info(f"  education: {repr(education)} (type: {type(education).__name__})")
    logger.info(f"  bio: {repr(bio)} (type: {type(bio).__name__})")
    logger.info(f"  description: {repr(description[:100]) if description else 'None'}... (type: {type(description).__name__})")
    
    # Count how many fields are provided (not None)
    provided_fields = []
    if resume_url is not None:
        provided_fields.append('resume_url')
    if phone is not None:
        provided_fields.append('phone')
    if location is not None:
        provided_fields.append('location')
    if linkedin_url is not None:
        provided_fields.append('linkedin_url')
    if portfolio_url is not None:
        provided_fields.append('portfolio_url')
    if skills is not None:
        provided_fields.append('skills')
    if experience_years is not None:
        provided_fields.append('experience_years')
    if education is not None:
        provided_fields.append('education')
    if bio is not None:
        provided_fields.append('bio')
    if description is not None:
        provided_fields.append('description')
    
    logger.info(f"Fields provided (not None): {provided_fields}")
    
    # Handle resume_url - only update if provided and non-empty (preserve existing if not provided)
    if resume_url is not None:
        if resume_url and resume_url.strip():
            updates['RESUME_URL'] = resume_url.strip()
            logger.info(f"✅ Added RESUME_URL to updates: {resume_url}")
        else:
            logger.info(f"⚠️ resume_url is empty/None, skipping (preserving existing value)")
    
    # Handle phone - update if provided (including empty string to clear)
    # CRITICAL: Check if phone is not None AND not empty string (or allow empty strings)
    if phone is not None:
        phone_str = phone.strip() if isinstance(phone, str) else str(phone) if phone else ''
        updates['PHONE'] = phone_str
        logger.info(f"✅ Added PHONE to updates: {repr(phone)} → {repr(phone_str)}")
    else:
        logger.warning(f"⚠️ PHONE is None - not updating")
    
    # Handle location - update if provided (including empty string to clear)
    if location is not None:
        location_str = location.strip() if isinstance(location, str) else str(location) if location else ''
        updates['LOCATION'] = location_str
        logger.info(f"✅ Added LOCATION to updates: {repr(location)} → {repr(location_str)}")
    else:
        logger.warning(f"⚠️ LOCATION is None - not updating")
    
    # Handle linkedin_url - update if provided (including empty string to clear)
    if linkedin_url is not None:
        linkedin_str = linkedin_url.strip() if isinstance(linkedin_url, str) else str(linkedin_url) if linkedin_url else ''
        updates['LINKEDIN_URL'] = linkedin_str
        logger.info(f"✅ Added LINKEDIN_URL to updates: {repr(linkedin_url)} → {repr(linkedin_str)}")
    else:
        logger.warning(f"⚠️ LINKEDIN_URL is None - not updating")
    
    # Handle portfolio_url - update if provided (including empty string to clear)
    if portfolio_url is not None:
        portfolio_str = portfolio_url.strip() if isinstance(portfolio_url, str) else str(portfolio_url) if portfolio_url else ''
        updates['PORTFOLIO_URL'] = portfolio_str
        logger.info(f"✅ Added PORTFOLIO_URL to updates: {repr(portfolio_url)} → {repr(portfolio_str)}")
    else:
        logger.warning(f"⚠️ PORTFOLIO_URL is None - not updating")
    
    # Handle skills - convert comma-separated string to array for Snowflake
    if skills is not None:
        if isinstance(skills, str):
            # Allow empty skills string (will result in empty array)
            skills_array = [s.strip() for s in skills.split(',') if s.strip()]
        else:
            skills_array = skills if skills else []
        updates['SKILLS'] = skills_array
        logger.info(f"✅ Added SKILLS to updates: {skills_array}")
    
    # Handle experience_years - update if provided (including 0)
    if experience_years is not None:
        updates['EXPERIENCE_YEARS'] = experience_years
        logger.info(f"✅ Added EXPERIENCE_YEARS to updates: {experience_years}")
    
    # Handle education - update if provided (including empty string to clear)
    if education is not None:
        updates['EDUCATION'] = education.strip() if isinstance(education, str) else education
        logger.info(f"✅ Added EDUCATION to updates: {repr(education)}")
    
    # Handle bio - update if provided (including empty string to clear)
    if bio is not None:
        updates['BIO'] = bio.strip() if isinstance(bio, str) else bio
        logger.info(f"✅ Added BIO to updates: {repr(bio)}")
    
    # Handle description - only update if provided and non-empty (preserve existing if not provided)
    # This is typically set by Gemini when uploading resume, so we preserve it if not explicitly updated
    if description is not None:
        if description and description.strip():
            updates['DESCRIPTION'] = description.strip()
            logger.info(f"✅ Added DESCRIPTION to update: {description[:100]}...")
        else:
            logger.info(f"⚠️ description is empty/None, skipping (preserving existing value)")
    
    logger.info(f"Total updates to apply: {len(updates)} fields: {list(updates.keys())}")
    
    # If no updates were added but fields were provided, that means all were filtered out
    # This should only happen if all provided fields were empty strings for resume_url/description
    # For other fields, empty strings are valid updates
    if not updates:
        if not provided_fields:
            logger.error(f"❌ No updates provided for user {user_id} - all parameters were None")
            return False
        else:
            # This shouldn't happen since we add all non-None fields except resume_url/description
            logger.error(f"❌ No updates to apply but fields were provided: {provided_fields}")
            logger.error(f"   This might indicate a logic error - all fields were filtered out")
            return False
    
    # Log what we're updating
    logger.info(f"Updating candidate profile for user {user_id}, candidate_id {candidate_id}")
    logger.info(f"Fields to update: {list(updates.keys())}")
    if 'DESCRIPTION' in updates:
        logger.info(f"Description value: {updates['DESCRIPTION'][:100] if updates['DESCRIPTION'] else 'None'}...")
    
    # Build UPDATE query for candidate_profiles table
    # Convert array fields properly for Snowflake
    set_clauses = []
    final_params = []
    
    for key, value in updates.items():
        if key == 'SKILLS' and isinstance(value, list):
            # Handle ARRAY type for skills - Snowflake accepts Python lists as arrays
            set_clauses.append(f"{key} = %s")
            final_params.append(value)
            logger.info(f"Adding SKILLS array with {len(value)} items")
        else:
            set_clauses.append(f"{key} = %s")
            final_params.append(value)
            if key == 'DESCRIPTION':
                logger.info(f"Adding DESCRIPTION parameter: {str(value)[:100] if value else 'None'}...")
    
    set_clause = ", ".join(set_clauses)
    # Use uppercase column names to match Snowflake schema
    query = f"UPDATE CANDIDATE_PROFILES SET {set_clause} WHERE USER_ID = %s"
    final_params.append(candidate_id)
    
    logger.info(f"Executing query: {query}")
    logger.info(f"Parameters count: {len(final_params)}")
    logger.info(f"Parameters: {[str(p)[:50] if p else 'None' for p in final_params]}")
    if 'DESCRIPTION' in updates:
        logger.info(f"DESCRIPTION parameter type: {type(updates['DESCRIPTION']).__name__}")
        logger.info(f"DESCRIPTION parameter length: {len(updates['DESCRIPTION']) if updates['DESCRIPTION'] else 0}")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            # First, verify the row exists and check current description
            check_query = "SELECT USER_ID, DESCRIPTION FROM CANDIDATE_PROFILES WHERE USER_ID = %s"
            cursor.execute(check_query, (candidate_id,))
            check_result = cursor.fetchone()
            if check_result:
                logger.info(f"Row exists. Current DESCRIPTION: {str(check_result[1])[:100] if check_result[1] else 'None'}...")
            else:
                logger.error(f"❌ Row not found for candidate_id {candidate_id}")
                cursor.close()
                return False
            
            # Execute the update
            cursor.execute(query, tuple(final_params))
            rows_affected = cursor.rowcount
            logger.info(f"Update executed. Rows affected: {rows_affected}")
            
            if rows_affected > 0:
                logger.info(f"✅ Updated candidate profile for user {user_id} (candidate_id: {candidate_id})")
                
                # Verify the update by reading back ALL updated fields
                verify_query = "SELECT PHONE, LINKEDIN_URL, PORTFOLIO_URL, LOCATION, EDUCATION, BIO, DESCRIPTION FROM CANDIDATE_PROFILES WHERE USER_ID = %s"
                cursor.execute(verify_query, (candidate_id,))
                result = cursor.fetchone()
                if result:
                    saved_phone, saved_linkedin, saved_portfolio, saved_location, saved_education, saved_bio, saved_description = result
                    logger.info(f"=== VERIFICATION OF SAVED VALUES ===")
                    logger.info(f"PHONE - Expected: {repr(updates.get('PHONE'))}, Saved: {repr(saved_phone)}")
                    logger.info(f"LINKEDIN_URL - Expected: {repr(updates.get('LINKEDIN_URL'))}, Saved: {repr(saved_linkedin)}")
                    logger.info(f"PORTFOLIO_URL - Expected: {repr(updates.get('PORTFOLIO_URL'))}, Saved: {repr(saved_portfolio)}")
                    logger.info(f"LOCATION - Expected: {repr(updates.get('LOCATION'))}, Saved: {repr(saved_location)}")
                    logger.info(f"EDUCATION - Expected: {repr(updates.get('EDUCATION'))}, Saved: {repr(saved_education)}")
                    logger.info(f"BIO - Expected: {repr(updates.get('BIO'))}, Saved: {repr(saved_bio)}")
                    if 'DESCRIPTION' in updates:
                        logger.info(f"DESCRIPTION - Expected: {repr(updates.get('DESCRIPTION'))[:100] if updates.get('DESCRIPTION') else 'None'}, Saved: {repr(saved_description)[:100] if saved_description else 'None'}")
                else:
                    logger.warning("⚠️ Could not verify update - no row found after update")
            else:
                logger.warning(f"⚠️ Update executed but no rows were affected")
            
            cursor.close()
            return rows_affected > 0
        except Exception as e:
            logger.error(f"❌ Error updating candidate profile: {str(e)}")
            logger.error(f"Query was: {query}")
            logger.error(f"Parameters were: {final_params}")
            logger.error(f"Parameter types: {[type(p).__name__ for p in final_params]}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            cursor.close()
            return False

