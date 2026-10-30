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
export default function Equipments({ user }: {
    user: User;
}) { const { data, err, reload } = useData<Equipment[]>('/equipamentos'), sectors = useData<Sector[]>('/setores'); const [show, setShow] = useState(false), [q, setQ] = useState(''); return <><div className="intro"><div><h2>Equipamentos</h2><p>Conheça os ativos da sua operação.</p></div>{user.perfil === 'administrador' && <button onClick={() => setShow(!show)}>Cadastrar equipamento</button>}</div>{show && <article><Form fields={[{ name: 'codigo', label: 'Código' }, { name: 'nome', label: 'Nome' }, { name: 'setor_id', label: 'Setor', options: sectors.data || [] }]} onSave={async (v) => { await api.post('/equipamentos', { ...v, setor_id: Number(v.setor_id) }); setShow(false); reload(); }}/></article>}<input aria-label="Pesquisar equipamentos" placeholder="Pesquisar equipamentos" value={q} onChange={e => setQ(e.target.value)}/>{err ? <ErrorState message={err} retry={reload}/> : !data ? <Loading /> : data.filter(e => e.nome.toLowerCase().includes(q.toLowerCase())).length === 0 ? <EmptyState title="Nenhum equipamento encontrado" description="Altere a busca ou cadastre um equipamento."/> : null}<div className="equipment-grid">{data?.filter((e: Equipment) => e.nome.toLowerCase().includes(q.toLowerCase())).map((e: Equipment) => <article key={e.id}><Box color="#2563eb"/><small>{e.codigo}</small><h3>{e.nome}</h3><p>{sectors.data?.find((s: Sector) => s.id === e.setor_id)?.nome} · {e.localizacao}</p><Badge>{e.status}</Badge><p><Link to={"/chamados?equipamento=" + e.id}>Abrir solicitação →</Link></p></article>)}</div></>; }
