import os, secrets, hashlib, asyncio, time
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict

load_dotenv(Path(__file__).parent / '.env')
client = AsyncIOMotorClient(os.environ['MONGO_URL'], compressors='zlib', maxPoolSize=20, minPoolSize=2, maxIdleTimeMS=120000, serverSelectionTimeoutMS=10000)
db = client[os.environ['DB_NAME']]
_settings_cache = {'value': None, 'at': 0.0}
_background = set()

def invalidate_settings(): _settings_cache['value'] = None

async def get_settings():
    if _settings_cache['value'] is None or time.monotonic() - _settings_cache['at'] > 30:
        _settings_cache.update(value=await db.settings.find_one({'id': 'main'}, {'_id': 0}), at=time.monotonic())
    return _settings_cache['value']

def fire_and_forget(coro):
    task = asyncio.ensure_future(coro)
    _background.add(task)
    task.add_done_callback(_background.discard)
def now(): return datetime.now(timezone.utc).isoformat()
def uid(): return str(uuid4())
class Record(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: str

async def current_user(authorization: str = Header(default='')):
    token = authorization.removeprefix('Bearer ')
    session = await db.sessions.find_one({'token_hash': hashlib.sha256(token.encode()).hexdigest()}, {'_id': 0})
    if not session:
        raise HTTPException(401, 'Sesi berakhir. Silakan masuk kembali.')
    if session.get('auth_version') != 2 or session.get('expires_at', datetime.now(timezone.utc)).replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        await db.sessions.delete_one({'id': session['id']})
        raise HTTPException(401, 'Sesi berakhir. Silakan login kembali.')
    settings = await get_settings()
    elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(session['last_seen'])).total_seconds()
    if elapsed > settings['idle_timeout']:
        await db.sessions.delete_one({'id': session['id']})
        raise HTTPException(401, 'Sesi berakhir karena tidak aktif.')
    user = await db.users.find_one({'id': session['user_id'], 'active': True}, {'_id': 0})
    if not user: raise HTTPException(403, 'Akun tidak aktif.')
    fire_and_forget(db.sessions.update_one({'id': session['id']}, {'$set': {'last_seen': now()}}))
    return user

def require(user, *roles):
    if user['role'] not in roles: raise HTTPException(403, 'Anda tidak memiliki hak akses untuk tindakan ini.')

async def audit(user, action, module, detail, request=None):
    await db.audit.insert_one({'id': uid(), 'user_id': user['id'], 'user_name': user['name'], 'action': action, 'module': module, 'detail': detail, 'ip': request.client.host if request and request.client else 'system', 'timestamp': now()})

async def notify(title, detail, link, roles=None, user_ids=None):
    await db.notifications.insert_one({'id': uid(), 'title': title, 'detail': detail, 'link': link, 'roles': roles or [], 'user_ids': user_ids or [], 'read_by': [], 'created_at': now()})

async def get_doc(collection, id):
    record = await db[collection].find_one({'id': id, 'is_deleted': {'$ne': True}}, {'_id': 0})
    if not record: raise HTTPException(404, 'Data tidak ditemukan.')
    return record

def eligible(quiz, user):
    return user['role'] == 'employee' and (not quiz['units'] or user['unit'] in quiz['units']) and (not quiz.get('positions') or user['position'] in quiz['positions'])