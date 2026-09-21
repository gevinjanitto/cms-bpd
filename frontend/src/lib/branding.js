import { useEffect, useState } from 'react';
import { api } from './api';

export const APP_NAME = 'COMPLIANCE MANAGEMENT SYSTEM';
export const BANK_NAME = 'Bank BPD Bali';
const localAssets = { logo: '/assets/logo-bpd-bali.png', login: '/assets/bali-login.jpg' };

export const useBranding = () => {
  const [assets, setAssets] = useState(localAssets);
  useEffect(() => {
    const load = () => api.get('/branding').then(({ data }) => setAssets({
      logo: data.logo_url || localAssets.logo,
      login: data.login_image_url || localAssets.login,
    })).catch(() => {});
    load();
    window.addEventListener('branding-updated', load);
    return () => window.removeEventListener('branding-updated', load);
  }, []);
  return assets;
};