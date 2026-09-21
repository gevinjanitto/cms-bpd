"""Private document storage in MongoDB GridFS; no external storage dependency."""
import os
from bson import ObjectId
from gridfs import GridFSBucket, NoFile
from pymongo import MongoClient
from fastapi import HTTPException

client = MongoClient(os.environ['MONGO_URL'])
database = client[os.environ['DB_NAME']]
bucket = GridFSBucket(database, bucket_name='document_files')


def put_object(path, data, content_type):
    file_id = bucket.upload_from_stream(path, data, metadata={'content_type': content_type})
    return {'path': f'gridfs:{file_id}', 'size': len(data)}


def get_object(path):
    if not path.startswith('gridfs:'):
        raise HTTPException(409, 'Berkas lama perlu dimigrasikan ke penyimpanan MongoDB oleh administrator.')
    try:
        return bucket.open_download_stream(ObjectId(path.split(':', 1)[1])).read()
    except (NoFile, ValueError):
        raise HTTPException(404, 'Berkas dokumen tidak ditemukan.')