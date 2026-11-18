import { lazy, Suspense, type ReactNode } from 'react';
import { Routes, Route, Link, useParams } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { ErrorState, Loading } from './components/Feedback';
import { useSession } from './hooks/useSession';
import Login from './pages/Login';
import { validId, validEquipmentIdentifier } from './services/navigation';

function ValidResource({children, equipment = false}: {children: ReactNode; equipment?: boolean}) {
    const params = useParams();
    const valid = equipment ? validEquipmentIdentifier(params.identifier) : validId(params.id);
    return valid ? children : <p role="alert">Identificador inválido. <Link to={equipment ? '/equipamentos' : '/chamados'}>Voltar à listagem</Link></p>;
}

const Admin = lazy(() => import('./pages/Admin'));
const Preventives = lazy(() => import('./pages/Preventives'));
const Notifications = lazy(() => import('./pages/Notifications'));
const Reports = lazy(() => import('./pages/Reports'));
const Scanner = lazy(() => import('./pages/Scanner'));
const EquipmentDetail = lazy(() => import('./pages/EquipmentDetail'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Tickets = lazy(() => import('./pages/Tickets'));
const Detail = lazy(() => import('./pages/Detail'));
const Orders = lazy(() => import('./pages/Orders'));
const Equipments = lazy(() => import('./pages/Equipments'));

export default function App() {
    const { user, setUser, loading, sessionError, retry, logout } = useSession();
    if (loading) return <Loading/>;
    if (sessionError) return <ErrorState message={sessionError} retry={retry}/>;
    if (!user) return <Login onLogin={setUser}/>;
    return <AppShell user={user} onLogout={logout}><Suspense fallback={<Loading/>}><Routes>
        <Route path="/usuarios" element={user.perfil === 'administrador' ? <Admin kind="usuarios"/> : <p>Acesso restrito</p>}/>
        <Route path="/setores" element={user.perfil === 'administrador' ? <Admin kind="setores"/> : <p>Acesso restrito</p>}/>
        <Route path="/" element={<Dashboard/>}/>
        <Route path="/chamados" element={<Tickets/>}/>
        <Route path="/chamados/:id" element={<ValidResource><Detail user={user}/></ValidResource>}/>
        <Route path="/ordens" element={<Orders user={user}/>}/>
        <Route path="/preventivas" element={user.perfil !== 'operador' ? <Preventives user={user}/> : <p>Acesso restrito</p>}/>
        <Route path="/notificacoes" element={<Notifications/>}/>
        <Route path="/relatorios" element={['administrador', 'supervisor'].includes(user.perfil) ? <Reports/> : <p>Acesso restrito</p>}/>
        <Route path="/scanner" element={<Scanner/>}/>
        <Route path="/equipamentos/:identifier" element={<ValidResource equipment><EquipmentDetail user={user}/></ValidResource>}/>
        <Route path="/equipamentos" element={<Equipments user={user}/>}/>
        <Route path="*" element={<p>Página não encontrada. <Link to="/">Voltar ao painel</Link></p>}/>
    </Routes></Suspense></AppShell>;
}
