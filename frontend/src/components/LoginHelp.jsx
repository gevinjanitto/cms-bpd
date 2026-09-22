import React, { useEffect, useState } from 'react';
import { ShieldCheck } from 'lucide-react';
import { api } from '../lib/api';

export const LoginHelp = () => {
  const [contact, setContact] = useState(null);
  useEffect(() => {
    let active = true;
    api.get('/settings/contact', { silentError: true }).then(({ data }) => {
      if (active) setContact(data);
    }).catch(() => {});
    return () => { active = false; };
  }, []);
  const url = contact?.contact_url || '';
  const label = contact?.contact_label || 'Hubungi administrator SISDUR.';
  const safeUrl = /^(https?:\/\/|mailto:|tel:)/i.test(url);
  return <div className="login-help" data-testid="login-help">
    <ShieldCheck size={17} aria-hidden="true" data-testid="login-help-icon" />
    <p data-testid="login-access-notice">Akses khusus pengguna yang berwenang.<br />
      <span>Butuh bantuan? {safeUrl
        ? <a data-testid="login-contact-link" href={url} target={/^https?:/i.test(url) ? '_blank' : undefined} rel="noopener noreferrer">{label}</a>
        : <span data-testid="login-contact-label">{label}</span>}
      </span>
    </p>
  </div>;
};