from db import get_db
from werkzeug.security import generate_password_hash
# ── Insert-reports-to-db ───────────────────────────────────────────────────

def insert_reports(tracking_id, ciphertext, category, filename, timestamp, nonce, tag, enc_key):
    db = get_db()
    db.execute("""
        INSERT INTO reports(tracking_id, encryptedtext, category, filename, timestamp, nonce, tag, enc_key, status, note)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, 'NEW', "No Note Created Yet")""",(tracking_id, ciphertext, category, filename, timestamp, nonce, tag, enc_key))
    db.commit()

# ── tracking-id-verifier ───────────────────────────────────────────────────

def tracking_id_exists(tracking_id):
    db = get_db()
    result = db.execute(
        "SELECT 1 FROM reports WHERE tracking_id = ?",
        (tracking_id,)
    ).fetchone()
    return result is not None

# ── Fetch-all-reports ───────────────────────────────────────────────────

def get_all_reports():
    db = get_db()
    rows = db.execute("SELECT * FROM reports").fetchall()
    return rows
    
def get_all_admins():
    db = get_db()
    rows = db.execute("SELECT * FROM admins").fetchall()
    return rows


# ── Status-of-report ───────────────────────────────────────────────────

def check_status(applicationID):
    db = get_db()
    return db.execute("SELECT status, note FROM reports WHERE tracking_id = ?", (applicationID,)).fetchone()

# ── Status-counter ───────────────────────────────────────────────────

def count_status():
    db = get_db()
    rows = db.execute(
        "SELECT status, COUNT(*) FROM reports GROUP BY status"
    ).fetchall()
    counts = {row[0] : row[1] for row in rows}
    return counts

# ── Blockchain ───────────────────────────────────────────────────

def update_tx_signature(tracking_id, tx_signature):
    db = get_db()
    db.execute(
        "UPDATE reports SET tx_signature = ? WHERE tracking_id = ?",
        (tx_signature, tracking_id)
    )
    db.commit()
 

# ── total-report-fetch ───────────────────────────────────────────────────

def total_reports():
    db = get_db()
    result = db.execute(
        "SELECT COUNT(*) FROM reports"
    ).fetchone()[0]

    return result

# ── display-all-report ───────────────────────────────────────────────────

def show_reports():
    db = get_db()
    return db.execute(
        "SELECT tracking_id, status, filename, timestamp, category FROM reports"
    ).fetchall()

# ── Admin-management ───────────────────────────────────────────────────

def admin_management(username, name, email, position, password_hash):
    db = get_db()
    db.execute(""" 
            INSERT INTO admins(username, name, email, position, password_hash)
            VALUES(?, ?, ?, ?, ?)""",(username, name, email, position, password_hash))
    db.commit()

# ── admin-verifier ───────────────────────────────────────────────────

def get_admin(admin_username):
    db = get_db()
    return db.execute(
        "SELECT username, name, email, position, password_hash FROM admins WHERE username = ?",(admin_username,)
    ).fetchone()

# ── Show-all-admins ───────────────────────────────────────────────────

def show_admins():
    db = get_db()
    return db.execute(
        "SELECT username, name, email, position FROM admins"
    ).fetchall()


def inr_admins():
    db = get_db()
    return db.execute("""
    INSERT OR IGNORE INTO admins (username, name, email, position, password_hash)
    VALUES (?, ?, ?, ?, ?)
""", (
    "admin",
    "Super Admin", 
    "admin@cipherdrop.com",
    "superadmin",
    generate_password_hash("changeme123")
))
