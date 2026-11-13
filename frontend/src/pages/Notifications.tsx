import {Link} from 'react-router-dom';
import {useState} from 'react';
import {useData} from '../hooks/useData';
import {api,error} from '../services/api';
import {Loading,ErrorState,EmptyState} from '../components/Feedback';
interface Notification {id:number;mensagem:string;destino:string;criado_em:string;lida:boolean}
export default function Notifications(){const {data,err,reload}=useData<Notification[]>('/notificacoes');const [message,setMessage]=useState('');async function read(path:string){try{await api.patch(path);reload()}catch(reason){setMessage(error(reason))}}return <><div className="intro"><h2>Notificações ({data?.filter(n=>!n.lida).length||0} não lidas)</h2><button disabled={!data?.some(n=>!n.lida)} onClick={()=>read('/notificacoes/ler-todas')}>Marcar todas como lidas</button></div>{message&&<p role="alert">{message}</p>}{err?<ErrorState message={err} retry={reload}/>:!data?<Loading/>:!data.length?<EmptyState title="Nenhuma notificação" description="Novos eventos autorizados aparecerão aqui."/>:data.map(n=><article key={n.id}><small>{new Date(n.criado_em).toLocaleString('pt-BR')}</small><h3>{n.mensagem}</h3><Link to={n.destino}>Abrir registro →</Link>{!n.lida&&<button className="secondary" onClick={()=>read(`/notificacoes/${n.id}/ler`)}>Marcar como lida</button>}</article>)}</>}
