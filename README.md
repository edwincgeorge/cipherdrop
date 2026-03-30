# 🔐 CipherDrop

> A secure, anonymous whistleblower reporting platform — built with end-to-end encryption, blockchain integrity verification, and a custom CAPTCHA engine.

🌐 **Live Demo:** [cipherdrop-1.onrender.com](https://cipherdrop-1.onrender.com)

---

## ✨ Features

- **End-to-End Encryption** — Reports are encrypted with AES-GCM and the key is wrapped using RSA-OAEP, meaning only the holder of the private key can decrypt submissions.
- **Blockchain Integrity** — Every submitted report's hash is anchored on-chain (Solana), providing tamper-proof, verifiable timestamps.
- **Anonymous Submissions** — No accounts required. Submitters receive a unique tracking ID to check their report status.
- **Custom CAPTCHA Engine** — A click-based CAPTCHA system built from scratch to protect forms from bots.
- **Honeypot Bot Protection** — Hidden form fields silently trap automated submissions.
- **Cloudinary File Uploads** — Supports evidence uploads (images, videos, documents) via Cloudinary.
- **WhatsApp Notifications** — Admin is notified via WhatsApp when a new report is submitted.
- **Admin Dashboard** — Protected admin panel with role-based access, report management, and multi-admin support.
- **Status Tracking** — Reporters can check their submission status using their tracking ID.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | SQLite |
| Encryption | PyCryptodome (AES-GCM + RSA-OAEP) |
| Blockchain | Solana (via `blockchain.py`) |
| File Storage | Cloudinary |
| Notifications | WhatsApp API |
| Frontend | HTML, CSS, JavaScript |
| Hosting | Render |

---

## 📁 Project Structure

```
cipherdrop/
├── app.py               # Main Flask application & all routes
├── blockchain.py        # Solana blockchain hash anchoring
├── captcha_engine.py    # Custom click-based CAPTCHA
├── config.py            # App configuration & environment variables
├── db.py                # Database initialization
├── db_operations.py     # All database queries
├── gen.py               # RSA keypair generator
├── wa.py                # WhatsApp notification integration
├── public_key.pem       # RSA public key (used to encrypt reports)
├── keypair.json         # Solana keypair for blockchain transactions
├── requirements.txt     # Python dependencies
├── static/              # CSS, JS, images
├── templates/           # HTML templates (Jinja2)
└── instance/
    └── database.db      # SQLite database
```

---

## ⚙️ Local Setup & Running

### Prerequisites

- Python 3.9+
- pip
- A Cloudinary account
- A WhatsApp Business API access (for notifications)
- A Solana wallet keypair (for blockchain anchoring)

### 1. Clone the repository

```bash
git clone https://github.com/edwincgeorge/cipherdrop.git
cd cipherdrop
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate RSA keypair

```bash
python gen.py
```

This creates `public_key.pem` and a private key file. **Keep the private key safe** — it is required to decrypt reports in the admin panel.

### 4. Set environment variables

Create a `.env` file or export these variables in your shell:

```env
SECRET_KEY=your_flask_secret_key
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
ACCESS_CODE=your_whatsapp_access_code
PHONE_NO=your_whatsapp_number
PHONE_ID=whatsapp_number_id
VERIFY_TOKEN=your_webhook_verify_token
SOLANA_KEYPAIR_PATH=your_solana_keypair_path
```

Generate a secure Flask secret key with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Run the app

```bash
python app.py
```

The app will be available at `http://localhost:5000`.

---

## 🚀 Hosting on Render

1. Push the repo to GitHub.
2. Create a new **Web Service** on [Render](https://render.com).
3. Set the **Build Command** to:
   ```
   pip install -r requirements.txt
   ```
4. Set the **Start Command** to:
   ```
   gunicorn app:app
   ```
5. Add all environment variables from the section above in the Render dashboard under **Environment**.
6. Set `SECRET_KEY` to a securely generated random hex string.
7. Deploy — Render will automatically build and serve the app.

> **Note:** The `instance/` folder and SQLite database are ephemeral on Render's free tier. For persistent storage, consider migrating to PostgreSQL.

---

## 🔑 How Encryption Works

1. When a report is submitted, a random 256-bit AES key is generated.
2. The report content is encrypted using **AES-GCM**.
3. The AES key itself is encrypted using the **RSA public key** stored on the server.
4. Only the holder of the corresponding **RSA private key** (the admin) can decrypt the report — even the server cannot read it in plaintext.

---

## 🛡️ Admin Panel

Access the admin dashboard at `/admin` (requires login at `/login`).

- View all submitted reports
- Upload the private key to decrypt and read a specific report
- Update report status and add notes
- Add or remove admin accounts

---

## 👨‍💻 Developer

**Edwin C George**
GitHub: [@edwincgeorge](https://github.com/edwincgeorge)

---

## 📄 License

This project is open source. Feel free to fork and build upon it.
