import React, { useEffect, useState } from 'react';
import { Save } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '../lib/api';
import { PageHead, Btn, Field, Loading } from '../components/common';

export default function Settings() {
  const [settings, setSettings] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const load = async () => {
    setError('');
    try { const { data } = await api.get('/settings'); setSettings(data); }
    catch { setError('Pengaturan belum dapat dimuat. Silakan coba kembali.'); }
  };
  useEffect(() => { load(); }, []);
  const change = (key, value) => setSettings(old => ({ ...old, [key]: value }));
  const save = async event => {
    event.preventDefault(); setBusy(true); setError('');
    try {
      const { data } = await api.put('/settings', settings, { silentError: true });
      setSettings(data);
      window.dispatchEvent(new CustomEvent('cms-settings-updated', { detail: data }));
      toast.success(<span data-testid="settings-save-success">Pengaturan berhasil disimpan.</span>);
    } catch (e) {
      const detail = e.response?.data?.detail;
      setError(Array.isArray(detail) ? detail.map(item => item.msg.replace(/^Value error, /, '')).join(' ') : typeof detail === 'string' ? detail : 'Pengaturan belum tersimpan. Silakan coba kembali.');
    } finally { setBusy(false); }
  };
  if (!settings) return error ? <div role="alert" data-testid="settings-load-error"><p>{error}</p><Btn data-testid="settings-retry" onClick={load}>Coba Lagi</Btn></div> : <Loading />;
  return <form onSubmit={save} data-testid="settings-form">
    <PageHead eyebrow="ADMINISTRASI" title="Pengaturan" subtitle="Parameter kuis, keamanan sesi, dan kontak bantuan.">
      <Btn data-testid="settings-save" type="submit" disabled={busy}><Save size={15} />{busy ? 'Menyimpan...' : 'Simpan Perubahan'}</Btn>
    </PageHead>
    {error && <div className="info-note danger-note" role="alert" data-testid="settings-save-error">{error}</div>}
    <fieldset disabled={busy} className="settings-fields">
      <section className="settings-section" data-testid="settings-quiz-section">
        <div><h2>Parameter Kuis</h2><p>Nilai bawaan untuk kuis baru. Kuis yang sudah dibuat tidak berubah.</p></div>
        <div className="settings-form">
          <Field label="Passing Grade Bawaan"><input data-testid="settings-passing-grade" required type="number" min={1} max={100} value={settings.passing_grade} onChange={e => change('passing_grade', Number(e.target.value))} /></Field>
          <Field label="Durasi Kuis Bawaan (menit)"><input data-testid="settings-duration" required type="number" min={1} max={180} value={settings.quiz_duration} onChange={e => change('quiz_duration', Number(e.target.value))} /></Field>
        </div>
      </section>
      <section className="settings-section" data-testid="settings-session-section">
        <div><h2>Keamanan Sesi</h2><p>Batas waktu tanpa aktivitas pengguna. Berlaku langsung setelah disimpan.</p></div>
        <div className="settings-form"><Field label="Idle Timeout (detik)"><input data-testid="settings-idle-timeout" required type="number" min={60} max={3600} value={settings.idle_timeout} onChange={e => change('idle_timeout', Number(e.target.value))} /></Field></div>
      </section>
      <section className="settings-section" data-testid="settings-contact-section">
        <div><h2>Hubungi</h2><p>Kontak administrator SISDUR.</p></div>
        <div className="settings-form">
          <Field label="Teks Hubungi" className="field-full"><input data-testid="settings-contact-label" required maxLength={120} value={settings.contact_label} onChange={e => change('contact_label', e.target.value)} /></Field>
          <Field label="Tautan Hubungi" className="field-full"><input data-testid="settings-contact-url" type="text" inputMode="url" maxLength={2048} autoComplete="off" spellCheck={false} placeholder="https://… / mailto:… / tel:…" value={settings.contact_url} onChange={e => change('contact_url', e.target.value)} /></Field>
        </div>
      </section>
    </fieldset>
  </form>;
}