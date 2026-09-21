import React from 'react';
import { ShieldCheck, Users } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, PieChart, Pie, Cell } from 'recharts';
import { ChartContainer } from '../ChartContainer';
import { SectionHead } from '../common';

export const TrendPanel = ({ data, average }) => <section className="chart-panel">
  <SectionHead title="Tren Kepatuhan" subtitle="Partisipasi dan pemahaman karyawan"><span className="chart-time">6 bulan terakhir</span></SectionHead>
  <div className="chart-legend"><span><i style={{ background: '#187c57' }} />Partisipasi kuis</span><span><i style={{ background: '#c4a760' }} />Rata-rata nilai</span></div>
  <div className="trend-chart" data-testid="compliance-trend-chart"><ChartContainer><AreaChart data={data} margin={{ top: 10, right: 8, left: -24, bottom: 0 }}>
    <defs><linearGradient id="trend-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#187c57" stopOpacity={.17} /><stop offset="100%" stopColor="#187c57" stopOpacity={0} /></linearGradient></defs>
    <CartesianGrid strokeDasharray="3 5" vertical={false} stroke="#e9eeeb" />
    <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#8c9c91', fontSize: 9 }} dy={9} />
    <YAxis domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} axisLine={false} tickLine={false} tick={{ fill: '#8c9c91', fontSize: 9 }} tickFormatter={v => `${v}%`} />
    <Tooltip contentStyle={{ border: '1px solid #e3ece5', borderRadius: 7, fontSize: 11 }} />
    <Area type="monotone" dataKey="participation" name="Partisipasi (%)" stroke="#187c57" strokeWidth={2.3} fill="url(#trend-fill)" dot={{ r: 2.5, fill: '#fff', strokeWidth: 1.5 }} />
    <Area type="monotone" dataKey="score" name="Rata-rata nilai" stroke="#c4a760" strokeWidth={1.6} strokeDasharray="4 4" fill="transparent" />
  </AreaChart></ChartContainer></div>
  <div className="chart-footnote"><ShieldCheck size={14} /><span>Rata-rata nilai periode ini</span><strong data-testid="average-score">{average}<small> / 100</small></strong></div>
</section>;

export const ParticipationPanel = ({ metrics: m }) => {
  const pie = [{ name: 'Sudah mengikuti', value: m.completed, color: '#187c57' }, { name: 'Belum mengikuti', value: m.pending, color: '#d9c383' }];
  const data = m.assigned ? pie : [{ name: 'Belum ada penugasan', value: 1, color: '#e9efeb' }];
  return <section className="participation-panel"><SectionHead title="Status Partisipasi" subtitle="Penyelesaian penugasan kuis" />
    <div className="donut-chart" data-testid="participation-donut"><ChartContainer><PieChart><Pie data={data} dataKey="value" innerRadius="73%" outerRadius="89%" startAngle={90} endAngle={-270} paddingAngle={m.pending && m.completed ? 3 : 0} stroke="none">{data.map((p, i) => <Cell key={i} fill={p.color} />)}</Pie><Tooltip /></PieChart></ChartContainer><div className="donut-center"><strong>{m.participation}<span>%</span></strong><small>Partisipasi keseluruhan</small></div></div>
    <div className="donut-legend">{pie.map((p, i) => <div key={p.name}><span><i style={{ background: p.color }} />{p.name}</span><strong data-testid={`participation-count-${i}`}>{p.value}</strong></div>)}</div><div className="participation-note"><Users size={13} />{m.employees} karyawan dalam periode ini</div>
  </section>;
};