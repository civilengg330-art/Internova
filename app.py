import streamlit as st
import pandas as pd
import json
import sqlite3
import database
from matching_engine import evaluate_match

# Page Configuration
st.set_page_config(page_title="Internova - AI Internship Matching", layout="wide")

# Ensure database tables exist
database.init_db()

def get_db():
    return database.get_connection()

# Sidebar Navigation
st.sidebar.title("🚀 INTERNOVA")
portal = st.sidebar.radio("Navigate to Portal", ["Student Portal", "Organization Portal", "Coordinator Dashboard"])

# ==========================================
# 1. STUDENT PORTAL
# ==========================================
if portal == "Student Portal":
    st.title("👨‍🎓 Student Portal")
    st.markdown("Submit or manage your profile for AI-based internship matching.")
    
    action = st.radio("Choose Action", ["New Profile Submission", "Lookup / Update Existing Profile"], horizontal=True)
    
    if action == "New Profile Submission":
        st.subheader("Create Student Profile")
        with st.form("new_student_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name *")
                s_id = st.text_input("Student ID / Roll No *")
                email = st.text_input("Email Address *")
                phone = st.text_input("Phone Number")
                university = st.text_input("University")
                degree = st.text_input("Degree Program (e.g., BS Civil Engineering)")
            with col2:
                dept = st.text_input("Department")
                semester = st.text_input("Current Semester")
                cgpa = st.number_input("CGPA", min_value=0.0, max_value=4.0, value=3.0, step=0.01)
                grad_year = st.number_input("Graduation Year", min_value=2024, max_value=2030, value=2025)
                pref_loc = st.text_input("Preferred Location (City, Sector)")
                pref_mode = st.selectbox("Preferred Work Mode", ["On-site", "Remote", "Hybrid"])

            st.markdown("---")
            tech_skills = st.text_area("Technical Skills (e.g., Python, ETABS, AutoCAD, Structural Analysis)")
            interests = st.text_area("Areas of Interest")
            projects = st.text_area("Projects & Experience")
            certs = st.text_area("Certifications & Other Skills")
            
            submit = st.form_submit_button("Submit Profile")
            
            if submit:
                if not name or not s_id or not email:
                    st.error("Please fill in all required fields marked with *.")
                else:
                    conn = get_db()
                    c = conn.cursor()
                    try:
                        c.execute('''
                            INSERT INTO students (student_name, university, student_id, email, phone, degree, department, current_semester, cgpa, grad_year, tech_skills, interests, projects_exp, certifications, pref_location, pref_work_mode, can_edit)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                        ''', (name, university, s_id, email, phone, degree, dept, semester, cgpa, grad_year, tech_skills, interests, projects, certs, pref_loc, pref_mode))
                        conn.commit()
                        st.success("Profile submitted successfully! Your profile is now locked for matching.")
                    except sqlite3.IntegrityError:
                        st.error("A student profile with this Student ID or Email already exists.")
                    finally:
                        conn.close()

    elif action == "Lookup / Update Existing Profile":
        st.subheader("Profile Lookup")
        search_id = st.text_input("Enter Student ID or Email")
        if st.button("Search Profile"):
            conn = get_db()
            student = conn.execute("SELECT * FROM students WHERE student_id = ? OR email = ?", (search_id, search_id)).fetchone()
            conn.close()
            if student:
                st.session_state['active_student'] = dict(student)
            else:
                st.error("No student profile found with those credentials.")

        if 'active_student' in st.session_state:
            s = st.session_state['active_student']
            st.markdown("---")
            st.subheader(f"Profile: {s['student_name']}")
            
            if s['can_edit'] == 0:
                st.warning("🔒 Your profile is currently **LOCKED** by the Coordinator. You can view your details below, but editing is disabled.")
                st.write(f"**Degree:** {s['degree']} | **CGPA:** {s['cgpa']}")
                st.write(f"**Technical Skills:** {s['tech_skills']}")
                st.write(f"**Preferred Location:** {s['pref_location']}")
            else:
                st.success("🔓 Your profile is **UNLOCKED**. You can update your details below.")
                with st.form("edit_student_form"):
                    u_cgpa = st.number_input("CGPA", min_value=0.0, max_value=4.0, value=float(s['cgpa']), step=0.01)
                    u_skills = st.text_area("Technical Skills", value=s['tech_skills'] or "")
                    u_projects = st.text_area("Projects & Experience", value=s['projects_exp'] or "")
                    u_loc = st.text_input("Preferred Location", value=s['pref_location'] or "")
                    
                    if st.form_submit_button("Update Profile"):
                        conn = get_db()
                        conn.execute("UPDATE students SET cgpa=?, tech_skills=?, projects_exp=?, pref_location=? WHERE id=?", 
                                     (u_cgpa, u_skills, u_projects, u_loc, s['id']))
                        conn.commit()
                        conn.close()
                        st.success("Profile updated successfully!")

# ==========================================
# 2. ORGANIZATION PORTAL
# ==========================================
elif portal == "Organization Portal":
    st.title("🏢 Organization Portal")
    
    org_auth_mode = st.radio("Action", ["Login", "Register Organization"], horizontal=True)
    
    if org_auth_mode == "Register Organization":
        st.subheader("Organization Account Registration")
        with st.form("reg_org"):
            org_name = st.text_input("Organization Name *")
            contact_person = st.text_input("Contact Person Name *")
            email = st.text_input("Official Email *")
            phone = st.text_input("Phone Number *")
            pwd = st.text_input("Password *", type="password")
            
            if st.form_submit_button("Register"):
                if not org_name or not email or not pwd:
                    st.error("Please fill in all required fields.")
                else:
                    conn = get_db()
                    try:
                        conn.execute("INSERT INTO org_accounts (org_name, contact_person, email, phone, password) VALUES (?, ?, ?, ?, ?)",
                                     (org_name, contact_person, email, phone, pwd))
                        conn.commit()
                        st.success("Account registered successfully! Please log in.")
                    except sqlite3.IntegrityError:
                        st.error("An account with this email already exists.")
                    finally:
                        conn.close()

    elif org_auth_mode == "Login":
        st.subheader("Organization Login")
        l_email = st.text_input("Email")
        l_pwd = st.text_input("Password", type="password")
        
        if st.button("Login"):
            conn = get_db()
            account = conn.execute("SELECT * FROM org_accounts WHERE email = ? AND password = ?", (l_email, l_pwd)).fetchone()
            conn.close()
            if account:
                st.session_state['logged_org'] = dict(account)
                st.success(f"Welcome back, {account['org_name']}!")
            else:
                st.error("Invalid email or password.")

        if 'logged_org' in st.session_state:
            org = st.session_state['logged_org']
            st.markdown("---")
            st.subheader(f"Post Internship Position — {org['org_name']}")
            
            with st.form("post_internship_form"):
                title = st.text_input("Internship Title * (e.g., Structural Engineer Intern)")
                desc = st.text_area("Job Description")
                col1, col2, col3 = st.columns(3)
                with col1:
                    positions = st.number_input("Number of Positions", min_value=1, value=1)
                    duration = st.text_input("Duration (e.g., 3 Months)")
                with col2:
                    location = st.text_input("Location (e.g., Islamabad, Sector G-10)")
                    mode = st.selectbox("Work Mode", ["On-site", "Remote", "Hybrid"])
                with col3:
                    req_degree = st.text_input("Required Degree")
                    min_cgpa = st.number_input("Minimum CGPA", min_value=0.0, max_value=4.0, value=2.5, step=0.1)
                
                req_skills = st.text_area("Required Skills * (e.g., ETABS, AutoCAD)")
                pref_skills = st.text_area("Preferred Skills")
                
                if st.form_submit_button("Post Internship"):
                    if not title or not req_skills:
                        st.error("Title and Required Skills are mandatory.")
                    else:
                        conn = get_db()
                        conn.execute('''
                            INSERT INTO organizations (org_id, internship_title, internship_desc, num_positions, duration, internship_location, work_mode, req_degree, min_cgpa, req_skills, pref_skills)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (org['id'], title, desc, positions, duration, location, mode, req_degree, min_cgpa, req_skills, pref_skills))
                        conn.commit()
                        conn.close()
                        st.success("Internship opening posted successfully!")

# ==========================================
# 3. COORDINATOR DASHBOARD
# ==========================================
elif portal == "Coordinator Dashboard":
    st.title("👔 Coordinator Dashboard")
    passcode = st.sidebar.text_input("Coordinator Passcode", type="password")
    
    if passcode != "admin123":
        st.warning("Please enter the valid Coordinator Passcode in the sidebar to access the dashboard.")
    else:
        tab1, tab2 = st.tabs(["📊 AI Candidate Matching", "🔓 Student Lock/Unlock Control"])
        
        # TAB 1: AI MATCHING ENGINE & LEADERBOARD
        with tab1:
            st.subheader("Select Internship Position to Run AI Match")
            conn = get_db()
            postings = conn.execute("SELECT o.id, o.internship_title, o.internship_location, a.org_name FROM organizations o JOIN org_accounts a ON o.org_id = a.id").fetchall()
            conn.close()
            
            if not postings:
                st.info("No internship postings found in the database.")
            else:
                posting_options = {f"{p['org_name']} — {p['internship_title']} ({p['internship_location']})": p['id'] for p in postings}
                selected_label = st.selectbox("Choose Internship Posting", list(posting_options.keys()))
                selected_post_id = posting_options[selected_label]
                
                if st.button("🤖 Run AI Matching Engine"):
                    with st.spinner("AI Engine evaluating student candidates..."):
                        conn = get_db()
                        posting_data = dict(conn.execute("SELECT * FROM organizations WHERE id = ?", (selected_post_id,)).fetchone())
                        all_students = [dict(s) for s in conn.execute("SELECT * FROM students").fetchall()]
                        conn.close()
                        
                        results = []
                        for s in all_students:
                            ai_eval = evaluate_match(posting_data, s)
                            results.append({
                                "student_id": s['id'],
                                "name": s['student_name'],
                                "degree": s['degree'],
                                "cgpa": s['cgpa'],
                                "score": ai_eval.get("score", 0),
                                "category": ai_eval.get("category", "No Match"),
                                "breakdown": ai_eval.get("criterion_breakdown", {}),
                                "explanation": ai_eval.get("explanation", "")
                            })
                        
                        # Sort descending by score
                        results.sort(key=lambda x: x['score'], reverse=True)
                        st.session_state['match_results'] = results

                if 'match_results' in st.session_state:
                    st.markdown("---")
                    st.subheader("📊 Candidate Leaderboard")
                    
                    for idx, res in enumerate(st.session_state['match_results'], start=1):
                        col1, col2, col3, col4 = st.columns([1, 4, 2, 2])
                        col1.write(f"**#{idx}**")
                        col2.write(f"**{res['name']}** ({res['degree']})")
                        col3.write(f"Score: **{res['score']} / 100**")
                        col4.write(f"Category: `{res['category']}`")
                        
                        with st.expander(f"View Evaluation Details for {res['name']}"):
                            st.write("**AI Explanation:**", res['explanation'])
                            st.write("**Criterion Breakdown:**")
                            st.json(res['breakdown'])
                            
                            if st.button(f"📌 Confirm Selection for {res['name']}", key=f"select_{res['student_id']}"):
                                conn = get_db()
                                conn.execute("INSERT INTO selections (internship_id, student_id, match_score, match_category) VALUES (?, ?, ?, ?)",
                                             (selected_post_id, res['student_id'], res['score'], res['category']))
                                conn.commit()
                                conn.close()
                                st.success(f"Selected {res['name']} for this internship position!")

        # TAB 2: LOCK / UNLOCK STUDENTS
        with tab2:
            st.subheader("Manage Student Editing Permissions")
            conn = get_db()
            students = conn.execute("SELECT id, student_name, student_id, email, can_edit FROM students").fetchall()
            conn.close()
            
            if students:
                for s in students:
                    col1, col2, col3 = st.columns([3, 2, 2])
                    col1.write(f"**{s['student_name']}** ({s['student_id']})")
                    col2.write("Status: " + ("🟢 Unlocked" if s['can_edit'] == 1 else "🔒 Locked"))
                    
                    btn_label = "Lock Profile" if s['can_edit'] == 1 else "Unlock Profile"
                    new_val = 0 if s['can_edit'] == 1 else 1
                    if col3.button(btn_label, key=f"perm_{s['id']}"):
                        conn = get_db()
                        conn.execute("UPDATE students SET can_edit = ? WHERE id = ?", (new_val, s['id']))
                        conn.commit()
                        conn.close()
                        st.rerun()
            else:
                st.info("No students registered in the database yet.")