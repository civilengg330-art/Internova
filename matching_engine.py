import os
import json
from google import genai
from google.genai import types

# Set your Gemini API key here or via environment variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

MATCHING_SYSTEM_INSTRUCTION = """
You are the AI Matching Engine for INTERNOVA, an intelligent university internship recommendation system.
Your job is to evaluate a Student Profile against an Internship Posting and calculate an accurate match score (0 to 100).

CRITICAL EVALUATION RULES:
1. SEMANTIC MATCHING (Domain & Skills):
   - Evaluate exact and relatable terms intelligently.
   - Exact term/skill match = 100% credit for that item.
   - Relatable/sister domain (e.g., "Project Engineering" vs "Project Management", or "ETABS" vs "RC Structural Design") = 80-90% credit.
   - Unrelated domain (e.g., "Civil Engineering" vs "Microbiology") = 0% credit.

2. STRICT LOCATION RULE:
   - Location matching is STRICTLY confined within the same city.
   - Same City & Same Sector/Neighborhood (e.g., Islamabad Sector G vs Sector G) = 100% location credit.
   - Same City & Nearby Sector (e.g., Islamabad Sector G vs Sector F) = 80% location credit.
   - Same City & Distant Sector (e.g., Islamabad Sector G vs Sector I) = 30% location credit.
   - Different Cities OR Outside the City = STRICT 0% location credit (No Match for location).

3. POINT BREAKDOWN (Total: 100 points):
   - Academic Fit & CGPA: Max 20 points
   - Technical Skills & Tools (Required & Preferred): Max 35 points
   - Projects, Experience & Certifications: Max 25 points
   - Areas of Interest: Max 10 points
   - Location & Work Mode Fit: Max 10 points

4. SCORE-TO-CATEGORY MAPPING:
   - 95 - 100: Exact Match
   - 80 - 94: Strong Match
   - 65 - 79: Good Match
   - 50 - 64: Related Match
   - 20 - 49: Poor Match
   - 0 - 19: No Match

OUTPUT FORMAT:
You MUST respond strictly in raw JSON without Markdown code blocks using this exact format:
{
  "score": <number between 0 and 100>,
  "category": "<Exact Match | Strong Match | Good Match | Related Match | Poor Match | No Match>",
  "criterion_breakdown": {
    "academic_fit": "<X>/20 - <brief note>",
    "technical_skills": "<X>/35 - <brief note>",
    "experience_projects": "<X>/25 - <brief note>",
    "areas_of_interest": "<X>/10 - <brief note>",
    "location_work_mode": "<X>/10 - <brief note>"
  },
  "explanation": "<2-3 sentences explaining the main reasons for the score, highlighting semantic matches and location evaluation>"
}
"""

def evaluate_match(internship_data: dict, student_data: dict) -> dict:
    prompt = f"""
    Evaluate the following student profile against the internship requirements.

    === INTERNSHIP DETAILS ===
    Title: {internship_data.get('internship_title')}
    Description: {internship_data.get('internship_desc')}
    Location: {internship_data.get('internship_location')}
    Work Mode: {internship_data.get('work_mode')}
    Required Degree: {internship_data.get('req_degree')}
    Min CGPA: {internship_data.get('min_cgpa')}
    Required Skills: {internship_data.get('req_skills')}
    Preferred Skills: {internship_data.get('pref_skills')}
    Preferred Interest: {internship_data.get('pref_interest')}
    Other Requirements: {internship_data.get('other_reqs')}

    === STUDENT PROFILE ===
    Name: {student_data.get('student_name')}
    Degree: {student_data.get('degree')}
    Department: {student_data.get('department')}
    CGPA: {student_data.get('cgpa')}
    Technical Skills: {student_data.get('tech_skills')}
    Interests: {student_data.get('interests')}
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
