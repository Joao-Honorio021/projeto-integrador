"""Consultas operacionais sempre limitadas ao escopo do usuário."""
import csv
from datetime import date
from io import StringIO
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import text
from ..core.security import current, allow
from ..database import db_session
from ..repositories.sql_repository import access

router = APIRouter(tags=['Consultas operacionais'])

@router.get('/busca')
def search(q: str = Query(min_length=2, max_length=100), u=Depends(current), db=Depends(db_session)):
    scope, params = access(u)
    params['pattern'] = '%' + q.replace('!', '!!').replace('%', '!%').replace('_', '!_') + '%'
    params['q'] = q.removeprefix('CH-').removeprefix('OS-').lstrip('0') or '0'
    equipment = db.execute(text("SELECT nome AS titulo, '/equipamentos/' || public_id AS destino FROM equipamentos WHERE lower(nome) LIKE lower(:pattern) ESCAPE '!' OR lower(codigo) LIKE lower(:pattern) ESCAPE '!' ORDER BY nome LIMIT 8"), params).mappings()
    tickets = db.execute(text("SELECT t.titulo, '/chamados/' || CAST(t.id AS TEXT) AS destino FROM chamados t WHERE " + scope + " AND (lower(t.titulo) LIKE lower(:pattern) ESCAPE '!' OR CAST(t.id AS TEXT)=:q) ORDER BY t.id DESC LIMIT 8"), params).mappings()
    orders = db.execute(text("SELECT 'OS-' || CAST(o.id AS TEXT) AS titulo, '/ordens' AS destino FROM ordens o JOIN chamados t ON t.id=o.chamado_id WHERE " + scope + " AND CAST(o.id AS TEXT)=:q LIMIT 8"), params).mappings()
    return [dict(r) for r in equipment] + [dict(r) for r in tickets] + [dict(r) for r in orders]

@router.get('/dashboard/operacional')
def operational(u=Depends(current), db=Depends(db_session)):
    scope, params = access(u)
    params.update(today=date.today().isoformat(), user=u.id)
    def rows(sql):
        return [dict(row) for row in db.execute(text(sql), params).mappings()]
    def scalar(sql):
        return db.execute(text(sql), params).scalar_one()
    plan_scope = "(:perfil IN ('administrador','supervisor') OR (:perfil='tecnico' AND responsavel_id=:user))"
    return {
        'equipamentos': scalar('SELECT COUNT(*) FROM equipamentos'),
        'equipamentos_manutencao': scalar("SELECT COUNT(*) FROM equipamentos WHERE status='Em manutenção'"),
        'ordens_status': rows('SELECT o.status AS nome, COUNT(*) AS quantidade FROM ordens o JOIN chamados t ON t.id=o.chamado_id WHERE '+scope+' GROUP BY o.status'),
        'chamados_mes': rows('SELECT substr(t.criado_em,1,7) AS nome, COUNT(*) AS quantidade FROM chamados t WHERE '+scope+' GROUP BY substr(t.criado_em,1,7) ORDER BY nome DESC LIMIT 12')[::-1],
        'atendimentos_mes': rows("SELECT substr(o.conclusao,1,7) AS nome, COUNT(*) AS quantidade FROM ordens o JOIN chamados t ON t.id=o.chamado_id WHERE "+scope+" AND o.status='Concluída' GROUP BY substr(o.conclusao,1,7) ORDER BY nome DESC LIMIT 12")[::-1],
        'equipamentos_ocorrencias': rows('SELECT e.nome, COUNT(*) AS quantidade FROM chamados t JOIN equipamentos e ON e.id=t.equipamento_id WHERE '+scope+' GROUP BY e.id,e.nome ORDER BY quantidade DESC LIMIT 5'),
        'preventivas_atrasadas': scalar('SELECT COUNT(*) FROM preventivas WHERE proxima_execucao<:today AND '+plan_scope),
        'proximas_preventivas': rows('SELECT id,atividade,proxima_execucao FROM preventivas WHERE '+plan_scope+' ORDER BY proxima_execucao LIMIT 5'),
        'ordens_prioritarias': rows("SELECT o.id,o.status,t.titulo,t.prioridade FROM ordens o JOIN chamados t ON t.id=o.chamado_id WHERE "+scope+" AND o.status NOT IN ('Concluída','Cancelada') ORDER BY CASE t.prioridade WHEN 'Crítica' THEN 0 WHEN 'Alta' THEN 1 ELSE 2 END,o.id LIMIT 5"),
        'atividades': rows('SELECT h.id,h.chamado_id,h.mensagem,h.criado_em,u.nome AS autor FROM historico h JOIN chamados t ON t.id=h.chamado_id JOIN usuarios u ON u.id=h.usuario_id WHERE '+scope+' ORDER BY h.id DESC LIMIT 8'),
    }

@router.get('/relatorios/{kind}.csv')
def export(kind: str, inicio: date | None = None, fim: date | None = None, equipamento_id: int | None = None, u=Depends(current), db=Depends(db_session)):
    allow(u, ['administrador', 'supervisor'])
    if inicio and fim and inicio > fim:
        raise HTTPException(422, 'Período inválido')
    params = {'inicio': inicio.isoformat() if inicio else '', 'fim': fim.isoformat() if fim else '', 'equipamento': equipamento_id, 'today': date.today().isoformat()}
    equipment_filter = '(CAST(:equipamento AS INTEGER) IS NULL OR e.id=:equipamento)'
    def period(column):
        return f"(:inicio='' OR substr({column},1,10)>=:inicio) AND (:fim='' OR substr({column},1,10)<=:fim)"
    reports = {
        'ordens-concluidas': (['OS','Equipamento','Conclusão','Diagnóstico','Solução'], "SELECT o.id,e.nome,o.conclusao,o.diagnostico,o.solucao FROM ordens o JOIN chamados t ON t.id=o.chamado_id JOIN equipamentos e ON e.id=t.equipamento_id WHERE o.status='Concluída' AND "+equipment_filter+' AND '+period('o.conclusao')+' ORDER BY o.id'),
        'equipamentos-falhas': (['Código','Equipamento','Ocorrências'], 'SELECT e.codigo,e.nome,COUNT(*) FROM chamados t JOIN equipamentos e ON e.id=t.equipamento_id WHERE '+equipment_filter+' AND '+period('t.criado_em')+' GROUP BY e.id,e.codigo,e.nome ORDER BY COUNT(*) DESC'),
        'preventivas-atrasadas': (['Plano','Equipamento','Atividade','Vencimento'], 'SELECT p.id,e.nome,p.atividade,p.proxima_execucao FROM preventivas p JOIN equipamentos e ON e.id=p.equipamento_id WHERE p.proxima_execucao<:today AND '+equipment_filter+' AND '+period('p.proxima_execucao')+' ORDER BY p.proxima_execucao'),
        'historico-equipamento': (['Código','Equipamento','Chamado','Data','Autor','Evento'], 'SELECT e.codigo,e.nome,t.id,h.criado_em,u.nome,h.mensagem FROM historico h JOIN chamados t ON t.id=h.chamado_id JOIN equipamentos e ON e.id=t.equipamento_id JOIN usuarios u ON u.id=h.usuario_id WHERE '+equipment_filter+' AND '+period('h.criado_em')+' ORDER BY h.id'),
    }
    if kind not in reports: raise HTTPException(404, 'Relatório não encontrado')
    headers, sql = reports[kind]
    out = StringIO(); writer = csv.writer(out); writer.writerow(headers)
    for row in db.execute(text(sql), params):
        writer.writerow(["'"+str(v) if str(v).lstrip().startswith(('=','+','-','@')) else v for v in row])
    return Response('\ufeff'+out.getvalue(), media_type='text/csv; charset=utf-8', headers={'Content-Disposition': f'attachment; filename="{kind}.csv"'})
