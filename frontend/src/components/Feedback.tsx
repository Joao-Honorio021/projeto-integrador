import { Inbox, AlertCircle, RotateCw } from 'lucide-react';
export function Loading() { return <div className="loading-state" role="status" aria-label="Carregando"><div className="skeleton"/><div className="skeleton"/><div className="skeleton"/><span>Carregando informações…</span></div>; }
export function EmptyState({ title, description }: {
    title: string;
    description: string;
}) { return <div className="empty-state"><Inbox size={30}/><h3>{title}</h3><p>{description}</p></div>; }
export function ErrorState({ message, retry }: {
    message: string;
    retry: () => void;
}) { return <div className="empty-state error-state" role="alert"><AlertCircle /><h3>Não foi possível carregar</h3><p>{message}</p><button onClick={retry}><RotateCw size={15}/>Tentar novamente</button></div>; }
