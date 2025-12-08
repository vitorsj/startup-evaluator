"""
Schemas Pydantic para entrada e saída estruturada.
Define os modelos de dados para extração e avaliação de startups.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class Estagio(str, Enum):
    """Estágios de investimento suportados pelo fundo."""
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    INDEFINIDO = "indefinido"


class PitchDeckInfo(BaseModel):
    """Informações extraídas do pitch deck pelo LLM."""
    nome_startup: str = Field(description="Nome da startup")
    localizacao: str = Field(description="País/cidade da startup")
    estagio: Estagio = Field(description="Estágio de investimento identificado")
    receita_anual: Optional[str] = Field(default=None, description="Receita anual (ex: R$ 5M)")
    tamanho_rodada: Optional[str] = Field(default=None, description="Tamanho da rodada buscada")
    valuation_pre_money: Optional[str] = Field(default=None, description="Valuation pre-money")
    crescimento_anual: Optional[str] = Field(default=None, description="Taxa de crescimento")
    produto_descricao: Optional[str] = Field(default=None, description="Descrição do produto/serviço")
    tracao_metricas: Optional[str] = Field(default=None, description="Métricas de tração (usuários, clientes, MRR)")
    equipe_fundadores: Optional[str] = Field(default=None, description="Informações sobre fundadores e equipe")
    clientes_atuais: Optional[str] = Field(default=None, description="Principais clientes atuais")
    modelo_negocio: Optional[str] = Field(default=None, description="Modelo de negócio (SaaS, marketplace, etc)")
    mercado_tamanho: Optional[str] = Field(default=None, description="TAM/SAM/SOM do mercado")
    diferencial_competitivo: Optional[str] = Field(default=None, description="Diferencial competitivo")
    cap_table: Optional[str] = Field(default=None, description="Informações do cap table")
    outras_informacoes: Optional[str] = Field(default=None, description="Outras informações relevantes")


class CriteriosAtendidos(BaseModel):
    """Critérios avaliados pelo analista."""
    localizacao: bool = Field(description="Startup está no Brasil")
    estagio_adequado: bool = Field(description="Estágio compatível com a tese do fundo")
    metricas_financeiro: bool = Field(description="Métricas financeiras adequadas para o estágio")
    produto_tracao: bool = Field(description="Produto com tração comprovada")
    equipe: bool = Field(description="Equipe qualificada e experiente")


class AvaliacaoStartup(BaseModel):
    """Resultado da avaliação de uma startup."""
    nota: int = Field(ge=0, le=5, description="Nota de 0 a 5")
    estagio_identificado: Estagio = Field(description="Estágio identificado da startup")
    justificativa: str = Field(description="Explicação detalhada da nota em 3-5 parágrafos")
    pontos_positivos: List[str] = Field(description="Lista de pontos positivos identificados")
    pontos_negativos: List[str] = Field(description="Lista de pontos negativos ou gaps")
    criterios_atendidos: CriteriosAtendidos = Field(description="Critérios avaliados")

