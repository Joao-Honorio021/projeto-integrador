import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Box, Plus } from 'lucide-react';
import { api } from '../services/api';
import { useData } from '../hooks/useData';
import { Badge } from '../components/Badge';
import { Form } from '../components/Form';
import { Loading, EmptyState, ErrorState } from '../components/Feedback';
import { priorities } from '../types/domain';
import type { User, Equipment, Sector } from '../types/domain';

export default function Equipments({ user }: { user: User }) {
    const { data, err, reload } = useData<Equipment[]>('/equipamentos');
    const sectors = useData<Sector[]>('/setores');
    const [show, setShow] = useState(false);
    const [params, setParams] = useSearchParams();
    const q = params.get('q') || '';
    const page = Math.max(1, Number(params.get('page')) || 1);
    const filtered = data?.filter(e => `${e.nome} ${e.codigo}`.toLowerCase().includes(q.toLowerCase())
        && (!params.get('setor') || String(e.setor_id) === params.get('setor'))
        && (!params.get('status') || e.status === params.get('status'))
        && (!params.get('criticidade') || e.criticidade === params.get('criticidade'))) || [];
    const totalPages = Math.max(1, Math.ceil(filtered.length / 12));
    const currentPage = Math.min(page, totalPages);
    function filter(key: string, value: string) {
        setParams(previous => { const next = new URLSearchParams(previous); if (value) next.set(key, value); else next.delete(key); if(key !== 'page') next.delete('page'); return next; }, { replace: true });
    }
    return <>
        <div className="intro"><div><span className="eyebrow">GESTÃO DE ATIVOS</span><h2>Equipamentos</h2><p>Identificação, histórico e manutenção de cada ativo.</p></div>{user.perfil === 'administrador' && <button onClick={() => setShow(!show)} aria-expanded={show}><Plus size={16}/>Cadastrar equipamento</button>}</div>
        {show && <article><h3>Novo equipamento</h3><Form fields={[
            { name: 'codigo', label: 'Código', minLength: 1, maxLength: 40 }, { name: 'nome', label: 'Nome', minLength: 2, maxLength: 120 },
            { name: 'setor_id', label: 'Setor', options: sectors.data || [] },
            { name: 'modelo', label: 'Modelo', required: false, maxLength: 120 }, { name: 'fabricante', label: 'Fabricante', required: false, maxLength: 120 },
            { name: 'localizacao', label: 'Localização', required: false, maxLength: 200 }, { name: 'descricao', label: 'Descrição', required: false, area: true, maxLength: 5000 },
            { name: 'criticidade', label: 'Criticidade', options: priorities, value: 'Média' },
            { name: 'status', label: 'Status', options: ['Operacional', 'Em manutenção', 'Inativo'], value: 'Operacional' },
        ]} onSave={async v => { await api.post('/equipamentos', { ...v, setor_id: Number(v.setor_id) }); setShow(false); reload(); }}/></article>}
        <div className="filters"><label>Busca<input placeholder="Nome ou código" value={q} onChange={e => filter('q', e.target.value)}/></label>
            <label>Setor<select value={params.get('setor') || ''} onChange={e => filter('setor', e.target.value)}><option value="">Todos</option>{sectors.data?.map(s => <option key={s.id} value={s.id}>{s.nome}</option>)}</select></label>
            <label>Status<select value={params.get('status') || ''} onChange={e => filter('status', e.target.value)}><option value="">Todos</option>{['Operacional', 'Em manutenção', 'Inativo'].map(s => <option key={s}>{s}</option>)}</select></label>
            <label>Criticidade<select value={params.get('criticidade') || ''} onChange={e => filter('criticidade', e.target.value)}><option value="">Todas</option>{priorities.map(s => <option key={s}>{s}</option>)}</select></label>
        </div>
        {err ? <ErrorState message={err} retry={reload}/> : !data ? <Loading/> : !filtered.length ? <EmptyState title="Nenhum equipamento encontrado" description="Revise os filtros ou cadastre um equipamento."/> : <>
            <div className="equipment-grid">{filtered.slice((currentPage - 1) * 12, currentPage * 12).map(e => <article key={e.id}><Box/><small>{e.codigo}</small><h3><Link to={'/equipamentos/' + e.public_id}>{e.nome}</Link></h3><p>{sectors.data?.find(s => s.id === e.setor_id)?.nome} · {e.localizacao || 'Localização não informada'}</p><Badge>{e.status}</Badge> <Badge>{e.criticidade}</Badge><p><Link to={'/equipamentos/' + e.public_id}>Ver detalhes e QR Code →</Link></p></article>)}</div>
            <div className="pagination"><span>{filtered.length} equipamentos</span><button disabled={currentPage === 1} onClick={() => filter('page', String(currentPage - 1))}>Anterior</button><span>{currentPage} de {totalPages}</span><button disabled={currentPage === totalPages} onClick={() => filter('page', String(currentPage + 1))}>Próxima</button></div>
        </>}
    </>;
}
