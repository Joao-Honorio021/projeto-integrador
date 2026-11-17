import { useCallback, useEffect, useState } from 'react';
import { api, error } from '../services/api';
import type { User } from '../types/domain';

export function useSession() {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [sessionError, setSessionError] = useState('');
    const restore = useCallback(async (signal?: AbortSignal) => {
        setSessionError('');
        if (!sessionStorage.getItem('token')) { setLoading(false); return; }
        setLoading(true);
        try {
            const response = await api.get<User>('/auth/me', { signal });
            if (!signal?.aborted) setUser(response.data);
        } catch (reason) {
            // Somente o interceptor de 401 encerra uma sessão; falhas de rede permitem tentar novamente.
            if (!signal?.aborted && sessionStorage.getItem('token')) setSessionError(error(reason));
        } finally {
            if (!signal?.aborted) setLoading(false);
        }
    }, []);
    useEffect(() => {
        const controller = new AbortController();
        const expire = () => { setUser(null); setSessionError(''); };
        window.addEventListener('auth:expired', expire);
        void restore(controller.signal);
        return () => { controller.abort(); window.removeEventListener('auth:expired', expire); };
    }, [restore]);
    function logout() { sessionStorage.removeItem('token'); setUser(null); setSessionError(''); }
    return { user, setUser, loading, sessionError, retry: () => void restore(), logout };
}
