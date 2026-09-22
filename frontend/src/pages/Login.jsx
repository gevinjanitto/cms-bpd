import React, { lazy, Suspense, useCallback, useEffect, useState } from 'react';
import { ArrowRight, Box, Eye, EyeOff, Image, LockKeyhole, RefreshCw, ShieldCheck, UserRound, LoaderCircle, Sun, Moon } from 'lucide-react';
import { api } from '../lib/api';
import { APP_NAME, BANK_NAME, useBranding } from '../lib/branding';
import { IconBtn, DeveloperCredit } from '../components/common';
import { LoginHelp } from '../components/LoginHelp';

const BaliScene = lazy(() => import('../components/scene/BaliScene'));

class SceneBoundary extends React.Component {
  state = { error: false };
  static getDerivedStateFromError() { return { error: true }; }
  render() { return this.state.error ? this.props.fallback : this.props.children; }
}

export default function Login({ onLogin, expired }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [answer, setAnswer] = useState('');
  const [captcha, setCaptcha] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [captchaLoading, setCaptchaLoading] = useState(false);
  const [error, setError] = useState('');
  const [mode, setMode] = useState('illustration');
  const [dark, setDark] = useState(localStorage.getItem('cms-dark') === 'true');
  const assets = useBranding();

  const refreshCaptcha = useCallback(async () => {
    setCaptchaLoading(true);
    setAnswer('');
    try { const { data } = await api.get('/auth/captcha', { silentError: true }); setCaptcha(data); }
    catch { setCaptcha(null); setError('CAPTCHA belum dapat dimuat. Silakan muat ulang.'); }
    finally { setCaptchaLoading(false); }
  }, []);
  useEffect(() => { refreshCaptcha(); }, [refreshCaptcha]);
  useEffect(() => { document.documentElement.classList.toggle('dark', dark); localStorage.setItem('cms-dark', dark); }, [dark]);

  const submit = async event => {
    event.preventDefault();
    if (!captcha || busy) return;
    setBusy(true); setError('');
    try {
      const { data } = await api.post('/auth/login', { username, password, captcha_id: captcha.id, captcha_answer: answer }, { silentError: true });
      onLogin(data);
    } catch (e) {
      setError(typeof e.response?.data?.detail === 'string' ? e.response.data.detail : 'Tidak dapat masuk. Silakan coba kembali.');
      await refreshCaptcha();
    } finally { setBusy(false); }
  };
  const poster = <img className="login-illustration" data-testid="login-bali-illustration" src={assets.login} alt="Ilustrasi tiga dimensi pegawai Bank BPD Bali berudeng di meja kerja, dengan candi bentar dan kain poleng" />;

  return <div className="login-page">
    <header className="login-topbar"><a href="/login" className="login-wordmark" data-testid="login-brand-link"><img src={assets.logo} alt="Logo Bank BPD Bali" /><span>{BANK_NAME}<small>COMPLIANCE & INTEGRITY</small></span></a><div className="login-top-actions"><span><ShieldCheck size={15} />Portal Internal</span><IconBtn label={dark ? 'Mode terang' : 'Mode gelap'} data-testid="login-theme-toggle" onClick={() => setDark(!dark)}>{dark ? <Sun size={18} /> : <Moon size={18} />}</IconBtn></div></header>
    <main className="login-composition">
      <section className="login-art" aria-label="Ilustrasi kantor bernuansa Bali"><div className="login-art-copy"><span className="login-art-eyebrow"><span />BERAKAR PADA INTEGRITAS</span><h2>Budaya patuh.<br />Kepercayaan yang tumbuh.</h2><p>Melangkah bersama, menjaga amanah.</p></div>
        <div className="login-scene-stage">{mode === 'interactive' ? <SceneBoundary fallback={poster}><Suspense fallback={poster}><BaliScene /></Suspense></SceneBoundary> : poster}</div>
        <div className="login-art-footer"><span className="bali-signature">BALI DWIPA JAYA <i />EST. 1962</span><div className="scene-switch" aria-label="Tampilan ilustrasi"><button title="Ilustrasi 3D" aria-label="Ilustrasi 3D" data-testid="login-mode-illustration" className={mode === 'illustration' ? 'active' : ''} onClick={() => setMode('illustration')}><Image size={16} /></button><button title="Model 3D interaktif" aria-label="Model 3D interaktif" data-testid="login-mode-interactive" className={mode === 'interactive' ? 'active' : ''} onClick={() => setMode('interactive')}><Box size={17} /><span>3D</span></button></div></div>
      </section>
      <section className="login-form-panel"><div className="login-form-content"><div className="login-system-brand"><img data-testid="login-logo" src={assets.logo} alt="Bali Dwipa Jaya" /><div><span data-testid="login-app-name">{APP_NAME}</span><strong data-testid="login-bank-name">{BANK_NAME}</strong></div></div><div className="login-welcome"><h1 data-testid="login-heading">Selamat datang<br />kembali.</h1><p>Masuk untuk melanjutkan aktivitas kepatuhan Anda.</p></div>
        {expired && !error && <div className="login-session-note" data-testid="login-session-expired">Sesi Anda telah berakhir. Silakan masuk kembali.</div>}
        <form className="login-form" onSubmit={submit}>
          <label className="login-field"><span>Username</span><div className="login-input-wrap"><UserRound size={18} /><input data-testid="login-username" name="username" autoComplete="username" autoFocus required maxLength={100} value={username} onChange={e => setUsername(e.target.value)} placeholder="Masukkan username" /></div></label>
          <label className="login-field"><span>Password</span><div className="login-input-wrap"><LockKeyhole size={18} /><input data-testid="login-password" name="password" autoComplete="current-password" required maxLength={72} type={showPassword ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} placeholder="Masukkan password" /><button type="button" data-testid="login-toggle-password" title={showPassword ? 'Sembunyikan password' : 'Lihat password'} aria-label={showPassword ? 'Sembunyikan password' : 'Lihat password'} onClick={() => setShowPassword(!showPassword)}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div></label>
          <div className="login-captcha"><div className="captcha-label"><span>Verifikasi keamanan</span><span>CAPTCHA</span></div><div className="captcha-row"><div className="captcha-picture">{captchaLoading ? <LoaderCircle size={20} className="spin" /> : captcha && <img data-testid="login-captcha-image" src={captcha.image} alt="Kode CAPTCHA enam karakter" />}</div><button type="button" className="captcha-refresh" data-testid="login-captcha-refresh" onClick={refreshCaptcha} disabled={captchaLoading || busy} title="Muat kode baru" aria-label="Muat kode CAPTCHA baru"><RefreshCw size={18} /></button><input data-testid="login-captcha-answer" aria-label="Jawaban CAPTCHA" required maxLength={6} autoComplete="off" spellCheck={false} value={answer} onChange={e => setAnswer(e.target.value.toUpperCase())} placeholder="Kode di samping" /></div></div>
          {error && <div className="login-error" role="alert" data-testid="login-error">{error}</div>}
          <button className="login-submit" data-testid="login-submit" type="submit" disabled={busy || captchaLoading || !captcha}>{busy ? <><LoaderCircle size={18} className="spin" />Memverifikasi...</> : <>Masuk ke Dashboard<ArrowRight size={18} /></>}</button>
        </form><LoginHelp /></div></section>
    </main><footer className="login-page-footer" data-testid="login-footer"><span data-testid="login-copyright">© {new Date().getFullYear()} Bank BPD Bali</span><span data-testid="login-footer-motto">Integritas. Kepatuhan. Kepercayaan.</span><DeveloperCredit id="login-page" /></footer>
  </div>;
}