"""Validação dos dados recebidos pelos controllers."""
from datetime import date
from typing import Annotated, Literal
from pydantic import BaseModel, Field, ConfigDict, StringConstraints

class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Login(Input):
    email: str = Field(min_length=3, max_length=254)
    senha: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(default='', max_length=1024)

class EquipmentInput(Input):
    codigo: str = Field(min_length=1, max_length=40)
    nome: str = Field(min_length=2, max_length=120)
    setor_id: int = Field(gt=0)
    modelo: str = Field(default='', max_length=120)
    fabricante: str = Field(default='', max_length=120)
    localizacao: str = Field(default='', max_length=200)
    descricao: str = Field(default='', max_length=5000)
    criticidade: Literal['Baixa', 'Média', 'Alta', 'Crítica'] = 'Média'
    status: Literal['Operacional', 'Em manutenção', 'Inativo'] = 'Operacional'

class TicketInput(Input):
    titulo: str = Field(min_length=3, max_length=160)
    descricao: str = Field(min_length=5, max_length=10000)
    equipamento_id: int = Field(gt=0, le=2147483647)
    categoria: str = Field(default='Falha mecânica', min_length=1, max_length=120)
    prioridade: Literal['Baixa', 'Média', 'Alta', 'Crítica'] = 'Média'

class Assign(Input):
    tecnico_id: int = Field(gt=0, le=2147483647)
    prioridade: Literal['Baixa', 'Média', 'Alta', 'Crítica'] = 'Média'

class OrderInput(Input):
    chamado_id: int = Field(gt=0, le=2147483647)

class Complete(Input):
    diagnostico: str = Field(min_length=3, max_length=10000)
    solucao: str = Field(min_length=3, max_length=10000)

class Comment(Input):
    mensagem: str = Field(min_length=1, max_length=5000)

class EquipmentPatch(Input):
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    modelo: str | None = Field(default=None, max_length=120)
    fabricante: str | None = Field(default=None, max_length=120)
    localizacao: str | None = Field(default=None, max_length=200)
    descricao: str | None = Field(default=None, max_length=5000)
    setor_id: int | None = Field(default=None, gt=0)
    status: Literal['Operacional', 'Em manutenção', 'Inativo'] | None = None
    criticidade: Literal['Baixa', 'Média', 'Alta', 'Crítica'] | None = None

class TicketPatch(Input):
    titulo: str = Field(min_length=3, max_length=160)
    descricao: str = Field(min_length=5, max_length=10000)

class Diagnosis(Input):
    diagnostico: str = Field(min_length=3, max_length=10000)

class Deadline(Input):
    prazo: date
