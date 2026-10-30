import React, { useState, useEffect } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { ArrowUpRight, Plus, Box, Wrench } from 'lucide-react';
import { api, error } from '../services/api';
import { useData } from '../hooks/useData';
import { Badge } from '../components/Badge';
import { Form } from '../components/Form';
import { Loading, EmptyState, ErrorState } from '../components/Feedback';
import { priorities } from '../types/domain';
import type { User, Equipment, Sector, Ticket, TicketPage, TicketDetail, Order } from '../types/domain';
export default function Orders({ user }: {
    user: User;
}) { const { data, err, reload } = useData<Order[]>('/ordens-servico'); const [selected, setSelected] = useState<number | null>(null), [msg, setMsg] = useState(''); const act = async (id: number, path: string) => { try {
    await api.patch(`/ordens-servico/${id}/${path}`);
    reload();
}
catch (e) {
    setMsg(error(e));
} }; return <><h2>Ordens de serviço</h2><p>Organize a execução e registre a solução aplicada.</p>{msg && <p role="alert" className="error">{msg}</p>}{err ? <ErrorState message={err} retry={reload}/> : !data ? <Loading /> : null}{data?.length === 0 && <EmptyState title="Nenhuma ordem disponível" description="As ordens atribuídas à sua área aparecerão aqui."/>}{data?.map((o: Order) => <article key={o.id} className="order"><div className="order-head"><h3>OS-{String(o.id).padStart(4, '0')}</h3><Link to={'/chamados/' + o.chamado_id}>Chamado #{o.chamado_id}</Link><Badge>{o.status}</Badge></div>{user.perfil !== 'operador' && <div className="actions">{['Pendente', 'Pausada'].includes(o.status) && <button onClick={() => act(o.id, 'iniciar')}>Iniciar atendimento</button>}{o.status === 'Em execução' && <><button className="secondary" onClick={() => act(o.id, 'pausar')}>Pausar</button><button onClick={() => setSelected(o.id)}>Registrar solução</button></>}</div>}{selected === o.id && o.status === 'Em execução' && <Form label="Concluir atendimento" fields={[{ name: 'diagnostico', label: 'Diagnóstico', area: true }, { name: 'solucao', label: 'Solução executada', area: true }]} onSave={async (v) => { await api.patch(`/ordens-servico/${o.id}/concluir`, v); setSelected(null); reload(); }}/>}{o.status === 'Concluída' && <p><b>{o.diagnostico}</b><br />{o.solucao}</p>}</article>)}</>; }
