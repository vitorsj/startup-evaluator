"""
Configuração de modelos disponíveis para o avaliador de startups.
Suporta múltiplos provedores: Google Gemini e OpenAI.
"""

from dataclasses import dataclass
from typing import Literal

# Tipos de provedores suportados
ModelProvider = Literal["gemini", "openai"]


@dataclass
class ModelPricing:
    """Preços do modelo por 1M tokens."""
    input_per_million: float
    output_per_million: float


@dataclass  
class ModelConfig:
    """Configuração de um modelo."""
    name: str
    provider: ModelProvider
    model_string: str  # String para o Pydantic AI
    env_var: str  # Variável de ambiente para API key
    pricing: ModelPricing
    supports_pdf: bool = True  # Se suporta envio de PDF direto
    description: str = ""


# Modelos disponíveis
AVAILABLE_MODELS: dict[str, ModelConfig] = {
    # Google Gemini
    "gemini-flash": ModelConfig(
        name="Gemini 2.5 Flash",
        provider="gemini",
        model_string="google-gla:gemini-2.5-flash",
        env_var="GEMINI_API_KEY",
        pricing=ModelPricing(input_per_million=0.075, output_per_million=0.30),
        supports_pdf=True,
        description="Rápido e econômico. Bom para análise de PDFs."
    ),
    "gemini-pro": ModelConfig(
        name="Gemini 2.5 Pro",
        provider="gemini",
        model_string="google-gla:gemini-2.5-pro",
        env_var="GEMINI_API_KEY",
        pricing=ModelPricing(input_per_million=1.25, output_per_million=5.00),
        supports_pdf=True,
        description="Mais capaz, melhor raciocínio. Mais caro."
    ),
    "gemini-3": ModelConfig(
        name="Gemini 3 Pro",
        provider="gemini",
        model_string="google-gla:gemini-3-pro",
        env_var="GEMINI_API_KEY",
        pricing=ModelPricing(input_per_million=2.00, output_per_million=12.00),
        supports_pdf=True,
        description="Modelo mais avançado do Google. Contexto de até 2M tokens."
    ),
    
    # OpenAI
    "gpt-5-mini": ModelConfig(
        name="GPT-5 Mini",
        provider="openai",
        model_string="openai:gpt-5-mini",
        env_var="OPENAI_API_KEY",
        pricing=ModelPricing(input_per_million=0.25, output_per_million=2.00),
        supports_pdf=False,  # OpenAI não suporta PDF direto, precisa converter
        description="Modelo intermediário da OpenAI. Equilibrado em custo e capacidade."
    ),
    "gpt-5-nano": ModelConfig(
        name="GPT-5 Nano",
        provider="openai",
        model_string="openai:gpt-5-nano",
        env_var="OPENAI_API_KEY",
        pricing=ModelPricing(input_per_million=0.05, output_per_million=0.40),
        supports_pdf=False,
        description="Versão mais econômica do GPT-5. Rápido e barato."
    ),
}

# Modelo padrão
DEFAULT_MODEL = "gemini-flash"


def get_model_config(model_name: str) -> ModelConfig:
    """
    Retorna a configuração do modelo.
    
    Args:
        model_name: Nome do modelo (ex: 'gemini-flash', 'gpt-4o')
        
    Returns:
        ModelConfig com as configurações
        
    Raises:
        ValueError: Se o modelo não for encontrado
    """
    if model_name not in AVAILABLE_MODELS:
        available = ", ".join(AVAILABLE_MODELS.keys())
        raise ValueError(f"Modelo '{model_name}' não encontrado. Disponíveis: {available}")
    
    return AVAILABLE_MODELS[model_name]


def list_models() -> str:
    """Retorna uma string formatada com os modelos disponíveis."""
    lines = ["Modelos disponíveis:", ""]
    
    for key, config in AVAILABLE_MODELS.items():
        cost_info = f"${config.pricing.input_per_million:.2f}/${config.pricing.output_per_million:.2f} por 1M tokens"
        pdf_support = "✓ PDF" if config.supports_pdf else "✗ PDF"
        lines.append(f"  {key:15} - {config.name:20} ({cost_info}) [{pdf_support}]")
        lines.append(f"                    {config.description}")
        lines.append("")
    
    return "\n".join(lines)

