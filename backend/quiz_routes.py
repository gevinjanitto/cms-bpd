from typing import Literal, Union
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, model_validator
from pymongo.errors import DuplicateKeyError
from core import db, now, uid, current_user, require, audit, notify, get_doc, Record, eligible
from routes import ActionInput

router = APIRouter()
class Question(BaseModel):
    id: str
    text: str = Field(min_length=3, max_length=2000)
    type: Literal['multiple', 'essay']
    options: list[str] = []
    correct: int = 0
    @model_validator(mode='after')
    def validate_question(self):
        if self.type == 'multiple' and (len(self.options) != 4 or not all(o.strip() for o in self.options) or self.correct not in range(4)):
            raise ValueError('Pilihan ganda wajib memiliki empat opsi dan kunci jawaban yang benar.')
        return self
class QuizInput(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default='', max_length=3000)
    document_id: str
    passing_grade: int = Field(ge=1, le=100)
    duration: int = Field(ge=1, le=180)
    units: list[str] = []
    positions: list[str] = []
    start_date: date
    end_date: date
    questions: list[Question] = Field(min_length=1, max_length=100)
    @model_validator(mode='after')
    def dates_valid(self):
        if self.end_date < self.start_date: raise ValueError('Tanggal selesai harus setelah tanggal mulai.')
        if len({q.id for q in self.questions}) != len(self.questions): raise ValueError('ID soal harus unik.')
        return self
class AnswerInput(BaseModel):
    answers: dict[str, Union[int, str]]
class FeedbackInput(BaseModel):
    feedback: str = Field(max_length=3000)
class GradeInput(BaseModel):
    essay_scores: dict[str, float]
    note: str = Field(default='', max_length=3000)

def state(quiz):
    if quiz['status'] != 'published': return quiz['status']
    today = date.today().isoformat()
    return 'scheduled' if today < quiz['start_date'] else 'closed' if today > quiz['end_date'] else 'active'

@router.get('/quizzes', response_model=list[Record])
async def quizzes(user=Depends(current_user)):
    query = {'is_deleted': {'$ne': True}}
    if user['role'] in ['employee', 'director']: query['status'] = 'published'
    records = await db.quizzes.find(query, {'_id': 0}).sort('created_at', -1).to_list(1000)
    employees = await db.users.find({'role': 'employee', 'active': True}, {'_id': 0}).to_list(10000)
    counts = await db.results.aggregate([
        {'$match': {'quiz_id': {'$in': [q['id'] for q in records]}}},
        {'$group': {'_id': '$quiz_id', 'count': {'$sum': 1}}},
        {'$project': {'_id': 0, 'quiz_id': '$_id', 'count': 1}}
    ]).to_list(1000)
    completed = {row['quiz_id']: row['count'] for row in counts}
    my_results = {}
    if user['role'] == 'employee':
        mine = await db.results.find({'user_id': user['id']}, {'_id': 0, 'answers': 0}).to_list(1000)
        my_results = {r['quiz_id']: r for r in mine}
    output = []
    for q in records:
        if user['role'] == 'employee' and not eligible(q, user): continue
        q['state'] = state(q)
        q['question_count'] = len(q.pop('questions'))
        q['completed_count'] = completed.get(q['id'], 0)
        q['participant_count'] = sum(eligible(q, u) for u in employees)
        if user['role'] == 'employee': q['my_result'] = my_results.get(q['id'])
        output.append(q)
    return output

@router.post('/quizzes', response_model=Record)
async def create_quiz(body: QuizInput, request: Request, user=Depends(current_user)):
    require(user, 'administrator')
    doc = await get_doc('documents', body.document_id)
    if doc.get('is_active') is False: raise HTTPException(409, 'Regulasi nonaktif tidak dapat digunakan untuk kuis. Pilih regulasi aktif.')
    if doc['status'] != 'published': raise HTTPException(400, 'Kuis harus terkait regulasi yang sudah dipublikasikan.')
    quiz = {**body.model_dump(mode='json'), 'id': uid(), 'status': 'draft', 'created_by': user['id'], 'created_at': now(), 'updated_at': now(), 'is_deleted': False}
    await db.quizzes.insert_one(quiz.copy())
    await audit(user, 'CREATE', 'Kuis', body.title, request)
    return quiz

@router.get('/quizzes/{id}', response_model=Record)
async def quiz_detail(id: str, user=Depends(current_user)):
    quiz = await get_doc('quizzes', id)
    if user['role'] == 'employee':
        if not eligible(quiz, user) or quiz['status'] != 'published': raise HTTPException(403, 'Kuis tidak ditugaskan kepada Anda.')
        for q in quiz['questions']: q.pop('correct', None)
    elif user['role'] == 'director':
        raise HTTPException(403, 'Direksi hanya dapat melihat ringkasan kuis.')
    quiz['state'] = state(quiz)
    return quiz

@router.put('/quizzes/{id}', response_model=Record)
async def edit_quiz(id: str, body: QuizInput, request: Request, user=Depends(current_user)):
    require(user, 'administrator')
    q = await get_doc('quizzes', id)
    if q['status'] not in ['draft','rejected']: raise HTTPException(400, 'Kuis aktif tidak dapat diubah.')
    doc = await get_doc('documents', body.document_id)
    if doc.get('is_active') is False: raise HTTPException(409, 'Regulasi nonaktif tidak dapat digunakan untuk kuis. Pilih regulasi aktif.')
    if doc['status'] != 'published': raise HTTPException(400, 'Regulasi belum dipublikasikan.')
    data = {**body.model_dump(mode='json'), 'updated_at': now()}
    await db.quizzes.update_one({'id': id}, {'$set': data})
    await audit(user, 'UPDATE', 'Kuis', body.title, request)
    return {**q, **data}

@router.delete('/quizzes/{id}')
async def delete_quiz(id: str, request: Request, user=Depends(current_user)):
    require(user, 'administrator')
    q = await get_doc('quizzes', id)
    if q['status'] not in ['draft','rejected']: raise HTTPException(400, 'Hanya draf atau kuis ditolak yang dapat dihapus.')
    await db.quizzes.update_one({'id': id}, {'$set': {'is_deleted': True}})
    await audit(user, 'DELETE', 'Kuis', q['title'], request)
    return {'success': True}

@router.post('/quizzes/{id}/action', response_model=Record)
async def quiz_action(id: str, body: ActionInput, request: Request, user=Depends(current_user)):
    q = await get_doc('quizzes', id)
    if body.action == 'submit':
        require(user, 'administrator')
        if q['status'] not in ['draft','rejected']: raise HTTPException(400, 'Status kuis tidak sesuai.')
        status = 'pending'
    else:
        require(user, 'supervisor')
        if q['status'] != 'pending': raise HTTPException(400, 'Kuis belum diajukan untuk review.')
        if body.action == 'reject' and not body.reason.strip(): raise HTTPException(400, 'Alasan penolakan wajib diisi.')
        status = 'published' if body.action == 'approve' else 'rejected'
    if body.action in ('submit', 'approve'):
        doc = await get_doc('documents', q['document_id'])
        if doc.get('is_active') is False: raise HTTPException(409, 'Regulasi terkait nonaktif. Aktifkan regulasi atau pilih regulasi aktif sebelum melanjutkan.')
    await db.quizzes.update_one({'id': id}, {'$set': {'status': status, 'review_note': body.reason, 'updated_at': now()}})
    await audit(user, body.action.upper(), 'Kuis', q['title'], request)
    if status == 'published':
        employees = await db.users.find({'role': 'employee', 'active': True}, {'_id': 0}).to_list(10000)
        await notify('Kuis baru ditugaskan', q['title'], '/kuis', user_ids=[u['id'] for u in employees if eligible(q,u)])
    else: await notify('Review kuis' if status == 'pending' else 'Kuis ditolak', q['title'], '/kuis', roles=['supervisor'] if status == 'pending' else ['administrator'])
    return {**q, 'status': status}

@router.post('/quizzes/{id}/start')
async def start_quiz(id: str, user=Depends(current_user)):
    quiz = await get_doc('quizzes', id)
    if not eligible(quiz, user) or state(quiz) != 'active': raise HTTPException(403, 'Kuis tidak tersedia untuk Anda saat ini.')
    if await db.results.find_one({'quiz_id': id, 'user_id': user['id']}): raise HTTPException(400, 'Kuis sudah dikumpulkan.')
    attempt_id = id+'-'+user['id']
    await db.attempts.update_one({'id': attempt_id}, {'$setOnInsert': {'id': attempt_id, 'started_at': now()}}, upsert=True)
    attempt = await db.attempts.find_one({'id': attempt_id}, {'_id': 0})
    return {'started_at': attempt['started_at'], 'duration': quiz['duration']}

@router.post('/quizzes/{id}/submit', response_model=Record)
async def submit_quiz(id: str, body: AnswerInput, request: Request, user=Depends(current_user)):
    quiz = await get_doc('quizzes', id)
    if not eligible(quiz, user) or state(quiz) != 'active': raise HTTPException(403, 'Kuis tidak tersedia.')
    attempt = await db.attempts.find_one({'id': id+'-'+user['id']}, {'_id': 0})
    if not attempt: raise HTTPException(400, 'Mulai kuis terlebih dahulu.')
    elapsed = (datetime.now(timezone.utc)-datetime.fromisoformat(attempt['started_at'])).total_seconds()
    if elapsed > quiz['duration']*60 + 60: raise HTTPException(400, 'Waktu pengerjaan sudah berakhir.')
    if set(body.answers) != {q['id'] for q in quiz['questions']}: raise HTTPException(400, 'Jawab seluruh pertanyaan sebelum mengumpulkan.')
    correct = 0
    for q in quiz['questions']:
        answer = body.answers[q['id']]
        if q['type'] == 'multiple':
            if not isinstance(answer, int) or answer not in range(4): raise HTTPException(400, 'Jawaban pilihan ganda tidak valid.')
            correct += int(answer == q['correct'])
        elif not isinstance(answer, str) or not answer.strip() or len(answer)>10000: raise HTTPException(400, 'Jawaban esai wajib diisi, maksimal 10.000 karakter.')
    score = round(correct/len(quiz['questions'])*100, 1)
    has_essay = any(q['type']=='essay' for q in quiz['questions'])
    status = 'reviewing' if has_essay else 'passed' if score >= quiz['passing_grade'] else 'failed'
    result = {'id': uid(), 'quiz_id': id, 'quiz_title': quiz['title'], 'user_id': user['id'], 'user_name': user['name'], 'unit': user['unit'], 'position': user['position'], 'score': score, 'status': status, 'passing_grade': quiz['passing_grade'], 'answers': body.answers, 'submitted_at': now(), 'feedback': '', 'essay_scores': {}}
    try: await db.results.insert_one(result.copy())
    except DuplicateKeyError: raise HTTPException(409, 'Kuis sudah dikumpulkan sebelumnya.')
    await audit(user, 'SUBMIT', 'Kuis', quiz['title'], request)
    if has_essay: await notify('Jawaban esai menunggu penilaian', quiz['title'], '/monitoring?tab=essay', roles=['supervisor','administrator'])
    members = await db.users.find({'role': 'employee', 'unit': user['unit'], 'active': True}, {'_id': 0}).to_list(10000)
    assigned = [u['id'] for u in members if eligible(quiz, u)]
    done = await db.results.count_documents({'quiz_id': id, 'user_id': {'$in': assigned}})
    if assigned and done == len(assigned): await notify('Partisipasi unit lengkap', user['unit']+' telah menyelesaikan '+quiz['title'], '/monitoring', roles=['administrator','supervisor'])
    return result

@router.get('/results', response_model=list[Record])
async def results(user=Depends(current_user)):
    query = {'user_id': user['id']} if user['role'] == 'employee' else {}
    require(user, 'employee','administrator','supervisor')
    return await db.results.find(query, {'_id': 0}).sort('submitted_at', -1).to_list(5000)

@router.post('/results/{id}/feedback')
async def feedback(id: str, body: FeedbackInput, request: Request, user=Depends(current_user)):
    result = await get_doc('results', id)
    if result['user_id'] != user['id']: raise HTTPException(403, 'Hanya peserta yang dapat mengisi feedback.')
    await db.results.update_one({'id': id}, {'$set': {'feedback': body.feedback}})
    await audit(user, 'FEEDBACK', 'Kuis', result['quiz_title'], request)
    return {'success': True}

@router.post('/results/{id}/grade', response_model=Record)
async def grade(id: str, body: GradeInput, request: Request, user=Depends(current_user)):
    require(user, 'supervisor')
    result = await get_doc('results', id)
    quiz = await get_doc('quizzes', result['quiz_id'])
    if result['status'] != 'reviewing': raise HTTPException(400, 'Hasil ini sudah dinilai.')
    essay_ids = {q['id'] for q in quiz['questions'] if q['type']=='essay'}
    if set(body.essay_scores) != essay_ids or any(s<0 or s>100 for s in body.essay_scores.values()): raise HTTPException(400, 'Berikan nilai 0–100 untuk setiap jawaban esai.')
    points = sum(100 for q in quiz['questions'] if q['type']=='multiple' and result['answers'].get(q['id'])==q['correct'])+sum(body.essay_scores.values())
    score = round(points/len(quiz['questions']),1)
    update = {'score': score, 'status': 'passed' if score >= quiz['passing_grade'] else 'failed', 'essay_scores': body.essay_scores, 'review_note': body.note, 'graded_by': user['id'], 'graded_at': now()}
    await db.results.update_one({'id': id, 'status': 'reviewing'}, {'$set': update})
    await audit(user, 'GRADE', 'Kuis', result['user_name']+' · '+quiz['title'], request)
    await notify('Hasil kuis telah dinilai', quiz['title'], '/hasil', user_ids=[result['user_id']])
    return {**result, **update}