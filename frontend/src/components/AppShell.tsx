import { useEffect, useState, type ReactNode } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { Factory, LayoutDashboard, Headphones, Wrench, Box, LogOut, ScanLine, CalendarDays, Bell, ChartNoAxesCombined, PanelLeftClose, Menu, Users, Building2 } from 'lucide-react';
import { api, error } from '../services/api';
import type { User } from '../types/domain';
const sections = [
    { title:'Principal', items:[['/','Dashboard',LayoutDashboard],['/equipamentos','Equipamentos',Box],['/chamados','Chamados',Headphones],['/ordens','Ordens de serviço',Wrench],['/scanner','Ler QR Code',ScanLine]] },
    { title:'Manutenção', items:[['/preventivas','Preventivas',CalendarDays],['/relatorios','Relatórios',ChartNoAxesCombined]] },
    { title:'Sistema', items:[['/notificacoes','Notificações',Bell],['/usuarios','Usuários',Users],['/setores','Setores',Building2]] },
] satisfies {title:string;items:[string,string,typeof Box][]}[];
export function AppShell({user,onLogout,children}:{user:User;onLogout:()=>void;children:ReactNode}) {
    const [collapsed,setCollapsed]=useState(false), [mobile,setMobile]=useState(false), [q,setQ]=useState('');
    const [results,setResults]=useState<{titulo:string;destino:string}[]>([]), [searchError,setSearchError]=useState(''), [searching,setSearching]=useState(false), [unread,setUnread]=useState(0);
    const location=useLocation();
    useEffect(()=>{setMobile(false);setQ('');setResults([])},[location.pathname]);
    useEffect(()=>{const controller=new AbortController();api.get('/notificacoes/contador',{signal:controller.signal}).then(r=>setUnread(r.data.nao_lidas)).catch(()=>{});return()=>controller.abort()},[location.pathname]);
    useEffect(()=>{
        if(q.trim().length<2){setResults([]);setSearching(false);return}
        const controller=new AbortController();setSearching(true);setSearchError('');
        const timeout=setTimeout(()=>api.get('/busca',{params:{q:q.trim()},signal:controller.signal}).then(r=>setResults(r.data)).catch(reason=>{if(!controller.signal.aborted)setSearchError(error(reason))}).finally(()=>{if(!controller.signal.aborted)setSearching(false)}),300);
        return()=>{clearTimeout(timeout);controller.abort()};
    },[q]);
    const title=sections.flatMap(s=>s.items).find(([path])=>path==='/'?location.pathname==='/':location.pathname.startsWith(path))?.[1]||'Detalhes';
    function permitted(path:string){return !(path==='/preventivas'&&user.perfil==='operador'||path==='/relatorios'&&!['administrador','supervisor'].includes(user.perfil)||['/usuarios','/setores'].includes(path)&&user.perfil!=='administrador')}
    return <div className={`shell ${collapsed?'collapsed':''} ${mobile?'mobile-open':''}`}>
        <a className="skip-link" href="#conteudo">Pular para o conteúdo</a>
        <aside id="navigation"><Link to="/" className="brand"><Factory/><span>IndusTrack <small>v1.0.2</small></span></Link><nav aria-label="Navegação principal">{sections.map(section=><section key={section.title}>{section.items.some(([p])=>permitted(p))&&<small className="nav-group">{section.title}</small>}{section.items.filter(([p])=>permitted(p)).map(([path,label,Icon])=><NavLink end={path==='/'} key={path} to={path} title={label}><Icon size={19}/><span>{label}</span></NavLink>)}</section>)}</nav><button className="collapse-control secondary" onClick={()=>setCollapsed(!collapsed)} aria-label={collapsed?'Expandir navegação':'Recolher navegação'}><PanelLeftClose size={18}/><span>Recolher</span></button></aside>
        <div className="workspace"><header><button className="mobile-menu" onClick={()=>setMobile(!mobile)} aria-controls="navigation" aria-expanded={mobile} aria-label="Abrir navegação"><Menu size={20}/></button><div className="breadcrumb"><Link to="/">IndusTrack</Link><span> / {title}</span></div>
            <div className="global-search"><label className="sr-only" htmlFor="global-search">Buscar equipamentos, chamados e ordens</label><input id="global-search" placeholder="Buscar na operação…" value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>{if(e.key==='Escape')setQ('')}}/>{q.trim().length>=2&&<div className="search-results" role="region" aria-label="Resultados da busca">{searching?<p role="status">Buscando…</p>:searchError?<p role="alert">{searchError}</p>:results.length?results.map((r,i)=><Link key={r.destino+i} to={r.destino} onClick={()=>setQ('')}>{r.titulo}</Link>):<p>Nenhum resultado acessível.</p>}</div>}</div>
            <Link to="/notificacoes" className="notification-link" aria-label={`Notificações: ${unread} não lidas`}><Bell size={20}/>{unread>0&&<b>{unread>99?'99+':unread}</b>}</Link>
            <details className="user-menu"><summary><span className="avatar">{user.nome.split(' ').map(n=>n[0]).slice(0,2).join('')}</span><span className="user-name">{user.nome}<small>{user.perfil}</small></span></summary><div className="user-menu-content"><b>{user.nome}</b><p>{user.email}</p><button onClick={onLogout}><LogOut size={16}/>Sair da conta</button></div></details>
        </header><main id="conteudo">{children}</main></div>
    </div>;
}
