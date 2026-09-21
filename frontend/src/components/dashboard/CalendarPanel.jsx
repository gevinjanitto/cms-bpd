import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, CalendarDays } from 'lucide-react';
import { IconBtn } from '../common';

export const CalendarPanel = ({ quizzes, onOpen }) => {
  const today = new Date();
  const [month, setMonth] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const [day, setDay] = useState(today.getDate());
  const days = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
  const offset = (month.getDay() + 6) % 7;
  const dateKey = d => `${month.getFullYear()}-${String(month.getMonth() + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
  const selected = dateKey(day);
  const events = quizzes.filter(q => q.start_date <= selected && q.end_date >= selected);
  const changeMonth = delta => { setMonth(m => new Date(m.getFullYear(), m.getMonth() + delta, 1)); setDay(1); };
  return <section className="calendar-panel"><div className="calendar-heading"><h2 data-testid="calendar-month">{month.toLocaleDateString('id-ID', { month: 'long', year: 'numeric' })}</h2><div><IconBtn label="Bulan sebelumnya" data-testid="calendar-previous" onClick={() => changeMonth(-1)}><ChevronLeft size={15} /></IconBtn><IconBtn label="Bulan berikutnya" data-testid="calendar-next" onClick={() => changeMonth(1)}><ChevronRight size={15} /></IconBtn></div></div><div className="calendar-grid"><div className="calendar-weekdays">{['S', 'S', 'R', 'K', 'J', 'S', 'M'].map((v, i) => <span key={i}>{v}</span>)}</div><div className="calendar-days">{Array.from({ length: offset }, (_, i) => <span key={`blank-${i}`} />)}{Array.from({ length: days }, (_, i) => i + 1).map(d => <button data-testid={`calendar-day-${d}`} key={d} onClick={() => setDay(d)} className={`${d === day ? 'selected' : ''} ${quizzes.some(q => q.end_date === dateKey(d)) ? 'has-event' : ''}`}>{d}</button>)}</div></div><div className="calendar-agenda"><span className="calendar-agenda-label"><CalendarDays size={13} />Agenda Kuis <span>{events.length}</span></span>{events.length ? events.slice(0, 2).map(q => <button key={q.id} data-testid={`calendar-quiz-${q.id}`} onClick={onOpen}><span className="agenda-line" /><div><strong>{q.title}</strong><small>Berakhir {new Date(q.end_date).toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })}</small></div><ChevronRight size={13} /></button>) : <p data-testid="calendar-no-event">Tidak ada kuis aktif pada tanggal ini.</p>}</div></section>;
};