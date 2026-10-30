import { useState } from 'react';
import { error } from '../services/api';
type Option = string | {
    id: number;
    nome: string;
};
interface Field {
    name: string;
    label: string;
    options?: Option[];
    value?: string;
    area?: boolean;
    type?: string;
    minLength?: number;
}
export function Form({ fields, onSave, label = 'Salvar' }: {
    fields: Field[];
    onSave: (values: Record<string, string>) => Promise<unknown>;
    label?: string;
}) {
    const [err, setErr] = useState(''), [success, setSuccess] = useState(''), [busy, setBusy] = useState(false);
    return <form onSubmit={async (event) => {
            event.preventDefault();
            if (busy)
                return;
            const form = event.currentTarget;
            const values = Object.fromEntries(new FormData(form)) as Record<string, string>;
            setBusy(true);
            setErr('');
            setSuccess('');
            try {
                await onSave(values);
                form.reset();
                setSuccess('Salvo com sucesso.');
            }
            catch (reason) {
                setErr(error(reason));
            }
            finally {
                setBusy(false);
            }
        }}><fieldset disabled={busy}>{fields.map(field => <label key={field.name}>{field.label}
 {field.options ? <select key={`${field.name}-${field.options.length}-${field.value ?? ""}`} name={field.name} required defaultValue={field.value || ''}><option value="">Selecione</option>{field.options.map(option => <option key={typeof option === 'string' ? option : option.id} value={typeof option === 'string' ? option : option.id}>{typeof option === 'string' ? option : option.nome}</option>)}</select> : field.area ? <textarea name={field.name} required minLength={field.minLength ?? 3} maxLength={10000}/> : <input name={field.name} type={field.type || 'text'} required minLength={field.type === 'number' ? undefined : field.minLength ?? 3}/>}
 </label>)}{err && <p role="alert" className="error">{err}</p>}{success && <p role="status" className="success">{success}</p>}<button disabled={busy}>{busy ? 'Salvando…' : label}</button></fieldset></form>;
}
