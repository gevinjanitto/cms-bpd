import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Save } from 'lucide-react';
import { toast } from 'sonner';
import { api, units } from '../lib/api';
import { Modal, Field, Btn, IconBtn } from './common';

const newQuestion = () => ({ id: crypto.randomUUID(), text: '', type: 'multiple', options: ['', '', '', ''], correct: 0 });
export const QuizForm = ({ initial, onClose, onSaved }) => {
  const today = new Date().toLocaleDateString('en-CA');
  const [form, setForm] = useState(initial || { title: '', description: '', document_id: '', passing_grade: 75, duration: 30, units: [], positions: [], start_date: today, end_date: today, questions: [newQuestion()] });
  const [docs, setDocs] = useState([]), [busy, setBusy] = useState(false);
  useEffect(() => {
    api.get('/documents?status=published&active=true').then(r => setDocs(r.data)).catch(() => {});
    if (!initial) api.get('/settings').then(r => setForm(f => ({ ...f, passing_grade: r.data.passing_grade, duration: r.data.quiz_duration }))).catch(() => {});
  }, [initial]);
  const change = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const question = (index, k, v) => setForm(f => ({ ...f, questions: f.questions.map((q, i) => i === index ? { ...q, [k]: v } : q) }));
  const save = async e => {
    e.preventDefault();
    if (form.end_date < form.start_date) { toast.error('Tanggal selesai harus setelah tanggal mulai.'); return; }
    setBusy(true);
    try {
      if (initial?.id) await api.put(`/quizzes/${initial.id}`, form); else await api.post('/quizzes', form);
      toast.success('Draf kuis berhasil disimpan.'); onSaved();
    } catch {} finally { setBusy(false); }
  };
  return <Modal title={initial ? 'Edit Kuis' : 'Buat Kuis Baru'} description="Materi evaluasi pemahaman regulasi" open onClose={() => !busy && onClose()} wide>
    <form onSubmit={save}><div className="form-grid">
      <Field className="field-full" label="Judul Kuis *"><input data-testid="quiz-title-input" required minLength={3} value={form.title} onChange={e => change('title', e.target.value)} placeholder="Contoh: Pemahaman Regulasi APU & PPT" /></Field>
      <Field className="field-full" label="Regulasi Terkait *"><select data-testid="quiz-document-input" required value={form.document_id} onChange={e => change('document_id', e.target.value)}><option value="">Pilih regulasi aktif yang sudah dipublikasikan</option>{form.document_id && !docs.some(d => d.id === form.document_id) && <option value={form.document_id} disabled>Regulasi tidak tersedia — pilih regulasi aktif</option>}{docs.map(d => <option key={d.id} value={d.id}>{d.title}</option>)}</select></Field>
      <Field className="field-full" label="Deskripsi"><textarea data-testid="quiz-description-input" rows={2} value={form.description} onChange={e => change('description', e.target.value)} placeholder="Ruang lingkup evaluasi..." /></Field>
      <Field label="Tanggal Mulai"><input data-testid="quiz-start-input" type="date" required value={form.start_date} onChange={e => change('start_date', e.target.value)} /></Field>
      <Field label="Tanggal Selesai"><input data-testid="quiz-end-input" type="date" required min={form.start_date} value={form.end_date} onChange={e => change('end_date', e.target.value)} /></Field>
      <Field label="Durasi (menit)"><input data-testid="quiz-duration-input" type="number" required min={1} max={180} value={form.duration} onChange={e => change('duration', Number(e.target.value))} /></Field>
      <Field label="Passing Grade"><input data-testid="quiz-grade-input" type="number" required min={1} max={100} value={form.passing_grade} onChange={e => change('passing_grade', Number(e.target.value))} /></Field>
      <Field label="Target Unit Kerja"><select data-testid="quiz-unit-input" value={form.units[0] || ''} onChange={e => change('units', e.target.value ? [e.target.value] : [])}><option value="">Semua Unit Kerja</option>{units.map(u => <option key={u}>{u}</option>)}</select></Field>
      <Field label="Target Jabatan"><select data-testid="quiz-position-input" value={form.positions[0] || ''} onChange={e => change('positions', e.target.value ? [e.target.value] : [])}><option value="">Semua Jabatan</option><option>Officer</option><option>Kepala Unit</option></select></Field>
    </div><div className="question-section">
      <header><h3 data-testid="quiz-question-count">Daftar Pertanyaan ({form.questions.length})</h3><Btn type="button" secondary data-testid="quiz-add-question" onClick={() => change('questions', [...form.questions, newQuestion()])}><Plus size={15} />Tambah Soal</Btn></header>
      {form.questions.map((q, i) => <div className="question-editor" data-testid={`question-editor-${i}`} key={q.id}>
        <div className="question-editor-head"><strong data-testid={`question-number-${i}`}>Soal {i + 1}</strong><div>
          <select data-testid={`question-type-${i}`} value={q.type} onChange={e => question(i, 'type', e.target.value)}><option value="multiple">Pilihan Ganda</option><option value="essay">Esai</option></select>
          <IconBtn label="Hapus soal" type="button" data-testid={`question-delete-${i}`} disabled={form.questions.length === 1} onClick={() => change('questions', form.questions.filter((_, j) => j !== i))}><Trash2 size={15} /></IconBtn>
        </div></div>
        <Field label="Pertanyaan"><textarea data-testid={`question-text-${i}`} required minLength={3} rows={2} value={q.text} onChange={e => question(i, 'text', e.target.value)} /></Field>
        {q.type === 'multiple' && <div className="options-grid">{q.options.map((o, j) => <label className="option-edit" key={j}>
          <input data-testid={`question-correct-${i}-${j}`} aria-label={`Kunci jawaban ${String.fromCharCode(65 + j)}`} type="radio" name={`correct-${q.id}`} checked={q.correct === j} onChange={() => question(i, 'correct', j)} />
          <input data-testid={`question-option-${i}-${j}`} type="text" required value={o} placeholder={`Pilihan ${String.fromCharCode(65 + j)}`} onChange={e => question(i, 'options', q.options.map((v, k) => k === j ? e.target.value : v))} />
        </label>)}</div>}
      </div>)}
    </div><div className="form-actions"><Btn type="button" secondary data-testid="quiz-form-cancel" disabled={busy} onClick={onClose}>Batal</Btn><Btn type="submit" data-testid="quiz-form-save" disabled={busy}><Save size={15} />{busy ? 'Menyimpan...' : 'Simpan Draf Kuis'}</Btn></div></form>
  </Modal>;
};