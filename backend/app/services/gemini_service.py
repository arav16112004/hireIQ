"""
Gemini integration for TeamSero using Google's AI API (with JSON-enforced responses).
"""
import json
import re
from google import genai
from typing import Dict, List


class GeminiService:
    def __init__(self, api_key: str = None):
        from app.core.config import settings
        print("[DEBUG] Loading settings...")
        try:
            self.api_key = api_key or settings.GEMINI_API_KEY
            print(f"[DEBUG] API key loaded: {bool(self.api_key)}")

            if self.api_key:
                print(f"[DEBUG] API key: {bool(self.api_key)}")
                # ✅ Initialize new-style Gemini client
                self.client = genai.Client(api_key=self.api_key)
            else:
                print("[DEBUG] No API key found.")
                self.client = None

        except Exception as e:
            print(f"[DEBUG] Error loading API key: {str(e)}")
            self.client = None

    # -------------------------------------------------------------------------
    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API and return structured JSON text."""
        if not self.client:
            print("[DEBUG] No API client found - using fallback")
            return '{"skills": ["Python", "FastAPI", "SQL"], "summary": "Development mode", "fit_score": 88}'

        print("[DEBUG] Making API call to Gemini...")

        try:
            # Add strict instruction to return valid JSON
            structured_prompt = f"""
            {prompt}

            Respond ONLY with a valid JSON object using this exact format:
            {{
                "skills": ["skill1", "skill2", ...],
                "summary": "2–3 clear, professional sentences about the candidate",
                "fit_score": number between 0 and 100
            }}
            """

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",  # ✅ Correct model name
                contents=structured_prompt
            )

            print("[DEBUG] Got response from Gemini.")
            text = (response.text or "").strip()

            # --- Robust JSON extraction ---
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return match.group(0)

            print("[DEBUG] No JSON object detected in response.")
            return "{}"

        except Exception as e:
            print(f"[DEBUG] API call failed: {str(e)}")
            raise

    # -------------------------------------------------------------------------
    def test_api_key(self) -> bool:
        """Test if the Gemini API key works."""
        if not self.client:
            return False
        try:
            result = self._call_gemini("Respond with exactly 'ok' if you can read this.")
            print(f"[DEBUG] Test result: {result}")
            return "ok" in result.lower()
        except Exception as e:
            print(f"[DEBUG] Test failed: {str(e)}")
            return False

    # -------------------------------------------------------------------------
    def extract_skills(self, resume_text: str, job_desc: str = None) -> Dict:
        """Extract skills and compute fit score using Gemini."""
        prompt = f"""
        You are a professional HR analyst. Analyze the given resume against the job description and extract key information. Compute a fit score from 0 to 100 based on how 
        well the candidate's skills match the job requirements, and also .

        Your task:
        1. Extract all relevant skills from the resume
        2. Write a short, professional summary (2–3 sentences)
        3. Compute a fit_score (0–100) based on match quality

        Resume:
        {resume_text}

        Job Description:
        {job_desc if job_desc else 'Not provided'}
        """

        try:
            result = self._call_gemini(prompt)
            return json.loads(result)

        except json.JSONDecodeError:
            print("[DEBUG] JSON parsing failed — using fallback.")
            return {
                "skills": [],
                "summary": "Parsing error: Gemini returned non-JSON output.",
                "fit_score": 0
            }

        except Exception as e:
            print(f"[DEBUG] Skill extraction failed: {str(e)}")
            return {
                "skills": [],
                "summary": f"Error analyzing resume: {str(e)}",
                "fit_score": 0
            }

    # -------------------------------------------------------------------------
    def generate_questions(self, job_description: str, n: int = 5) -> List[Dict]:
        """Generate interview questions based on job description."""
        prompt = f"""
        Generate {n} interview questions for the following job description.
        Return a JSON array of questions, each with a "text" field.

        Job Description:
        {job_description}

        Respond with a JSON array in this format:
        [{{"text": "Question 1"}}, {{"text": "Question 2"}}, ...]
        """
        
        try:
            result = self._call_gemini(prompt)
            questions_data = json.loads(result)
            
            # Handle both array and object responses
            if isinstance(questions_data, list):
                return questions_data
            elif isinstance(questions_data, dict) and "questions" in questions_data:
                return questions_data["questions"]
            else:
                # Fallback: create simple questions
                return [{"text": f"Tell me about your experience with {job_description[:50]}..."} for _ in range(n)]
        except Exception as e:
            print(f"[DEBUG] Question generation failed: {str(e)}")
            # Return fallback questions
            return [{"text": f"Question {i+1}: Describe your relevant experience."} for i in range(n)]

    # -------------------------------------------------------------------------
    def evaluate_response(self, response_text: str) -> Dict:
        """Evaluate a candidate's response to an interview question."""
        prompt = f"""
        Evaluate the following interview response. Return a JSON object with:
        - "score": number between 0 and 100
        - "feedback": brief feedback on the response
        - "strengths": list of strengths
        - "improvements": list of areas for improvement

        Response:
        {response_text}
        """
        
        try:
            result = self._call_gemini(prompt)
            evaluation = json.loads(result)
            
            # Ensure required fields exist
            if "score" not in evaluation:
                evaluation["score"] = 75
            if "feedback" not in evaluation:
                evaluation["feedback"] = "Response received"
            
            return evaluation
        except Exception as e:
            print(f"[DEBUG] Response evaluation failed: {str(e)}")
            return {
                "score": 75,
                "feedback": "Evaluation pending",
                "strengths": [],
                "improvements": []
            }

    # -------------------------------------------------------------------------
    def rank_jobs(self, skills: List[str], jobs: List[Dict]) -> List[Dict]:
        """Rank jobs based on candidate skills."""
        if not skills or not jobs:
            return []
        
        skills_text = ", ".join(skills)
        jobs_text = "\n".join([
            f"Job {job.get('id')}: {job.get('title', '')} - {job.get('description', '')[:200]}"
            for job in jobs
        ])
        
        prompt = f"""
        Rank the following jobs based on how well they match these skills: {skills_text}
        
        Jobs:
        {jobs_text}
        
        Return a JSON array of job matches, each with:
        - "job_id": the job ID
        - "score": match score between 0 and 100
        - "matching_skills": list of matching skills
        - "explanation": brief explanation
        
        Format:
        [{{"job_id": 1, "score": 85, "matching_skills": ["skill1"], "explanation": "..."}}, ...]
        """
        
        try:
            result = self._call_gemini(prompt)
            matches = json.loads(result)
            
            # Handle both array and object responses
            if isinstance(matches, list):
                return matches
            elif isinstance(matches, dict) and "matches" in matches:
                return matches["matches"]
            else:
                # Fallback: simple scoring based on keyword matches
                return self._simple_job_ranking(skills, jobs)
        except Exception as e:
            print(f"[DEBUG] Job ranking failed: {str(e)}")
            return self._simple_job_ranking(skills, jobs)

    # -------------------------------------------------------------------------
    def _simple_job_ranking(self, skills: List[str], jobs: List[Dict]) -> List[Dict]:
        """Simple fallback ranking based on keyword matching."""
        matches = []
        for job in jobs:
            job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
            matching_skills = [skill for skill in skills if skill.lower() in job_text]
            score = len(matching_skills) / len(skills) * 100 if skills else 0
            
            matches.append({
                "job_id": job.get("id"),
                "score": score,
                "matching_skills": matching_skills,
                "explanation": f"Matched {len(matching_skills)} out of {len(skills)} skills"
            })
        
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches
