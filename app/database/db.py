import os
import json
import sqlite3

DB_PATH = os.path.normpath("data/gitimpact.db")


def get_db_connection():
    """Initializes and returns a SQLite connection for caching analyzed repositories."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Sets up the repository cache tables if they do not exist."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS repos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_name TEXT UNIQUE NOT NULL,
                owner TEXT NOT NULL,
                repo_url TEXT NOT NULL,
                tech_stack TEXT,
                total_files INTEGER DEFAULT 0,
                total_sql INTEGER DEFAULT 0,
                directories_json TEXT,
                entry_points_json TEXT,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def save_repo_metadata(repo_name: str, owner: str, repo_url: str, scan_result: dict):
    """Saves or updates repository metadata in the database."""
    init_db()
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO repos (
                repo_name, owner, repo_url, tech_stack,
                total_files, total_sql, directories_json, entry_points_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(repo_name) DO UPDATE SET
                tech_stack=excluded.tech_stack,
                total_files=excluded.total_files,
                total_sql=excluded.total_sql,
                directories_json=excluded.directories_json,
                entry_points_json=excluded.entry_points_json,
                analyzed_at=CURRENT_TIMESTAMP
        """, (
            repo_name,
            owner,
            repo_url,
            json.dumps(scan_result.get("tech_stack", [])),
            scan_result.get("total_code_files", 0),
            scan_result.get("total_sql_files", 0),
            json.dumps(scan_result.get("directory_map", {})),
            json.dumps(scan_result.get("entry_points", []))
        ))
        conn.commit()


def get_cached_repo(repo_name: str) -> dict | None:
    """Retrieves cached repository metadata by repo name."""
    init_db()
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM repos WHERE repo_name = ?", (repo_name,)).fetchone()
        if row:
            return {
                "repo_name": row["repo_name"],
                "owner": row["owner"],
                "repo_url": row["repo_url"],
                "tech_stack": json.loads(row["tech_stack"] or "[]"),
                "total_files": row["total_files"],
                "total_sql": row["total_sql"],
                "directory_map": json.loads(row["directories_json"] or "{}"),
                "entry_points": json.loads(row["entry_points_json"] or "[]"),
                "analyzed_at": row["analyzed_at"]
            }
    return None
