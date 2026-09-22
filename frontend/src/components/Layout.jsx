import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, Files, ClipboardList, ChartNoAxesCombined, Users, ShieldCheck, Settings2, Bell, Search, ChevronDown, X, Sun, Moon, LogOut, Menu, KeyRound } from 'lucide-react';
import { toast } from 'sonner';
import { api, roleNames } from '../lib/api';
import { BANK_NAME, useBranding } from '../lib/branding';
import { IconBtn, Btn, Empty, Modal, Field, DeveloperCredit } from './common';

const menus = [
  { to: '/', name: 'Dashboard', icon: LayoutDashboard, roles: ['administrator','supervisor','director','employee'] },
  { to: '/regulasi', name: 'Regulasi', icon: Files, roles: ['administrator','supervisor','director','employee'] },
  { to: '/kuis', name: 'Manajemen Kuis', employeeName: 'Kuis Saya', icon: ClipboardList, roles: ['administrator','supervisor','director','employee'] },
  { to: '/monitoring', name: 'Monitoring & Laporan', icon: ChartNoAxesCombined, roles: ['administrator','supervisor','director'] },
  { to: '/hasil', name: 'Hasil Kuis', icon: ChartNoAxesCombined, roles: ['employee'] },
];
const adminMenus = [
  { to: '/pengguna', name: 'Manajemen Pengguna', icon: Users, roles: ['administrator','supervisor'] },
  { to: '/audit', name: 'Audit Trail', icon: ShieldCheck, roles: ['administrator','supervisor','director'] },
  { to: '/pengaturan', name: 'Pengaturan', icon: Settings2, roles: ['administrator'] },
];

export const Layout = ({ user, onLogout, children }) => {
  const [mobile, setMobile] = useState(false), [notices, setNotices] = useState([]), [showNotices, setShowNotices] = useState(false);
  const [search, setSearch] = useState(''), [dark, setDark] = useState(localStorage.getItem('cms-dark') === 'true');
  const [passwordModal, setPasswordModal] = useState(false), [passwords, setPasswords] = useState({ current_password: '', new_password: '' }), [busy, setBusy] = useState(false);
  const navigate = useNavigate(), location = useLocation(), assets = useBranding();
  useEffect(() => { api.get('/notifications').then(r => setNotices(r.data)).catch(() => {}); setMobile(false); setShowNotices(false); }, [user, location.pathname]);
  useEffect(() => { document.documentElement.classList.toggle('dark', dark); localStorage.setItem('cms-dark', dark); }, [dark]);
  const read = async n => { try { await api.post(`/notifications/${n.id}/read`); setNotices(old => old.map(v => v.id === n.id ? { ...v, read_by: [...v.read_by, user.id] } : v)); setShowNotices(false); navigate(n.link); } catch {} };
  const savePassword = async event => {
    event.preventDefault(); setBusy(true);
    try { await api.post('/auth/change-password', passwords); toast.success('Password berhasil diperbarui.'); setPasswordModal(false); setPasswords({ current_password: '', new_password: '' }); }
    catch {} finally { setBusy(false); }
  };
  const current = [...menus, ...adminMenus].find(item => item.to === location.pathname);
  const renderNav = items => items.filter(m => m.roles.includes(user.role)).map(({ to, name, employeeName, icon: Icon }) => <NavLink end={to === '/'} key={to} data-testid={`nav-${to === '/' ? 'dashboard' : to.slice(1)}`} to={to} className={({ isActive }) => `nav-item ${isActive ? 'nav-active' : ''}`}><Icon size={18} /><span>{user.role === 'employee' && employeeName ? employeeName : name}</span></NavLink>);

  return <div className="app-shell">
    {mobile && <button data-testid="sidebar-backdrop" className="sidebar-backdrop" aria-label="Tutup menu" onClick={() => setMobile(false)} />}
    <aside className={`sidebar ${mobile ? 'sidebar-open' : ''}`}>
      <NavLink to="/" className="brand" data-testid="brand-home"><img src={assets.logo} alt="Logo Bali Dwipa Jaya" data-testid="logo-bank-bpd-bali" /><div><strong data-testid="sidebar-app-name">COMPLIANCE<br />MANAGEMENT SYSTEM</strong><span data-testid="sidebar-bank-name">{BANK_NAME}</span></div></NavLink>
      <div className="workspace-label"><span className="workspace-icon"><ShieldCheck size={17} /></span><div>Ruang Kepatuhan<small>Divisi Kepatuhan · SISDUR</small></div></div>
      <div className="nav-caption">MENU UTAMA</div><nav>{renderNav(menus)}</nav>
      {adminMenus.some(m => m.roles.includes(user.role)) && <><div className="nav-caption second-caption">ADMINISTRASI</div><nav>{renderNav(adminMenus)}</nav></>}
      <div className="sidebar-bottom"><div className="compliance-note"><ShieldCheck size={23} /><h3>Integritas dalam<br />setiap langkah.</h3><p>Bersama menjaga kepercayaan<br />dan budaya kepatuhan.</p><span className="gold-line" /></div><div className="sidebar-version"><span className="live-dot" />CMS <span>Bank BPD Bali</span></div></div>
    </aside>
    <div className="main-shell"><header className="topbar"><div className="topbar-left"><IconBtn label="Buka menu" data-testid="mobile-menu" onClick={() => setMobile(!mobile)}><Menu size={20} /></IconBtn><div className="breadcrumb"><span>{BANK_NAME}</span><i>/</i><strong data-testid="topbar-current-page">{current?.name || 'Kuis Saya'}</strong></div></div><form className="global-search" onSubmit={e => { e.preventDefault(); navigate('/regulasi?q=' + encodeURIComponent(search)); }}><Search size={17} /><input data-testid="global-search-input" value={search} onChange={e => setSearch(e.target.value)} placeholder="Cari regulasi atau nomor dokumen..." /><kbd>↵</kbd></form><div className="topbar-right">
      <IconBtn data-testid="theme-toggle-button" label={dark ? 'Mode terang' : 'Mode gelap'} onClick={() => setDark(!dark)}>{dark ? <Sun size={18} /> : <Moon size={18} />}</IconBtn>
      <div className="notice-wrapper"><IconBtn data-testid="notification-toggle" label="Notifikasi" onClick={() => setShowNotices(!showNotices)}><Bell size={19} />{notices.some(n => !n.read_by.includes(user.id)) && <span className="notification-dot" />}</IconBtn>{showNotices && <div className="notification-panel" data-testid="notification-panel"><div className="section-head"><h2>Notifikasi</h2><IconBtn label="Tutup notifikasi" data-testid="notification-close" onClick={() => setShowNotices(false)}><X size={16} /></IconBtn></div>{notices.length ? notices.map(n => <button data-testid={`notification-${n.id}`} key={n.id} onClick={() => read(n)} className={`notification-item ${n.read_by.includes(user.id) ? 'read' : ''}`}><span className="notice-icon"><Bell size={17} /></span><div><strong>{n.title}</strong><p>{n.detail}</p></div></button>) : <Empty text="Tidak ada notifikasi baru." />}</div>}</div>
      <span className="topbar-divider" /><div className="user-identity"><span className="avatar">{user.name.split(' ').slice(0, 2).map(x => x[0]).join('')}</span><div><strong data-testid="current-user-name">{user.name}</strong><small data-testid="current-user-role">{roleNames[user.role]}</small></div></div><IconBtn label="Ubah password" data-testid="change-password-open" onClick={() => setPasswordModal(true)}><KeyRound size={17} /></IconBtn><IconBtn label="Keluar" data-testid="logout-button" onClick={onLogout}><LogOut size={17} /></IconBtn>
    </div></header><main className="main-content" key={location.pathname}>{children}</main><footer className="page-footer" data-testid="app-footer"><span data-testid="app-copyright">© {new Date().getFullYear()} {BANK_NAME}. Seluruh hak dilindungi.</span><DeveloperCredit id="app" /></footer></div>
    <Modal title="Ubah Password" open={passwordModal} onClose={() => setPasswordModal(false)}><form onSubmit={savePassword}><div className="form-grid"><Field label="Password saat ini" className="field-full"><input data-testid="password-current" type="password" autoComplete="current-password" required value={passwords.current_password} onChange={e => setPasswords({ ...passwords, current_password: e.target.value })} /></Field><Field label="Password baru (minimal 8 karakter)" className="field-full"><input data-testid="password-new" type="password" autoComplete="new-password" minLength={8} maxLength={72} required value={passwords.new_password} onChange={e => setPasswords({ ...passwords, new_password: e.target.value })} /></Field></div><div className="form-actions"><Btn secondary type="button" data-testid="password-cancel" onClick={() => setPasswordModal(false)}>Batal</Btn><Btn type="submit" disabled={busy} data-testid="password-save">Simpan Password</Btn></div></form></Modal>
  </div>;
};