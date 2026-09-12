import streamlit as st
import json
from database import (
    init_db, add_organization, get_organizations, 
    add_job, get_jobs_by_org, get_all_jobs, 
    add_student, get_all_students, 
    save_match_result, get_match_results
)
from matching_engine import evaluate_candidate

# Initialize database
init_db()

st.set_page_config(
    page_title="Internova - Internship Matching Platform",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Internova")
st.caption("AI-Driven Smart Internship Matching & Selection Platform")

# Sidebar Navigation
st.sidebar.title("Navigation")
portal = st.sidebar.radio("Navigate to Portal", ["Student Portal", "Organization Portal", "Coordinator Dashboard"])

# ==========================================
# 1. STUDENT PORTAL
# ==========================================
if portal == "Student Portal":
    st.header("🎓 Student Profile Registration")
    st.write("Submit your profile details to be evaluated for internship positions.")
    
    with st.form("student_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name *")
            email = st.text_input("Email Address *")
            phone = st.text_input("Phone Number")
            degree = st.text_input("Degree Program (e.g. BS Computer Science) *")
        with col2:
            cgpa = st.number_input("Current CGPA *", min_value=0.0, max_value=4.0, value=3.0, step=0.01)
            pref_location = st.text_input("Preferred Location (e.g. Islamabad)")
            pref_work_mode = st.selectbox("Preferred Work Mode", ["On-site", "Hybrid", "Remote"])
            
        skills = st.text_area("Technical & Soft Skills (comma separated) *", placeholder="Python, Machine Learning, Data Analysis, SQL")
        projects_exp = st.text_area("Key Projects / Work Experience", placeholder="Developed a web scraper using Python; Completed 2-month web dev internship.")
        certifications = st.text_area("Certifications & Achievements", placeholder="AWS Certified Cloud Practitioner, Coursera Machine Learning")
        interests = st.text_area("Career Interests / Goals", placeholder="Passionate about AI research, cloud architecture, and automation.")
        
        submitted = st.form_submit_button("Submit Profile")
        if submitted:
            if not name or not email or not degree or not skills:
                st.error("Please fill in all required fields (*).")
            else:
                student_data = {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "degree": degree,
                    "cgpa": cgpa,
                    "skills": skills,
                    "projects_exp": projects_exp,
                    "certifications": certifications,
                    "interests": interests,
                    "pref_location": pref_location,
                    "pref_work_mode": pref_work_mode
                }
                add_student(student_data)
                st.success(f"Profile for {name} registered successfully!")

# ==========================================
# 2. ORGANIZATION PORTAL
# ==========================================
elif portal == "Organization Portal":
    st.header("🏢 Organization & Internship Management")
    
    org_action = st.radio("Select Action", ["Register Organization", "Post New Internship"], horizontal=True)
    
    if org_action == "Register Organization":
        st.subheader("Register Organization Account")
        with st.form("org_reg_form"):
            org_name = st.text_input("Organization / Company Name *")
            contact_person = st.text_input("Contact Person Name *")
            email = st.text_input("Official Email *")
            phone = st.text_input("Contact Phone")
            password = st.text_input("Account Password *", type="password")
            
            reg_submitted = st.form_submit_button("Register Account")
            if reg_submitted:
                if not org_name or not email or not password:
                    st.error("Please fill in required fields (*).")
                else:
                    org_data = {
                        "org_name": org_name,
                        "contact_person": contact_person,
                        "email": email,
                        "phone": phone,
                        "password": password
                    }
                    if add_organization(org_data):
                        st.success("Organization registered successfully!")
                    else:
                        st.error("An account with this email already exists.")
                        
    elif org_action == "Post New Internship":
        st.subheader("Post an Internship Opportunity")
        orgs = get_organizations()
        if not orgs:
            st.info("No organizations registered yet. Please register an organization first.")
        else:
            org_options = {org["org_name"]: org["id"] for org in orgs}
            selected_org_name = st.selectbox("Select Organization", list(org_options.keys()))
            selected_org_id = org_options[selected_org_name]
            
            with st.form("job_form"):
                title = st.text_input("Internship Title *", placeholder="e.g. AI & Machine Learning Intern")
                description = st.text_area("Role Description *", placeholder="Details about responsibilities and day-to-day tasks...")
                
                col1, col2 = st.columns(2)
                with col1:
                    positions = st.number_input("Number of Positions", min_value=1, value=1)
                    duration = st.text_input("Duration", value="3 Months")
                    req_degree = st.text_input("Required Degree Field", placeholder="BS Computer Science")
                with col2:
                    location = st.text_input("Job Location", placeholder="Islamabad, Sector H-12")
                    work_mode = st.selectbox("Work Mode", ["On-site", "Hybrid", "Remote"])
                    min_cgpa = st.number_input("Minimum CGPA Requirement", min_value=0.0, max_value=4.0, value=2.5, step=0.1)
                    
                req_skills = st.text_area("Required Skills (comma separated) *", placeholder="Python, PyTorch, SQL")
                pref_skills = st.text_area("Preferred / Bonus Skills", placeholder="Docker, Git, Streamlit")
                
                job_submitted = st.form_submit_button("Post Internship")
                if job_submitted:
                    if not title or not description or not req_skills:
                        st.error("Please fill in all required fields (*).")
                    else:
                        job_data = {
                            "org_id": selected_org_id,
                            "title": title,
                            "description": description,
                            "positions": positions,
                            "duration": duration,
                            "location": location,
                            "work_mode": work_mode,
                            "req_degree": req_degree,
                            "min_cgpa": min_cgpa,
                            "req_skills": req_skills,
                            "pref_skills": pref_skills
                        }
                        add_job(job_data)
                        st.success(f"Internship position '{title}' posted successfully!")

# ==========================================
# 3. COORDINATOR DASHBOARD
# ==========================================
elif portal == "Coordinator Dashboard":
    st.header("📊 University Coordinator Dashboard")
    
    passcode = st.sidebar.text_input("Coordinator Passcode", type="password")
    if passcode != "admin123":
        st.warning("Please enter the correct passcode in the sidebar to access the dashboard. (Default passcode: admin123)")
    else:
        st.success("Authorized Access")
        
        tab1, tab2, tab3 = st.tabs(["🤖 AI Matcher", "🏢 Organizations & Listings", "🎓 Student Directory"])
        
        # --- TAB 1: AI Matcher ---
        with tab1:
            st.subheader("Run AI Matching Engine")
            all_jobs = get_all_jobs()
            all_students = get_all_students()
            
            if not all_jobs:
                st.info("No internship positions posted yet.")
            elif not all_students:
                st.info("No student profiles registered yet.")
            else:
                job_map = {f"{j['title']} at {j['org_name']} (ID: {j['id']})": j for j in all_jobs}
                selected_job_label = st.selectbox("Select Internship Position to Evaluate", list(job_map.keys()))
                selected_job = job_map[selected_job_label]
                
                if st.button("🤖 Run AI Matching Engine"):
                    with st.spinner("Evaluating candidates using Gemini AI..."):
                        progress_bar = st.progress(0)
                        results = []
                        
                        for idx, student in enumerate(all_students):
                            eval_result = evaluate_candidate(student, selected_job)
                            results.append({
                                "student_id": student["id"],
                                "student_name": student["name"],
                                "degree": student["degree"],
                                "score": eval_result.get("score", 0),
                                "category": eval_result.get("category", "No Match"),
                                "breakdown": eval_result.get("criterion_breakdown", {}),
                                "explanation": eval_result.get("explanation", "No evaluation available.")
                            })
                            progress_bar.progress((idx + 1) / len(all_students))
                            
                        results.sort(key=lambda x: x["score"], reverse=True)
                        st.session_state["match_results"] = results
                        st.success("AI Matching Evaluation Complete!")
                        
                if "match_results" in st.session_state:
                    st.write("---")
                    st.subheader("📊 Candidate Leaderboard")
                    
                    for idx, res in enumerate(st.session_state["match_results"]):
                        score = res["score"]
                        category = res["category"]
                        badge_color = "green" if score >= 80 else "orange" if score >= 60 else "red"
                        
                        with st.expander(f"#{idx+1} {res['student_name']} ({res['degree']}) — Score: {score}/100 — [{category}]"):
                            st.write(f"**AI Explanation:** {res['explanation']}")
                            st.write("**Criterion Breakdown:**")
                            st.json(res["breakdown"])
                            
                            if st.button(f"📌 Confirm Selection for {res['student_name']}", key=f"select_{res['student_id']}"):
                                save_match_result(res["student_id"], selected_job["id"], score, category, json.dumps(res["breakdown"]))
                                st.success(f"Confirmed selection for {res['student_name']}!")

        # --- TAB 2: Organizations & Listings ---
        with tab2:
            st.subheader("Registered Organizations & Job Postings")
            jobs = get_all_jobs()
            if jobs:
                st.dataframe(jobs, use_container_width=True)
            else:
                st.info("No organization job postings registered yet.")

        # --- TAB 3: Student Directory ---
        with tab3:
            st.subheader("Registered Student Profiles")
            students = get_all_students()
            if students:
                st.dataframe(students, use_container_width=True)
            else:
                st.info("No student profiles registered yet.")
