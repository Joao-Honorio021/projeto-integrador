"""Validação dos dados recebidos pelos controllers."""
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Login(Input):
    email: str
    senha: str

class EquipmentInput(Input):
    codigo: str = Field(min_length=1, max_length=40)
    nome: str = Field(min_length=2, max_length=120)
    setor_id: int
    modelo: str = ''
    fabricante: str = ''
    localizacao: str = ''

class TicketInput(Input):
    titulo: str = Field(min_length=3, max_length=160)
    descricao: str = Field(min_length=5, max_length=10000)
    equipamento_id: int
    categoria: str = 'Falha mecânica'
    prioridade: Literal['Baixa', 'Média', 'Alta', 'Crítica'] = 'Média'

class Assign(Input):
    tecnico_id: int
    prioridade: Literal['Baixa', 'Média', 'Alta', 'Crítica'] = 'Média'

class OrderInput(Input):
    chamado_id: int

class Complete(Input):
    diagnostico: str = Field(min_length=3, max_length=10000)
    solucao: str = Field(min_length=3, max_length=10000)

class Comment(Input):
    mensagem: str = Field(min_length=1, max_length=5000)
