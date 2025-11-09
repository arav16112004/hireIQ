"""
OA Platform Database Client
Functions for interacting with OA tables in Snowflake
"""
import json
from typing import Optional, Dict, List, Any
from app.db.snowflake_client import get_connection
from app.core.logger import logger


# ============================================================
# QUESTIONS FUNCTIONS
# ============================================================

def get_question(question_id: int, include_test_cases: bool = False) -> Optional[Dict[str, Any]]:
    """Get a question by ID"""
    query = "SELECT * FROM oa_questions WHERE id = %s"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (question_id,))
        results = cursor.fetchall()
        if not results:
            cursor.close()
            return None
        
        desc = cursor.description
        columns = [d[0] for d in desc]
        question = dict(zip(columns, results[0]))
        cursor.close()
        
        if include_test_cases:
            question['test_cases'] = get_test_cases(question_id)
        
        return question


def get_all_questions(active_only: bool = True) -> List[Dict[str, Any]]:
    """Get all questions"""
    query = "SELECT * FROM oa_questions"
    if active_only:
        query += " WHERE is_active = TRUE"
    query += " ORDER BY created_at DESC"
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        if not results:
            cursor.close()
            return []
        
        desc = cursor.description
        columns = [d[0] for d in desc]
        questions = [dict(zip(columns, row)) for row in results]
        cursor.close()
        return questions


def create_question(
    title: str,
    description: str,
    difficulty: str,
    language: str,
    time_limit: float = 5.0,
    memory_limit: int = 128000,
    points: int = 100,
    starter_code: Optional[str] = None,
    is_active: bool = True
) -> int:
    """Create a new question"""
    query = """
        INSERT INTO oa_questions 
        (title, description, difficulty, language, time_limit, memory_limit, points, starter_code, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (
            title, description, difficulty, language,
            time_limit, memory_limit, points, starter_code, is_active
        ))
        cursor.execute("SELECT MAX(id) FROM oa_questions")
        question_id = cursor.fetchone()[0]
        cursor.close()
        return question_id


def update_question(question_id: int, **kwargs) -> bool:
    """Update a question"""
    allowed_fields = [
        'title', 'description', 'difficulty', 'language',
        'time_limit', 'memory_limit', 'points', 'starter_code', 'is_active'
    ]
    
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
    if not updates:
        return False
    
    set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
    query = f"UPDATE oa_questions SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (*updates.values(), question_id))
        rowcount = cursor.rowcount
        cursor.close()
        return rowcount > 0


def delete_question(question_id: int) -> bool:
    """Soft delete a question by setting is_active to false"""
    return update_question(question_id, is_active=False)


# ============================================================
# TEST CASES FUNCTIONS
# ============================================================

def get_test_cases(question_id: int, include_hidden: bool = True) -> List[Dict[str, Any]]:
    """Get test cases for a question"""
    query = "SELECT * FROM oa_test_cases WHERE question_id = %s"
    if not include_hidden:
        query += " AND is_hidden = FALSE"
    query += " ORDER BY id"
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (question_id,))
        results = cursor.fetchall()
        if not results:
            cursor.close()
            return []
        
        desc = cursor.description
        columns = [d[0] for d in desc]
        test_cases = [dict(zip(columns, row)) for row in results]
        cursor.close()
        return test_cases


def create_test_case(
    question_id: int,
    input_data: str,
    expected_output: str,
    is_hidden: bool = False,
    points: int = 1
) -> int:
    """Create a test case for a question"""
    query = """
        INSERT INTO oa_test_cases (question_id, input, expected_output, is_hidden, points)
        VALUES (%s, %s, %s, %s, %s)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (question_id, input_data, expected_output, is_hidden, points))
        cursor.execute("SELECT MAX(id) FROM oa_test_cases")
        test_case_id = cursor.fetchone()[0]
        cursor.close()
        return test_case_id


def delete_test_case(test_case_id: int) -> bool:
    """Delete a test case"""
    query = "DELETE FROM oa_test_cases WHERE id = %s"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (test_case_id,))
        rowcount = cursor.rowcount
        cursor.close()
        return rowcount > 0


# ============================================================
# OA SESSIONS FUNCTIONS
# ============================================================

def create_oa_session(
    candidate_id: int,
    question_ids: List[int],
    duration_minutes: int = 60
) -> int:
    """Create a new OA session for a candidate"""
    # Build ARRAY_CONSTRUCT using SELECT for Snowflake
    array_values = ','.join(str(qid) for qid in question_ids)
    query = f"""
        INSERT INTO oa_sessions (candidate_id, question_ids, duration_minutes, status)
        SELECT %s, ARRAY_CONSTRUCT({array_values}), %s, %s
    """
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (candidate_id, duration_minutes, 'pending'))
        cursor.execute("SELECT MAX(id) FROM oa_sessions")
        session_id = cursor.fetchone()[0]
        cursor.close()
        return session_id


def get_oa_session(session_id: int) -> Optional[Dict[str, Any]]:
    """Get an OA session by ID"""
    query = "SELECT * FROM oa_sessions WHERE id = %s"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (session_id,))
        results = cursor.fetchall()
        if not results:
            cursor.close()
            return None
        
        desc = cursor.description
        columns = [d[0] for d in desc]
        session = dict(zip(columns, results[0]))
        cursor.close()
        
        # Convert question_ids ARRAY to Python list
        if session.get('QUESTION_IDS'):
            try:
                # Snowflake returns array as string like "[1,2,3]"
                qids = session['QUESTION_IDS']
                if isinstance(qids, str):
                    session['QUESTION_IDS'] = json.loads(qids)
                elif isinstance(qids, list):
                    session['QUESTION_IDS'] = qids
            except:
                pass
        
        return session


def get_sessions_by_candidate(candidate_id: int) -> List[Dict[str, Any]]:
    """Get all OA sessions for a candidate"""
    query = "SELECT * FROM oa_sessions WHERE candidate_id = %s ORDER BY created_at DESC"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (candidate_id,))
        results = cursor.fetchall()
        if not results:
            cursor.close()
            return []
        
        desc = cursor.description
        columns = [d[0] for d in desc]
        sessions = [dict(zip(columns, row)) for row in results]
        cursor.close()
        
        # Convert question_ids ARRAY to Python list for each session
        for session in sessions:
            if session.get('QUESTION_IDS'):
                try:
                    qids = session['QUESTION_IDS']
                    if isinstance(qids, str):
                        session['QUESTION_IDS'] = json.loads(qids)
                    elif isinstance(qids, list):
                        session['QUESTION_IDS'] = qids
                except:
                    pass
        
        return sessions


def start_oa_session(session_id: int) -> bool:
    """Mark an OA session as started"""
    query = """
        UPDATE oa_sessions 
        SET status = %s, started_at = CURRENT_TIMESTAMP
        WHERE id = %s AND status = %s
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, ('in_progress', session_id, 'pending'))
        rowcount = cursor.rowcount
        cursor.close()
        return rowcount > 0


def complete_oa_session(session_id: int, score: float, max_score: float, max_cheating_score: Optional[float] = None) -> bool:
    """Mark an OA session as completed"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            # Check if max_cheating_score column exists using information schema
            column_exists = False
            try:
                check_query = """
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = UPPER('PUBLIC') 
                    AND TABLE_NAME = UPPER('OA_SESSIONS') 
                    AND COLUMN_NAME = UPPER('MAX_CHEATING_SCORE')
                """
                cursor.execute(check_query)
                result = cursor.fetchone()
                column_exists = result[0] > 0 if result else False
            except Exception as e:
                logger.warning(f"Could not check for MAX_CHEATING_SCORE column: {str(e)}")
                column_exists = False
            
            # Build query based on whether column exists and value is provided
            if max_cheating_score is not None and column_exists:
                query = """
                    UPDATE oa_sessions 
                    SET status = %s, completed_at = CURRENT_TIMESTAMP, score = %s, max_score = %s, max_cheating_score = %s
                    WHERE id = %s
                """
                params = ('completed', score, max_score, max_cheating_score, session_id)
            else:
                query = """
                    UPDATE oa_sessions 
                    SET status = %s, completed_at = CURRENT_TIMESTAMP, score = %s, max_score = %s
                    WHERE id = %s
                """
                params = ('completed', score, max_score, session_id)
            
            cursor.execute(query, params)
            rowcount = cursor.rowcount
            return rowcount > 0
        except Exception as e:
            logger.error(f"Error completing OA session {session_id}: {str(e)}")
            # If error is about missing column, try without it
            if "MAX_CHEATING_SCORE" in str(e) or "max_cheating_score" in str(e) or "invalid identifier" in str(e).lower():
                try:
                    logger.warning(f"Column MAX_CHEATING_SCORE doesn't exist, completing session without it")
                    query = """
                        UPDATE oa_sessions 
                        SET status = %s, completed_at = CURRENT_TIMESTAMP, score = %s, max_score = %s
                        WHERE id = %s
                    """
                    params = ('completed', score, max_score, session_id)
                    cursor.execute(query, params)
                    rowcount = cursor.rowcount
                    logger.info(f"Completed OA session {session_id} without max_cheating_score (column doesn't exist yet)")
                    return rowcount > 0
                except Exception as e2:
                    logger.error(f"Error completing OA session (fallback): {str(e2)}")
                    return False
            raise
        finally:
            cursor.close()


def update_oa_session_status(session_id: int, status: str) -> bool:
    """Update OA session status"""
    query = "UPDATE oa_sessions SET status = %s WHERE id = %s"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (status, session_id))
        rowcount = cursor.rowcount
        cursor.close()
        return rowcount > 0


# ============================================================
# SUBMISSIONS FUNCTIONS
# ============================================================

def create_submission(
    session_id: int,
    question_id: int,
    source_code: str,
    language: str
) -> int:
    """Create a new code submission"""
    query = """
        INSERT INTO oa_submissions (session_id, question_id, source_code, language, status)
        VALUES (%s, %s, %s, %s, %s)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (session_id, question_id, source_code, language, 'pending'))
        cursor.execute("SELECT MAX(id) FROM oa_submissions")
        submission_id = cursor.fetchone()[0]
        cursor.close()
        return submission_id


def get_submission(submission_id: int) -> Optional[Dict[str, Any]]:
    """Get a submission by ID"""
    query = "SELECT * FROM oa_submissions WHERE id = %s"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (submission_id,))
        results = cursor.fetchall()
        if not results:
            cursor.close()
            return None
        
        desc = cursor.description
        columns = [d[0] for d in desc]
        submission = dict(zip(columns, results[0]))
        cursor.close()
        
        # Parse test_results from JSON
        if submission.get('TEST_RESULTS'):
            try:
                submission['TEST_RESULTS'] = json.loads(submission['TEST_RESULTS'])
            except:
                pass
        
        return submission


def get_submissions_by_session(session_id: int) -> List[Dict[str, Any]]:
    """Get all submissions for an OA session"""
    query = "SELECT * FROM oa_submissions WHERE session_id = %s ORDER BY submitted_at DESC"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (session_id,))
        results = cursor.fetchall()
        if not results:
            cursor.close()
            return []
        
        desc = cursor.description
        columns = [d[0] for d in desc]
        submissions = [dict(zip(columns, row)) for row in results]
        cursor.close()
        
        # Parse test_results for each submission
        for submission in submissions:
            if submission.get('TEST_RESULTS'):
                try:
                    submission['TEST_RESULTS'] = json.loads(submission['TEST_RESULTS'])
                except:
                    pass
        
        return submissions


def get_submissions_by_question(session_id: int, question_id: int) -> List[Dict[str, Any]]:
    """Get all submissions for a specific question in a session"""
    query = """
        SELECT * FROM oa_submissions 
        WHERE session_id = %s AND question_id = %s 
        ORDER BY submitted_at DESC
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (session_id, question_id))
        results = cursor.fetchall()
        if not results:
            cursor.close()
            return []
        
        desc = cursor.description
        columns = [d[0] for d in desc]
        submissions = [dict(zip(columns, row)) for row in results]
        cursor.close()
        
        for submission in submissions:
            if submission.get('TEST_RESULTS'):
                try:
                    submission['TEST_RESULTS'] = json.loads(submission['TEST_RESULTS'])
                except:
                    pass
        
        return submissions


def update_submission(
    submission_id: int,
    status: str,
    score: Optional[float] = None,
    passed_tests: Optional[int] = None,
    total_tests: Optional[int] = None,
    execution_time: Optional[float] = None,
    memory_used: Optional[int] = None,
    stdout: Optional[str] = None,
    stderr: Optional[str] = None,
    compile_output: Optional[str] = None,
    test_results: Optional[Dict[str, Any]] = None
) -> bool:
    """Update a submission with execution results"""
    # Build dynamic update query
    updates = {'status': status}
    if score is not None:
        updates['score'] = score
    if passed_tests is not None:
        updates['passed_tests'] = passed_tests
    if total_tests is not None:
        updates['total_tests'] = total_tests
    if execution_time is not None:
        updates['execution_time'] = execution_time
    if memory_used is not None:
        updates['memory_used'] = memory_used
    if stdout is not None:
        updates['stdout'] = stdout
    if stderr is not None:
        updates['stderr'] = stderr
    if compile_output is not None:
        updates['compile_output'] = compile_output
    if test_results is not None:
        updates['test_results'] = json.dumps(test_results)
    
    set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
    query = f"UPDATE oa_submissions SET {set_clause} WHERE id = %s"
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (*updates.values(), submission_id))
        rowcount = cursor.rowcount
        cursor.close()
        return rowcount > 0


# ============================================================
# STATISTICS FUNCTIONS
# ============================================================

def get_question_stats() -> Dict[str, Any]:
    """Get statistics about the question bank"""
    query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN difficulty = 'easy' THEN 1 ELSE 0 END) as easy,
            SUM(CASE WHEN difficulty = 'medium' THEN 1 ELSE 0 END) as medium,
            SUM(CASE WHEN difficulty = 'hard' THEN 1 ELSE 0 END) as hard,
            SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as active
        FROM oa_questions
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        
        return {
            'total_questions': result[0] or 0,
            'easy': result[1] or 0,
            'medium': result[2] or 0,
            'hard': result[3] or 0,
            'active': result[4] or 0
        }


def get_candidate_oa_stats(candidate_id: int) -> Dict[str, Any]:
    """Get OA statistics for a candidate"""
    query = """
        SELECT 
            COUNT(*) as total_sessions,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            AVG(CASE WHEN status = 'completed' THEN score ELSE NULL END) as avg_score
        FROM oa_sessions
        WHERE candidate_id = %s
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (candidate_id,))
        result = cursor.fetchone()
        
        # Get submission count
        cursor.execute(
            "SELECT COUNT(*) FROM oa_submissions WHERE session_id IN (SELECT id FROM oa_sessions WHERE candidate_id = %s)",
            (candidate_id,)
        )
        submission_count = cursor.fetchone()[0]
        
        cursor.close()
        
        return {
            'total_sessions': result[0] or 0,
            'completed_sessions': result[1] or 0,
            'average_score': float(result[2]) if result[2] else 0.0,
            'total_submissions': submission_count or 0
        }

