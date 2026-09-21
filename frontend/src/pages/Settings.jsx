import React, { useEffect, useState } from 'react';
import { Save, CloudUpload, Image } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '../lib/api';
import { useBranding } from '../lib/branding';
import { PageHead, Btn, Field, Badge, Loading } from '../components/common';

export default function Settings() {
  const [settings, setSettings] = useState(null), [media, setMedia] = useState(null), [busy, setBusy] = useState(false), [uploading, setUploading] = useState('');
  const assets = useBranding();
  useEffect(() => { Promise.all([api.get('/settings'), api.get('/media/status')]).then(([s, m]) => { setSettings(s.data); setMedia(m.data); }).catch(() => {}); }, []);
  const save = async event => {
    event.preventDefault(); setBusy(true);
    try { const { data } = await api.put('/settings', settings); setSettings(data); window.dispatchEvent(new CustomEvent('cms-settings-updated', { detail: data })); toast.success('Parameter aplikasi berhasil disimpan.'); }
    catch {} finally { setBusy(false); }
  };
  const upload = async (purpose, file) => {
    if (!file) return;
    setUploading(purpose);
    try { const body = new FormData(); body.append('file', file); await api.post(`/media/images?purpose=${purpose}`, body); window.dispatchEvent(new Event('branding-updated')); toast.success('Gambar berhasil disimpan di Cloudinary.'); }
    catch {} finally { setUploading(''); }
  };
  if (!settings || !media) return <Loading />;
  return <form onSubmit={save}><PageHead eyebrow="ADMINISTRASI" title="Pengaturan" subtitle="Parameter evaluasi, keamanan sesi, dan identitas aplikasi."><Btn data-testid="settings-save" type="submit" disabled={busy}><Save size={15} />{busy ? 'Menyimpan...' : 'Simpan Perubahan'}</Btn></PageHead>
    <section className="settings-section"><div><h2>Parameter Kuis</h2><p>Nilai bawaan untuk kuis baru. Kuis yang sudah dibuat tidak berubah.</p></div><div className="settings-form"><Field label="Passing Grade Bawaan"><input data-testid="settings-passing-grade" required type="number" min={1} max={100} value={settings.passing_grade} onChange={e => setSettings({ ...settings, passing_grade: Number(e.target.value) })} /></Field><Field label="Durasi Kuis Bawaan (menit)"><input data-testid="settings-duration" required type="number" min={1} max={180} value={settings.quiz_duration} onChange={e => setSettings({ ...settings, quiz_duration: Number(e.target.value) })} /></Field></div></section>
    <section className="settings-section"><div><h2>Keamanan Sesi</h2><p>Batas waktu tanpa aktivitas pengguna. Berlaku langsung setelah disimpan.</p></div><div className="settings-form"><Field label="Idle Timeout (detik)"><input data-testid="settings-idle-timeout" required type="number" min={60} max={3600} value={settings.idle_timeout} onChange={e => setSettings({ ...settings, idle_timeout: Number(e.target.value) })} /></Field></div></section>
    <section className="settings-section"><div><h2>Identitas & Gambar</h2><p>Logo dan ilustrasi login disimpan di Cloudinary setelah layanan dikonfigurasi.</p></div><div className="media-settings"><div className="connection-row"><div><strong>Cloudinary</strong><small>PNG, JPEG, WebP · Maksimal 5 MB</small></div><Badge id="cloudinary-status" status={media.cloudinary_configured ? 'Terhubung' : 'Belum dikonfigurasi'} /></div>{!media.cloudinary_configured && <div className="info-note" data-testid="cloudinary-config-note">Isi CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, dan CLOUDINARY_API_SECRET pada konfigurasi server. Aset bawaan tetap tersedia tanpa koneksi Cloudinary.</div>}{[['logo', 'Logo Bank', assets.logo], ['login', 'Ilustrasi Login', assets.login]].map(([purpose, label, image]) => <div className="media-upload-row" key={purpose}><img src={image} alt={label} /><div><Field label={label}><input type="file" data-testid={`branding-upload-${purpose}`} accept="image/png,image/jpeg,image/webp" disabled={!media.cloudinary_configured || !!uploading} onChange={e => upload(purpose, e.target.files[0])} /></Field><small>{uploading === purpose ? 'Mengunggah...' : 'Gambar saat ini'}</small></div></div>)}</div></section>
    <section className="settings-section"><div><h2>Koneksi Sistem</h2><p>Status penyimpanan dan layanan pendukung.</p></div><div>{[['MongoDB', 'Data aplikasi dan dokumen privat melalui GridFS', 'Terhubung'], ['Autentikasi', 'Username, password, CAPTCHA, dan pembatasan percobaan', 'Aktif'], ['Notifikasi Dalam Aplikasi', 'Penugasan, persetujuan, dan pengingat', 'Aktif'], ['Active Directory / SSO', 'Integrasi akun internal bank', 'Belum dikonfigurasi'], ['Mail Server / OTP', 'Notifikasi email dan verifikasi tambahan', 'Belum dikonfigurasi'], ['SIM SDM', 'Sinkronisasi data karyawan', 'Belum dikonfigurasi']].map(([label, detail, status], i) => <div className="connection-row" key={label}><div><strong>{label}</strong><small>{detail}</small></div><Badge id={`connection-status-${i}`} status={status} /></div>)}</div></section>
  </form>;
}