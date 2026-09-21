import React, { useState } from 'react';
import { Download, ChevronDown, FileSpreadsheet, FileText, LoaderCircle } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from './ui/dropdown-menu';
import { download } from '../lib/api';

export const ExportMenu = ({ params, id }) => {
  const [busy, setBusy] = useState(false);
  const save = async format => {
    setBusy(true);
    try {
      const query = new URLSearchParams({ ...params, format });
      await download(`/reports/export?${query}`, `laporan-kepatuhan.${format}`);
    } catch {} finally { setBusy(false); }
  };
  return <DropdownMenu><DropdownMenuTrigger asChild>
    <button type="button" className="btn btn-secondary" data-testid={id} disabled={busy}>
      {busy ? <LoaderCircle size={16} className="spin" /> : <Download size={16} />}Ekspor Laporan<ChevronDown size={14} />
    </button>
  </DropdownMenuTrigger><DropdownMenuContent align="end" className="export-menu" data-testid={`${id}-menu`}>
    <DropdownMenuItem data-testid={`${id}-xlsx`} onSelect={() => save('xlsx')}><FileSpreadsheet size={17} /><span>Excel (.xlsx)<small>Kolom dan format siap pakai</small></span></DropdownMenuItem>
    <DropdownMenuItem data-testid={`${id}-csv`} onSelect={() => save('csv')}><FileText size={17} /><span>CSV (.csv)<small>Kompatibel Excel · UTF-8</small></span></DropdownMenuItem>
  </DropdownMenuContent></DropdownMenu>;
};