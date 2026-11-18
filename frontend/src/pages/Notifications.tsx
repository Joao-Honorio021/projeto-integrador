import { Link } from 'react-router-dom';
import { useState } from 'react';
import { useData } from '../hooks/useData';
import { api, error } from '../services/api';
import { Loading, ErrorState, EmptyState } from '../components/Feedback';

interface Notification {
    id: number;
    mensagem: string;
    destino: string | null;
    criado_em: string;
    lida: boolean;
}

function destinationFor(notification: Notification): string | null {
    const legacyOrder = notification.destino === '/ordens'
        ? notification.mensagem.match(/\bOS-(\d+)\b/)
        : null;
    const destination = legacyOrder
        ? `/ordens?id=${legacyOrder[1]}`
        : notification.destino;

    if (!destination) return null;
    return /^\/(?:equipamentos\/(?:[1-9]\d*|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})|chamados\/[1-9]\d*|ordens(?:\?id=[1-9]\d*)?|preventivas)$/.test(destination)
        ? destination
        : null;
}

export default function Notifications() {
    const { data, err, reload } = useData<Notification[]>('/notificacoes');
    const [message, setMessage] = useState('');

    async function read(path: string) {
        try {
            await api.patch(path);
            setMessage('');
            reload();
        } catch (reason) {
            setMessage(error(reason));
        }
    }

    return <>
        <div className="intro">
            <h2>Notificações ({data?.filter(n => !n.lida).length || 0} não lidas)</h2>
            <button disabled={!data?.some(n => !n.lida)} onClick={() => read('/notificacoes/ler-todas')}>Marcar todas como lidas</button>
        </div>
        {message && <p role="alert">{message}</p>}
        {err ? <ErrorState message={err} retry={reload}/> : !data ? <Loading/> : !data.length
            ? <EmptyState title="Nenhuma notificação" description="Novos eventos autorizados aparecerão aqui."/>
            : data.map(n => {
                const destination = destinationFor(n);
                return <article key={n.id}>
                    <small>{new Date(n.criado_em).toLocaleString('pt-BR')}</small>
                    <h3>{n.mensagem}</h3>
                    {destination ? <Link to={destination}>Abrir registro →</Link> : <span>Registro indisponível</span>}
                    {!n.lida && <button className="secondary" onClick={() => read(`/notificacoes/${n.id}/ler`)}>Marcar como lida</button>}
                </article>;
            })}
    </>;
}
