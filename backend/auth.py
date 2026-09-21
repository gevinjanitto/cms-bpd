"""Independent password authentication and one-use image CAPTCHA."""
import base64
import hashlib
import io
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
from starlette.concurrency import run_in_threadpool

from core import audit, current_user, db, now, uid

router = APIRouter()
ACCOUNTS = {'admin': 'demo-admin', 'supervisor': 'demo-supervisor', 'karyawan': 'demo-employee', 'direksi': 'demo-director'}


async def initialize_auth():
    await db.credentials.create_index('username', unique=True)
    await db.credentials.create_index('user_id', unique=True)
    await db.captchas.create_index('expires_at', expireAfterSeconds=0)
    await db.auth_limits.create_index('expires_at', expireAfterSeconds=0)
    await db.sessions.create_index('expires_at', expireAfterSeconds=0)
    version = await db.system_meta.find_one({'id': 'auth'}, {'_id': 0})
    if not version or version.get('version') != 2:
        await db.sessions.delete_many({})
        await db.system_meta.update_one({'id': 'auth'}, {'$set': {'id': 'auth', 'version': 2}}, upsert=True)
<<<<<<< HEAD
    password = os.environ.get('BOOTSTRAP_PASSWORD')
    if not password or len(password) < 8:
        raise RuntimeError('BOOTSTRAP_PASSWORD minimal 8 karakter wajib diatur untuk inisialisasi akun.')
    for username, user_id in ACCOUNTS.items():
        existing = await db.credentials.find_one({'username': username})
        if existing:
            if not await run_in_threadpool(bcrypt.checkpw, password.encode(), existing['password_hash'].encode()):
                digest = await run_in_threadpool(bcrypt.hashpw, password.encode(), bcrypt.gensalt())
                await db.credentials.update_one({'username': username}, {'$set': {'password_hash': digest.decode(), 'failed_attempts': 0, 'updated_at': now()}, '$unset': {'locked_until': ''}})
            await db.users.update_one({'id': user_id}, {'$set': {'username': username}})
            continue
=======
    for username, user_id in ACCOUNTS.items():
        if await db.credentials.find_one({'username': username}):
            continue
        password = os.environ.get('BOOTSTRAP_PASSWORD')
        if not password or len(password) < 8:
            raise RuntimeError('BOOTSTRAP_PASSWORD minimal 8 karakter wajib diatur untuk inisialisasi akun.')
>>>>>>> 91ae9f0a5bad37493205b97706d3dde110afcab8
        digest = await run_in_threadpool(bcrypt.hashpw, password.encode(), bcrypt.gensalt())
        await db.credentials.update_one({'username': username}, {'$setOnInsert': {
            'id': uid(), 'username': username, 'user_id': user_id,
            'password_hash': digest.decode(), 'failed_attempts': 0, 'created_at': now()
        }}, upsert=True)
        await db.users.update_one({'id': user_id}, {'$set': {'username': username}})


async def rate_limit(request, action, maximum):
    ip = request.client.host if request.client else 'unknown'
    time = datetime.now(timezone.utc)
    key = hashlib.sha256(f'{action}:{ip}:{int(time.timestamp()) // 60}'.encode()).hexdigest()
    row = await db.auth_limits.find_one_and_update({'id': key}, {
        '$inc': {'count': 1}, '$setOnInsert': {'expires_at': time + timedelta(minutes=2)}
    }, upsert=True, return_document=ReturnDocument.AFTER, projection={'_id': 0})
    if row['count'] > maximum:
        raise HTTPException(429, 'Terlalu banyak permintaan. Silakan coba satu menit lagi.')


def captcha_image(code):
    image = Image.new('RGB', (260, 70), '#eef6f0')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(Path(__file__).parent / 'assets' / 'Manrope.ttf'), 32)
    rng = secrets.SystemRandom()
    for _ in range(45):
        x, y = rng.randrange(260), rng.randrange(70)
        draw.ellipse((x, y, x + 2, y + 2), fill='#bed8c8')
    for _ in range(3):
        draw.line((0, rng.randrange(70), 260, rng.randrange(70)), fill='#aecfbb', width=1)
    for i, character in enumerate(code):
        draw.text((19 + i * 38, rng.randrange(12, 22)), character, font=font, fill='#176342')
    output = io.BytesIO()
    image.save(output, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(output.getvalue()).decode()


@router.get('/auth/captcha')
async def captcha(request: Request):
    await rate_limit(request, 'captcha', 90)
    code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(6))
    challenge_id = uid()
    await db.captchas.insert_one({
        'id': challenge_id,
        'answer_hash': hashlib.sha256(f'{challenge_id}:{code}'.encode()).hexdigest(),
        'expires_at': datetime.now(timezone.utc) + timedelta(minutes=3)
    })
    return {'id': challenge_id, 'image': captcha_image(code), 'expires_in': 180}


class LoginInput(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=72)
    captcha_id: str = Field(max_length=100)
    captcha_answer: str = Field(min_length=1, max_length=20)


@router.post('/auth/login')
async def login(body: LoginInput, request: Request):
    await rate_limit(request, 'login', 60)
    current = datetime.now(timezone.utc)
    challenge = await db.captchas.find_one_and_delete({'id': body.captcha_id}, projection={'_id': 0})
    digest = hashlib.sha256(f'{body.captcha_id}:{body.captcha_answer.strip().upper()}'.encode()).hexdigest()
    if not challenge or challenge['expires_at'].replace(tzinfo=timezone.utc) < current or not secrets.compare_digest(challenge['answer_hash'], digest):
        raise HTTPException(400, 'CAPTCHA salah atau kedaluwarsa. Masukkan kode yang baru.')
    username = body.username.strip().lower()
    credentials = await db.credentials.find_one({'username': username}, {'_id': 0})
    if credentials and credentials.get('locked_until') and datetime.fromisoformat(credentials['locked_until']) > current:
        raise HTTPException(423, 'Akun terkunci sementara. Coba kembali setelah 5 menit atau hubungi administrator.')
    valid = credentials and await run_in_threadpool(bcrypt.checkpw, body.password.encode(), credentials['password_hash'].encode())
    if not valid:
        if credentials:
            attempts = credentials.get('failed_attempts', 0) + 1
            if credentials.get('locked_until') and datetime.fromisoformat(credentials['locked_until']) <= current:
                attempts = 1
            update = {'failed_attempts': attempts}
            if attempts >= 3: update['locked_until'] = (current + timedelta(minutes=5)).isoformat()
            await db.credentials.update_one({'username': username}, {'$set': update})
        raise HTTPException(401, 'Username atau password tidak sesuai.')
    user = await db.users.find_one({'id': credentials['user_id'], 'active': True}, {'_id': 0})
    if not user: raise HTTPException(403, 'Akun tidak aktif. Hubungi administrator SISDUR.')
    await db.credentials.update_one({'username': username}, {'$set': {'failed_attempts': 0, 'last_login': now()}, '$unset': {'locked_until': ''}})
    token = secrets.token_urlsafe(48)
    await db.sessions.insert_one({'id': uid(), 'token_hash': hashlib.sha256(token.encode()).hexdigest(), 'user_id': user['id'], 'last_seen': now(), 'expires_at': current + timedelta(hours=12), 'auth_version': 2})
    await audit(user, 'LOGIN', 'Akses', 'Login username dan CAPTCHA berhasil', request)
    return {'token': token, 'user': user}


class PasswordInput(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)


@router.post('/auth/change-password')
async def change_password(body: PasswordInput, request: Request, user=Depends(current_user)):
    credentials = await db.credentials.find_one({'user_id': user['id']}, {'_id': 0})
    if not credentials or not await run_in_threadpool(bcrypt.checkpw, body.current_password.encode(), credentials['password_hash'].encode()):
        raise HTTPException(400, 'Password saat ini tidak sesuai.')
    digest = await run_in_threadpool(bcrypt.hashpw, body.new_password.encode(), bcrypt.gensalt())
    await db.credentials.update_one({'user_id': user['id']}, {'$set': {'password_hash': digest.decode(), 'updated_at': now()}})
    current_token = request.headers.get('authorization', '').removeprefix('Bearer ')
    await db.sessions.delete_many({'user_id': user['id'], 'token_hash': {'$ne': hashlib.sha256(current_token.encode()).hexdigest()}})
    await audit(user, 'CHANGE_PASSWORD', 'Akses', 'Password akun diperbarui', request)
    return {'success': True}