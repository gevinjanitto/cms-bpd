import axios from 'axios';
import { toast } from 'sonner';

export const api = axios.create({ baseURL: `${process.env.REACT_APP_BACKEND_URL}/api` });
api.interceptors.request.use(config => {
  const token = localStorage.getItem('cms-token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use(r => r, e => {
  if (e.response?.status === 401) window.dispatchEvent(new Event('session-expired'));
  const detail = e.response?.data?.detail;
  toast.error(typeof detail === 'string' ? detail : 'Data belum dapat diproses. Periksa isian dan coba kembali.');
  return Promise.reject(e);
});
export const download = async (path, name) => {
  const { data } = await api.get(path, { responseType: 'blob' });
  const url = URL.createObjectURL(data);
  const a = document.createElement('a'); a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};
export const dateLabel = value => new Date(value).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });
export const roleNames = { administrator: 'Administrator', supervisor: 'Supervisor', employee: 'Karyawan', director: 'Direksi' };
export const units = ['Divisi Kepatuhan', 'Divisi Operasional', 'Divisi Teknologi Informasi', 'KC Denpasar', 'KC Singaraja', 'KC Gianyar'];