import pytest
import jwt
import datetime
from main import app, db, Tamu, cache, SECRET_KEY

@pytest.fixture
def client():
    # Konfigurasi khusus testing
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # DB sementara
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            cache.flushdb() # Bersihkan Redis sebelum tiap test
        yield client

def test_login_success(client):
    """Tes apakah login admin berhasil mendapatkan token"""
    res = client.post('/login', json={"username": "admin", "password": "123"})
    assert res.status_code == 200
    assert 'token' in res.get_json()

def test_full_auth_workflow(client):
    """Skenario: Login -> Simpan (OK) -> Logout -> Simpan (Gagal/401)"""
    
    # 1. LOGIN
    login_res = client.post('/login', json={"username": "admin", "password": "123"})
    token = login_res.get_json()['token']
    headers = {'Authorization': f'Bearer {token}'}

    # 2. SIMPAN DATA (HARUS BERHASIL)
    res_save1 = client.post('/simpan', headers=headers, json={"nama": "Tester", "telepon": "111"})
    assert res_save1.status_code == 200
    assert b"berhasil disimpan" in res_save1.data

    # 3. LOGOUT
    res_logout = client.post('/logout', headers=headers)
    assert res_logout.status_code == 200
    assert b"berhasil logout" in res_logout.data

    # 4. COBA AKSES LAGI (HARUS DITOLAK KARENA BLACKLIST)
    res_save2 = client.post('/simpan', headers=headers, json={"nama": "Hacker", "telepon": "999"})
    assert res_save2.status_code == 401
    assert b"Sudah Logout" in res_save2.data

def test_invalid_token(client):
    """Tes apakah token acak/palsu ditolak"""
    headers = {'Authorization': 'Bearer token_palsu_123'}
    res = client.get('/tampil', headers=headers)
    assert res.status_code == 401
    assert b"Token tidak valid" in res.data
