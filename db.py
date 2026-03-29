import sqlite3
from werkzeug.security import generate_password_hash
from flask import current_app, g

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            timeout=10,
            check_same_thread=False
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()

    #report-table
    db.execute("""
        CREATE TABLE IF NOT EXISTS reports(
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               tracking_id TEXT UNIQUE NOT NULL,
               encryptedtext TEXT NOT NULL,
               category TEXT NOT NULL,
               filename TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
               timestamp TEXT NOT NULL,
               nonce TEXT,
               tag TEXT,
               enc_key TEXT,
               status TEXT NOT NULL,
               note TEXT,
               tx_signature TEXT DEFAULT NULL
               )
""")
    

    db.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            position TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    db.commit()
    db.execute("""
        INSERT OR IGNORE INTO admins (username, name, email, position, password_hash)
        VALUES (?, ?, ?, ?, ?)
    """, ("admin", "Super Admin", "admin@cipherdrop.com", "superadmin",
          generate_password_hash("changeme123")))
    db.commit()
