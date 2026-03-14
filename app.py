from flask import Flask, render_template, request, jsonify, abort, Blueprint
import os
import secrets
import json
from captcha_engine import validate_click, generate_challenge
from werkzeug.utils import secure_filename
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
import base64
from db import init_db, close_db
from datetime import datetime
import db_operations as dbop
import config as vf
from wa import send_whatsapp_text
 
captcha_bp = Blueprint("captcha", __name__)

app = Flask(__name__)
app.config["DATABASE"] = "/tmp/database.db"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config['DATABASE'] = os.path.join(BASE_DIR, 'instance', 'database.db')

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

with open("public_key.pem", "rb") as f:
    public_key = RSA.import_key(f.read())

rsa_cipher = PKCS1_OAEP.new(public_key)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/submit")
def submit():
    return render_template("submit-form.html")

@app.route("/status")
def status():
    return render_template("status-form.html")
@app.route("/init-db")
def init():
    init_db()
    return "fuck u"


@app.route("/404")
def error():
    return render_template("404.html")

@app.route("/admin")
def admin():
    counts = dbop.count_status()
    total = dbop.total_reports()
    reports = dbop.show_reports()
    return render_template("admin.html", counts = counts, total=total, reports=reports)

@app.route("/check-db")
def view_reports():
    reports = dbop.get_all_reports()
    return str([dict(r) for r in reports])

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == vf.VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Verification failed", 403

def generate_tracking_id():
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = secrets.token_hex(4).upper()
    return f"WB-{date_part}-{random_part}"

def generate_unique_tracking_id():
    while True:
        tracking_id = generate_tracking_id()
        if not dbop.tracking_id_exists(tracking_id):
            return tracking_id

def encrypt_report(data):
    text = json.dumps(data)
    report_key = get_random_bytes(32)

    cipher = AES.new(report_key, AES.MODE_GCM)
    cipher_text , tag = cipher.encrypt_and_digest(text.encode())

    encrypt = rsa_cipher.encrypt(report_key)

    return (
        base64.b64encode(cipher_text).decode(),
        base64.b64encode(cipher.nonce).decode(),
        base64.b64encode(tag).decode(),
        base64.b64encode(encrypt).decode()
    )


@app.route("/submit-report", methods=["POST"])
def submit_report():

    honeypot = request.form.get("website", "")
    if honeypot:
        return jsonify({"success": True, "tracking_id": "INVALID"})
    
    captcha_token = request.form.get("captcha_token", "")
    captcha_x     = float(request.form.get("captcha_x", -1))
    captcha_y     = float(request.form.get("captcha_y", -1))

    ok, reason = validate_click(captcha_token, captcha_x, captcha_y)
    if not ok:
        return jsonify({"success": False, "error": "CAPTCHA verification failed"}), 422

    title = request.form.get('titleInput')
    category = request.form.get('category')
    desc = request.form.get('descInput')
    file = request.files.get('fileInput')
    tracking_id = generate_unique_tracking_id()
    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = None

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        print("Saved:", filename)
    
    phone = "918281959949"
    send_whatsapp_text(phone, f"A new report has been submitted with \n\ntracking ID: {tracking_id} \n\nsecret code:")
    
    ciphertext, nonce, tag, enc_key = encrypt_report({
        "title": title,
        "description": desc
    })

    dbop.insert_reports(tracking_id, ciphertext, category, filename, timestamp, nonce, tag, enc_key)
    return jsonify({
        "success": True,
        "tracking_id": tracking_id
    })

@app.route("/status-reports", methods=["POST"])
def status_reports():
    application_id = request.form.get("application_id")

    result = dbop.check_status(application_id)

    if result is None:
        return jsonify({
            "success": False,
            "message": "Application ID not found"
        })

    result_dict = dict(result)

    return jsonify({
        "success": True,
        "status": result_dict.get("status"),
        "note": result_dict.get("note")
    })


@captcha_bp.get("/challenge")
def get_challenge():
    """GET /captcha/challenge"""
    data = generate_challenge()
    return jsonify({
        "image": f"data:image/png;base64,{data['image_b64']}",
        "token": data["token"],
        "prompt": data["prompt"],
    })
 
 
app.register_blueprint(captcha_bp, url_prefix="/captcha")

if __name__ == "__main__":
    app.run(debug=True)
