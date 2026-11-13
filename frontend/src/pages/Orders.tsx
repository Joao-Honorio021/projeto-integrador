import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { api, error } from '../services/api';
import { useData } from '../hooks/useData';
import { Badge } from '../components/Badge';
import { Form } from '../components/Form';
import { Loading, EmptyState, ErrorState } from '../components/Feedback';
import type { User, Order } from '../types/domain';
export default function Orders({user}:{user:User}) {
    const {data,err,reload}=useData<Order[]>('/ordens-servico');
    const [params,setParams]=useSearchParams();
    const [selected,setSelected]=useState<number|null>(null),[message,setMessage]=useState(''),[busy,setBusy]=useState(false);
    const manager=['administrador','supervisor'].includes(user.perfil);
    const filtered=data?.filter(o=>(!params.get('status')||o.status===params.get('status'))&&(!params.get('q')||String(o.id).includes(params.get('q')!)))||[];
    async function action(id:number,path:string){setBusy(true);setMessage('');try{await api.patch(`/ordens-servico/${id}/${path}`);reload()}catch(reason){setMessage(error(reason))}finally{setBusy(false)}}
    function filter(key:string,value:string){setParams(previous=>{const next=new URLSearchParams(previous);if(value)next.set(key,value);else next.delete(key);return next},{replace:true})}
    return <><h2>Ordens de serviço</h2><p>Acompanhe prazos, registre o diagnóstico e conclua o atendimento.</p>
        <div className="filters"><label>Número da OS<input value={params.get('q')||''} onChange={e=>filter('q',e.target.value)}/></label><label>Status<select value={params.get('status')||''} onChange={e=>filter('status',e.target.value)}><option value="">Todos</option>{['Pendente','Em execução','Pausada','Concluída','Cancelada'].map(s=><option key={s}>{s}</option>)}</select></label></div>
        {message&&<p role="alert" className="error">{message}</p>}{err?<ErrorState message={err} retry={reload}/>:!data?<Loading/>:!filtered.length?<EmptyState title="Nenhuma ordem encontrada" description="Revise os filtros ou aguarde a atribuição de um atendimento."/>:filtered.map(o=>{
            const active=!['Concluída','Cancelada'].includes(o.status);
            return <article key={o.id} className="order"><div className="order-head"><h3>OS-{String(o.id).padStart(4,'0')}</h3><Link to={'/chamados/'+o.chamado_id}>Chamado #{o.chamado_id} e histórico</Link><Badge>{o.status}</Badge></div>
                <p>Prazo: {o.prazo?o.prazo.split('-').reverse().join('/'):'Não definido'} · Início: {o.inicio?new Date(o.inicio).toLocaleString('pt-BR'):'Não iniciado'}</p>
                {user.perfil!=='operador'&&<div className="actions">{['Pendente','Pausada'].includes(o.status)&&<button disabled={busy} onClick={()=>action(o.id,'iniciar')}>{o.status==='Pausada'?'Retomar':'Iniciar atendimento'}</button>}{o.status==='Em execução'&&<><button disabled={busy} className="secondary" onClick={()=>action(o.id,'pausar')}>Pausar</button><button onClick={()=>setSelected(selected===o.id?null:o.id)}>Registrar atendimento</button></>}</div>}
                {selected===o.id&&o.status==='Em execução'&&<><Form label="Salvar diagnóstico" fields={[{name:'diagnostico',label:'Diagnóstico parcial',value:o.diagnostico,area:true}]} onSave={async v=>{await api.patch(`/ordens-servico/${o.id}/diagnostico`,v);reload()}}/><Form label="Concluir atendimento" fields={[{name:'diagnostico',label:'Diagnóstico final',value:o.diagnostico,area:true},{name:'solucao',label:'Solução executada',area:true}]} onSave={async v=>{if(!window.confirm('Concluir esta ordem e resolver o chamado?'))return false;await api.patch(`/ordens-servico/${o.id}/concluir`,v);setSelected(null);reload()}}/></>}
                {manager&&active&&<details><summary>Prazo e cancelamento</summary><Form label="Definir prazo" fields={[{name:'prazo',label:'Prazo de atendimento',type:'date',value:o.prazo||''}]} onSave={async v=>{await api.patch(`/ordens-servico/${o.id}/prazo`,v);reload()}}/><Form label="Cancelar ordem" fields={[{name:'mensagem',label:'Motivo do cancelamento',area:true}]} onSave={async v=>{if(!window.confirm('Cancelar a ordem e o chamado associado? O histórico será preservado.'))return false;await api.patch(`/ordens-servico/${o.id}/cancelar`,v);reload()}}/></details>}
                {o.diagnostico&&<p><b>Diagnóstico:</b> {o.diagnostico}</p>}{o.solucao&&<p><b>Solução:</b> {o.solucao}</p>}{o.conclusao&&<small>Concluída em {new Date(o.conclusao).toLocaleString('pt-BR')}</small>}
            </article>
        })}
    </>;
}
