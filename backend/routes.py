import os, secrets, hashlib, io
from urllib.parse import quote
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from core import db, now, uid, current_user, require, audit, notify, get_doc, Record
from storage import put_object, get_object

router = APIRouter()
class DemoLogin(BaseModel):
    role: Literal['administrator', 'supervisor', 'employee', 'director']
class DocumentInput(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    number: str = Field(min_length=3, max_length=100)
    category: Literal['Internal', 'Eksternal']
    unit: str
    description: str = Field(default='', max_length=10000)
    version: str = '1.0'
class ActionInput(BaseModel):
    action: Literal['submit', 'approve', 'reject']
    reason: str = ''
class SettingsInput(BaseModel):
    passing_grade: int = Field(ge=1, le=100)
    idle_timeout: int = Field(ge=60, le=3600)
    quiz_duration: int = Field(ge=1, le=180)
class UserInput(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    email: str = Field(min_length=5, max_length=200)
    nrk: str = Field(min_length=3, max_length=30)
    unit: str
    position: str
    role: Literal['employee', 'supervisor', 'director'] = 'employee'

@router.get('/health')
async def health(): return {'status': 'ok'}

@router.post('/auth/demo')
async def demo_login(body: DemoLogin, request: Request):
    if os.environ.get('DEMO_MODE') != 'true': raise HTTPException(403, 'Mode demo tidak aktif.')
    user = await db.users.find_one({'id': 'demo-' + ('admin' if body.role == 'administrator' else body.role), 'active': True}, {'_id': 0})
    if not user: raise HTTPException(403, 'Akun demo tidak aktif.')
    token = secrets.token_urlsafe(48)
    await db.sessions.insert_one({'id': uid(), 'token_hash': hashlib.sha256(token.encode()).hexdigest(), 'user_id': user['id'], 'last_seen': now()})
    await audit(user, 'LOGIN_DEMO', 'Akses', 'Masuk ke ruang demo sebagai ' + body.role, request)
    return {'token': token, 'user': user, 'demo': True}

@router.get('/auth/me', response_model=Record)
async def me(user=Depends(current_user)): return user

@router.post('/auth/logout')
async def logout(request: Request):
    token = request.headers.get('authorization', '').removeprefix('Bearer ')
    await db.sessions.delete_one({'token_hash': hashlib.sha256(token.encode()).hexdigest()})
    return {'success': True}

@router.get('/documents', response_model=list[Record])
async def documents(q: str = '', category: str = '', status: str = '', user=Depends(current_user)):
    query = {'is_deleted': {'$ne': True}}
    if user['role'] not in ['administrator', 'supervisor']: query['status'] = 'published'
    elif status: query['status'] = status
    if category: query['category'] = category
    records = await db.documents.find(query, {'_id': 0, 'storage_path': 0}).sort('created_at', -1).to_list(1000)
    return [r for r in records if q.lower() in (r['title']+' '+r['number']).lower()]

@router.post('/documents', response_model=Record)
async def create_document(body: DocumentInput, request: Request, user=Depends(current_user)):
    require(user, 'administrator')
    doc = {**body.model_dump(), 'id': uid(), 'status': 'draft', 'created_by': user['id'], 'created_at': now(), 'updated_at': now(), 'filename': None, 'is_deleted': False, 'sample': False}
    await db.documents.insert_one(doc.copy())
    await audit(user, 'CREATE', 'Ketentuan', 'Membuat ' + doc['title'], request)
    return doc

@router.put('/documents/{id}', response_model=Record)
async def update_document(id: str, body: DocumentInput, request: Request, user=Depends(current_user)):
    require(user, 'administrator')
    doc = await get_doc('documents', id)
    if doc['status'] not in ['draft', 'rejected']: raise HTTPException(400, 'Hanya draf atau dokumen ditolak yang dapat diubah.')
    values = {**body.model_dump(), 'updated_at': now()}
    await db.documents.update_one({'id': id}, {'$set': values})
    await audit(user, 'UPDATE', 'Ketentuan', body.title, request)
    return {**doc, **values}

@router.post('/documents/{id}/upload')
async def upload(id: str, request: Request, file: UploadFile = File(...), user=Depends(current_user)):
    require(user, 'administrator')
    doc = await get_doc('documents', id)
    if doc['status'] not in ['draft','rejected']: raise HTTPException(400, 'Dokumen dalam proses review tidak dapat diubah.')
    ext = file.filename.rsplit('.', 1)[-1].lower()
    types = {'pdf': 'application/pdf', 'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
    if ext not in types: raise HTTPException(400, 'Hanya dokumen PDF atau DOCX yang diperbolehkan.')
    data = await file.read(10*1024*1024+1)
    if not data or len(data)>10*1024*1024: raise HTTPException(400, 'Ukuran dokumen harus antara 1 byte dan 10 MB.')
    if (ext == 'pdf' and not data.startswith(b'%PDF')) or (ext == 'docx' and not data.startswith(b'PK')): raise HTTPException(400, 'Isi berkas tidak sesuai format dokumen.')
    result = await run_in_threadpool(put_object, f'cms-bali-dwipa/uploads/{user["id"]}/{uid()}.{ext}', data, types[ext])
    await db.documents.update_one({'id': id}, {'$set': {'storage_path': result['path'], 'filename': file.filename, 'content_type': types[ext], 'file_size': len(data), 'updated_at': now()}})
    await audit(user, 'UPLOAD', 'Ketentuan', file.filename, request)
    return {'success': True, 'filename': file.filename}

@router.get('/documents/{id}/download')
async def download_doc(id: str, request: Request, user=Depends(current_user)):
    doc = await get_doc('documents', id)
    if doc['status'] != 'published': require(user, 'administrator', 'supervisor')
    if doc.get('storage_path'):
        data = await run_in_threadpool(get_object, doc['storage_path'])
        filename, mime = doc['filename'], doc['content_type']
    elif doc.get('sample'):
        data = f"DOKUMEN CONTOH — BUKAN KETENTUAN RESMI\n\n{doc['title']}\n{doc['number']}\n\n{doc['description']}\n".encode()
        filename, mime = doc['number'].replace('/', '-')+'.txt', 'text/plain; charset=utf-8'
    else: raise HTTPException(404, 'Berkas belum diunggah.')
    await audit(user, 'DOWNLOAD', 'Ketentuan', doc['title'], request)
    return Response(data, media_type=mime, headers={'Content-Disposition': "attachment; filename*=UTF-8''"+quote(filename), 'X-Content-Type-Options': 'nosniff'})

@router.post('/documents/{id}/action', response_model=Record)
async def document_action(id: str, body: ActionInput, request: Request, user=Depends(current_user)):
    doc = await get_doc('documents', id)
    if body.action == 'submit':
        require(user, 'administrator')
        if doc['status'] not in ['draft','rejected']: raise HTTPException(400, 'Status dokumen tidak sesuai.')
        if not doc.get('filename') and not doc.get('sample'): raise HTTPException(400, 'Unggah berkas dokumen terlebih dahulu.')
        status = 'pending'
    else:
        require(user, 'supervisor')
        if doc['status'] != 'pending': raise HTTPException(400, 'Dokumen belum diajukan untuk review.')
        if body.action == 'reject' and not body.reason.strip(): raise HTTPException(400, 'Alasan penolakan wajib diisi.')
        status = 'published' if body.action == 'approve' else 'rejected'
    update = {'status': status, 'review_note': body.reason, 'updated_at': now()}
    await db.documents.update_one({'id': id}, {'$set': update})
    await audit(user, body.action.upper(), 'Ketentuan', doc['title'], request)
    await notify('Ketentuan '+{'pending': 'menunggu review', 'published': 'baru dipublikasikan', 'rejected': 'ditolak'}[status], doc['title'], '/ketentuan', roles=['supervisor'] if status == 'pending' else ['administrator'] if status == 'rejected' else ['employee','administrator','director'])
    doc.pop('storage_path', None)
    return {**doc, **update}

@router.delete('/documents/{id}')
async def delete_document(id: str, request: Request, user=Depends(current_user)):
    require(user, 'administrator')
    doc = await get_doc('documents', id)
    if doc['status'] not in ['draft','rejected']: raise HTTPException(400, 'Hanya draf atau dokumen ditolak yang dapat dihapus.')
    await db.documents.update_one({'id': id}, {'$set': {'is_deleted': True}})
    await audit(user, 'DELETE', 'Ketentuan', doc['title'], request)
    return {'success': True}

@router.get('/notifications', response_model=list[Record])
async def notifications(user=Depends(current_user)):
    return await db.notifications.find({'$or': [{'roles': user['role']}, {'user_ids': user['id']}]}, {'_id': 0}).sort('created_at', -1).to_list(50)

@router.post('/notifications/{id}/read')
async def read_notification(id: str, user=Depends(current_user)):
    await db.notifications.update_one({'id': id, '$or': [{'roles': user['role']}, {'user_ids': user['id']}]}, {'$addToSet': {'read_by': user['id']}})
    return {'success': True}

@router.get('/settings', response_model=Record)
async def settings(user=Depends(current_user)): return await db.settings.find_one({'id': 'main'}, {'_id': 0})

@router.put('/settings', response_model=Record)
async def save_settings(body: SettingsInput, request: Request, user=Depends(current_user)):
    require(user, 'administrator')
    await db.settings.update_one({'id': 'main'}, {'$set': body.model_dump()})
    await audit(user, 'UPDATE', 'Parameter', 'Memperbarui parameter aplikasi', request)
    return await db.settings.find_one({'id': 'main'}, {'_id': 0})

@router.get('/users', response_model=list[Record])
async def users(user=Depends(current_user)):
    require(user, 'administrator', 'supervisor')
    values = await db.users.find({}, {'_id': 0}).to_list(1000)
    for v in values:
        v['email'] = v['email'][:2]+'***@'+v['email'].split('@')[-1]
        v['nrk'] = v['nrk'][:2]+'****'
    return values

@router.get('/users/{id}/detail', response_model=Record)
async def user_detail(id: str, request: Request, user=Depends(current_user)):
    require(user, 'administrator')
    await audit(user, 'VIEW_PERSONAL_DATA', 'Pengguna', 'Melihat detail pengguna '+id, request)
    return await get_doc('users', id)

@router.post('/users', response_model=Record)
async def create_user(body: UserInput, request: Request, user=Depends(current_user)):
    require(user, 'administrator')
    from email_validator import validate_email, EmailNotValidError
    try: validate_email(body.email, check_deliverability=False)
    except EmailNotValidError: raise HTTPException(400, 'Format email tidak valid.')
    if await db.users.find_one({'$or': [{'nrk': body.nrk}, {'email': body.email}]}): raise HTTPException(400, 'NRK atau email sudah terdaftar.')
    record = {**body.model_dump(), 'id': uid(), 'active': True, 'created_at': now()}
    await db.users.insert_one(record.copy())
    await audit(user, 'CREATE', 'Pengguna', body.name, request)
    return record

@router.post('/users/{id}/toggle', response_model=Record)
async def toggle_user(id: str, request: Request, user=Depends(current_user)):
    require(user, 'administrator')
    if id.startswith('demo-'): raise HTTPException(400, 'Akun demo utama tidak dapat dinonaktifkan.')
    record = await get_doc('users', id)
    await db.users.update_one({'id': id}, {'$set': {'active': not record['active']}})
    if record['active']: await db.sessions.delete_many({'user_id': id})
    await audit(user, 'BLOCK' if record['active'] else 'UNBLOCK', 'Pengguna', record['name'], request)
    return {**record, 'active': not record['active']}

@router.get('/audit', response_model=list[Record])
async def audit_list(q: str = '', module: str = '', user=Depends(current_user)):
    require(user, 'administrator', 'supervisor', 'director')
    query = {'module': module} if module else {}
    values = await db.audit.find(query, {'_id': 0}).sort('timestamp', -1).to_list(500)
    return [v for v in values if q.lower() in (v['user_name']+' '+v['detail']+' '+v['action']).lower()]