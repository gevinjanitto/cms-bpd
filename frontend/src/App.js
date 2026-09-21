import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { Toaster } from './components/ui/sonner';
import { Layout } from './components/Layout';
import { Loading, Btn } from './components/common';
import { api, roleNames } from './lib/api';
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import Quizzes from './pages/Quizzes';
import TakeQuiz from './pages/TakeQuiz';
import Monitoring from './pages/Monitoring';
import { UsersPage, AuditPage, SettingsPage, ResultsPage } from './pages/Administration';
import './App.css';

function Workspace() {
  const [user, setUser] = useState(null), [loading, setLoading] = useState(true), [expired, setExpired] = useState(false), [lastRole, setLastRole] = useState(localStorage.getItem('cms-role') || 'administrator');
  const navigate = useNavigate();
  useEffect(() => { document.title = 'CMS Kepatuhan | Bank BPD Bali'; }, []);
  const login = useCallback(async (role, redirect=true) => {
    try { const {data} = await api.post('/auth/demo', {role}); localStorage.setItem('cms-token',data.token); localStorage.setItem('cms-role',role); setUser(data.user); setLastRole(role); setExpired(false); if(redirect) navigate('/'); } catch { setExpired(true); } finally {setLoading(false);}
  }, [navigate]);
  useEffect(()=> { const fn = ()=>{setExpired(true);}; window.addEventListener('session-expired',fn); if(localStorage.getItem('cms-token')) api.get('/auth/me').then(r=>setUser(r.data)).catch(()=>setExpired(true)).finally(()=>setLoading(false)); else login('administrator',false); return ()=>window.removeEventListener('session-expired',fn); },[login]);
  useEffect(() => {
    if (!user || expired) return;
    let lastActivity = Date.now(), lastHeartbeat = Date.now(), timeout = 180;
    api.get('/settings').then(r => { timeout = r.data.idle_timeout; }).catch(() => {});
    const settingsChanged = event => { timeout = event.detail.idle_timeout; lastActivity = Date.now(); };
    window.addEventListener('cms-settings-updated', settingsChanged);
    const activity = () => { lastActivity = Date.now(); };
    const events = ['pointerdown', 'keydown', 'scroll', 'touchstart'];
    events.forEach(name => window.addEventListener(name, activity, { passive: true }));
    const timer = setInterval(() => {
      const time = Date.now();
      if (time - lastActivity >= timeout * 1000) {
        const token = localStorage.getItem('cms-token');
        setExpired(true);
        api.post('/auth/logout', null, { headers: { Authorization: `Bearer ${token}` } }).catch(() => {});
        localStorage.removeItem('cms-token');
      } else if (time - lastHeartbeat > 40000 && time - lastActivity < 45000) {
        lastHeartbeat = time;
        api.get('/auth/me').catch(() => {});
      }
    }, 5000);
    return () => { clearInterval(timer); events.forEach(name => window.removeEventListener(name, activity)); window.removeEventListener('cms-settings-updated', settingsChanged); };
  }, [user, expired]);
  const logout = async()=>{ await api.post('/auth/logout').catch(()=>{}); localStorage.removeItem('cms-token'); setExpired(true); };
  const guard = (roles, page) => roles.includes(user.role) ? page : <Navigate to="/" replace/>;
  if(loading) return <Loading/>;
  if(expired || !user) return <div className="session-screen"><img src="https://customer-assets-m6fa6gv7.emergentagent.net/job_283eb062-afd4-459d-9507-f84f42e09f9a/artifacts/mzkw1aog_image%201.png" alt="Bali Dwipa Jaya"/><span className="eyebrow">COMPLIANCE MANAGEMENT SYSTEM</span><h1 data-testid="session-title">Selamat datang kembali.</h1><p>Ruang demo Bank BPD Bali</p><select data-testid="session-role" value={lastRole} onChange={e=>setLastRole(e.target.value)}>{Object.entries(roleNames).map(([r,l])=><option value={r} key={r}>{l}</option>)}</select><Btn data-testid="session-resume" onClick={()=>login(lastRole)}>Masuk sebagai {roleNames[lastRole]}</Btn></div>;
  return <Layout user={user} onSwitch={login} onLogout={logout}><Routes><Route path="/" element={<Dashboard user={user}/>}/><Route path="/ketentuan" element={<Documents user={user}/>}/><Route path="/kuis" element={<Quizzes user={user}/>}/><Route path="/kuis/:id/kerjakan" element={guard(['employee'],<TakeQuiz user={user}/>)}/><Route path="/monitoring" element={guard(['administrator','supervisor','director'],<Monitoring user={user}/>)}/><Route path="/hasil" element={guard(['employee'],<ResultsPage user={user}/>)}/><Route path="/pengguna" element={guard(['administrator','supervisor'],<UsersPage user={user}/>)}/><Route path="/audit" element={guard(['administrator','supervisor','director'],<AuditPage/>)}/><Route path="/pengaturan" element={guard(['administrator'],<SettingsPage/>)}/><Route path="*" element={<Navigate to="/" replace/>}/></Routes></Layout>;
}
export default function App(){return <BrowserRouter><Workspace/><Toaster position="top-right" richColors/></BrowserRouter>;}