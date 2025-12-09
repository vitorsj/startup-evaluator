"""
Módulo de avaliação usando Pydantic AI.
Suporta múltiplos modelos: Gemini e OpenAI.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import logging
import logfire

from pydantic_ai import Agent, BinaryContent
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import NOTA_DESCRICOES
from models import PitchDeckInfo, AvaliacaoStartup
from model_config import get_model_config, ModelConfig, DEFAULT_MODEL
from prompts import get_prompts, DEFAULT_PROMPT_VERSION

# Configuração de Logger
logger = logging.getLogger(__name__)
logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_pydantic_ai()


@dataclass
class UsageInfo:
    """Informações de uso da API."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    requests: int
    model_name: str
    
    def __str__(self) -> str:
        return (
            f"Modelo: {self.model_name} | "
            f"Tokens: {self.total_tokens:,} "
            f"(input: {self.input_tokens:,}, output: {self.output_tokens:,}) | "
            f"Requests: {self.requests}"
        )


class StartupEvaluator:
    """Avaliador de startups usando Pydantic AI com múltiplos modelos."""
    
    def __init__(
        self, 
        extraction_model: str = DEFAULT_MODEL, 
        evaluation_model: str = DEFAULT_MODEL, 
        prompt_version: str = DEFAULT_PROMPT_VERSION
    ):
        """
        Inicializa o avaliador com modelos separados para extração e avaliação.
        
        Args:
            extraction_model: Modelo para extração do PDF (ex: 'gemini-flash')
            evaluation_model: Modelo para avaliação da startup (ex: 'gemini-pro')
            prompt_version: Versão do prompt a ser utilizada (ex: 'v1', 'v2', 'astella')
        """
        self.extraction_config = get_model_config(extraction_model)
        self.evaluation_config = get_model_config(evaluation_model)
        self.extraction_model_name = extraction_model
        self.evaluation_model_name = evaluation_model
        self.prompt_version = prompt_version
        
        # Carrega a versão correta dos prompts
        self.prompts = get_prompts(prompt_version)
        
        # Verifica se as API keys estão configuradas
        for config in [self.extraction_config, self.evaluation_config]:
            api_key = os.getenv(config.env_var)
            if not api_key:
                raise ValueError(
                    f"{config.env_var} não encontrada. "
                    f"Configure a variável de ambiente para usar {config.name}."
                )
        
        # Configurações de geração para extração
        self.extraction_settings = {
            'temperature': self.extraction_config.temperature,
            'top_p': self.extraction_config.top_p,
        }
        if self.extraction_config.seed is not None:
            self.extraction_settings['seed'] = self.extraction_config.seed
        
        # Configurações de geração para avaliação
        self.evaluation_settings = {
            'temperature': self.evaluation_config.temperature,
            'top_p': self.evaluation_config.top_p,
        }
        if self.evaluation_config.seed is not None:
            self.evaluation_settings['seed'] = self.evaluation_config.seed

        # Agente para extração de informações do pitch deck
        self.extraction_agent = Agent(
            self.extraction_config.model_string,
            output_type=PitchDeckInfo,
            system_prompt=self.prompts.EXTRACTION_SYSTEM_PROMPT
        )
        
        # Agente para avaliação da startup
        self.evaluation_agent = Agent(
            self.evaluation_config.model_string,
            output_type=AvaliacaoStartup,
            system_prompt=self.prompts.get_evaluation_system_prompt()
        )
        
        logger.info(
            f"Evaluator inicializado | "
            f"Extração: {extraction_model} | "
            f"Avaliação: {evaluation_model} | "
            f"Prompt: {prompt_version}"
        )
        
        # Tracking de uso
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_requests = 0
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def _run_agent_sync(self, agent: Agent, content, model_settings: dict):
        """Executa agente com retry automático e configurações de modelo."""
        try:
            return agent.run_sync(content, model_settings=model_settings)
        except TypeError:
            logger.warning("Versão do PydanticAI não suporta model_settings em run_sync. Usando defaults.")
            return agent.run_sync(content)
        except Exception as e:
            logger.warning(f"Erro na chamada do LLM (tentativa de retry): {e}")
            raise e

    def _track_usage(self, usage) -> None:
        """Acumula uso de tokens."""
        if usage:
            self._total_input_tokens += usage.input_tokens or 0
            self._total_output_tokens += usage.output_tokens or 0
            self._total_requests += usage.requests or 0
    
    def get_usage(self) -> UsageInfo:
        """Retorna informações de uso acumulado."""
        return UsageInfo(
            input_tokens=self._total_input_tokens,
            output_tokens=self._total_output_tokens,
            total_tokens=self._total_input_tokens + self._total_output_tokens,
            requests=self._total_requests,
            model_name=f"{self.extraction_config.name} / {self.evaluation_config.name}"
        )
    
    def reset_usage(self) -> None:
        """Reseta o tracking de uso."""
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_requests = 0
    
    def extract_info(self, pdf_path: str) -> PitchDeckInfo:
        """Extrai informações do pitch deck."""
        logger.info(f"Iniciando extração de informações: {pdf_path} (modelo: {self.extraction_config.name})")
        pdf_bytes = Path(pdf_path).read_bytes()
        
        if self.extraction_config.supports_pdf:
            content = [
                self.prompts.EXTRACTION_USER_PROMPT,
                BinaryContent(data=pdf_bytes, media_type='application/pdf')
            ]
            result = self._run_agent_sync(self.extraction_agent, content, self.extraction_settings)
        else:
            logger.info("Convertendo PDF para imagens (modelo não suporta PDF nativo)...")
            images = self._pdf_to_images(pdf_path)
            content = [self.prompts.EXTRACTION_USER_PROMPT]
            for img_bytes in images:
                content.append(BinaryContent(data=img_bytes, media_type='image/png'))
            result = self._run_agent_sync(self.extraction_agent, content, self.extraction_settings)
        
        self._track_usage(result.usage())
        
        if not self._validate_extraction(result.output):
            logger.warning(f"Extração de baixa qualidade para {pdf_path}")
            
        return result.output
    
    def _validate_extraction(self, info: PitchDeckInfo) -> bool:
        """Verifica se a extração obteve informações mínimas."""
        has_name = info.nome_startup and info.nome_startup.lower() not in ["indefinido", "desconhecido", "null", "none"]
        
        filled_fields = 0
        for field, value in info.model_dump().items():
            if value and str(value).lower() not in ["indefinido", "desconhecido", "null", "none"]:
                filled_fields += 1
                
        is_valid = has_name and filled_fields >= 3
        if not is_valid:
            logger.warning(f"Validação de extração falhou. Nome: {info.nome_startup}, Campos preenchidos: {filled_fields}")
        
        return is_valid
    
    def _pdf_to_images(self, pdf_path: str, max_pages: int = 10) -> list[bytes]:
        """Converte PDF em imagens."""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("PyMuPDF é necessário. pip install PyMuPDF")
        
        images = []
        doc = fitz.open(pdf_path)
        
        for page_num in range(min(len(doc), max_pages)):
            page = doc[page_num]
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            images.append(pix.tobytes("png"))
        
        doc.close()
        return images
    
    def evaluate_startup(self, pdf_info: PitchDeckInfo) -> AvaliacaoStartup:
        """Avalia a startup com base nas informações extraídas."""
        logger.info(f"Iniciando avaliação da startup: {pdf_info.nome_startup} (modelo: {self.evaluation_config.name})")
        pdf_summary = self._format_pdf_info(pdf_info)
        prompt = self.prompts.get_evaluation_user_prompt(pdf_summary)
        
        result = self._run_agent_sync(self.evaluation_agent, prompt, self.evaluation_settings)
        self._track_usage(result.usage())
        
        return result.output
    
    def _validate_evaluation_consistency(self, avaliacao: AvaliacaoStartup) -> None:
        """Valida consistência da avaliação."""
        criterios = avaliacao.criterios_atendidos
        localizacao_atendida = criterios.localizacao.atendido
        
        # Na V2, localização 'null' pode ser não atendida mas com nota > 0
        # Então relaxamos o aviso se for apenas não atendida (null), 
        # mas mantemos se for explicitamente recusada e nota alta
        if not localizacao_atendida and avaliacao.nota > 0 and self.prompt_version == 'v1':
             logger.warning(
                f"Inconsistência detectada (V1): Startup não está no Brasil mas recebeu nota {avaliacao.nota}."
            )
        
        criterios_criticos = [
            criterios.localizacao,
            criterios.estagio_adequado,
            criterios.metricas_financeiro,
        ]
        
        atendidos_criticos = sum(1 for c in criterios_criticos if c.atendido)
        
        if avaliacao.nota >= 4 and atendidos_criticos < 2:
            logger.warning(
                f"Inconsistência detectada: Nota alta ({avaliacao.nota}) mas apenas {atendidos_criticos}/3 "
                f"critérios críticos atendidos. Revisar avaliação."
            )
    
    def _format_pdf_info(self, info: PitchDeckInfo) -> str:
        """Formata as informações do PDF para o prompt."""
        lines = []
        for field_name, field_value in info.model_dump().items():
            if field_value and field_value != "indefinido":
                label = field_name.replace('_', ' ').title()
                lines.append(f"  - {label}: {field_value}")
        return "\n".join(lines) if lines else "  - Nenhuma informação extraída"
    
    def evaluate(self, pdf_path: str) -> dict:
        """Realiza avaliação completa da startup."""
        self.reset_usage()
        
        pdf_info = self.extract_info(pdf_path)
        avaliacao = self.evaluate_startup(pdf_info)
        
        self._validate_evaluation_consistency(avaliacao)
        
        usage = self.get_usage()
        
        result = avaliacao.model_dump()
        result['nota_descricao'] = NOTA_DESCRICOES.get(avaliacao.nota, "Desconhecida")
        result['pdf_info_extracted'] = pdf_info.model_dump()
        result['extraction_model'] = self.extraction_config.name
        result['evaluation_model'] = self.evaluation_config.name
        result['prompt_version'] = self.prompt_version
        result['usage'] = {
            'input_tokens': usage.input_tokens,
            'output_tokens': usage.output_tokens,
            'total_tokens': usage.total_tokens,
            'requests': usage.requests,
        }
        
        return result
