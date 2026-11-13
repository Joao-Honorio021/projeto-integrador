import { useState } from 'react';
import { api, error } from '../services/api';
import { useData } from '../hooks/useData';
import type { Equipment } from '../types/domain';
const reports = [ ['chamados', 'Chamados por período'], ['ordens-concluidas', 'Ordens concluídas'], ['equipamentos-falhas', 'Equipamentos com mais falhas'], ['preventivas-atrasadas', 'Preventivas atrasadas'], ['historico-equipamento', 'Histórico por equipamento'] ];
export default function Reports() {
    const [from,setFrom]=useState(''), [to,setTo]=useState(''), [kind,setKind]=useState('chamados'), [equipment,setEquipment]=useState('');
    const [message,setMessage]=useState(''), [busy,setBusy]=useState(false);
    const equipments = useData<Equipment[]>('/equipamentos');
    return <article><span className="eyebrow">ANÁLISE OPERACIONAL</span><h2>Relatórios</h2><p>Exporte dados reais em CSV para análise e acompanhamento.</p>
        <form onSubmit={async event=>{
            event.preventDefault(); setBusy(true); setMessage('');
            try {
                const response=await api.get(`/relatorios/${kind}.csv`,{params:{inicio:from||undefined,fim:to||undefined,equipamento_id:equipment||undefined},responseType:'blob'});
                const url=URL.createObjectURL(response.data), a=document.createElement('a');a.href=url;a.download=kind+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);setMessage('Relatório exportado.');
            } catch(reason) { setMessage(error(reason)); } finally {setBusy(false)}
        }}><fieldset disabled={busy}>
            <label>Relatório<select value={kind} onChange={e=>setKind(e.target.value)}>{reports.map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></label>
            <label>Equipamento<select value={equipment} onChange={e=>setEquipment(e.target.value)}><option value="">Todos</option>{equipments.data?.map(e=><option value={e.id} key={e.id}>{e.codigo} · {e.nome}</option>)}</select></label>
            <label>De<input type="date" value={from} onChange={e=>setFrom(e.target.value)}/></label><label>Até<input type="date" min={from} value={to} onChange={e=>setTo(e.target.value)}/></label>
            <button>{busy?'Exportando…':'Exportar CSV'}</button>{message&&<p role="status">{message}</p>}
        </fieldset></form>
    </article>;
}
