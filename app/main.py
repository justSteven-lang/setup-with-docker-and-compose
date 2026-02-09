import os
import jwt
import datetime
import redis
from flask import Flask, request, jsonify
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- 1. KONFIGURASI DATABASE & KEAMANAN ---
# Ambil dari environment variable (pindah ke atas agar bisa dipakai inisialisasi)
SECRET_KEY = os.getenv("API_SECRET_KEY", "RAHASIA_DOCKER_2026")

DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = "db_server"

# Tambahkan print debug ini (Hapus jika sudah jalan)
print(f"DEBUG: Mencoba konek ke {DB_NAME} sebagai {DB_USER}")

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# INISIALISASI DB (Wajib di atas Class Model)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- 2. KONEKSI REDIS ---
cache = redis.Redis(host='redis_service', port=6379, db=0, decode_responses=True)

# --- 3. MODEL DATABASE ---
# Sekarang 'db' sudah dikenal karena sudah diinisialisasi di atas
class Tamu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    telepon = db.Column(db.String(20))

# --- 4. DECORATOR JWT ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'message': 'Token hilang!'}), 401

        if cache.get(token):
            return jsonify({'message': 'Token sudah tidak berlaku (Sudah Logout)!'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = data['user']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token kedaluwarsa!'}), 401
        except Exception:
            return jsonify({'message': 'Token tidak valid!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

# --- 5. ROUTES API ---

@app.route('/login', methods=['POST'])
def login():
    auth = request.json
    if auth and auth.get('username') == 'admin' and auth.get('password') == '123':
        token = jwt.encode({
            'user': 'admin',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")
        
        return jsonify({'token': token})
    
    return jsonify({'message': 'Login Gagal!'}), 401

@app.route('/simpan', methods=['POST'])
@token_required
def simpan_nama(current_user):
    data = request.json
    if not data or not data.get('nama'):
        return jsonify({"error": "Data nama wajib diisi"}), 400
        
    tamu_baru = Tamu(nama=data.get('nama'), telepon=data.get('telepon'))
    db.session.add(tamu_baru)
    db.session.commit()
    return jsonify({"pesan": f"Halo {current_user}, data berhasil disimpan!"})

@app.route('/tampil', methods=['GET'])
@token_required
def tampil_data(current_user):
    semua_tamu = Tamu.query.order_by(Tamu.id.desc()).all()
    return jsonify([{"id": t.id, "nama": t.nama, "telepon": t.telepon} for t in semua_tamu])

@app.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(" ")[1]
    cache.setex(token, 86400, "blacklisted")
    return jsonify({"message": f"User {current_user} berhasil logout!"})

@app.route('/')
def index():
    return "<h1>Backend API is Running!</h1>"

@app.route('/health')
def health():
    return {"status": "ok"}, 200


# --- 6. JALANKAN SERVER ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
