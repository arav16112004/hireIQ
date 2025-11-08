"""
Gemini integration for TeamSero using Google's AI API (with JSON-enforced responses).
"""
import json
import re
from google import genai
from typing import Dict


class GeminiService:
    def __init__(self):
        from backend.app.core.config import settings
        print("[DEBUG] Loading settings...")
        try:
            self.api_key = settings.GEMINI_API_KEY
            print(f"[DEBUG] API key loaded: {bool(self.api_key)}")

            if self.api_key:
                print(f"[DEBUG] API key: {self.api_key}")
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
