from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class TabelaPreco:
    id: int
    filial: str
    codigo: str
    descricao: str
    ativa: bool

@dataclass
class PrecoProduto:
    id: int
    filial: str
    tabela_id: int
    produto: str
    preco: float
    dt_ini: date
    dt_fim: Optional[date]