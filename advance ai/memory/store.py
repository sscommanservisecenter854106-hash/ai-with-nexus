import sqlite3
import json
import uuid
import datetime
import hashlib
import secrets
from typing import List, Dict, Optional, Any, Tuple
from config import DB_FILE

def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return pwd_hash, salt

def verify_password(password: str, pwd_hash: str, salt: str) -> bool:
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, pwd_hash)

class MemoryStore:
    def __init__(self, db_path: str = str(DB_FILE)):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Auth tokens table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_tokens (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    user_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Check if user_id column exists in sessions (for migrations)
            cursor.execute("PRAGMA table_info(sessions)")
            columns = [row["name"] for row in cursor.fetchall()]
            if "user_id" not in columns:
                try:
                    cursor.execute("ALTER TABLE sessions ADD COLUMN user_id TEXT")
                except Exception:
                    pass

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    thoughts TEXT DEFAULT '',
                    tool_calls TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    # --- User Authentication Methods ---

    def register_user(self, email: str, password: str) -> Dict[str, Any]:
        email = email.strip().lower()
        if not email or "@" not in email or "." not in email:
            raise ValueError("Please provide a valid email address.")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")

        pwd_hash, salt = hash_password(password)
        user_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                raise ValueError("An account with this email already exists.")

            cursor.execute(
                "INSERT INTO users (id, email, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, email, pwd_hash, salt, now)
            )
            
            token = secrets.token_urlsafe(32)
            cursor.execute(
                "INSERT INTO auth_tokens (token, user_id, created_at) VALUES (?, ?, ?)",
                (token, user_id, now)
            )
            conn.commit()

        return {
            "token": token,
            "user": {"id": user_id, "email": email}
        }

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        email = email.strip().lower()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, email, password_hash, salt FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if not row:
                return None

            if not verify_password(password, row["password_hash"], row["salt"]):
                return None

            user_id = row["id"]
            token = secrets.token_urlsafe(32)
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            cursor.execute(
                "INSERT INTO auth_tokens (token, user_id, created_at) VALUES (?, ?, ?)",
                (token, user_id, now)
            )
            conn.commit()

        return {
            "token": token,
            "user": {"id": user_id, "email": email}
        }

    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        if not token:
            return None
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.email, u.created_at
                FROM users u
                INNER JOIN auth_tokens t ON u.id = t.user_id
                WHERE t.token = ?
            """, (token,))
            row = cursor.fetchone()
            if row:
                return {"id": row["id"], "email": row["email"]}
            return None

    def delete_token(self, token: str) -> bool:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
            conn.commit()
            return cursor.rowcount > 0

    # --- Session & Message Methods ---

    def create_session(self, title: str = "New Conversation", user_id: Optional[str] = None) -> str:
        session_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (id, title, user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, title, user_id, now, now)
            )
            conn.commit()
        return session_id

    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute(
                    "SELECT id, title, user_id, created_at, updated_at FROM sessions WHERE user_id = ? ORDER BY updated_at DESC",
                    (user_id,)
                )
            else:
                cursor.execute("SELECT id, title, user_id, created_at, updated_at FROM sessions ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def delete_session(self, session_id: str, user_id: Optional[str] = None) -> bool:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT id FROM sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
                if not cursor.fetchone():
                    return False
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0

    def update_session_title(self, session_id: str, title: str, user_id: Optional[str] = None):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute(
                    "UPDATE sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                    (title, session_id, user_id)
                )
            else:
                cursor.execute(
                    "UPDATE sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (title, session_id)
                )
            conn.commit()

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        thoughts: str = "",
        tool_calls: Optional[List[dict]] = None,
        user_id: Optional[str] = None
    ) -> str:
        msg_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        tool_calls_json = json.dumps(tool_calls or [])

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO sessions (id, title, user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                    (session_id, content[:35] or "New Conversation", user_id, now, now)
                )

            cursor.execute(
                """
                INSERT INTO messages (id, session_id, role, content, thoughts, tool_calls, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (msg_id, session_id, role, content, thoughts, tool_calls_json, now)
            )
            cursor.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
            conn.commit()
        return msg_id

    def get_messages(self, session_id: str, limit: int = 50, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT id FROM sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
                if not cursor.fetchone():
                    return []

            cursor.execute(
                """
                SELECT id, session_id, role, content, thoughts, tool_calls, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (session_id, limit)
            )
            rows = cursor.fetchall()
            result = []
            for r in rows:
                item = dict(r)
                try:
                    item["tool_calls"] = json.loads(item["tool_calls"])
                except Exception:
                    item["tool_calls"] = []
                result.append(item)
            return result
