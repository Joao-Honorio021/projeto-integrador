import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useData } from '../hooks/useData';
import { api, error } from '../services/api';
import { Loading, ErrorState, EmptyState } from '../components/Feedback';
import { notificationDestination } from '../services/navigation';

interface Notification {
    id: number;
    mensagem: string;
    destino: string | null;
    criado_em: string;
    lida: boolean;
}

export default function Notifications() {
    const { data, err, reload } = useData<Notification[]>('/notificacoes');
    const count = useData<{nao_lidas:number}>('/notificacoes/contador');
    const navigate = useNavigate();
    const [message, setMessage] = useState('');
    const [busy, setBusy] = useState(false);

    async function read(path: string, destination?: string) {
        if (busy) return;
        setBusy(true);
        try {
            await api.patch(path);
            setMessage('');
            if (destination) navigate(destination);
        } catch (reason) {
            setMessage(error(reason));
        } finally {
            setBusy(false);
        }
    }

    return <>
        <div className="intro">
            <h2>Notificações{count.data ? ` (${count.data.nao_lidas} não lidas)` : ''}</h2>
            <button disabled={busy || !count.data?.nao_lidas} onClick={() => read('/notificacoes/ler-todas')}>Marcar todas como lidas</button>
        </div>
        {count.err && <ErrorState message={count.err} retry={count.reload}/>}
        {message && <p role="alert">{message}</p>}
        {err ? <ErrorState message={err} retry={reload}/> : !data ? <Loading/> : !data.length
            ? <EmptyState title="Nenhuma notificação" description="Novos eventos autorizados aparecerão aqui."/>
            : data.map(n => {
                const destination = notificationDestination(n);
                return <article key={n.id}>
                    <small>{new Date(n.criado_em).toLocaleString('pt-BR')}</small>
                    <h3>{n.mensagem}</h3>
                    {destination ? <Link to={destination} onClick={event => {
                        if (!n.lida && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) {
                            event.preventDefault();
                            void read(`/notificacoes/${n.id}/ler`, destination);
                        }
                    }}>Abrir registro →</Link> : <span>Registro indisponível</span>}
                    {!n.lida && <button disabled={busy} className="secondary" onClick={() => read(`/notificacoes/${n.id}/ler`)}>Marcar como lida</button>}
                </article>;
            })}
    </>;
}
