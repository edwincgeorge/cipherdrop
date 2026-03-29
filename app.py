from flask import Flask, render_template, request, jsonify, abort, Blueprint, session, redirect, url_for
import os
import secrets
import json
from captcha_engine import validate_click, generate_challenge
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
import base64
from db import init_db, close_db
from datetime import datetime
import db_operations as dbop
import config as vf
from wa import send_whatsapp_text
from functools import wraps
import cloudinary
import cloudinary.uploader
from blockchain import store_hash_on_chain

captcha_bp = Blueprint("captcha", __name__)

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ── Session secret key ────────────────────────────────────────────────────────
# Set SECRET_KEY in your environment variables on Render!
# Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production")

# Ensure instance/ folder exists before setting DB path
os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)

app.config['DATABASE'] = os.path.join(BASE_DIR, 'instance', 'database.db')
app.config["UPLOAD_FOLDER"] = "static/uploads"

with open("public_key.pem", "rb") as f:
    public_key = RSA.import_key(f.read())

rsa_cipher = PKCS1_OAEP.new(public_key)


# ── Auto-init DB on startup ───────────────────────────────────────────────────
with app.app_context():
    init_db()

# ── Auth decorator ────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/submit")
def submit():
    return render_template("submit-form.html")

@app.route("/status")
def status():
    return render_template("status-form.html")

@app.route("/404")
def error():
    return render_template("404.html")


# ── Admin login ───────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET"])
def login_page():
    # If already logged in, go straight to admin
    if session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_submit():
    # 1. CAPTCHA
    captcha_token = request.form.get("captcha_token", "")
    captcha_x     = float(request.form.get("captcha_x", -1))
    captcha_y     = float(request.form.get("captcha_y", -1))
    ok, reason = validate_click(captcha_token, captcha_x, captcha_y)
    if not ok:
        return jsonify({"success": False, "error": "CAPTCHA verification failed"}), 422

    # 2. Credentials
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    admin = dbop.get_admin(username)
    if not admin or not check_password_hash(admin["password_hash"], password):
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    # 3. Set session
    session["admin_logged_in"] = True
    session["admin_username"]  = admin["username"]
    session["admin_role"]      = admin["position"]

    return jsonify({"success": True, "redirect": "/admin"})



# ── Admin dashboard (protected) ───────────────────────────────────────────────

@app.route("/admin")
@login_required
def admin():
    counts  = dbop.count_status()
    total   = dbop.total_reports()
    reports = dbop.show_reports()
    admins = dbop.show_admins()

    return render_template(
        "admin.html",
        counts=counts,
        total=total,
        reports=reports,
        admins = admins,
        admin_username=session.get("admin_username"),
        admin_role=session.get("admin_role")
    )

@app.route("/add-admin" , methods=["POST"])
@login_required
def add_admin():
    username = request.form.get("admin-username", "").strip()
    name = request.form.get("admin-name")
    email = request.form.get("admin-email")
    position = request.form.get("admin-position")
    password = request.form.get("admin-password")

    if not password:
        return jsonify({"success": False, "error": "Password is required"}), 400

    dbop.admin_management(username, name, email, position, generate_password_hash(password))
    return jsonify({
            "success": True
        })

@app.route('/get-report', methods=['POST'])
@login_required
def get_report():
    tracking_id = request.form.get('tracking_id')
    private_key_file = request.files.get('private_key')


    if not private_key_file:
        return jsonify({'success': False, 'message': 'No private key uploaded'})

    report = dbop.get_report_by_id(tracking_id)

    if not report:
        return jsonify({'success': False, 'message': 'Report not found'})

    report = dict(report)

    try:
        private_key_data = private_key_file.read()
        private_key = RSA.import_key(private_key_data)
        rsa_decipher = PKCS1_OAEP.new(private_key)
        enc_key    = base64.b64decode(report['enc_key'])
        ciphertext = base64.b64decode(report['encryptedtext'])
        nonce      = base64.b64decode(report['nonce'])
        tag        = base64.b64decode(report['tag'])
        report_key = rsa_decipher.decrypt(enc_key)
        cipher = AES.new(report_key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        data = json.loads(plaintext.decode())
        return jsonify({
            'success': True,
            'title':       data.get('title', 'N/A'),
            'category':    report.get('category', 'N/A'),
            'description': data.get('description', 'N/A'),
            'evidence':    report.get('filename', 'N/A'),
            'status':      report.get('status', 'N/A')
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'{type(e).__name__}: {str(e)}'})

@app.route('/update-report', methods=['POST'])
@login_required
def update_report():
    tracking_id = request.form.get('tracking_id')
    status      = request.form.get('status')
    note        = request.form.get('note')

    dbop.update_report_status(tracking_id, status, note)
    return jsonify({'success': True})

@app.route("/delete-admin", methods=["POST"])
@login_required
def delete_admin():
    username = request.form.get("username")
    if username == session.get("admin_username"):
        return jsonify({"success": False, "message": "Cannot delete yourself"})
    dbop.delete_admin(username)
    return jsonify({"success": True})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))
# ── Debug route (remove in production) ───────────────────────────────────────

@app.route("/check-db")

def view_reports():
    reports = dbop.get_all_admins()
    return str([dict(r) for r in reports])


# ── Webhook ───────────────────────────────────────────────────────────────────

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == vf.VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403


# ── Helpers ───────────────────────────────────────────────────────────────────

def generate_tracking_id():
    date_part   = datetime.now().strftime("%Y%m%d")
    random_part = secrets.token_hex(4).upper()
    return f"WB-{date_part}-{random_part}"

def generate_unique_tracking_id():
    while True:
        tracking_id = generate_tracking_id()
        if not dbop.tracking_id_exists(tracking_id):
            return tracking_id

def encrypt_report(data):
    text       = json.dumps(data)
    report_key = get_random_bytes(32)
    cipher     = AES.new(report_key, AES.MODE_GCM)
    cipher_text, tag = cipher.encrypt_and_digest(text.encode())
    encrypt    = rsa_cipher.encrypt(report_key)
    return (
        base64.b64encode(cipher_text).decode(),
        base64.b64encode(cipher.nonce).decode(),
        base64.b64encode(tag).decode(),
        base64.b64encode(encrypt).decode()
    )


# ── Submit report ─────────────────────────────────────────────────────────────

@app.route("/submit-report", methods=["POST"])
def submit_report():

    # 1. Honeypot
    if request.form.get("website", ""):
        return jsonify({"success": True, "tracking_id": "INVALID"})

    # 2. CAPTCHA
    captcha_token = request.form.get("captcha_token", "")
    captcha_x     = float(request.form.get("captcha_x", -1))
    captcha_y     = float(request.form.get("captcha_y", -1))
    ok, reason = validate_click(captcha_token, captcha_x, captcha_y)
    if not ok:
        return jsonify({"success": False, "error": "CAPTCHA verification failed"}), 422

    title       = request.form.get('titleInput')
    category    = request.form.get('category')
    desc        = request.form.get('descInput')
    tracking_id = generate_unique_tracking_id()
    timestamp   = datetime.now().strftime("%Y-%m-%d")

    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
        api_key=os.environ["CLOUDINARY_API_KEY"],
        api_secret=os.environ["CLOUDINARY_API_SECRET"]
    )

    files     = request.files.getlist("fileInput")
    file_urls = []

    for file in files:
        if file and file.filename != "":
            ext            = file.filename.rsplit(".", 1)[-1].lower()
            upload_options = {"folder": "cipherdrop", "resource_type": "auto"}
            if ext in ["mp4", "webm", "mov"]:
                upload_options["format"] = "mp4"
            result = cloudinary.uploader.upload(file, **upload_options)
            file_urls.append(result["secure_url"])

    filename = ",".join(file_urls) if file_urls else None

    # 4. Encrypt & save
    ciphertext, nonce, tag, enc_key = encrypt_report({
        "title":       title,
        "description": desc
    })

    dbop.insert_reports(tracking_id, ciphertext, category, filename, timestamp, nonce, tag, enc_key)
    chain_result = store_hash_on_chain(tracking_id, timestamp)
 
    if chain_result["success"]:
        # Save the transaction signature in DB for later verification
        dbop.update_tx_signature(tracking_id, chain_result["tx_signature"])
        print(f"[blockchain] Hash stored: {chain_result['explorer_url']}")
    else:
        # Blockchain failure does NOT stop the submission
        print(f"[blockchain] Hash storage failed (non-critical): {chain_result.get('error')}")
        
    phone = "918281959949"
    send_whatsapp_text(phone, f"A new report has been submitted with \n\ntracking ID: {tracking_id}")
    return jsonify({
        "success":      True,
        "tracking_id":  tracking_id,
        "tx_signature": chain_result.get("tx_signature"),   # optional, show to user
        "explorer_url": chain_result.get("explorer_url"),   # optional
    })

    return jsonify({"success": True, "tracking_id": tracking_id})


# ── Status check ──────────────────────────────────────────────────────────────

@app.route("/status-reports", methods=["POST"])
def status_reports():
    application_id = request.form.get("application_id")
    result         = dbop.check_status(application_id)
    if result is None:
        return jsonify({"success": False, "message": "Application ID not found"})
    result_dict = dict(result)
    return jsonify({
        "success": True,
        "status": result_dict.get("status"),
        "note":   result_dict.get("note")
    })


# ── CAPTCHA blueprint ─────────────────────────────────────────────────────────

@captcha_bp.get("/challenge")
def get_challenge():
    data = generate_challenge()
    return jsonify({
        "image":  f"data:image/png;base64,{data['image_b64']}",
        "token":  data["token"],
        "prompt": data["prompt"],
    })


app.register_blueprint(captcha_bp, url_prefix="/captcha")


if __name__ == "__main__":
    app.run(debug=True)
