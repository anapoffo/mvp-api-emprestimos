from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class CaixaCreate(BaseModel):
    codigo_classificacao: str = Field(..., examples=["024.1"])
    descricao: str = Field(..., examples=["Folhas de pagamento - jan a jun/2020"])
    localizacao: str = Field(..., examples=["Depósito A, Estante 12, Prateleira 3"])
    data_criacao: date


class CaixaUpdate(BaseModel):
    codigo_classificacao: Optional[str] = None
    descricao: Optional[str] = None
    localizacao: Optional[str] = None
    data_criacao: Optional[date] = None


class Caixa(CaixaCreate):
    id: int


class EmprestimoCreate(BaseModel):
    caixa_id: int
    solicitante: str = Field(..., examples=["Divisão de Recursos Humanos"])
    cep_solicitante: str = Field(..., examples=["70040020"])
    data_emprestimo: date
    data_devolucao_prevista: date


class Emprestimo(BaseModel):
    id: int
    caixa_id: int
    solicitante: str
    cep_solicitante: str
    endereco_solicitante: Optional[str] = None
    data_emprestimo: date
    data_devolucao_prevista: date
    data_devolucao_real: Optional[date] = None
