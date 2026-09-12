import sqlite3
import json

DB_NAME = "internova.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create Organizations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS organizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_name TEXT NOT NULL,
        contact_person TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        password TEXT NOT NULL
    )
    """)
    
    # Create Jobs table
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
        pref_skills TEXT,
        FOREIGN KEY (org_id) REFERENCES organizations (id) ON DELETE CASCADE
    )
    """)
    
    # Create Students table
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
    )
    """)
    
    # Create Match Results table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS match_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        job_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        category TEXT NOT NULL,
        breakdown TEXT,
        FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    conn.close()

# --- ORGANIZATION & JOB FUNCTIONS ---
def add_organization(org_data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO organizations (org_name, contact_person, email, phone, password)
            VALUES (?, ?, ?, ?, ?)
        """, (
            org_data["org_name"],
            org_data["contact_person"],
            org_data["email"],
            org_data["phone"],
            org_data["password"]
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.OperationalError:
        conn.close()
        init_db()
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO organizations (org_name, contact_person, email, phone, password)
                VALUES (?, ?, ?, ?, ?)
            """, (
                org_data["org_name"],
                org_data["contact_person"],
                org_data["email"],
                org_data["phone"],
                org_data["password"]
            ))
            conn.commit()
            return True
        except Exception:
            return False
    finally:
        conn.close()

def verify_organization_login(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM organizations WHERE email = ? AND password = ?", (email, password))
    org = cursor.fetchone()
    conn.close()
    return dict(org) if org else None

def add_job(job_data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs (org_id, title, description, positions, duration, location, work_mode, req_degree, min_cgpa, req_skills, pref_skills)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_data["org_id"], job_data["title"], job_data["description"], job_data["positions"],
        job_data["duration"], job_data["location"], job_data["work_mode"], job_data["req_degree"],
        job_data["min_cgpa"], job_data["req_skills"], job_data["pref_skills"]
    ))
    conn.commit()
    conn.close()

def update_job(job_id, job_data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE jobs
        SET title=?, description=?, positions=?, duration=?, location=?, work_mode=?, req_degree=?, min_cgpa=?, req_skills=?, pref_skills=?
        WHERE id=?
    """, (
        job_data["title"], job_data["description"], job_data["positions"], job_data["duration"],
        job_data["location"], job_data["work_mode"], job_data["req_degree"], job_data["min_cgpa"],
        job_data["req_skills"], job_data["pref_skills"], job_id
    ))
    conn.commit()
    conn.close()

def delete_organization(org_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs WHERE org_id = ?", (org_id,))
    cursor.execute("DELETE FROM organizations WHERE id = ?", (org_id,))
    conn.commit()
    conn.close()

def delete_job(job_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    cursor.execute("DELETE FROM match_results WHERE job_id = ?", (job_id,))
    conn.commit()
    conn.close()

def delete_student(student_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    cursor.execute("DELETE FROM match_results WHERE student_id = ?", (student_id,))
    conn.commit()
    conn.close()

def get_jobs_by_org(org_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE org_id = ?", (org_id,))
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jobs

def get_all_jobs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT j.*, o.org_name
        FROM jobs j
        JOIN organizations o ON j.org_id = o.id
    """)
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jobs

def get_all_organizations():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, org_name, contact_person, email, phone FROM organizations")
    orgs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return orgs

# --- STUDENT FUNCTIONS ---
def add_student(student_data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO students (name, email, phone, degree, cgpa, skills, projects_exp, certifications, interests, pref_location, pref_work_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_data["name"], student_data["email"], student_data["phone"], student_data["degree"],
            student_data["cgpa"], student_data["skills"], student_data["projects_exp"], student_data["certifications"],
            student_data["interests"], student_data["pref_location"], student_data["pref_work_mode"]
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        cursor.execute("""
            UPDATE students
            SET name=?, phone=?, degree=?, cgpa=?, skills=?, projects_exp=?, certifications=?, interests=?, pref_location=?, pref_work_mode=?
            WHERE email=?
        """, (
            student_data["name"], student_data["phone"], student_data["degree"], student_data["cgpa"],
            student_data["skills"], student_data["projects_exp"], student_data["certifications"], student_data["interests"],
            student_data["pref_location"], student_data["pref_work_mode"], student_data["email"]
        ))
        conn.commit()
    finally:
        conn.close()

def get_all_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    students = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return students

# --- MATCH RESULTS FUNCTIONS ---
def save_match_result(student_id, job_id, score, category, breakdown):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO match_results (student_id, job_id, score, category, breakdown)
        VALUES (?, ?, ?, ?, ?)
    """, (student_id, job_id, score, category, breakdown))
    conn.commit()
    conn.close()

def get_match_results(job_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT mr.*, s.name as student_name, s.degree, s.email
        FROM match_results mr
        JOIN students s ON mr.student_id = s.id
        WHERE mr.job_id = ?
        ORDER BY mr.score DESC
    """, (job_id,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results
