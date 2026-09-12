import json
import os
from google import genai
from google.genai import types

# Initialize client (uses GEMINI_API_KEY or GOOGLE_API_KEY from env/secrets)
client = genai.Client()

MATCHING_SYSTEM_INSTRUCTION = """
You are an expert AI Internship Placement Matching Engine for Internova.
Your job is to strictly analyze candidate profiles against internship requirements and evaluate match fitness.

You MUST respond in valid JSON format only, matching this structure:
{
    "score": 85,
    "category": "Strong Match",
    "criterion_breakdown": {
        "degree_fit": 20,
        "cgpa_fit": 20,
        "skills_fit": 25,
        "experience_fit": 10,
        "location_mode_fit": 10
    },
    "explanation": "Detailed professional reasoning behind the score."
}

Rules for scoring (Total 100):
1. Degree & Academic Fit (Max 20): Direct relevant major gets full marks.
2. CGPA Threshold (Max 20): Meets or exceeds min CGPA requirement.
3. Skill Alignment (Max 30): Match between required/preferred skills and student skills.
4. Projects & Certifications (Max 15): Relevant project experience.
5. Location & Work Mode (Max 15): Alignment with preferred location and work mode.

Categories:
- "Strong Match" (Score 80-100)
- "Good Match" (Score 65-79)
- "Potential Match" (Score 50-64)
- "No Match" (Score < 50)
"""

def evaluate_candidate(student_data, job_data):
    """
    Evaluates a single student profile against a specific internship job posting using Gemini.
    """
    prompt = f"""
    Please evaluate the following candidate for the given internship position.

    --- INTERNSHIP POSITION DETAILS ---
    Title: {job_data.get('title')}
    Description: {job_data.get('description')}
    Required Degree Field: {job_data.get('req_degree')}
    Min CGPA Requirement: {job_data.get('min_cgpa')}
    Required Skills: {job_data.get('req_skills')}
    Preferred Skills: {job_data.get('pref_skills')}
    Location: {job_data.get('location')}
    Work Mode: {job_data.get('work_mode')}

    --- STUDENT CANDIDATE PROFILE ---
    Name: {student_data.get('name')}
    Degree: {student_data.get('degree')}
    CGPA: {student_data.get('cgpa')}
    Technical & Soft Skills: {student_data.get('skills')}
    Career Interests: {student_data.get('interests')}
    Projects/Experience: {student_data.get('projects_exp')}
    Certifications: {student_data.get('certifications')}
    Preferred Location: {student_data.get('pref_location')}
    Preferred Work Mode: {student_data.get('pref_work_mode')}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=MATCHING_SYSTEM_INSTRUCTION,
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return {
            "score": 0,
            "category": "No Match",
            "criterion_breakdown": {"error": str(e)},
            "explanation": "Failed to run AI evaluation due to an API error."
        }
