import sqlite3
import json
import os

DB_FILE = "internova.db"
BACKUP_FILE = "data_backup.json"

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
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

    # Automatically restore data from JSON backup if database is empty
    restore_from_backup()

# --- BACKUP & RESTORE SYSTEM ---
def save_backup():
    """Export all tables into a JSON backup file."""
    data = {
        "organizations": get_all_organizations(),
        "jobs": execute_query("SELECT * FROM jobs", fetchall=True) or [],
        "students": get_all_students(),
        "match_results": execute_query("SELECT * FROM match_results", fetchall=True) or []
    }
    try:
        with open(BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving backup: {e}")

def restore_from_backup():
    """Restore records from JSON file if local database is empty upon reboot."""
    if not os.path.exists(BACKUP_FILE):
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM organizations")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return  # DB already populated

    try:
        with open(BACKUP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        for org in data.get("organizations", []):
            cursor.execute("""
                INSERT OR IGNORE INTO organizations (id, org_name, contact_person, email, phone, password)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (org["id"], org["org_name"], org["contact_person"], org["email"], org["phone"], org["password"]))

        for job in data.get("jobs", []):
            cursor.execute("""
                INSERT OR IGNORE INTO jobs (id, org_id, title, description, positions, duration, location, work_mode, req_degree, min_cgpa, req_skills, pref_skills)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (job["id"], job["org_id"], job["title"], job["description"], job["positions"], job["duration"], job["location"], job["work_mode"], job["req_degree"], job["min_cgpa"], job["req_skills"], job["pref_skills"]))

        for student in data.get("students", []):
            cursor.execute("""
                INSERT OR IGNORE INTO students (id, name, email, phone, degree, cgpa, skills, projects_exp, certifications, interests, pref_location, pref_work_mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (student["id"], student["name"], student["email"], student["phone"], student["degree"], student["cgpa"], student["skills"], student["projects_exp"], student["certifications"], student["interests"], student["pref_location"], student["pref_work_mode"]))

        for match in data.get("match_results", []):
            cursor.execute("""
                INSERT OR IGNORE INTO match_results (id, student_id, job_id, score, category, breakdown)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (match["id"], match["student_id"], match["job_id"], match["score"], match["category"], match.get("breakdown", "")))

        conn.commit()
    except Exception as e:
        print(f"Error restoring backup: {e}")
    finally:
        conn.close()

# --- HELPER QUERY EXECUTION ---
def execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = get_connection()
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
    query = "INSERT INTO organizations (org_name, contact_person, email, phone, password) VALUES (?, ?, ?, ?, ?)"
    res = execute_query(query, (org_data["org_name"], org_data["contact_person"], org_data["email"], org_data["phone"], org_data["password"]), commit=True)
    if res:
        save_backup()
    return res

def verify_organization_login(email, password):
    query = "SELECT * FROM organizations WHERE email = ? AND password = ?"
    return execute_query(query, (email, password), fetchone=True)

def get_all_organizations():
    return execute_query("SELECT id, org_name, contact_person, email, phone, password FROM organizations", fetchall=True) or []

def delete_organization(org_id):
    execute_query("DELETE FROM jobs WHERE org_id = ?", (org_id,), commit=True)
    res = execute_query("DELETE FROM organizations WHERE id = ?", (org_id,), commit=True)
    if res:
        save_backup()
    return res

# --- JOB FUNCTIONS ---
def add_job(job_data):
    query = """INSERT INTO jobs (org_id, title, description, positions, duration, location, work_mode, req_degree, min_cgpa, req_skills, pref_skills)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    res = execute_query(query, (job_data["org_id"], job_data["title"], job_data["description"], job_data["positions"], job_data["duration"], job_data["location"], job_data["work_mode"], job_data["req_degree"], job_data["min_cgpa"], job_data["req_skills"], job_data["pref_skills"]), commit=True)
    if res:
        save_backup()
    return res

def update_job(job_id, job_data):
    query = """UPDATE jobs SET title=?, description=?, positions=?, duration=?, location=?, work_mode=?, req_degree=?, min_cgpa=?, req_skills=?, pref_skills=? WHERE id=?"""
    res = execute_query(query, (job_data["title"], job_data["description"], job_data["positions"], job_data["duration"], job_data["location"], job_data["work_mode"], job_data["req_degree"], job_data["min_cgpa"], job_data["req_skills"], job_data["pref_skills"], job_id), commit=True)
    if res:
        save_backup()
    return res

def delete_job(job_id):
    execute_query("DELETE FROM match_results WHERE job_id = ?", (job_id,), commit=True)
    res = execute_query("DELETE FROM jobs WHERE id = ?", (job_id,), commit=True)
    if res:
        save_backup()
    return res

def get_jobs_by_org(org_id):
    query = "SELECT * FROM jobs WHERE org_id = ?"
    return execute_query(query, (org_id,), fetchall=True) or []

def get_all_jobs():
    query = "SELECT j.*, o.org_name FROM jobs j JOIN organizations o ON j.org_id = o.id"
    return execute_query(query, fetchall=True) or []

# --- STUDENT FUNCTIONS ---
def add_student(student_data):
    query = """INSERT OR REPLACE INTO students (name, email, phone, degree, cgpa, skills, projects_exp, certifications, interests, pref_location, pref_work_mode)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    res = execute_query(query, (student_data["name"], student_data["email"], student_data["phone"], student_data["degree"], student_data["cgpa"], student_data["skills"], student_data["projects_exp"], student_data["certifications"], student_data["interests"], student_data["pref_location"], student_data["pref_work_mode"]), commit=True)
    if res:
        save_backup()
    return res

def get_all_students():
    return execute_query("SELECT * FROM students", fetchall=True) or []

def delete_student(student_id):
    execute_query("DELETE FROM match_results WHERE student_id = ?", (student_id,), commit=True)
    res = execute_query("DELETE FROM students WHERE id = ?", (student_id,), commit=True)
    if res:
        save_backup()
    return res

# --- MATCH RESULTS FUNCTIONS ---
def save_match_result(student_id, job_id, score, category, breakdown):
    query = "INSERT INTO match_results (student_id, job_id, score, category, breakdown) VALUES (?, ?, ?, ?, ?)"
    res = execute_query(query, (student_id, job_id, score, category, breakdown), commit=True)
    if res:
        save_backup()
    return res

def get_match_results(job_id):
    query = "SELECT mr.*, s.name as student_name, s.degree, s.email FROM match_results mr JOIN students s ON mr.student_id = s.id WHERE mr.job_id = ? ORDER BY mr.score DESC"
    return execute_query(query, (job_id,), fetchall=True) or []
