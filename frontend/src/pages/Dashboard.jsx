import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Files, ClipboardCheck, Users, BadgeCheck, ArrowUpRight, Plus, CalendarDays, Building2, ChevronRight, CircleCheck, FileText, Clock3, ShieldCheck } from 'lucide-react';
import { api, units } from '../lib/api';
import { PageHead, Btn, Stat, SectionHead, Loading, ArrowLink } from '../components/common';
import { ExportMenu } from '../components/ExportMenu';
import { CalendarPanel } from '../components/dashboard/CalendarPanel';
import { TrendPanel, ParticipationPanel } from '../components/dashboard/ChartPanels';

export const PeriodFilter = ({ value, onChange, id = 'period-filter' }) => <div className="select-wrap"><CalendarDays size={15} /><select data-testid={id} value={value} onChange={e => onChange(e.target.value)}><option value="2026">Tahun 2026</option><option value="2026-Q1">Triwulan I 2026</option><option value="2026-Q2">Triwulan II 2026</option><option value="2026-Q3">Triwulan III 2026</option><option value="2026-Q4">Triwulan IV 2026</option><option value="2026-S1">Semester I 2026</option><option value="2026-S2">Semester II 2026</option><option value="all">Semua periode</option></select></div>;
export const UnitFilter = ({ value, onChange, id = 'unit-filter' }) => <div className="select-wrap"><Building2 size={15} /><select data-testid={id} value={value} onChange={e => onChange(e.target.value)}><option value="">Semua Unit Kerja</option>{units.map(u => <option key={u}>{u}</option>)}</select></div>;

export default function Dashboard({ user }) {
  const [data, setData] = useState(null), [period, setPeriod] = useState('2026'), [unit, setUnit] = useState('');
  const navigate = useNavigate();
  useEffect(() => { api.get('/dashboard', { params: { period, unit } }).then(r => setData(r.data)).catch(() => {}); }, [period, unit, user]);
  if (!data) return <Loading />;
  const m = data.metrics, employee = user.role === 'employee';
  return <>
    <PageHead eyebrow="RUANG KEPATUHAN" title="Dashboard Kepatuhan" subtitle={`Selamat datang, ${user.name}. Mari tumbuhkan budaya kepatuhan bersama.`}>
      {!employee && <ExportMenu id="dashboard-export" params={{ period, unit }} />}
      {user.role === 'administrator' && <Btn data-testid="dashboard-create-quiz" onClick={() => navigate('/kuis?create=1')}><Plus size={16} />Buat Kuis</Btn>}
      {employee && <Btn data-testid="dashboard-my-quizzes" onClick={() => navigate('/kuis')}>Kuis Saya<ArrowUpRight size={16} /></Btn>}
    </PageHead>
    <div className="dashboard-filter"><div className="overview-tab"><span className="live-dot" />Ringkasan Kepatuhan<span className="tiny-tag">{employee ? 'Personal' : 'Bankwide'}</span></div><div className="filter-group"><PeriodFilter value={period} onChange={setPeriod} />{!employee && <UnitFilter value={unit} onChange={setUnit} />}</div></div>
    <div className="stats-grid">
      <Stat id="documents" label="Ketentuan Aktif" value={m.documents} icon={Files} detail={<><span className="mini-dot green" />{m.internal} Internal<span className="detail-divider" /><span className="mini-dot blue" />{m.external} Eksternal</>} />
      <Stat id="quizzes" label="Kuis Berlangsung" value={m.active_quizzes} tone="blue" icon={ClipboardCheck} detail={<><span className="sub-badge">Aktif</span>{m.employees} karyawan terdaftar</>} />
      <Stat id="participation" label="Tingkat Partisipasi" value={`${m.participation}%`} icon={Users} detail={<><span className="trend-mark"><ArrowUpRight size={12} />{m.completed}</span>dari {m.assigned} penugasan selesai</>} />
      <Stat id="pass-rate" label="Tingkat Kelulusan" value={`${m.pass_rate}%`} tone="gold" icon={BadgeCheck} detail={<><span className="trend-mark"><CircleCheck size={12} />{m.passed}</span>hasil di atas passing grade</>} />
    </div>
    <div className="dashboard-visuals"><CalendarPanel quizzes={data.quizzes} onOpen={() => navigate('/kuis')} /><TrendPanel data={data.trend} average={m.average} /><ParticipationPanel metrics={m} /></div>
    <div className="bottom-grid"><section className="unit-section"><SectionHead title={employee ? 'Ketentuan Terbaru' : 'Performa Unit Kerja'} subtitle={employee ? 'Materi kepatuhan yang telah dipublikasikan' : 'Partisipasi dan hasil evaluasi per unit kerja'}><ArrowLink data-testid="dashboard-view-units" onClick={() => navigate(employee ? '/ketentuan' : '/monitoring')}>Lihat semua</ArrowLink></SectionHead>
      {employee ? <div>{data.recent_documents.map(d => <button className="recent-doc" key={d.id} data-testid={`recent-doc-${d.id}`} onClick={() => navigate('/ketentuan?q=' + encodeURIComponent(d.title))}><FileText size={19} /><div><strong>{d.title}</strong><small>{d.number}</small></div><ChevronRight size={16} /></button>)}</div> : <div className="table-scroll"><table className="data-table compact" data-testid="unit-performance-table"><thead><tr><th>UNIT KERJA</th><th>PARTISIPASI</th><th>RATA-RATA NILAI</th><th>STATUS</th></tr></thead><tbody>{data.units.slice(0, 5).map((u, i) => <tr key={u.unit} data-testid={`unit-performance-${i}`}><td><div className="unit-name"><span className="unit-icon"><Building2 size={14} /></span>{u.unit}</div></td><td><div className="table-progress"><div><i style={{ width: `${u.participation}%` }} /></div><span>{u.participation}%</span></div></td><td><strong>{u.average}</strong><span className="muted"> / 100</span></td><td><span className={`status ${u.average >= 75 ? 'status-passed' : 'status-pending'}`}><span />{u.average >= 75 ? 'Baik' : 'Perlu perhatian'}</span></td></tr>)}</tbody></table></div>}
    </section><section className="attention-section"><SectionHead title="Perlu Perhatian" subtitle="Tindak lanjut untuk kepatuhan yang lebih baik" /><div className="attention-list">
      {!employee && <><button className="attention-item" data-testid="attention-documents" onClick={() => navigate('/ketentuan?status=pending')}><span className="attention-icon amber"><Files size={18} /></span><div><strong>{data.tasks.documents} ketentuan menunggu review</strong><small>Periksa dan tinjau dokumen baru</small></div><ChevronRight size={15} /></button><button className="attention-item" data-testid="attention-essays" onClick={() => navigate('/monitoring?tab=essay')}><span className="attention-icon blue"><ClipboardCheck size={18} /></span><div><strong>{data.tasks.essays} esai belum dinilai</strong><small>Lengkapi hasil evaluasi karyawan</small></div><ChevronRight size={15} /></button></>}
      <button className="attention-item" data-testid="attention-quizzes" onClick={() => navigate('/kuis')}><span className="attention-icon green"><Clock3 size={18} /></span><div><strong>{m.active_quizzes} kuis sedang berlangsung</strong><small>Pantau penyelesaian sebelum tenggat</small></div><ChevronRight size={15} /></button>
    </div><div className="integrity-strip"><ShieldCheck size={19} /><p>Kepatuhan hari ini.<br /><strong>Kepercayaan untuk masa depan.</strong></p></div></section></div>
  </>;
}