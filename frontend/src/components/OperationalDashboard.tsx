import { Link } from 'react-router-dom';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import { useData } from '../hooks/useData';
import { Loading, ErrorState, EmptyState } from './Feedback';
import type { Metric } from '../types/domain';
interface Operational {
    equipamentos: number; equipamentos_manutencao: number; preventivas_atrasadas: number;
    ordens_status: Metric[]; chamados_mes: Metric[]; atendimentos_mes: Metric[]; equipamentos_ocorrencias: Metric[];
    proximas_preventivas: {id:number;atividade:string;proxima_execucao:string}[];
    ordens_prioritarias: {id:number;titulo:string;prioridade:string;status:string}[];
    atividades: {id:number;chamado_id:number;mensagem:string;criado_em:string;autor:string}[];
}
export function OperationalDashboard() {
    const { data, err, reload } = useData<Operational>('/dashboard/operacional');
    if (!data) return err ? <ErrorState message={err} retry={reload}/> : <Loading/>;
    const total = (status:string) => data.ordens_status.find(s=>s.nome===status)?.quantidade || 0;
    return <>
        <div className="stats">{[['Equipamentos', data.equipamentos], ['Em manutenção', data.equipamentos_manutencao], ['Ordens em execução', total('Em execução')], ['Ordens concluídas', total('Concluída')], ['Preventivas atrasadas', data.preventivas_atrasadas]].map(([name,value])=><article key={name}><span>{name}</span><strong>{value}</strong><small>Dados da sua área de acesso</small></article>)}</div>
        <div className="charts">{[['Chamados por mês', data.chamados_mes], ['Atendimentos concluídos por mês', data.atendimentos_mes], ['Ordens por status', data.ordens_status], ['Equipamentos com mais ocorrências', data.equipamentos_ocorrencias]].map(([title,values])=><article key={title as string}><h3>{title as string}</h3>{(values as Metric[]).length ? <><ResponsiveContainer width="100%" height={220}><BarChart data={values as Metric[]} margin={{left:-20,right:10}}><XAxis dataKey="nome" tick={{fill:'#94A3B8',fontSize:10}}/><YAxis allowDecimals={false} tick={{fill:'#94A3B8'}}/><Tooltip contentStyle={{background:'#141C2B',borderColor:'#273449',color:'#F1F5F9'}}/><Bar dataKey="quantidade" name="Quantidade" fill="#3B82F6" radius={[4,4,0,0]}/></BarChart></ResponsiveContainer><details><summary>Ver dados do gráfico</summary>{(values as Metric[]).map(v=><p key={v.nome}>{v.nome}: {v.quantidade}</p>)}</details></> : <EmptyState title="Sem registros" description="Os indicadores aparecerão conforme as operações forem registradas."/>}</article>)}</div>
        <div className="charts"><article><h3>Ordens prioritárias</h3>{data.ordens_prioritarias.map(o=><p key={o.id}><Link to="/ordens">OS-{o.id} · {o.titulo}</Link><br/>{o.prioridade} · {o.status}</p>)}{!data.ordens_prioritarias.length&&<p>Nenhuma ordem pendente.</p>}</article><article><h3>Próximas preventivas</h3>{data.proximas_preventivas.map(p=><p key={p.id}><Link to="/preventivas">{p.atividade}</Link><br/>{p.proxima_execucao.split('-').reverse().join('/')}</p>)}{!data.proximas_preventivas.length&&<p>Nenhum plano acessível.</p>}</article></div>
        <article><h3>Atividades recentes</h3>{data.atividades.map(a=><div className="timeline" key={a.id}><small>{new Date(a.criado_em).toLocaleString('pt-BR')} · {a.autor}</small><Link to={'/chamados/'+a.chamado_id}>CH-{a.chamado_id}</Link><p>{a.mensagem}</p></div>)}{!data.atividades.length&&<p>Nenhuma atividade registrada.</p>}</article>
    </>;
}
