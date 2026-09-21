import React from 'react';
import { Search, X, LoaderCircle, Inbox, ArrowUpRight } from 'lucide-react';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';

export const Btn = ({ children, secondary, className = '', ...props }) => <Button className={`btn ${secondary ? 'btn-secondary' : 'btn-primary'} ${className}`} {...props}>{children}</Button>;
export const IconBtn = ({ children, label, ...props }) => <button className="icon-btn" title={label} aria-label={label} {...props}>{children}</button>;
export const PageHead = ({ eyebrow, title, subtitle, children }) => <div className="page-head"><div><div className="eyebrow" data-testid="page-eyebrow">{eyebrow || 'WORKSPACE / KEPATUHAN'}</div><h1 data-testid="page-title">{title}</h1><p data-testid="page-subtitle">{subtitle}</p></div><div className="page-actions">{children}</div></div>;
const labels = { draft: 'Draf', pending: 'Menunggu review', published: 'Dipublikasikan', rejected: 'Ditolak', active: 'Berlangsung', scheduled: 'Terjadwal', closed: 'Berakhir', passed: 'Lulus', failed: 'Belum lulus', reviewing: 'Menunggu penilaian', Internal: 'Internal', Eksternal: 'Eksternal' };
export const Badge = ({ status, id }) => <span className={`status status-${status}`} data-testid={id || `status-${status}`}><span />{labels[status] || status}</span>;
export const Field = ({ label, children, className = '' }) => <label className={`field ${className}`}><span>{label}</span>{children}</label>;
export const SearchBox = ({ value, onChange, placeholder, id }) => <div className="search-box"><Search size={17}/><input data-testid={id} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder || 'Cari...'} /></div>;
export const Modal = ({ title, description, children, open, onClose, wide }) => <Dialog open={open} onOpenChange={v => !v && onClose()}><DialogContent data-testid="active-modal" className={`cms-modal ${wide ? 'modal-wide' : ''}`}><DialogHeader><DialogTitle data-testid="modal-title">{title}</DialogTitle><DialogDescription>{description || 'Compliance Management System · Bank BPD Bali'}</DialogDescription></DialogHeader>{children}</DialogContent></Dialog>;
export const Loading = () => <div className="loading" data-testid="page-loading"><LoaderCircle className="spin" size={24}/><span>Memuat data...</span></div>;
export const Empty = ({ text = 'Belum ada data untuk ditampilkan.' }) => <div className="empty" data-testid="empty-state"><Inbox size={32}/><p>{text}</p></div>;
export const Stat = ({ label, value, detail, icon: Icon, tone = 'green', children, id }) => <article className={`stat stat-${tone}`} data-testid={`stat-${id}`}><div className="stat-top"><span>{label}</span><div className="stat-icon"><Icon size={18}/></div></div><div className="stat-value" data-testid={`stat-value-${id}`}>{value}{children}</div><div className="stat-detail">{detail}</div></article>;
export const SectionHead = ({ title, subtitle, children }) => <div className="section-head"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{children}</div>;
export const ArrowLink = ({ children, ...props }) => <button className="text-link" {...props}>{children}<ArrowUpRight size={15}/></button>;
export const DeveloperCredit = ({ id }) => <span className="developer-credit" data-testid={`developer-credit-${id}`}>Design &amp; Develop by <a data-testid={`developer-credit-link-${id}`} href="https://www.maiharta.com" target="_blank" rel="noopener noreferrer">MaiHarta</a></span>;