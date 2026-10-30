import { useState, useEffect, lazy, Suspense } from 'react';
import { NavLink, Routes, Route, Link } from 'react-router-dom';
import { Factory, LayoutDashboard, Headphones, Wrench, Box, LogOut } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { api, error } from './services/api';
import { Loading } from './components/Feedback';
import type { User } from './types/domain';
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Tickets = lazy(() => import('./pages/Tickets'));
const Detail = lazy(() => import('./pages/Detail'));
const Orders = lazy(() => import('./pages/Orders'));
const Equipments = lazy(() => import('./pages/Equipments'));
const loginSchema = z.object({ email: z.email('Informe um e-mail válido'), senha: z.string().min(1, 'Informe a senha') });
export default function App() { const [user, setUser] = useState<User | null>(null), [loading, setLoading] = useState(true), [err, setErr] = useState(''); const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({ resolver: zodResolver(loginSchema) }); useEffect(() => { const expire = () => { setUser(null); setErr('Sua sessão expirou. Entre novamente.'); }; window.addEventListener('auth:expired', expire); if (sessionStorage.getItem('token'))
    api.get('/auth/me').then(r => setUser(r.data)).catch(() => sessionStorage.removeItem('token')).finally(() => setLoading(false));
else
    setLoading(false); return () => window.removeEventListener("auth:expired", expire); }, []); if (loading)
    return <Loading />; if (!user)
    return <div className="login"><div className="login-brand"><Factory size={38}/><h1>IndusTrack<span>Manutenção conectada.<br />Operação organizada.</span></h1><p>Uma central para cuidar dos seus equipamentos e de cada atendimento.</p></div><article><span className="eyebrow">BEM-VINDO DE VOLTA</span><h2>Acesse sua conta</h2><p>Entre para acompanhar sua operação.</p><form onSubmit={handleSubmit(async (v) => { try {
        const r = await api.post('/auth/login', v);
        sessionStorage.setItem('token', r.data.access_token);
        setUser(r.data.usuario);
    }
    catch (e) {
        setErr(error(e));
    } })}><label>E-mail<input autoComplete="username" type="email" {...register('email')}/></label><small>{errors.email?.message}</small><label>Senha<input autoComplete="current-password" type="password" {...register('senha')}/></label>{err && <p className="error" role="alert">{err}</p>}<button disabled={isSubmitting}>{isSubmitting ? 'Entrando…' : 'Entrar na plataforma'}</button></form></article></div>; return <div className="shell"><a className="skip-link" href="#conteudo">Pular para o conteúdo</a><aside><div className="brand"><Factory /> IndusTrack</div><small>GESTÃO INDUSTRIAL</small><nav>{([['/', 'Dashboard', LayoutDashboard], ['/chamados', 'Central de suporte', Headphones], ['/ordens', 'Ordens de serviço', Wrench], ['/equipamentos', 'Equipamentos', Box]] satisfies [
    string,
    string,
    typeof Box
][]).map(([path, title, Icon]) => <NavLink end={path === '/'} key={path} to={path}><Icon size={19}/>{title}</NavLink>)}</nav><div className="sidebar-foot">SUPORTE & MANUTENÇÃO<small>Projeto Integrador · SENAI</small></div></aside><div className="workspace"><header><span>GESTÃO DE ATIVOS / CENTRAL DE OPERAÇÕES</span><span className="avatar">{user.nome.split(" ").map(n => n[0]).slice(0, 2).join("")}</span><div><b>{user.nome}</b><small>{user.perfil}</small></div><button className="logout" aria-label="Sair" onClick={() => { sessionStorage.removeItem('token'); setUser(null); }}><LogOut size={18}/></button></header><main id="conteudo"><Suspense fallback={<Loading />}><Routes><Route path="/" element={<Dashboard />}/><Route path="/chamados" element={<Tickets />}/><Route path="/chamados/:id" element={<Detail user={user}/>}/><Route path="/ordens" element={<Orders user={user}/>}/><Route path="/equipamentos" element={<Equipments user={user}/>}/><Route path="*" element={<p>Página não encontrada. <Link to="/">Voltar ao painel</Link></p>}/></Routes></Suspense></main></div></div>; }
