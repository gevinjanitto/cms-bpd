import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Bell, Users, BadgeCheck, ClipboardCheck, Check } from 'lucide-react';
import { toast } from 'sonner';
import { api, dateLabel } from '../lib/api';
import { PageHead, Btn, Stat, Badge, Loading, Empty, SearchBox, Modal, Field } from '../components/common';
import { ExportMenu } from '../components/ExportMenu';
import { PeriodFilter, UnitFilter } from './Dashboard';

export default function Monitoring({ user }) {
  const [params] = useSearchParams();
  const [tab, setTab] = useState(params.get('tab') || 'units'), [unit, setUnit] = useState(''), [period, setPeriod] = useState('2026');
  const [data, setData] = useState(null), [dashboard, setDashboard] = useState(null), [q, setQ] = useState('');
  const [quizId, setQuizId] = useState(params.get('quiz') || ''), [quizzes, setQuizzes] = useState([]), [essay, setEssay] = useState(null);
  const [busy, setBusy] = useState(false), [remindConfirm, setRemindConfirm] = useState(false);
  const load = useCallback(() => Promise.all([api.get('/monitoring', { params: { unit, period } }), api.get('/dashboard', { params: { unit, period } })]).then(([r, d]) => { setData(r.data); setDashboard(d.data); }).catch(() => {}), [unit, period]);
  useEffect(() => { load(); }, [load, user]);
  useEffect(() => { api.get('/quizzes').then(r => setQuizzes(r.data)).catch(() => {}); }, []);
  useEffect(() => { setTab(params.get('tab') || (params.get('quiz') ? 'results' : 'units')); setQuizId(params.get('quiz') || ''); }, [params]);
  const remind = async () => {
    setBusy(true);
    try { const { data } = await api.post('/monitoring/remind', { unit, period }); toast.success(`Pengingat dalam aplikasi dikirim ke ${data.count} karyawan.`); setRemindConfirm(false); }
    catch {} finally { setBusy(false); }
  };
  const grade = async result => {
    try { const [r, d] = await Promise.all([api.get('/results'), api.get(`/quizzes/${result.quiz_id}`)]); setEssay({ result: r.data.find(x => x.id === result.id), quiz: d.data }); } catch {}
  };
  if (!data || !dashboard) return <Loading />;
  const m = dashboard.metrics;
  const tabs = [['units', 'Per Unit Kerja'], ['results', 'Hasil Kuis'], ['pending', 'Belum Mengikuti'], ['top', '10 Nilai Terbaik'], ['bottom', '10 Nilai Terendah'], ['never', 'Tidak Pernah Mengikuti'], ...(user.role !== 'director' ? [['essay', 'Penilaian Esai']] : [])];
  const resultTab = ['results', 'essay', 'pending'].includes(tab);
  const source = tab === 'units' ? dashboard.units : tab === 'essay' ? data.results.filter(r => r.status === 'reviewing') : data[tab] || [];
  const rows = source.filter(r => `${r.user_name || r.name || ''} ${r.unit} ${r.quiz_title || ''}`.toLowerCase().includes(q.toLowerCase()) && (!quizId || !resultTab || r.quiz_id === quizId));
  const headers = tab === 'units' ? ['UNIT KERJA', 'KARYAWAN', 'SELESAI / PENUGASAN', 'PARTISIPASI', 'RATA-RATA NILAI', 'KELULUSAN'] : resultTab ? ['KARYAWAN', 'UNIT KERJA', 'KUIS', tab === 'pending' ? 'TENGGAT' : 'NILAI', 'STATUS', ...(tab === 'essay' ? ['AKSI'] : [])] : ['PERINGKAT', 'KARYAWAN', 'UNIT KERJA', 'SELESAI / PENUGASAN', 'RATA-RATA NILAI'];
  return <>
    <PageHead eyebrow="ANALITIK & EVALUASI" title="Monitoring & Laporan" subtitle="Pantau partisipasi, hasil evaluasi, dan pemahaman ketentuan di seluruh unit kerja."><ExportMenu id="monitoring-export" params={{ unit, period, view: tab, q, quiz_id: resultTab ? quizId : '' }} />{user.role !== 'director' && <Btn data-testid="monitoring-remind" onClick={() => setRemindConfirm(true)}><Bell size={15} />Kirim Pengingat</Btn>}</PageHead>
    <div className="toolbar"><div><PeriodFilter value={period} onChange={setPeriod} /><UnitFilter value={unit} onChange={setUnit} /></div></div>
    <div className="metrics-inline"><Stat id="monitoring-completed" label="Penugasan Selesai" value={m.completed} icon={ClipboardCheck} detail={`Dari ${m.assigned} penugasan kuis`} /><Stat id="monitoring-pending" label="Belum Mengikuti" value={m.pending} icon={Users} tone="gold" detail="Penugasan yang belum diselesaikan" /><Stat id="monitoring-average" label="Rata-rata Nilai" value={m.average} icon={BadgeCheck} detail={`${m.pass_rate}% tingkat kelulusan`} /></div>
    <div className="tab-bar">{tabs.map(([v, l]) => <button key={v} className={tab === v ? 'active' : ''} data-testid={`monitoring-tab-${v}`} onClick={() => setTab(v)}>{l}</button>)}</div>
    <div className="toolbar"><SearchBox id="monitoring-search" value={q} onChange={setQ} placeholder="Cari karyawan atau unit kerja..." />{resultTab && <select data-testid="monitoring-quiz-filter" value={quizId} onChange={e => setQuizId(e.target.value)}><option value="">Semua Kuis</option>{quizzes.map(q => <option key={q.id} value={q.id}>{q.title}</option>)}</select>}</div>
    <div className="content-table"><div className="table-scroll"><table className="data-table" data-testid="monitoring-table"><thead><tr>{headers.map(t => <th key={t}>{t}</th>)}</tr></thead><tbody>{rows.map((r, i) => <tr key={r.id || r.unit} data-testid={`monitoring-row-${i}`}>
      {tab === 'units' ? <><td><strong>{r.unit}</strong></td><td>{r.employees}</td><td>{r.completed} / {r.assigned}</td><td><div className="table-progress"><div><i style={{ width: `${r.participation}%` }} /></div>{r.participation}%</div></td><td>{r.average}</td><td>{r.pass_rate}%</td></> : resultTab ? <><td>{r.user_name}</td><td>{r.unit}</td><td>{r.quiz_title}</td><td>{tab === 'pending' ? dateLabel(r.deadline) : r.score}</td><td><Badge status={tab === 'pending' ? 'Belum mengikuti' : r.status} id={`monitoring-status-${r.id}`} /></td>{tab === 'essay' && <td>{user.role === 'supervisor' ? <Btn secondary data-testid={`essay-grade-${r.id}`} onClick={() => grade(r)}>Nilai Esai</Btn> : <span className="muted">Menunggu supervisor</span>}</td>}</> : <><td><span className="avatar" style={{ width: 27, height: 27, borderRadius: 5 }}>{i + 1}</span></td><td>{r.name}</td><td>{r.unit}</td><td>{r.completed} / {r.assigned}</td><td>{r.completed ? r.average : '—'}</td></>}
    </tr>)}</tbody></table></div>{!rows.length && <Empty text="Tidak ada data untuk filter dan periode ini." />}<div className="table-bottom"><span data-testid="monitoring-row-count">{rows.length} data ditampilkan</span><span>{period === 'all' ? 'Semua Periode' : period.replace('-', ' · ')}</span></div></div>
    <Modal title="Kirim Pengingat Kuis" open={remindConfirm} onClose={() => setRemindConfirm(false)}><p data-testid="reminder-confirmation">Pengingat dalam aplikasi akan dikirim kepada karyawan yang belum menyelesaikan penugasan pada {unit || 'semua unit kerja'} dalam periode terpilih.</p><div className="form-actions"><Btn secondary data-testid="reminder-cancel" onClick={() => setRemindConfirm(false)}>Batal</Btn><Btn data-testid="reminder-confirm" disabled={busy} onClick={remind}>{busy ? 'Mengirim...' : 'Kirim Pengingat'}</Btn></div></Modal>
    {essay && <EssayGrade data={essay} onClose={() => setEssay(null)} onSaved={() => { setEssay(null); load(); }} />}
  </>;
}

function EssayGrade({ data, onClose, onSaved }) {
  const [scores, setScores] = useState({}), [note, setNote] = useState(''), [busy, setBusy] = useState(false);
  const essays = data.quiz.questions.filter(q => q.type === 'essay');
  const save = async e => {
    e.preventDefault(); setBusy(true);
    try { await api.post(`/results/${data.result.id}/grade`, { essay_scores: scores, note }); toast.success('Penilaian esai berhasil disimpan.'); onSaved(); }
    catch {} finally { setBusy(false); }
  };
  return <Modal title="Penilaian Jawaban Esai" description={`${data.result.user_name} · ${data.quiz.title}`} open onClose={onClose} wide><form onSubmit={save}>{essays.map((q, i) => <div className="question-editor" key={q.id}><h3 style={{ fontSize: 14 }}>{i + 1}. {q.text}</h3><div className="info-note" data-testid={`essay-answer-${i}`}>{data.result.answers[q.id]}</div><Field label="Nilai (0–100)"><input data-testid={`essay-score-${i}`} type="number" min={0} max={100} step="0.1" required value={scores[q.id] ?? ''} onChange={e => setScores(s => ({ ...s, [q.id]: Number(e.target.value) }))} /></Field></div>)}<Field label="Catatan untuk peserta"><textarea data-testid="essay-note-input" rows={3} value={note} onChange={e => setNote(e.target.value)} /></Field><div className="form-actions"><Btn type="button" secondary data-testid="essay-cancel" onClick={onClose}>Batal</Btn><Btn type="submit" data-testid="essay-save" disabled={busy}><Check size={15} />Simpan Penilaian</Btn></div></form></Modal>;
}