import axios from 'axios';
export const api = axios.create({ baseURL: '/api', timeout: 15000 });
api.interceptors.request.use(config => {
    const token = sessionStorage.getItem('token');
    if (token)
        config.headers.Authorization = `Bearer ${token}`;
    return config;
});
api.interceptors.response.use(response => response, reason => {
    if (reason.response?.status === 401 && !reason.config?.url?.includes('/auth/login')) {
        sessionStorage.removeItem('token');
        window.dispatchEvent(new Event('auth:expired'));
    }
    return Promise.reject(reason);
});
export function error(reason: unknown): string {
    if (!axios.isAxiosError(reason))
        return 'Ocorreu um erro inesperado. Tente novamente.';
    const detail = reason.response?.data?.detail;
    if (typeof detail === 'string')
        return detail;
    if (Array.isArray(detail))
        return detail.map((item: {
            loc?: string[];
            msg?: string;
        }) => `${item.loc?.slice(1).join('.') || 'Campo'}: ${item.msg || 'valor inválido'}`).join(' · ');
    return reason.response ? 'Não foi possível concluir a operação. Tente novamente.' : 'Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.';
}
