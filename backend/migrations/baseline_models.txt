from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

def now():
    return datetime.now(timezone.utc).isoformat()

class User(Base):
    __tablename__ = 'usuarios'
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    senha_hash: Mapped[str]
    perfil: Mapped[str]
    ativo: Mapped[bool] = mapped_column(default=True)

class Sector(Base):
    __tablename__ = 'setores'
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(unique=True)

class Equipment(Base):
    __tablename__ = 'equipamentos'
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(unique=True)
    nome: Mapped[str]
    modelo: Mapped[str] = mapped_column(default='')
    fabricante: Mapped[str] = mapped_column(default='')
    localizacao: Mapped[str] = mapped_column(default='')
    setor_id: Mapped[int] = mapped_column(ForeignKey('setores.id'))
    criticidade: Mapped[str] = mapped_column(default='Média')
    status: Mapped[str] = mapped_column(default='Operacional')
    ativo: Mapped[bool] = mapped_column(default=True)

class Ticket(Base):
    __tablename__ = 'chamados'
    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str]
    descricao: Mapped[str] = mapped_column(Text)
    equipamento_id: Mapped[int] = mapped_column(ForeignKey('equipamentos.id'))
    solicitante_id: Mapped[int] = mapped_column(ForeignKey('usuarios.id'))
    tecnico_id: Mapped[int | None] = mapped_column(ForeignKey('usuarios.id'))
    categoria: Mapped[str]
    prioridade: Mapped[str] = mapped_column(default='Média')
    status: Mapped[str] = mapped_column(default='Aberto')
    criado_em: Mapped[str] = mapped_column(default=now)
    resolvido_em: Mapped[str | None]

class Order(Base):
    __tablename__ = 'ordens'
    id: Mapped[int] = mapped_column(primary_key=True)
    chamado_id: Mapped[int] = mapped_column(ForeignKey('chamados.id'), unique=True)
    tecnico_id: Mapped[int] = mapped_column(ForeignKey('usuarios.id'))
    status: Mapped[str] = mapped_column(default='Pendente')
    diagnostico: Mapped[str] = mapped_column(default='')
    solucao: Mapped[str] = mapped_column(default='')
    criado_em: Mapped[str] = mapped_column(default=now)
    inicio: Mapped[str | None]
    conclusao: Mapped[str | None]

class Activity(Base):
    __tablename__ = 'historico'
    id: Mapped[int] = mapped_column(primary_key=True)
    chamado_id: Mapped[int] = mapped_column(ForeignKey('chamados.id'))
    usuario_id: Mapped[int] = mapped_column(ForeignKey('usuarios.id'))
    mensagem: Mapped[str]
    tipo: Mapped[str] = mapped_column(default='evento')
    criado_em: Mapped[str] = mapped_column(default=now)
