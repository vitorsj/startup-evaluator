"""
Prompts centralizados para o agente de avaliação de startups.
Edite este arquivo para ajustar o comportamento da IA.
"""

from typing import Dict, Type
from config import FUND_CRITERIA, LOCATION


# =============================================================================
# FORMATTERS & HELPERS
# =============================================================================

def format_fund_criteria() -> str:
    """Formata os critérios do fundo para inclusão no prompt."""
    criteria_lines = []
    
    for stage_key, stage_data in FUND_CRITERIA.items():
        criteria_lines.append(f"\n=== {stage_data['nome']} ===")
        criteria_lines.append(f"Foco: {stage_data['foco']}")
        
        metrics = stage_data['metricas_financeiro']
        criteria_lines.append(f"\nMétricas & Financeiro:")
        criteria_lines.append(f"  - Receita Anual: R$ {metrics['receita_anual']['min']:,.0f} – R$ {metrics['receita_anual']['max']:,.0f}")
        criteria_lines.append(f"  - Tamanho da Rodada: R$ {metrics['tamanho_rodada']['min']:,.0f} – R$ {metrics['tamanho_rodada']['max']:,.0f}")
        criteria_lines.append(f"  - Valuation (Pre-Money): R$ {metrics['valuation_pre_money']['min']:,.0f} – R$ {metrics['valuation_pre_money']['max']:,.0f}")
        criteria_lines.append(f"  - Crescimento: {metrics['crescimento']}")
        
        cap_table = stage_data['estrutura_cap_table']
        criteria_lines.append(f"\nEstrutura & Cap Table:")
        criteria_lines.append(f"  - Composição Ideal: {cap_table['composicao_ideal']}")
        criteria_lines.append(f"  - Diluição na Rodada: {cap_table['diluição_rodada']['min']}% – {cap_table['diluição_rodada']['max']}%")
        
        criteria_lines.append(f"\nProduto & Processos:")
        criteria_lines.append(f"  - {stage_data['produto_processos']['produto']}")
    
    return "\n".join(criteria_lines)


# =============================================================================
# PROMPT VERSIONS
# =============================================================================

class BasePrompt:
    """Classe base para definições de prompt."""
    EXTRACTION_SYSTEM_PROMPT = ""
    EXTRACTION_USER_PROMPT = ""
    
    @staticmethod
    def get_evaluation_system_prompt() -> str:
        raise NotImplementedError
    
    @staticmethod
    def get_evaluation_user_prompt(pdf_summary: str) -> str:
        raise NotImplementedError


class PromptV1(BasePrompt):
    """
    Versão 1: Critérios eliminatórios estritos.
    Se localização não for Brasil (ou null), elimina.
    """
    EXTRACTION_SYSTEM_PROMPT = """Você é um especialista em análise de pitch decks de startups.
Sua tarefa é extrair informações relevantes do pitch deck em PDF.

INSTRUÇÕES:
- Extraia todas as informações disponíveis no documento
- Para valores numéricos, mantenha o formato original (ex: "R$ 5M", "3x ao ano")
- IMPORTANTE: Extraia valores numéricos exatos quando disponíveis. Se encontrar "R$ 5 milhões", extraia como "R$ 5M" ou "5000000" para facilitar comparações matemáticas posteriores.
- Se uma informação não estiver presente, deixe como null
- Não invente informações. A fidelidade aos dados do documento é a prioridade máxima.
- Identifique o estágio baseado nas métricas apresentadas:
  * Pre-Seed: Receita até R$ 1M, foco em validação
  * Seed: Receita R$ 3.5M-10M, primeiros sinais de PMF
  * Series A: Receita R$ 18M-30M, máquina de vendas pronta
- Seja detalhado e preciso na extração"""

    EXTRACTION_USER_PROMPT = "Analise este pitch deck e extraia todas as informações relevantes:"

    EVALUATION_SCALE = """ESCALA DE NOTAS:
- 0: Descartável - não atende critérios básicos ou não está no Brasil
- 1: Muito fraca - poucos pontos positivos, muitos gaps críticos
- 2: Fraca - alguns pontos positivos, mas gaps significativos
- 3: Mediana - potencial interessante, mas precisa de mais validação
- 4: Forte - atende maioria dos critérios, definitivamente vale conversar
- 5: Excepcional - atende todos os critérios, prioridade máxima para reunião"""

    EVALUATION_INSTRUCTIONS = """INSTRUÇÕES (SIGA ESTA ORDEM):

PASSO 1 - ANÁLISE PRELIMINAR (Chain of Thought):
- Primeiro, preencha o campo "analise_preliminar" com seu raciocínio passo a passo
- Compare sistematicamente os dados extraídos com os critérios do estágio identificado
- Para valores numéricos, faça validação matemática explícita:
  * Exemplo: "Receita anual extraída: R$ 4M. Faixa esperada para Seed: R$ 3.5M-10M. Verificação: 4M está dentro do intervalo? Sim, pois 3.5M ≤ 4M ≤ 10M"
- Cite diretamente os dados extraídos ao fazer comparações
- Identifique quais critérios são atendidos e quais não são, com base nas evidências

PASSO 2 - AVALIAÇÃO DE CRITÉRIOS:
- Para cada critério (localização, estágio, métricas, produto, equipe):
  * Determine se foi atendido (atendido: true/false)
  * Cite a evidência específica encontrada nos dados extraídos (evidencia_encontrada)
  * Exemplo: "Localização: atendido=true, evidencia_encontrada='Localização: São Paulo, Brasil'"
- Seja rigoroso: se a evidência não estiver clara nos dados, marque como não atendido

PASSO 3 - ATRIBUIÇÃO DA NOTA:
1. Verifique se a startup está localizada no Brasil (critério eliminatório)
2. Identifique o estágio mais provável baseado nas métricas
3. Compare com os critérios do estágio identificado
4. Avalie cada dimensão: métricas, produto, tração, equipe, cap table
5. Se informações críticas estiverem faltando, impacte negativamente a nota
6. Seja rigoroso mas justo na avaliação
7. Forneça justificativa detalhada explicando a nota
8. Justifique a nota baseando-se EXCLUSIVAMENTE nas evidências extraídas

IMPORTANTE:
- NUNCA invente dados que não foram extraídos
- SEMPRE cite a fonte (dados extraídos) ao avaliar cada critério
- Se um valor numérico não estiver na faixa esperada, documente isso claramente na evidência"""

    @staticmethod
    def get_evaluation_system_prompt() -> str:
        criteria_text = format_fund_criteria()
        return f"""Você é um analista experiente de um fundo de Venture Capital brasileiro.
Sua tarefa é avaliar startups baseado nas informações extraídas do pitch deck.

CRITÉRIOS DO FUNDO:
{criteria_text}

LOCALIZAÇÃO: {LOCATION}

{PromptV1.EVALUATION_SCALE}

{PromptV1.EVALUATION_INSTRUCTIONS}"""

    @staticmethod
    def get_evaluation_user_prompt(pdf_summary: str) -> str:
        return f"""Avalie esta startup baseado nas informações extraídas do pitch deck:

INFORMAÇÕES DO PITCH DECK:
{pdf_summary}

IMPORTANTE: Siga a ordem das instruções:
1. Primeiro, preencha "analise_preliminar" com seu raciocínio passo a passo comparando os dados com os critérios
2. Depois, avalie cada critério fornecendo evidências específicas dos dados extraídos
3. Por fim, atribua a nota final baseada exclusivamente nas evidências encontradas

Forneça uma avaliação completa com nota de 0-5 e justificativa detalhada."""


class PromptV2(BasePrompt):
    """
    Versão 2: Lógica de 'Presunção de Inocência'.
    Se localização é 'null', não elimina imediatamente (alerta amarelo).
    """
    # Reusa o prompt de extração da V1, pois a extração em si não mudou
    EXTRACTION_SYSTEM_PROMPT = PromptV1.EXTRACTION_SYSTEM_PROMPT
    EXTRACTION_USER_PROMPT = PromptV1.EXTRACTION_USER_PROMPT

    EVALUATION_SCALE = """ESCALA DE NOTAS:
- 0: Descartável - NÃO ATENDE CRITÉRIOS ELIMINATÓRIOS (ex: localização confirmada fora do Brasil) ou modelo de negócio inviável.
- 1: Muito fraca - atende critérios básicos, mas com muitos gaps críticos.
- 2: Fraca - alguns pontos positivos, mas gaps significativos ou falta de clareza em pontos chave.
- 3: Mediana - potencial interessante, mas precisa de mais validação em 1 ou 2 frentes.
- 4: Forte - atende maioria dos critérios, tese sólida, definitivamente vale conversar.
- 5: Excepcional - atende todos os critérios, prioridade máxima para reunião."""

    EVALUATION_INSTRUCTIONS = """INSTRUÇÕES (SIGA ESTA ORDEM):

PASSO 1 - ANÁLISE PRELIMINAR (Chain of Thought):
- Primeiro, preencha o campo "analise_preliminar" com seu raciocínio passo a passo
- Compare sistematicamente os dados extraídos com os critérios do estágio identificado
- Para valores numéricos, faça validação matemática explícita:
  * Exemplo: "Receita anual extraída: R$ 4M. Faixa esperada para Seed: R$ 3.5M-10M. Verificação: 4M está dentro do intervalo? Sim, pois 3.5M ≤ 4M ≤ 10M"
- Cite diretamente os dados extraídos ao fazer comparações
- Identifique quais critérios são atendidos e quais não são, com base nas evidências

PASSO 2 - AVALIAÇÃO DE CRITÉRIOS:
- Para cada critério (localização, estágio, métricas, produto, equipe):
  * Determine se foi atendido (atendido: true/false)
  * Cite a evidência específica encontrada nos dados extraídos (evidencia_encontrada)
  * IMPORTANTE SOBRE LOCALIZAÇÃO: Se a localização for 'null' (não informada), considere como "Não Atendido" mas NÃO ELIMINE a startup apenas por isso. Marque a evidência como "Localização não informada no deck".

PASSO 3 - ATRIBUIÇÃO DA NOTA:
1. Verificação de Localização (Critério Eliminatório):
   - Se a localização for EXPLICITAMENTE fora do Brasil (ex: EUA, Europa) -> Atribua Nota 0 e Encerre.
   - Se a localização for 'null' ou 'indefinida' -> NÃO elimine. Considere como um "Alerta Amarelo" (ponto negativo pela falta de clareza), mas avalie o mérito do negócio (equipe, produto, mercado). Se o resto for excelente, a nota pode ser alta (3 ou 4) com a ressalva de verificar a sede.
   - Se for Brasil -> Prossiga normalmente.

2. Identifique o estágio mais provável baseado nas métricas
3. Compare com os critérios do estágio identificado
4. Avalie cada dimensão: métricas, produto, tração, equipe, cap table
5. Se informações críticas (além da localização) estiverem faltando, impacte a nota proporcionalmente à importância da informação.
6. Forneça justificativa detalhada explicando a nota
7. Justifique a nota baseando-se EXCLUSIVAMENTE nas evidências extraídas

IMPORTANTE:
- NUNCA invente dados que não foram extraídos
- SEMPRE cite a fonte (dados extraídos) ao avaliar cada critério
- Se um valor numérico não estiver na faixa esperada, documente isso claramente na evidência"""

    @staticmethod
    def get_evaluation_system_prompt() -> str:
        criteria_text = format_fund_criteria()
        return f"""Você é um analista experiente de um fundo de Venture Capital brasileiro.
Sua tarefa é avaliar startups baseado nas informações extraídas do pitch deck.

CRITÉRIOS DO FUNDO:
{criteria_text}

LOCALIZAÇÃO: {LOCATION}

{PromptV2.EVALUATION_SCALE}

{PromptV2.EVALUATION_INSTRUCTIONS}"""

    @staticmethod
    def get_evaluation_user_prompt(pdf_summary: str) -> str:
        return f"""Avalie esta startup baseado nas informações extraídas do pitch deck:

INFORMAÇÕES DO PITCH DECK:
{pdf_summary}

IMPORTANTE: Siga a ordem das instruções:
1. Primeiro, preencha "analise_preliminar" com seu raciocínio passo a passo comparando os dados com os critérios
2. Depois, avalie cada critério fornecendo evidências específicas dos dados extraídos
3. Por fim, atribua a nota final baseada exclusivamente nas evidências encontradas

Forneça uma avaliação completa com nota de 0-5 e justificativa detalhada."""


# =============================================================================
# REGISTRY & ACCESS
# =============================================================================

PROMPT_VERSIONS: Dict[str, Type[BasePrompt]] = {
    "v1": PromptV1,
    "v2": PromptV2
}

DEFAULT_PROMPT_VERSION = "v2"

def get_prompts(version: str = None) -> Type[BasePrompt]:
    """Retorna a classe de prompts para a versão especificada."""
    if not version:
        version = DEFAULT_PROMPT_VERSION
    
    return PROMPT_VERSIONS.get(version.lower(), PROMPT_VERSIONS[DEFAULT_PROMPT_VERSION])

def list_prompt_versions() -> list[str]:
    """Lista as versões de prompt disponíveis."""
    return list(PROMPT_VERSIONS.keys())
