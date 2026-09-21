# Auth Testing Notes (CMS BPD)

Login flow: GET /api/auth/captcha -> {id, image(data URL png)}; POST /api/auth/login {username, password, captcha_id, captcha_answer}. CAPTCHA answer case-insensitive (uppercased server-side), single-use, expires 3 menit. 3x password salah -> akun terkunci 5 menit (HTTP 423).

Quick API test (plant captcha dengan jawaban diketahui):
```bash
cd /app/backend && python3 -c "
from pymongo import MongoClient
import hashlib
from datetime import datetime, timedelta, timezone
db = MongoClient('mongodb://localhost:27017')['test_database']
cid = 'test-captcha-e2e'
db.captchas.delete_many({'id': cid})
db.captchas.insert_one({'id': cid, 'answer_hash': hashlib.sha256(f'{cid}:ABC123'.encode()).hexdigest(), 'expires_at': datetime.now(timezone.utc) + timedelta(minutes=3)})
"
curl -s -X POST http://localhost:8001/api/auth/login -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"bpdjaya3x","captcha_id":"test-captcha-e2e","captcha_answer":"ABC123"}'
```
Expected: 200 dengan {token, user}.

Bootstrap sync: backend startup (initialize_auth di auth.py) memverifikasi hash tersimpan terhadap BOOTSTRAP_PASSWORD; jika tidak cocok, hash dibuat ulang dan lockout direset. Jadi mengubah BOOTSTRAP_PASSWORD lalu restart backend = reset password semua akun bawaan.
