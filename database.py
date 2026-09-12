import sqlite3

DB_NAME = "internova.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
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
            min_cgpa REAL DEFAULT 0.0,
            req_skills TEXT NOT NULL,
            pref_skills TEXT,
            FOREIGN KEY (org_id) REFERENCES organizations (id)
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
            score REAL NOT NULL,
            category TEXT NOT NULL,
            breakdown_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (job_id) REFERENCES jobs (id)
        )
    """)
    
    conn.commit()
    conn.close()

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
    finally:
        conn.close()

def get_organizations():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM organizations")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_job(job_data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs (org_id, title, description, positions, duration, location, work_mode, req_degree, min_cgpa, req_skills, pref_skills)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_data["org_id"],
        job_data["title"],
        job_data["description"],
        job_data["positions"],
        job_data["duration"],
        job_data["location"],
        job_data["work_mode"],
        job_data["req_degree"],
        job_data["min_cgpa"],
        job_data["req_skills"],
        job_data["pref_skills"]
    ))
    conn.commit()
    conn.close()

def get_jobs_by_org(org_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE org_id = ?", (org_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_jobs():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                jobs.id,
                jobs.org_id,
                jobs.title,
                jobs.description,
                jobs.positions,
                jobs.duration,
                jobs.location,
                jobs.work_mode,
                jobs.req_degree,
                jobs.min_cgpa,
                jobs.req_skills,
                jobs.pref_skills,
                COALESCE(organizations.org_name, 'Unknown Organization') as org_name
            FROM jobs 
            LEFT JOIN organizations ON jobs.org_id = organizations.id
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()

def add_student(student_data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO students (name, email, phone, degree, cgpa, skills, projects_exp, certifications, interests, pref_location, pref_work_mode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student_data["name"],
        student_data["email"],
        student_data["phone"],
        student_data["degree"],
        student_data["cgpa"],
        student_data["skills"],
        student_data["projects_exp"],
        student_data["certifications"],
        student_data["interests"],
        student_data["pref_location"],
        student_data["pref_work_mode"]
    ))
    conn.commit()
    conn.close()

def get_all_students():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM students")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()

def save_match_result(student_id, job_id, score, category, breakdown_json):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO match_results (student_id, job_id, score, category, breakdown_json)
        VALUES (?, ?, ?, ?, ?)
    """, (student_id, job_id, score, category, breakdown_json))
    conn.commit()
    conn.close()

def get_match_results():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT match_results.*, students.name as student_name, jobs.title as job_title
            FROM match_results
            LEFT JOIN students ON match_results.student_id = students.id
            LEFT JOIN jobs ON match_results.job_id = jobs.id
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()
