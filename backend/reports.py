import csv, io, asyncio
from datetime import datetime, date
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import Response
from core import db, uid, current_user, require, audit, notify, eligible
from quiz_routes import state
from pydantic import BaseModel
from typing import Literal
from exporting import report_data, csv_bytes, xlsx_bytes

router = APIRouter()
def in_period(value, period):
    if not period or period == 'all': return True
    year, *part = period.split('-')
    if value[:4] != year: return False
    if not part: return True
    month = int(value[5:7])
    if part[0].startswith('Q'): return (month-1)//3+1 == int(part[0][1:])
    if part[0].startswith('S'): return (month-1)//6+1 == int(part[0][1:])
    return False

async def aggregate(unit='', period='', user=None):
    users, quizzes = await asyncio.gather(
        db.users.find({'role': 'employee', 'active': True}, {'_id': 0}).to_list(10000),
        db.quizzes.find({'status':'published', 'is_deleted': {'$ne':True}}, {'_id':0, 'questions':0}).to_list(1000))
    if unit: users = [u for u in users if u['unit']==unit]
    if user and user['role']=='employee': users = [u for u in users if u['id']==user['id']]
    quizzes = [q for q in quizzes if in_period(q['start_date'],period)]
    ids = {u['id'] for u in users}
    qids = {q['id'] for q in quizzes}
    results = await db.results.find({'quiz_id': {'$in':list(qids)}, 'user_id': {'$in':list(ids)}}, {'_id':0, 'answers':0, 'essay_scores':0}).to_list(100000)
    pairs = {(q['id'],u['id']) for q in quizzes for u in users if eligible(q,u)}
    results = [r for r in results if (r['quiz_id'],r['user_id']) in pairs]
    done = {(r['quiz_id'],r['user_id']) for r in results}
    pending = [{'id': q['id']+'-'+u['id'], 'quiz_id':q['id'], 'quiz_title':q['title'], 'user_id':u['id'], 'user_name':u['name'], 'unit':u['unit'], 'position':u['position'], 'deadline':q['end_date'], 'status':'Belum mengikuti'} for q in quizzes for u in users if (q['id'],u['id']) in pairs-done]
    return users,quizzes,results,pairs,pending

@router.get('/dashboard')
async def dashboard(unit: str='', period: str='', user=Depends(current_user)):
    (users,quizzes,results,pairs,pending), docs = await asyncio.gather(aggregate(unit,period,user), db.documents.find({'is_deleted': {'$ne':True}, 'is_active': {'$ne':False}}, {'_id':0, 'storage_path':0}).to_list(1000))
    published = [d for d in docs if d['status']=='published']
    graded = [r for r in results if r['status'] != 'reviewing']
    passed = sum(r['status']=='passed' for r in graded)
    average = round(sum(r['score'] for r in graded)/len(graded),1) if graded else 0
    units = []
    for name in sorted({u['unit'] for u in users}):
        members = [u for u in users if u['unit']==name]
        member_ids = {u['id'] for u in members}
        assigned = sum(p[1] in member_ids for p in pairs)
        done = [r for r in results if r['unit']==name]
        scored = [r for r in done if r['status']!='reviewing']
        units.append({'unit':name, 'employees':len(members), 'assigned':assigned, 'completed':len(done), 'pending':assigned-len(done), 'participation':round(len(done)/assigned*100,1) if assigned else 0, 'average':round(sum(r['score'] for r in scored)/len(scored),1) if scored else 0, 'pass_rate':round(sum(r['status']=='passed' for r in scored)/len(scored)*100,1) if scored else 0})
    units.sort(key=lambda u:u['participation'],reverse=True)
    months=['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des']
    trend=[]
    current_month = date.today().month
    year = period[:4] if period and period!='all' else str(date.today().year)
    for m in range(max(1,current_month-5),current_month+1):
        prefix=f'{year}-{m:02}'
        month_quizzes = {q['id'] for q in quizzes if q['start_date'].startswith(prefix)}
        subset=[r for r in graded if r['quiz_id'] in month_quizzes]
        total=sum(p[0] in month_quizzes for p in pairs)
        submitted=sum(r['quiz_id'] in month_quizzes for r in results)
        trend.append({'month':months[m-1], 'participation':round(submitted/total*100,1) if total else 0, 'score':round(sum(r['score'] for r in subset)/len(subset),1) if subset else 0})
    return {'metrics': {'documents':len(published),'internal':sum(d['category']=='Internal' for d in published),'external':sum(d['category']=='Eksternal' for d in published),'active_quizzes':sum(state(q)=='active' for q in quizzes),'employees':len(users),'assigned':len(pairs),'completed':len(results),'pending':len(pending),'participation':round(len(results)/len(pairs)*100,1) if pairs else 0,'average':average,'pass_rate':round(passed/len(graded)*100,1) if graded else 0,'passed':passed,'failed':len(graded)-passed,'reviewing':len(results)-len(graded)}, 'trend':trend,'units':units,'recent_documents':[{k:v for k,v in d.items() if k!='storage_path'} for d in sorted(published,key=lambda x:x['created_at'],reverse=True)[:4]],'tasks':{'documents':sum(d['status']=='pending' for d in docs) if user['role'] in ['administrator','supervisor'] else 0,'essays':sum(r['status']=='reviewing' for r in results),'quizzes':sum(state(q)=='active' for q in quizzes)},'quizzes':[{k:v for k,v in q.items() if k!='questions'} for q in quizzes if state(q)=='active']}

@router.get('/monitoring')
async def monitoring(unit: str='', period: str='', user=Depends(current_user)):
    require(user,'administrator','supervisor','director')
    users,quizzes,results,pairs,pending = await aggregate(unit,period)
    rows=[]
    for u in users:
        scores=[r for r in results if r['user_id']==u['id'] and r['status']!='reviewing']
        total=sum(p[1]==u['id'] for p in pairs)
        rows.append({'id':u['id'],'name':u['name'],'unit':u['unit'],'position':u['position'],'completed':sum(r['user_id']==u['id'] for r in results),'assigned':total,'average':round(sum(r['score'] for r in scores)/len(scores),1) if scores else 0})
    participated=[r for r in rows if r['completed']]
    safe_results=[{k:v for k,v in r.items() if k not in ['answers','essay_scores']} for r in results]
    return {'results':safe_results,'pending':pending,'top':sorted(participated,key=lambda r:r['average'],reverse=True)[:10],'bottom':sorted(participated,key=lambda r:r['average'])[:10],'never':[r for r in rows if r['completed']==0 and r['assigned']>0][:10],'employees':rows}

class ReminderInput(BaseModel):
    unit: str=''
    period: str=''
@router.post('/monitoring/remind')
async def remind(body: ReminderInput, request: Request, user=Depends(current_user)):
    require(user,'administrator','supervisor')
    *_, pending = await aggregate(body.unit,body.period)
    ids=list({p['user_id'] for p in pending})
    if ids: await notify('Pengingat kuis kepatuhan', 'Masih ada kuis yang belum Anda selesaikan. Periksa jadwal penugasan Anda.', '/kuis', user_ids=ids)
    await audit(user,'REMINDER','Monitoring',f'Pengingat dalam aplikasi dikirim kepada {len(ids)} karyawan',request)
    return {'count':len(ids)}

@router.get('/reports/export')
async def export(unit: str='', period: str='', quiz_id: str='', q: str='', view: Literal['all','units','results','pending','essay','top','bottom','never']='all', format: Literal['csv','xlsx']='csv', request: Request=None, user=Depends(current_user)):
    require(user,'administrator','supervisor','director')
    users,quizzes,results,pairs,pending = await aggregate(unit,period)
    if quiz_id:
        quizzes = [quiz for quiz in quizzes if quiz['id'] == quiz_id]
        results = [r for r in results if r['quiz_id'] == quiz_id]
        pending = [r for r in pending if r['quiz_id'] == quiz_id]
        pairs = {pair for pair in pairs if pair[0] == quiz_id}
    headers, rows = report_data(users,quizzes,results,pairs,pending,view,q)
    content = xlsx_bytes(headers,rows,period,unit) if format == 'xlsx' else csv_bytes(headers,rows)
    media = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if format == 'xlsx' else 'text/csv; charset=utf-8'
    await audit(user,'EXPORT','Laporan',f'Mengunduh laporan {format.upper()} · {len(rows)} baris · {view}',request)
    return Response(content,media_type=media,headers={'Content-Disposition':f'attachment; filename="laporan-kepatuhan.{format}"'})