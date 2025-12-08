"""
Configuração dos critérios de avaliação do fundo de Venture Capital.
Define os parâmetros para cada estágio de investimento.
"""

# Localização geográfica de interesse
LOCATION = "Brasil"

# Critérios por estágio
FUND_CRITERIA = {
    "pre_seed": {
        "nome": "Pre-Seed",
        "foco": "Validação de hipóteses e descoberta. A empresa ainda não tem Product-Market Fit (PMF), mas deve ter um caminho claro para buscá-lo.",
        "metricas_financeiro": {
            "receita_anual": {"min": 0, "max": 1000000},  # R$ 0 – R$ 1 Milhão
            "tamanho_rodada": {"min": 2500000, "max": 5000000},  # R$ 2,5M – R$ 5M
            "valuation_pre_money": {"min": 15000000, "max": 35000000},  # R$ 15M – R$ 35M
            "crescimento": "Visibilidade para atingir tração de Seed em 18-24 meses"
        },
        "estrutura_cap_table": {
            "composicao_ideal": "90%+ das ações com Fundadores + ESOP",
            "diluição_rodada": {"min": 10, "max": 15}  # 10% – 15%
        },
        "produto_processos": {
            "produto": "Visibilidade para atingir sinais de PMF nos próximos 18-24 meses"
        }
    },
    "seed": {
        "nome": "Seed",
        "foco": "Primeiros sinais de PMF e construção da máquina de vendas. O produto já gera valor real e a empresa deixa de ser apenas um projeto.",
        "metricas_financeiro": {
            "receita_anual": {"min": 3500000, "max": 10000000},  # R$ 3,5M – R$ 10M
            "tamanho_rodada": {"min": 8000000, "max": 20000000},  # R$ 8M – R$ 20M
            "valuation_pre_money": {"min": 32000000, "max": 60000000},  # R$ 32M – R$ 60M
            "crescimento": "3x ao ano (aprox. +10% a.m.)"
        },
        "estrutura_cap_table": {
            "composicao_ideal": "80%+ das ações com Fundadores + ESOP",
            "diluição_rodada": {"min": 15, "max": 20}  # 15% – 20%
        },
        "produto_processos": {
            "produto": "Gera valor real com sinais claros de PMF: NPS alto, Alta recorrência/retenção, Baixo churn, Posicionamento e ICP (Ideal Customer Profile) claros"
        }
    },
    "series_a": {
        "nome": "Series A",
        "foco": "Escalabilidade e eficiência. A máquina de vendas deve estar pronta para receber capital e acelerar.",
        "metricas_financeiro": {
            "receita_anual": {"min": 18000000, "max": 30000000},  # R$ 18M – R$ 30M
            "tamanho_rodada": {"min": 25000000, "max": 50000000},  # R$ 25M – R$ 50M
            "valuation_pre_money": {"min": 75000000, "max": 200000000},  # R$ 75M – R$ 200M
            "crescimento": "2,5x ao ano (aprox. +8% a.m.)"
        },
        "estrutura_cap_table": {
            "composicao_ideal": "65%+ das ações com Fundadores + ESOP",
            "diluição_rodada": {"min": 20, "max": 25}  # 20% – 25%
        },
        "produto_processos": {
            "produto": "Máquina de vendas pronta para escalar"
        }
    }
}

# Escala de notas
NOTA_DESCRICOES = {
    0: "Descartável - não atende critérios básicos",
    1: "Muito fraca - poucos pontos positivos",
    2: "Fraca - alguns pontos, mas gaps significativos",
    3: "Mediana - potencial, mas precisa de mais validação",
    4: "Forte - atende maioria dos critérios, vale conversar",
    5: "Excepcional - prioridade máxima, agendar reunião"
}

