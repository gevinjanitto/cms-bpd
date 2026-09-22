import React, { useState } from 'react';
import { toast } from 'sonner';
import { api } from '../lib/api';
import { Badge, Btn, Modal } from './common';
import { Switch } from './ui/switch';

export const DocumentAvailability = ({ document, onChange, id }) => {
  const active = document.is_active !== false;
  return <div className="document-availability">
    <Badge id={`${id}-status`} status={active ? 'Aktif' : 'Nonaktif'} />
    {onChange && <Switch data-testid={`${id}-switch`} checked={active} aria-label={`${active ? 'Nonaktifkan' : 'Aktifkan'} regulasi ${document.title}`} onCheckedChange={() => onChange(document)} />}
  </div>;
};

export const DocumentActivationModal = ({ document, onClose, onSaved }) => {
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const activating = document.is_active === false;
  const save = async () => {
    setBusy(true); setError('');
    try {
      const { data } = await api.put(`/documents/${document.id}/activation`, { is_active: activating }, { silentError: true });
      toast.success(<span data-testid="document-activation-success">Regulasi berhasil {activating ? 'diaktifkan kembali' : 'dinonaktifkan'}.</span>);
      onSaved(data);
    } catch (e) {
      const detail = e.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Status regulasi belum tersimpan. Silakan coba kembali.');
    } finally { setBusy(false); }
  };
  return <Modal title={activating ? 'Aktifkan regulasi kembali?' : 'Nonaktifkan regulasi?'} open onClose={() => !busy && onClose()}>
    <p data-testid="document-activation-confirmation">{activating
      ? `“${document.title}” akan tersedia kembali sesuai status publikasinya.`
      : `“${document.title}” akan disembunyikan dari pengguna selain admin dan tidak dapat dipilih untuk kuis baru. Data, kuis yang sudah diterbitkan, dan hasilnya tidak dihapus atau diubah.`}</p>
    {error && <div className="info-note danger-note" role="alert" data-testid="document-activation-error">{error}</div>}
    <div className="form-actions">
      <Btn secondary data-testid="document-activation-cancel" disabled={busy} onClick={onClose}>Batal</Btn>
      <Btn data-testid="document-activation-confirm" disabled={busy} onClick={save}>{busy ? 'Menyimpan...' : activating ? 'Aktifkan Kembali' : 'Nonaktifkan'}</Btn>
    </div>
  </Modal>;
};