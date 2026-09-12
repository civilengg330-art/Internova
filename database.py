import sqlite3
import json
import os
import streamlit as st

# Check if PostgreSQL URL exists in Secrets or Environment
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL and "DATABASE_URL" in st.secrets:
    DATABASE_URL = st.secrets.get("DATABASE_URL")

USE_PG = bool(DATABASE_URL)

if USE_PG:
    import psycopg2
    from psycopg2.extras import RealDictCursor

def get_connection():
    if USE_PG:
        return psycopg2.connect(DATABASE_URL)
    else:
        conn = sqlite3.connect("internova.db", check_same_thread=False)
        return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_PG:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id SERIAL PRIMARY KEY,
            org_name TEXT NOT NULL,
            contact_person TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            org_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            positions INTEGER DEFAULT 1,
            duration TEXT,
            location TEXT,
            work_mode TEXT,
            req_degree TEXT,
            min_cgpa REAL,
            req_skills TEXT,
            pref_skills TEXT
        );
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            degree TEXT NOT NULL,
            cgpa REAL NOT NULL,
            skills TEXT NOT NULL,
            projects_exp TEXT,
            certifications TEXT,
            interests TEXT,
            pref_location TEXT,
            pref_work_mode TEXT
        );
        CREATE TABLE IF NOT EXISTS match_results (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            score INTEGER NOT NULL,
            category TEXT NOT NULL,
            breakdown TEXT
        );
        """)
    else:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_name TEXT NOT NULL,
            contact_person TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            positions INTEGER DEFAULT 1,
            duration TEXT,
            location TEXT,
            work_mode TEXT,
            req_degree TEXT,
            min_cgpa REAL,
            req_skills TEXT,
            pref_skills TEXT
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            degree TEXT NOT NULL,
            cgpa REAL NOT NULL,
            skills TEXT NOT NULL,
            projects_exp TEXT,
            certifications TEXT,
            interests TEXT,
            pref_location TEXT,
            pref_work_mode TEXT
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            category TEXT NOT NULL,
            breakdown TEXT
        );
        """)

    conn.commit()
    conn.close()

def execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = get_connection()
    if USE_PG:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
    else:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
    try:
        cursor.execute(query, params)
        if commit:
            conn.commit()
            result = True
        elif fetchone:
            res = cursor.fetchone()
            result = dict(res) if res else None
        elif fetchall:
            res = cursor.fetchall()
            result = [dict(row) for row in res]
        else:
            result = True
    except Exception as e:
        print(f"Database error: {e}")
        result = False
    finally:
        conn.close()
    return result

# --- ORGANIZATION FUNCTIONS ---
def add_organization(org_data):
    query = """
        INSERT INTO organizations (org_name, contact_person, email, phone, password)
        VALUES (%s, %s, %s, %s, %s)
    """ if USE_PG else """
        INSERT INTO organizations (org_name, contact_person, email, phone, password)
        VALUES (?, ?, ?, ?, ?)
    """
    return execute_query(query, (
        org_data["org_name"], org_data["contact_person"], org_data["email"],
        org_data["phone"], org_data["password"]
    ), commit=True)

def verify_organization_login(email, password):
    query = "SELECT * FROM organizations WHERE email = %s AND password = %s" if USE_PG else "SELECT * FROM organizations WHERE email = ? AND password = ?"
    return execute_query(query, (email, password), fetchone=True)

def get_all_organizations():
    query = "SELECT id, org_name, contact_person, email, phone FROM organizations"
    return execute_query(query, fetchall=True) or []

def delete_organization(org_id):
    q1 = "DELETE FROM jobs WHERE org_id = %s" if USE_PG else "DELETE FROM jobs WHERE org_id = ?"
    q2 = "DELETE FROM organizations WHERE id = %s" if USE_PG else "DELETE FROM organizations WHERE id = ?"
    execute_query(q1, (org_id,), commit=True)
    return execute_query(q2, (org_id,), commit=True)

# --- JOB FUNCTIONS ---
def add_job(job_data):
    query = """
        INSERT INTO jobs (org_id, title, description, positions, duration, location, work_mode, req_degree, min_cgpa, req_skills, pref_skills)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """ if USE_PG else """
        INSERT INTO jobs (org_id, title, description, positions, duration, location, work_mode, req_degree, min_cgpa, req_skills, pref_skills)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    return execute_query(query, (
        job_data["org_id"], job_data["title"], job_data["description"], job_data["positions"],
        job_data["duration"], job_data["location"], job_data["work_mode"], job_data["req_degree"],
        job_data["min_cgpa"], job_data["req_skills"], job_data["pref_skills"]
    ), commit=True)

def update_job(job_id, job_data):
    query = """
        UPDATE jobs
        SET title=%s, description=%s, positions=%s, duration=%s, location=%s, work_mode=%s, req_degree=%s, min_cgpa=%s, req_skills=%s, pref_skills=%s
        WHERE id=%s
    """ if USE_PG else """
        UPDATE jobs
        SET title=?, description=?, positions=?, duration=?, location=?, work_mode=?, req_degree=?, min_cgpa=?, req_skills=?, pref_skills=?
        WHERE id=?
    """
    return execute_query(query, (
        job_data["title"], job_data["description"], job_data["positions"], job_data["duration"],
        job_data["location"], job_data["work_mode"], job_data["req_degree"], job_data["min_cgpa"],
        job_data["req_skills"], job_data["pref_skills"], job_id
    ), commit=True)

def delete_job(job_id):
    q1 = "DELETE FROM match_results WHERE job_id = %s" if USE_PG else "DELETE FROM match_results WHERE job_id = ?"
    q2 = "DELETE FROM jobs WHERE id = %s" if USE_PG else "DELETE FROM jobs WHERE id = ?"
    execute_query(q1, (job_id,), commit=True)
    return execute_query(q2, (job_id,), commit=True)

def get_jobs_by_org(org_id):
    query = "SELECT * FROM jobs WHERE org_id = %s" if USE_PG else "SELECT * FROM jobs WHERE org_id = ?"
    return execute_query(query, (org_id,), fetchall=True) or []

def get_all_jobs():
    query = """
        SELECT j.*, o.org_name
        FROM jobs j
        JOIN organizations o ON j.org_id = o.id
    """
    return execute_query(query, fetchall=True) or []

# --- STUDENT FUNCTIONS ---
def add_student(student_data):
    if USE_PG:
        query = """
            INSERT INTO students (name, email, phone, degree, cgpa, skills, projects_exp, certifications, interests, pref_location, pref_work_mode)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET
                name = EXCLUDED.name,
                phone = EXCLUDED.phone,
                degree = EXCLUDED.degree,
                cgpa = EXCLUDED.cgpa,
                skills = EXCLUDED.skills,
                projects_exp = EXCLUDED.projects_exp,
                certifications = EXCLUDED.certifications,
                interests = EXCLUDED.interests,
                pref_location = EXCLUDED.pref_location,
                pref_work_mode = EXCLUDED.pref_work_mode
        """
    else:
        query = """
            INSERT OR REPLACE INTO students (name, email, phone, degree, cgpa, skills, projects_exp, certifications, interests, pref_location, pref_work_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    return execute_query(query, (
        student_data["name"], student_data["email"], student_data["phone"], student_data["degree"],
        student_data["cgpa"], student_data["skills"], student_data["projects_exp"], student_data["certifications"],
        student_data["interests"], student_data["pref_location"], student_data["pref_work_mode"]
    ), commit=True)

def get_all_students():
    query = "SELECT * FROM students"
    return execute_query(query, fetchall=True) or []

def delete_student(student_id):
    q1 = "DELETE FROM match_results WHERE student_id = %s" if USE_PG else "DELETE FROM match_results WHERE student_id = ?"
    q2 = "DELETE FROM students WHERE id = %s" if USE_PG else "DELETE FROM students WHERE id = ?"
    execute_query(q1, (student_id,), commit=True)
    return execute_query(q2, (student_id,), commit=True)

# --- MATCH RESULTS FUNCTIONS ---
def save_match_result(student_id, job_id, score, category, breakdown):
    query = """
        INSERT INTO match_results (student_id, job_id, score, category, breakdown)
        VALUES (%s, %s, %s, %s, %s)
    """ if USE_PG else """
        INSERT INTO match_results (student_id, job_id, score, category, breakdown)
        VALUES (?, ?, ?, ?, ?)
    """
    return execute_query(query, (student_id, job_id, score, category, breakdown), commit=True)

def get_match_results(job_id):
    query = """
        SELECT mr.*, s.name as student_name, s.degree, s.email
        FROM match_results mr
        JOIN students s ON mr.student_id = s.id
        WHERE mr.job_id = %s
        ORDER BY mr.score DESC
    """ if USE_PG else """
        SELECT mr.*, s.name as student_name, s.degree, s.email
        FROM match_results mr
        JOIN students s ON mr.student_id = s.id
        WHERE mr.job_id = ?
        ORDER BY mr.score DESC
    """
    return execute_query(query, (job_id,), fetchall=True) or []
