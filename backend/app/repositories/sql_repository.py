"""SQL parametrizado. Somente nomes de tabelas/colunas internos são interpolados.

Os models retornados são desacoplados da sessão. insert/save persistem os dados;
o controller controla o commit da operação completa, incluindo sua auditoria.
"""
from sqlalchemy import text
from ..models import User, Sector, Equipment, Ticket, Order, Activity
MODELS = {User, Sector, Equipment, Ticket, Order, Activity}

def rows(db, model, sql, params=None):
    return [model(**dict(row)) for row in db.execute(text(sql), params or {}).mappings()]

def one(db, model, sql, params=None):
    result = rows(db, model, sql, params)
    return result[0] if result else None

def table(model):
    if model not in MODELS:
        raise ValueError('Model não permitido')
    return model.__tablename__

def find(db, model, id):
    return one(db, model, f'SELECT * FROM {table(model)} WHERE id = :id', {'id': id})

def insert(db, model, **values):
    name = table(model)
    columns = {c.name: c for c in model.__table__.columns}
    if not values.keys() <= columns.keys():
        raise ValueError('Coluna desconhecida')
    for key, column in columns.items():
        if key not in values and column.default is not None:
            default = column.default
            values[key] = default.arg(None) if default.is_callable else default.arg
    names = ', '.join(values)
    placeholders = ', '.join(':' + key for key in values)
    result = db.execute(text(f'INSERT INTO {name} ({names}) VALUES ({placeholders}) RETURNING id'), values)
    return find(db, model, result.scalar_one())

def save(db, obj):
    name = table(type(obj))
    values = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    assignments = ', '.join(f'{key} = :{key}' for key in values if key != 'id')
    db.execute(text(f'UPDATE {name} SET {assignments} WHERE id = :id'), values)

def access(user):
    return """(:perfil IN ('administrador', 'supervisor')
        OR (:perfil = 'operador' AND t.solicitante_id = :usuario_id)
        OR (:perfil = 'tecnico' AND t.tecnico_id = :usuario_id))""", {
        'perfil': user.perfil, 'usuario_id': user.id,
    }

def ticket_page(db, user, q, status, priority, equipment_id, technician_id, page):
    scope, params = access(user)
    params.update(q=q, pattern='%' + q.replace('!', '!!').replace('%', '!%').replace('_', '!_') + '%', status=status, priority=priority, equipment_id=equipment_id,
                  technician_id=technician_id, offset=(max(page, 1)-1)*20)
    filters = scope + """
        AND (:q = '' OR lower(t.titulo) LIKE lower(:pattern) ESCAPE '!' OR CAST(t.id AS TEXT) = :q)
        AND (:status = '' OR t.status = :status)
        AND (:priority = '' OR t.prioridade = :priority)
        AND (CAST(:equipment_id AS INTEGER) IS NULL OR t.equipamento_id = :equipment_id)
        AND (CAST(:technician_id AS INTEGER) IS NULL OR t.tecnico_id = :technician_id)
    """
    total = db.execute(text('SELECT COUNT(*) FROM chamados t WHERE ' + filters), params).scalar_one()
    result = db.execute(text('SELECT t.* FROM chamados t WHERE ' + filters +
                             ' ORDER BY t.id DESC LIMIT 20 OFFSET :offset'), params).mappings()
    return {'items': [dict(row) for row in result], 'total': total}

def history_for_tickets(db, ids):
    if not ids:
        return []
    params = {f'id{i}': id for i, id in enumerate(ids)}
    placeholders = ', '.join(':' + key for key in params)
    return rows(db, Activity, f'SELECT * FROM historico WHERE chamado_id IN ({placeholders}) ORDER BY id', params)

def dashboard_summary(db, user):
    scope, params = access(user)
    status = dict(db.execute(text('SELECT t.status, COUNT(*) FROM chamados t WHERE ' + scope + ' GROUP BY t.status'), params).all())
    priorities = dict(db.execute(text('SELECT t.prioridade, COUNT(*) FROM chamados t WHERE ' + scope + ' GROUP BY t.prioridade'), params).all())
    pending = db.execute(text("SELECT COUNT(*) FROM ordens o JOIN chamados t ON t.id = o.chamado_id WHERE o.status = 'Pendente' AND " + scope), params).scalar_one()
    return {'total': sum(status.values()),
        'status': [{'nome': s, 'quantidade': status.get(s, 0)} for s in
                   ['Aberto', 'Em análise', 'Em atendimento', 'Aguardando informações', 'Resolvido', 'Cancelado']],
        'prioridades': [{'nome': p, 'quantidade': priorities.get(p, 0)} for p in ['Baixa', 'Média', 'Alta', 'Crítica']],
        'ordens_pendentes': pending}


def all_records(db, model):
    return rows(db, model, f'SELECT * FROM {table(model)} ORDER BY id')


def user_by_email(db, email):
    return one(db, User, 'SELECT * FROM usuarios WHERE email = :email', {'email': email})


def order_for_ticket(db, id):
    return one(db, Order, 'SELECT * FROM ordens WHERE chamado_id = :id', {'id': id})


def equipment_tickets(db, id, user):
    scope, params = access(user)
    params['id'] = id
    return rows(db, Ticket, 'SELECT t.* FROM chamados t WHERE t.equipamento_id = :id AND ' + scope, params)


def ticket_history(db, id):
    result = db.execute(text('''
        SELECT h.*, u.nome AS autor FROM historico h
        JOIN usuarios u ON u.id = h.usuario_id
        WHERE h.chamado_id = :id ORDER BY h.criado_em, h.id
    '''), {'id': id}).mappings()
    return [dict(row) for row in result]


def visible_orders(db, user):
    scope, params = access(user)
    return rows(db, Order, 'SELECT o.* FROM ordens o JOIN chamados t ON t.id = o.chamado_id WHERE ' + scope + ' ORDER BY o.id DESC', params)
