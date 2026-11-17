import { useState } from 'react';
import { Factory } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { api, error } from '../services/api';
import { useData } from '../hooks/useData';
import { ErrorState, Loading } from '../components/Feedback';
import type { User } from '../types/domain';

const loginSchema = z.object({ email: z.email('Informe um e-mail válido'), senha: z.string() });
export default function Login({ onLogin }: { onLogin: (user: User) => void }) {
    const { data: config, err: configError, reload } = useData<{ modo_demo: boolean }>('/auth/config');
    const [err, setErr] = useState('');
    const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm({ resolver: zodResolver(loginSchema) });
    return <div className="login"><div className="login-brand"><Factory size={38}/><h1>IndusTrack<span>Manutenção conectada.<br />Operação organizada.</span></h1><p>Uma central para cuidar dos seus equipamentos e de cada atendimento.</p></div><article><span className="eyebrow">BEM-VINDO DE VOLTA</span><h2>Acesse sua conta</h2><p>{config?.modo_demo ? 'Demonstração: use um e-mail cadastrado. A senha é opcional.' : 'Entre para acompanhar sua operação.'}</p>
        {configError ? <ErrorState message={configError} retry={reload}/> : !config ? <Loading/> : <form onSubmit={handleSubmit(async values => {
            if (!config.modo_demo && !values.senha) { setError('senha', { message: 'Informe a senha' }); return; }
            setErr('');
            try {
                const response = await api.post<{ access_token: string; usuario: User }>('/auth/login', values);
                sessionStorage.setItem('token', response.data.access_token);
                onLogin(response.data.usuario);
            } catch (reason) { setErr(error(reason)); }
        })}>
            <label>E-mail<input autoComplete="username" type="email" {...register('email')}/></label><small>{errors.email?.message}</small>
            <label>Senha<input autoComplete="current-password" type="password" {...register('senha')}/></label><small>{errors.senha?.message}</small>
            {err && <p className="error" role="alert">{err}</p>}
            <button disabled={isSubmitting}>{isSubmitting ? 'Entrando…' : 'Entrar na plataforma'}</button>
        </form>}
    </article></div>;
}
