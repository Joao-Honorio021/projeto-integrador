"""Representação JSON: nunca inclui o hash da senha."""

def public(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns if c.name != 'senha_hash'}
