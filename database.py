import sqlite3

DB_NAME = "internova.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Organization Accounts Table (Login credentials)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS org_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_name TEXT NOT NULL,
            contact_person TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Internship Postings Table (Linked to org_accounts via org_id)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL,
            internship_title TEXT NOT NULL,
            internship_desc TEXT,
            num_positions INTEGER,
            duration TEXT,
            internship_location TEXT,
            work_mode TEXT,
            req_degree TEXT,
            min_cgpa REAL,
            req_skills TEXT,
            pref_skills TEXT,
            pref_interest TEXT,
            other_reqs TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (org_id) REFERENCES org_accounts (id)
        )
    ''')
    
    # 3. Students Table (with can_edit permission controlled by Coordinator)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            university TEXT,
            student_id TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            degree TEXT,
            department TEXT,
            current_semester TEXT,
            cgpa REAL,
            grad_year INTEGER,
            tech_skills TEXT,
            interests TEXT,
            projects_exp TEXT,
            certifications TEXT,
            other_skills TEXT,
            pref_location TEXT,
            pref_work_mode TEXT,
            other_prefs TEXT,
            can_edit INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 4. Final Selections Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS selections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            internship_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            match_score REAL,
            match_category TEXT,
            notes TEXT,
            selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (internship_id) REFERENCES organizations (id),
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Internova Database initialized successfully!")