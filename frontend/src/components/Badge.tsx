import type { ReactNode } from 'react';
export function Badge({ children }: {
    children: ReactNode;
}) {
    const text = String(children);
    const tone = ['Crítica', 'Alta'].includes(text) ? 'red' : ['Resolvido', 'Concluída', 'Operacional'].includes(text) ? 'green' : ['Pendente', 'Pausada', 'Em análise'].includes(text) ? 'amber' : '';
    return <span className={`badge ${tone}`}><span aria-hidden="true">●</span> {children}</span>;
}
