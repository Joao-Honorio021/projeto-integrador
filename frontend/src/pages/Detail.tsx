import { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, error } from '../services/api';
import { useData } from '../hooks/useData';
import { Badge } from '../components/Badge';
import { Form } from '../components/Form';
import { Loading, ErrorState } from '../components/Feedback';
import { priorities } from '../types/domain';
import type { User, TicketDetail } from '../types/domain';
export default function Detail({ user }: {
    user: User;
}) { const { id } = useParams(); const { data: t, err, reload } = useData<TicketDetail>('/chamados/' + id); const manager = ['administrador', 'supervisor'].includes(user.perfil); const [tech, setTech] = useState<User[]>([]); useEffect(() => { if (manager)
    api.get('/usuarios').then(r => setTech(r.data.filter((u: User) => u.perfil === 'tecnico' && u.ativo))).catch(e => setMsg(error(e))); }, [manager]); const [msg, setMsg] = useState(''); if (!t)
    return err ? <ErrorState message={err} retry={reload}/> : <Loading />; return <><Link to="/chamados">← Todos os chamados</Link><div className="intro"><div><span className="eyebrow">CH-{String(t.id).padStart(4, '0')}</span><h2>{t.titulo}</h2><p>{t.descricao}</p></div><Badge>{t.status}</Badge></div><div className="charts"><article><h3>Histórico de atendimento</h3>{t.historico.map((h: TicketDetail["historico"][number]) => <div className="timeline" key={h.id}><b>{h.autor}</b><small>{new Date(h.criado_em).toLocaleString('pt-BR')}</small><p>{h.mensagem}</p></div>)}<Form label="Enviar comentário" fields={[{ name: 'mensagem', label: 'Comentário', area: true }]} onSave={async (v) => { await api.post(`/chamados/${id}/comentarios`, v); reload(); }}/></article><article><h3>Gerenciar atendimento</h3><p>Prioridade: <Badge>{t.prioridade}</Badge></p>{t.status==='Aberto'&&(manager||t.solicitante_id===user.id)&&<details><summary>Editar chamado</summary><Form fields={[{name:'titulo',label:'Título',value:t.titulo,maxLength:160},{name:'descricao',label:'Descrição',value:t.descricao,area:true,minLength:5}]} onSave={async v=>{await api.patch('/chamados/'+id,v);reload()}}/></details>}{manager&&!['Resolvido','Cancelado'].includes(t.status)&&<details><summary>Cancelar chamado sem OS</summary><Form label="Cancelar chamado" fields={[{name:'mensagem',label:'Motivo',area:true}]} onSave={async v=>{if(!window.confirm('Cancelar este chamado?'))return false;await api.patch(`/chamados/${id}/cancelar`,v);reload()}}/></details>}{manager && <><Form label="Atribuir técnico" fields={[{ name: 'tecnico_id', label: 'Responsável', options: tech }, { name: 'prioridade', label: 'Prioridade', options: priorities }]} onSave={async (v) => { await api.patch(`/chamados/${id}/atribuir`, { ...v, tecnico_id: Number(v.tecnico_id) }); reload(); }}/><button className="secondary" onClick={async () => { try {
    await api.post('/ordens-servico', { chamado_id: Number(id) });
    setMsg('Ordem criada. Acesse Ordens de serviço.');
    reload();
}
catch (e) {
    setMsg(error(e));
} }}>Criar ordem de serviço</button></>}{msg && <p role="status">{msg}</p>}<Link to="/ordens">Acompanhar ordens →</Link></article></div></>; }
