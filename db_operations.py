from db import get_db

def insert_reports(tracking_id, ciphertext, category, filename, timestamp, nonce, tag, enc_key):
    db = get_db()
    db.execute("""
        INSERT INTO reports(tracking_id, encryptedtext, category, filename, timestamp, nonce, tag, enc_key, status, note)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, 'NEW', "No Note Created Yet")""",(tracking_id, ciphertext, category, filename, timestamp, nonce, tag, enc_key))
    db.commit()

def tracking_id_exists(tracking_id):
    db = get_db()
    result = db.execute(
        "SELECT 1 FROM reports WHERE tracking_id = ?",
        (tracking_id,)
    ).fetchone()
    return result is not None

def get_all_reports():
    db = get_db()
    rows = db.execute("SELECT * FROM reports").fetchall()
    return rows

def check_status(applicationID):
    db = get_db()
    return db.execute("SELECT status, note FROM reports WHERE tracking_id = ?", (applicationID,)).fetchone()

def count_status():
    db = get_db()
    rows = db.execute(
        "SELECT status, COUNT(*) FROM reports GROUP BY status"
    ).fetchall()
    counts = {row[0] : row[1] for row in rows}
    return counts

def total_reports():
    db = get_db()
    result = db.execute(
        "SELECT COUNT(*) FROM reports"
    ).fetchone()[0]

    return result

def show_reports():
    db = get_db()
    return db.execute(
        "SELECT tracking_id, title, status, filename, timestamp, category FROM reports"
    ).fetchall()