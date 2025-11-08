"""
Judge0 API integration for code execution
Documentation: https://judge0.com/
"""
import requests
import time
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.logger import logger


# Language ID mapping for Judge0
LANGUAGE_MAP = {
    "python": 71,      # Python 3.8
    "javascript": 63,  # JavaScript (Node.js)
    "java": 62,        # Java (OpenJDK 13.0.1)
    "cpp": 54,         # C++ (GCC 9.2.0)
    "c": 50,           # C (GCC 9.2.0)
    "ruby": 72,        # Ruby (2.7.0)
    "go": 60,          # Go (1.13.5)
    "rust": 73,        # Rust (1.40.0)
    "kotlin": 78,      # Kotlin (1.3.70)
    "swift": 83,       # Swift (5.2.3)
    "typescript": 74,  # TypeScript (3.7.4)
}


class Judge0Client:
    """Client for Judge0 API"""
    
    def __init__(self):
        self.base_url = settings.judge0_url.rstrip('/')
        self.api_key = settings.judge0_api_key
        self.headers = {
            "Content-Type": "application/json"
        }
        # Only add RapidAPI headers if using RapidAPI (has API key)
        if self.api_key and settings.judge0_rapidapi_host:
            self.headers["X-RapidAPI-Key"] = self.api_key
            self.headers["X-RapidAPI-Host"] = settings.judge0_rapidapi_host
    
    def submit_code(
        self,
        source_code: str,
        language: str,
        stdin: Optional[str] = None,
        expected_output: Optional[str] = None,
        time_limit: float = 5.0,
        memory_limit: int = 128000  # KB
    ) -> Dict[str, Any]:
        """
        Submit code to Judge0 for execution
        
        Args:
            source_code: The code to execute
            language: Programming language (python, java, cpp, etc.)
            stdin: Standard input for the program
            expected_output: Expected output for comparison
            time_limit: CPU time limit in seconds
            memory_limit: Memory limit in KB
        
        Returns:
            Dictionary with submission token and initial status
        """
        language_id = LANGUAGE_MAP.get(language.lower())
        if not language_id:
            raise ValueError(f"Unsupported language: {language}")
        
        payload = {
            "source_code": source_code,
            "language_id": language_id,
            "stdin": stdin or "",
            "expected_output": expected_output or "",
            "cpu_time_limit": time_limit,
            "memory_limit": memory_limit
        }
        
        try:
            url = f"{self.base_url}/submissions?base64_encoded=false&wait=false"
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Code submitted to Judge0: token={result.get('token')}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to submit code to Judge0: {str(e)}")
            raise Exception(f"Judge0 submission failed: {str(e)}")
    
    def get_submission(self, token: str) -> Dict[str, Any]:
        """
        Get submission result from Judge0
        
        Args:
            token: Submission token from submit_code
        
        Returns:
            Dictionary with execution results
        """
        try:
            url = f"{self.base_url}/submissions/{token}?base64_encoded=false"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get submission from Judge0: {str(e)}")
            raise Exception(f"Judge0 get submission failed: {str(e)}")
    
    def wait_for_result(
        self,
        token: str,
        max_wait_time: int = 30,
        poll_interval: float = 1.0
    ) -> Dict[str, Any]:
        """
        Wait for submission to complete and return result
        
        Args:
            token: Submission token
            max_wait_time: Maximum time to wait in seconds
            poll_interval: Time between polls in seconds
        
        Returns:
            Final submission result
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            result = self.get_submission(token)
            status_id = result.get("status", {}).get("id")
            
            # Status IDs:
            # 1: In Queue, 2: Processing
            # 3: Accepted, 4: Wrong Answer, 5: Time Limit Exceeded
            # 6: Compilation Error, 7-14: Various runtime errors
            if status_id not in [1, 2]:  # Not queued or processing
                logger.info(
                    f"Submission {token} completed: "
                    f"status={result.get('status', {}).get('description')}"
                )
                return result
            
            time.sleep(poll_interval)
        
        logger.warning(f"Submission {token} timed out after {max_wait_time}s")
        return {
            "status": {"id": 13, "description": "Internal Error"},
            "error": "Execution timeout"
        }
    
    def execute_code(
        self,
        source_code: str,
        language: str,
        stdin: Optional[str] = None,
        expected_output: Optional[str] = None,
        time_limit: float = 5.0,
        memory_limit: int = 128000
    ) -> Dict[str, Any]:
        """
        Submit code and wait for result (convenience method)
        
        Returns:
            Complete execution result
        """
        submission = self.submit_code(
            source_code=source_code,
            language=language,
            stdin=stdin,
            expected_output=expected_output,
            time_limit=time_limit,
            memory_limit=memory_limit
        )
        
        token = submission.get("token")
        if not token:
            raise Exception("No token received from Judge0")
        
        return self.wait_for_result(token)
    
    def batch_submit(
        self,
        submissions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Submit multiple code submissions at once
        
        Args:
            submissions: List of submission dictionaries
        
        Returns:
            List of submission results with tokens
        """
        try:
            url = f"{self.base_url}/submissions/batch?base64_encoded=false"
            payload = {"submissions": submissions}
            
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Batch submission failed: {str(e)}")
            raise Exception(f"Judge0 batch submission failed: {str(e)}")


# Singleton instance
judge0_client = Judge0Client()


def run_test_cases(
    source_code: str,
    language: str,
    test_cases: List[Dict[str, str]],
    time_limit: float = 5.0,
    memory_limit: int = 128000
) -> Dict[str, Any]:
    """
    Run code against multiple test cases
    
    Args:
        source_code: The code to test
        language: Programming language
        test_cases: List of test cases with 'input' and 'expected_output'
        time_limit: CPU time limit per test case
        memory_limit: Memory limit in KB
    
    Returns:
        Dictionary with overall results and individual test case results
    """
    results = {
        "total_tests": len(test_cases),
        "passed": 0,
        "failed": 0,
        "error": 0,
        "test_results": []
    }
    
    for i, test_case in enumerate(test_cases):
        try:
            result = judge0_client.execute_code(
                source_code=source_code,
                language=language,
                stdin=test_case.get("input", ""),
                expected_output=test_case.get("expected_output", ""),
                time_limit=time_limit,
                memory_limit=memory_limit
            )
            
            status_id = result.get("status", {}).get("id")
            status_desc = result.get("status", {}).get("description")
            
            test_result = {
                "test_case": i + 1,
                "status": status_desc,
                "status_id": status_id,
                "passed": status_id == 3,  # 3 = Accepted
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "time": result.get("time", 0),
                "memory": result.get("memory", 0),
                "compile_output": result.get("compile_output", "")
            }
            
            if status_id == 3:
                results["passed"] += 1
            elif status_id == 4:  # Wrong Answer
                results["failed"] += 1
            else:  # Runtime errors, TLE, etc.
                results["error"] += 1
            
            results["test_results"].append(test_result)
            
        except Exception as e:
            logger.error(f"Test case {i+1} execution error: {str(e)}")
            results["error"] += 1
            results["test_results"].append({
                "test_case": i + 1,
                "status": "Error",
                "passed": False,
                "error": str(e)
            })
    
    results["all_passed"] = results["passed"] == results["total_tests"]
    results["pass_rate"] = results["passed"] / results["total_tests"] if results["total_tests"] > 0 else 0
    
    return results


def get_supported_languages() -> List[Dict[str, Any]]:
    """
    Get list of supported programming languages
    
    Returns:
        List of language dictionaries with name and ID
    """
    return [
        {"name": name, "id": lang_id, "display_name": name.capitalize()}
        for name, lang_id in LANGUAGE_MAP.items()
    ]

