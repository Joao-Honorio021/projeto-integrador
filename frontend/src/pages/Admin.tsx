import { useState } from 'react';
import { api } from '../services/api';
import { useData } from '../hooks/useData';
import { Form } from '../components/Form';
import { Loading, ErrorState } from '../components/Feedback';
import type { User, Sector } from '../types/domain';
const roles=['administrador','supervisor','tecnico','operador'];
export default function Admin({kind}:{kind:'usuarios'|'setores'}) {
    const {data,err,reload}=useData<(User|Sector)[]>('/'+kind);
    const [selected,setSelected]=useState<number|null>(null),[show,setShow]=useState(false);
    const users=kind==='usuarios';
    return <><div className="intro"><div><span className="eyebrow">ADMINISTRAÇÃO</span><h2>{users?'Usuários':'Setores'}</h2><p>{users?'Gerencie os acessos à operação.':'Organize os equipamentos por área.'}</p></div><button onClick={()=>setShow(!show)}>{users?'Cadastrar usuário':'Cadastrar setor'}</button></div>
        {show&&<article><Form fields={users?[{name:'nome',label:'Nome',minLength:2,maxLength:120},{name:'email',label:'E-mail',type:'email',maxLength:254},{name:'perfil',label:'Perfil',options:roles},{name:'senha',label:'Senha inicial (mínimo 12 caracteres)',type:'password',minLength:12,maxLength:128}]:[{name:'nome',label:'Nome do setor',minLength:2,maxLength:120}]} onSave={async v=>{await api.post('/'+kind,v);setShow(false);reload()}}/></article>}
        {err?<ErrorState message={err} retry={reload}/>:!data?<Loading/>:data.map(item=><article key={item.id}><div className="order-head"><h3>{item.nome}</h3><button className="secondary" onClick={()=>setSelected(selected===item.id?null:item.id)}>Editar</button></div>{'email' in item&&<p>{item.email} · {item.perfil} · {item.ativo?'Ativo':'Inativo'}</p>}{selected===item.id&&<Form key={item.id} fields={'email' in item?[{name:'nome',label:'Nome',value:item.nome,minLength:2,maxLength:120},{name:'perfil',label:'Perfil',options:roles,value:item.perfil},{name:'ativo',label:'Acesso',options:[{id:1,nome:'Ativo'},{id:0,nome:'Inativo'}],value:item.ativo?'1':'0'}]:[{name:'nome',label:'Nome do setor',value:item.nome,minLength:2,maxLength:120}]} onSave={async v=>{if(users&&v.ativo==='0'&&!window.confirm('Desativar o acesso deste usuário?'))return false;await api.patch(`/${kind}/${item.id}`,users?{...v,ativo:v.ativo==='1'}:v);setSelected(null);reload()}}/>}</article>)}
    </>;
}
