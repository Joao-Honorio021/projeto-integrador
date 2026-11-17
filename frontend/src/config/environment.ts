/** O navegador conhece somente a API HTTP; credenciais PostgreSQL ficam no backend. */
export const API_URL = (import.meta.env.VITE_API_URL?.trim() || '/api').replace(/\/+$/, '');
