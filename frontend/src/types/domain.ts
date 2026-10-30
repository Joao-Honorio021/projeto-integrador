export type Role = 'administrador' | 'supervisor' | 'tecnico' | 'operador';
export interface User {
    id: number;
    nome: string;
    email: string;
    perfil: Role;
    ativo: boolean;
}
export interface Sector {
    id: number;
    nome: string;
}
export interface Equipment {
    id: number;
    codigo: string;
    nome: string;
    setor_id: number;
    localizacao: string;
    status: string;
    ativo: boolean;
}
export interface Ticket {
    id: number;
    titulo: string;
    descricao: string;
    equipamento_id: number;
    solicitante_id: number;
    tecnico_id: number | null;
    prioridade: string;
    status: string;
    criado_em: string;
    resolvido_em: string | null;
}
export interface TicketPage {
    items: Ticket[];
    total: number;
}
export interface TicketDetail extends Ticket {
    historico: {
        id: number;
        autor: string;
        criado_em: string;
        mensagem: string;
        tipo: string;
    }[];
}
export interface Order {
    id: number;
    chamado_id: number;
    tecnico_id: number;
    status: string;
    diagnostico: string;
    solucao: string;
    inicio: string | null;
    conclusao: string | null;
}
export interface Metric {
    nome: string;
    quantidade: number;
}
export interface Summary {
    total: number;
    status: Metric[];
    prioridades: Metric[];
    ordens_pendentes: number;
}
export const priorities = ['Baixa', 'Média', 'Alta', 'Crítica'];
