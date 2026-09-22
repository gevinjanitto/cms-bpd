import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Plus, FileText, Download, Eye, Pencil, Trash2, Send, Check, X } from 'lucide-react';
import { toast } from 'sonner';
import { api, download, dateLabel, units } from '../lib/api';
import { PageHead, Btn, IconBtn, Modal, Field, SearchBox, Badge, Empty, Loading } from '../components/common';
import { DocumentForm } from '../components/DocumentForm';
import { DocumentAvailability, DocumentActivationModal } from '../components/DocumentActivation';

const blank = { title: '', number: '', category: 'Internal', unit: units[0], description: '', version: '1.0' };
export default function Documents({ user }) {
  const [params] = useSearchParams();
  const [docs, setDocs] = useState(null), [q, setQ] = useState(params.get('q') || ''), [category, setCategory] = useState(''), [status, setStatus] = useState(params.get('status') || '');
  const [editing, setEditing] = useState(null), [detail, setDetail] = useState(null), [remove, setRemove] = useState(null), [reject, setReject] = useState(null), [reason, setReason] = useState(''), [busy, setBusy] = useState(false);
  const [availability, setAvailability] = useState(''), [activation, setActivation] = useState(null);
  const admin = user.role === 'administrator', supervisor = user.role === 'supervisor';
  const load = () => api.get('/documents').then(r => setDocs(r.data)).catch(() => {});
  useEffect(() => { load(); }, [user]);
  useEffect(() => { setQ(params.get('q') || ''); setStatus(params.get('status') || ''); }, [params]);
  const action = async (doc, action, reason = '') => {
    setBusy(true);
    try {
      await api.post(`/documents/${doc.id}/action`, { action, reason });
      toast.success(action === 'approve' ? 'Regulasi disetujui dan dipublikasikan.' : action === 'submit' ? 'Regulasi diajukan untuk review.' : 'Regulasi ditolak dengan catatan.');
      setDetail(null); setReject(null); load();
    } catch {} finally { setBusy(false); }
  };
  const destroy = async () => { setBusy(true); try { await api.delete(`/documents/${remove.id}`); toast.success('Draf regulasi dihapus.'); setRemove(null); load(); } catch {} finally { setBusy(false); } };
  const downloadDocument = doc => download(`/documents/${doc.id}/download`, doc.filename || `${doc.title}-contoh.txt`).catch(() => {});
  if (!docs) return <Loading />;
  const filtered = docs.filter(d => (!availability || (d.is_active !== false) === (availability === 'active')) && (!category || d.category === category) && (!status || d.status === status) && `${d.title} ${d.number}`.toLowerCase().includes(q.toLowerCase()));
  const tabs = [['', 'Semua Regulasi'], ['published', 'Dipublikasikan'], ...(admin || supervisor ? [['pending', 'Menunggu Review'], ['draft', 'Draf'], ['rejected', 'Ditolak']] : [])];
  return <>
    <PageHead eyebrow="DOKUMEN & REGULASI" title="Regulasi" subtitle="Kelola regulasi internal dan eksternal dalam satu repositori terpusat.">{admin && <Btn data-testid="document-create" onClick={() => setEditing({ ...blank })}><Plus size={16} />Tambah Regulasi</Btn>}</PageHead>
    <div className="tab-bar">{tabs.map(([v, label]) => <button data-testid={`document-tab-${v || 'all'}`} className={status === v ? 'active' : ''} onClick={() => setStatus(v)} key={v}>{label}<span>{docs.filter(d => !v || d.status === v).length}</span></button>)}</div>
    <div className="toolbar"><div><SearchBox id="document-search" value={q} onChange={setQ} placeholder="Cari judul atau nomor regulasi..." /></div><div><select data-testid="document-category-filter" value={category} onChange={e => setCategory(e.target.value)}><option value="">Semua Kategori</option><option>Internal</option><option>Eksternal</option></select>{admin && <select data-testid="document-availability-filter" aria-label="Status aktivasi regulasi" value={availability} onChange={e => setAvailability(e.target.value)}><option value="">Aktif & Nonaktif</option><option value="active">Aktif</option><option value="inactive">Nonaktif</option></select>}<span className="muted" data-testid="document-count">{filtered.length} dokumen</span></div></div>
    <div className="content-table"><div className="table-scroll"><table className="data-table" data-testid="documents-table">
      <thead><tr><th data-testid="document-table-title">REGULASI</th><th>KATEGORI</th><th>UNIT PEMILIK</th><th>TANGGAL</th><th>STATUS</th>{admin && <th>AKTIVASI</th>}<th>AKSI</th></tr></thead>
      <tbody>{filtered.map(d => <tr key={d.id} data-testid={`document-row-${d.id}`}>
        <td><div className="doc-title-cell"><span className="file-icon"><FileText size={20} /></span><div><strong data-testid={`document-title-${d.id}`}>{d.title}</strong><small data-testid={`document-number-${d.id}`}>{d.number}</small></div></div></td>
        <td><Badge status={d.category} id={`doc-category-${d.id}`} /></td><td>{d.unit}</td><td>{dateLabel(d.created_at)}</td><td><Badge status={d.status} id={`doc-status-${d.id}`} /></td>
        {admin && <td><DocumentAvailability document={d} id={`document-availability-${d.id}`} onChange={setActivation} /></td>}
        <td><div className="table-actions">
          <IconBtn label="Lihat regulasi" data-testid={`document-view-${d.id}`} onClick={() => setDetail(d)}><Eye size={16} /></IconBtn>
          {(d.filename || d.sample) && <IconBtn label="Unduh dokumen" data-testid={`document-download-${d.id}`} onClick={() => downloadDocument(d)}><Download size={16} /></IconBtn>}
          {admin && ['draft', 'rejected'].includes(d.status) && <><IconBtn label="Edit regulasi" data-testid={`document-edit-${d.id}`} onClick={() => setEditing(d)}><Pencil size={15} /></IconBtn><IconBtn label="Hapus draf" data-testid={`document-delete-${d.id}`} onClick={() => setRemove(d)}><Trash2 size={15} /></IconBtn></>}
          {supervisor && d.status === 'pending' && <Btn secondary data-testid={`document-review-${d.id}`} onClick={() => setDetail(d)}>Review</Btn>}
        </div></td>
      </tr>)}</tbody>
    </table></div>{!filtered.length && <Empty text="Tidak ada regulasi yang sesuai dengan pencarian." />}<div className="table-bottom"><span data-testid="document-table-summary">Menampilkan {filtered.length} dari {docs.length} regulasi</span><span data-testid="document-repository-label">Repositori Regulasi</span></div></div>
    {editing && <DocumentForm initial={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />}
    <Modal title={detail?.title} open={!!detail} onClose={() => setDetail(null)} wide>{detail && <>
      <div className="details-meta"><div data-testid="document-detail-number"><small>Nomor Regulasi</small>{detail.number}</div><div><small>Status</small><Badge status={detail.status} id="document-detail-status" /></div><div data-testid="document-detail-unit"><small>Unit Pemilik</small>{detail.unit}</div><div data-testid="document-detail-version"><small>Kategori / Versi</small>{detail.category} / v{detail.version}</div></div>
      {admin && <DocumentAvailability document={detail} id="document-detail-availability" onChange={doc => { setDetail(null); setActivation(doc); }} />}
      <p className="detail-description" data-testid="document-description">{detail.description || 'Tidak ada ringkasan regulasi.'}</p>
      {detail.review_note && <div className="info-note danger-note" data-testid="document-review-note">Catatan supervisor: {detail.review_note}</div>}
      {detail.sample && <div className="info-note" data-testid="document-sample-note">Dokumen contoh untuk ruang demo, bukan regulasi resmi bank.</div>}
      <div className="form-actions">
        {(detail.filename || detail.sample) && <Btn secondary data-testid="document-detail-download" onClick={() => downloadDocument(detail)}><Download size={16} />Unduh {detail.sample && !detail.filename ? 'Materi Contoh' : 'Dokumen'}</Btn>}
        {admin && ['draft', 'rejected'].includes(detail.status) && <Btn disabled={busy || detail.is_active === false} data-testid="document-submit-review" onClick={() => action(detail, 'submit')}><Send size={15} />Ajukan Review</Btn>}
        {supervisor && detail.status === 'pending' && <><Btn secondary disabled={busy} data-testid="document-reject" onClick={() => { setReject(detail); setDetail(null); setReason(''); }}><X size={15} />Tolak</Btn><Btn disabled={busy} data-testid="document-approve" onClick={() => action(detail, 'approve')}><Check size={15} />Setujui & Publikasikan</Btn></>}
      </div>
    </>}</Modal>
    {admin && activation && <DocumentActivationModal document={activation} onClose={() => setActivation(null)} onSaved={updated => { setDocs(old => old.map(d => d.id === updated.id ? updated : d)); setActivation(null); }} />}
    <Modal title="Tolak Regulasi" open={!!reject} onClose={() => setReject(null)}><Field label="Alasan penolakan"><textarea data-testid="document-reject-reason" rows={4} value={reason} onChange={e => setReason(e.target.value)} placeholder="Catatan perbaikan untuk administrator..." /></Field><div className="form-actions"><Btn disabled={busy || !reason.trim()} data-testid="document-reject-confirm" onClick={() => action(reject, 'reject', reason)}>Kirim Catatan</Btn></div></Modal>
    <Modal title="Hapus draf regulasi?" open={!!remove} onClose={() => setRemove(null)}><p data-testid="delete-document-confirmation">Draf “{remove?.title}” akan dihapus dari daftar regulasi.</p><div className="form-actions"><Btn secondary data-testid="document-delete-cancel" onClick={() => setRemove(null)}>Batal</Btn><Btn className="btn-danger" disabled={busy} data-testid="document-delete-confirm" onClick={destroy}>Hapus Draf</Btn></div></Modal>
  </>;
}