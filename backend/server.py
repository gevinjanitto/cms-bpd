import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core import db, client
from seed import seed_data
from routes import router
from quiz_routes import router as quiz_router
from reports import router as report_router

@asynccontextmanager
async def lifespan(app):
    await db.sessions.create_index('token_hash', unique=True)
    await db.results.create_index([('quiz_id', 1), ('user_id', 1)], unique=True)
    await seed_data()
    yield
    client.close()

app = FastAPI(title='Bali Dwipa Jaya · Compliance Management System', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.environ['CORS_ORIGINS'].split(','), allow_credentials=False, allow_methods=['*'], allow_headers=['*'])
app.include_router(router, prefix='/api')
app.include_router(quiz_router, prefix='/api')
app.include_router(report_router, prefix='/api')