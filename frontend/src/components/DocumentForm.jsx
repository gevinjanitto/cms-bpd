import React, { useState } from 'react';
import { UploadCloud } from 'lucide-react';
import { toast } from 'sonner';
import { api, units } from '../lib/api';
import { Modal, Field, Btn } from './common';

export const DocumentForm = ({ initial, onClose, onSaved }) => {
  const [form, setForm] = useState(initial), [file, setFile] = useState(null), [busy, setBusy] = useState(false), [id, setId] = useState(initial.id);
  const change = (key, value) => setForm(f => ({ ...f, [key]: value }));
  const save = async e => {
    e.preventDefault(); setBusy(true);
    try {
      let docId = id;
      if (docId) await api.put(`/documents/${docId}`, form);
      else { const { data } = await api.post('/documents', form); docId = data.id; setId(docId); }
      if (file) { const upload = new FormData(); upload.append('file', file); await api.post(`/documents/${docId}/upload`, upload); }
      toast.success('Draf regulasi berhasil disimpan.'); onSaved();
    } catch {} finally { setBusy(false); }
  };
  return <Modal title={initial.id ? 'Edit Regulasi' : 'Tambah Regulasi'} open onClose={() => !busy && onClose()} wide>
    <form onSubmit={save}><div className="form-grid">
      <Field label="Judul Regulasi *" className="field-full"><input data-testid="document-title-input" required minLength={3} maxLength={200} value={form.title} onChange={e => change('title', e.target.value)} placeholder="Contoh: Pedoman Penerapan APU dan PPT" /></Field>
      <Field label="Nomor Regulasi *"><input data-testid="document-number-input" required minLength={3} maxLength={100} value={form.number} onChange={e => change('number', e.target.value)} placeholder="001/SK/DIR/2026" /></Field>
      <Field label="Kategori"><select data-testid="document-category-input" value={form.category} onChange={e => change('category', e.target.value)}><option>Internal</option><option>Eksternal</option></select></Field>
      <Field label="Unit Pemilik"><select data-testid="document-unit-input" value={form.unit} onChange={e => change('unit', e.target.value)}>{units.map(u => <option key={u}>{u}</option>)}</select></Field>
      <Field label="Versi"><input data-testid="document-version-input" required value={form.version} onChange={e => change('version', e.target.value)} /></Field>
      <Field label="Ringkasan Regulasi" className="field-full"><textarea data-testid="document-description-input" maxLength={10000} rows={3} value={form.description} onChange={e => change('description', e.target.value)} placeholder="Ringkasan isi dan ruang lingkup regulasi..." /></Field>
      <Field label="Berkas Dokumen" className="field-full"><div className="upload-zone"><UploadCloud size={27} /><span data-testid="document-file-name">{file?.name || initial.filename || 'Pilih berkas regulasi'}</span><input data-testid="document-file-input" type="file" accept=".pdf,.docx" onChange={e => setFile(e.target.files[0])} /><small>PDF atau DOCX · Maksimal 10 MB</small></div></Field>
    </div><div className="form-actions"><Btn type="button" secondary data-testid="document-form-cancel" onClick={onClose} disabled={busy}>Batal</Btn><Btn type="submit" data-testid="document-form-save" disabled={busy}>{busy ? 'Menyimpan...' : 'Simpan Draf'}</Btn></div></form>
  </Modal>;
};