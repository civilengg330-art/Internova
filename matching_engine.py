import json
import os
from google import genai
from google.genai import types

client = genai.Client()

MATCHING_SYSTEM_INSTRUCTION = """
You are an expert AI Internship Placement Matching Engine for Internova.
Your job is to strictly analyze candidate profiles against internship requirements and evaluate match fitness.

You MUST respond in valid JSON format only, matching this structure:
{
    "score": 57,
    "category": "Potential Match",
    "criterion_breakdown": [
        {
            "criterion": "Degree & Academic Fit",
            "score_obtained": 20,
            "max_score": 20,
            "deduction_reason": "Perfect match in Civil Engineering degree program."
        },
        {
            "criterion": "CGPA Threshold",
            "score_obtained": 20,
            "max_score": 20,
            "deduction_reason": "Comfortably exceeds the minimum requirement with 3.0 CGPA."
        },
        {
            "criterion": "Skill Alignment",
            "score_obtained": 10,
            "max_score": 30,
            "deduction_reason": "Lacks required technical skills (Etabs, Revit), though possesses related software knowledge (SAP, AutoCAD)."
        },
        {
            "criterion": "Projects & Experience",
            "score_obtained": 0,
            "max_score": 15,
            "deduction_reason": "No relevant projects or certifications listed in profile."
        },
        {
            "criterion": "Location & Work Mode",
            "score_obtained": 7,
            "max_score": 15,
            "deduction_reason": "Conflict in work mode preferences (Candidate prefers On-site while position is Remote)."
        }
    ],
    "explanation": "Detailed professional reasoning behind the overall score."
}

Scoring Criteria Totals:
1. Degree & Academic Fit (Max 20)
2. CGPA Threshold (Max 20)
3. Skill Alignment (Max 30)
4. Projects & Experience (Max 15)
5. Location & Work Mode (Max 15)

Categories:
- "Strong Match" (Score 80-100)
- "Good Match" (Score 65-79)
- "Potential Match" (Score 50-64)
- "No Match" (Score < 50)
"""

def evaluate_candidate(student_data, job_data):
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
            "criterion_breakdown": [],
            "explanation": "Failed to run AI evaluation due to an API error."
        }
