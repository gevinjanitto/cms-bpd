"""Optional, official Cloudinary integration for administrator-managed images."""
import io
import os
import warnings
from urllib.parse import urlparse

import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool
from core import audit, current_user, db, get_doc, now, require, uid

router = APIRouter()
def configured():
    return all(os.environ.get(k, '').strip() for k in ['CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET'])

def upload_image(data, public_id):
    if not configured():
        raise HTTPException(503, 'Cloudinary belum dikonfigurasi. Isi CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, dan CLOUDINARY_API_SECRET di server.')
    cloudinary.config(cloud_name=os.environ['CLOUDINARY_CLOUD_NAME'], api_key=os.environ['CLOUDINARY_API_KEY'], api_secret=os.environ['CLOUDINARY_API_SECRET'], secure=True)
    try:
        result = cloudinary.uploader.upload(io.BytesIO(data), resource_type='image', public_id=public_id, overwrite=False, allowed_formats=['png','jpg','jpeg','webp'])
    except cloudinary.exceptions.Error:
        raise HTTPException(502, 'Unggah gambar ke Cloudinary gagal. Periksa konfigurasi layanan.')
    if not result.get('secure_url', '').startswith('https://res.cloudinary.com/'):
        raise HTTPException(502, 'Respons layanan gambar tidak valid.')
    return {'url': result['secure_url'], 'public_id': result['public_id']}


@router.get('/media/status')
async def status(user=Depends(current_user)):
    require(user, 'administrator')
    return {'cloudinary_configured': configured(), 'documents_storage': 'MongoDB GridFS'}


@router.get('/branding')
async def branding():
    record = await db.branding.find_one({'id': 'main'}, {'_id': 0})
    return {'logo_url': record.get('logo_url') if record else None, 'login_image_url': record.get('login_image_url') if record else None}


@router.post('/media/images')
async def upload(request: Request, purpose: str = 'library', file: UploadFile = File(...), user=Depends(current_user)):
    require(user, 'administrator')
    if purpose not in ['library', 'logo', 'login']:
        raise HTTPException(400, 'Tujuan gambar tidak valid.')
    data = await file.read(5 * 1024 * 1024 + 1)
    if not data or len(data) > 5 * 1024 * 1024:
        raise HTTPException(400, 'Ukuran gambar maksimal 5 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            image = Image.open(io.BytesIO(data))
            if image.format not in ['PNG', 'JPEG', 'WEBP'] or image.width * image.height > 25000000:
                raise ValueError('Invalid image')
            image.verify()
    except (UnidentifiedImageError, ValueError, OSError, SyntaxError, Image.DecompressionBombWarning, Image.DecompressionBombError):
        raise HTTPException(400, 'Berkas harus gambar PNG, JPEG, atau WebP yang valid.')
    result = await run_in_threadpool(upload_image, data, f'users/{user["id"]}/images/{uid()}')
    await db.images.insert_one({'id': uid(), **result, 'purpose': purpose, 'created_by': user['id'], 'created_at': now()})
    if purpose != 'library':
        key = 'logo_url' if purpose == 'logo' else 'login_image_url'
        await db.branding.update_one({'id': 'main'}, {'$set': {key: result['url']}}, upsert=True)
    await audit(user, 'UPLOAD_IMAGE', 'Pengaturan', f'Gambar {purpose} disimpan di Cloudinary', request)
    return result