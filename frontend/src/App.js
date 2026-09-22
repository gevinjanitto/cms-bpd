import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { Toaster } from './components/ui/sonner';
import { Layout } from './components/Layout';
import { Loading } from './components/common';
import { api } from './lib/api';
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import Quizzes from './pages/Quizzes';
import TakeQuiz from './pages/TakeQuiz';
import Monitoring from './pages/Monitoring';
import Login from './pages/Login';
import { UsersPage, AuditPage, ResultsPage } from './pages/Administration';
import SettingsPage from './pages/Settings';
import './App.css';
import './styles/redesign.css';
import './styles/login.css';
import './styles/settings.css';

function LegacyRegulationRedirect() {
  const { search, hash } = useLocation();
  return <Navigate to={`/regulasi${search}${hash}`} replace />;
}

function Workspace() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expired, setExpired] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const endSession = () => { setUser(null); setExpired(true); localStorage.removeItem('cms-token'); };
    window.addEventListener('session-expired', endSession);
    if (localStorage.getItem('cms-token')) {
      api.get('/auth/me', { silentError: true }).then(r => setUser(r.data)).catch(() => endSession()).finally(() => setLoading(false));
    } else setLoading(false);
    return () => window.removeEventListener('session-expired', endSession);
  }, []);

  const logout = useCallback(async () => {
    const token = localStorage.getItem('cms-token');
    localStorage.removeItem('cms-token');
    setUser(null);
    await api.post('/auth/logout', null, { headers: { Authorization: `Bearer ${token}` }, silentError: true }).catch(() => {});
    navigate('/login', { replace: true });
  }, [navigate]);

  useEffect(() => {
    if (!user) return;
    let lastActivity = Date.now(), lastHeartbeat = Date.now(), timeout = 180;
    api.get('/settings').then(r => { timeout = r.data.idle_timeout; }).catch(() => {});
    const settingsChanged = event => { timeout = event.detail.idle_timeout; lastActivity = Date.now(); };
    const activity = () => { lastActivity = Date.now(); };
    const events = ['pointerdown', 'keydown', 'scroll', 'touchstart'];
    window.addEventListener('cms-settings-updated', settingsChanged);
    events.forEach(name => window.addEventListener(name, activity, { passive: true }));
    const timer = setInterval(() => {
      const time = Date.now();
      if (time - lastActivity >= timeout * 1000) { setExpired(true); logout(); }
      else if (time - lastHeartbeat > 40000 && time - lastActivity < 45000) {
        lastHeartbeat = time;
        api.get('/auth/me', { silentError: true }).catch(() => {});
      }
    }, 5000);
    return () => {
      clearInterval(timer);
      events.forEach(name => window.removeEventListener(name, activity));
      window.removeEventListener('cms-settings-updated', settingsChanged);
    };
  }, [user, logout]);

  const onLogin = data => {
    localStorage.setItem('cms-token', data.token);
    setUser(data.user);
    setExpired(false);
    navigate('/', { replace: true });
  };
  if (loading) return <Loading />;
  if (!user) return <Login onLogin={onLogin} expired={expired} />;
  const guard = (roles, page) => roles.includes(user.role) ? page : <Navigate to="/" replace />;
  return <Layout user={user} onLogout={logout}><Routes>
    <Route path="/" element={<Dashboard user={user} />} />
    <Route path="/regulasi" element={<Documents user={user} />} />
    <Route path="/ketentuan" element={<LegacyRegulationRedirect />} />
    <Route path="/kuis" element={<Quizzes user={user} />} />
    <Route path="/kuis/:id/kerjakan" element={guard(['employee'], <TakeQuiz user={user} />)} />
    <Route path="/monitoring" element={guard(['administrator', 'supervisor', 'director'], <Monitoring user={user} />)} />
    <Route path="/hasil" element={guard(['employee'], <ResultsPage user={user} />)} />
    <Route path="/pengguna" element={guard(['administrator', 'supervisor'], <UsersPage user={user} />)} />
    <Route path="/audit" element={guard(['administrator', 'supervisor', 'director'], <AuditPage />)} />
    <Route path="/pengaturan" element={guard(['administrator'], <SettingsPage />)} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></Layout>;
}

export default function App() {
  return <BrowserRouter><Workspace /><Toaster position="top-right" richColors /></BrowserRouter>;
}