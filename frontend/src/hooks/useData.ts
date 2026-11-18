import { useCallback, useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { api, error } from '../services/api';
/** Cancela requisições antigas para que filtros rápidos não exibam resultados obsoletos. */
export function useData<T>(url: string) {
    const [data, setData] = useState<T | null>(null), [err, setErr] = useState('');
    const active = useRef<AbortController | null>(null);
    const reload = useCallback(async () => {
        active.current?.abort();
        const controller = new AbortController();
        active.current = controller;
        setErr('');
        try {
            const response = await api.get<T>(url, { signal: controller.signal });
            if (!controller.signal.aborted)
                setData(response.data);
        }
        catch (reason) {
            if (!axios.isCancel(reason) && !controller.signal.aborted) {
                setData(null);
                setErr(error(reason));
            }
        }
    }, [url]);
    useEffect(() => {
        setData(null);
        void reload();
        const refresh = () => { void reload(); };
        window.addEventListener('data:changed', refresh);
        return () => { active.current?.abort(); window.removeEventListener('data:changed', refresh); };
    }, [reload]);
    return { data, err, reload };
}
