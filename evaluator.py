"""
Módulo de avaliação usando Pydantic AI.
Suporta múltiplos modelos: Gemini e OpenAI.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from pydantic_ai import Agent, BinaryContent

from config import NOTA_DESCRICOES
from models import PitchDeckInfo, AvaliacaoStartup
from model_config import get_model_config, ModelConfig, DEFAULT_MODEL
from prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    EXTRACTION_USER_PROMPT,
    get_evaluation_system_prompt,
    get_evaluation_user_prompt,
)


@dataclass
class UsageInfo:
    """Informações de uso e custo da API."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    requests: int
    estimated_cost_usd: float
    model_name: str
    
    def __str__(self) -> str:
        return (
            f"Modelo: {self.model_name} | "
            f"Tokens: {self.total_tokens:,} "
            f"(input: {self.input_tokens:,}, output: {self.output_tokens:,}) | "
            f"Requests: {self.requests} | "
            f"Custo estimado: ${self.estimated_cost_usd:.4f}"
        )


class StartupEvaluator:
    """Avaliador de startups usando Pydantic AI com múltiplos modelos."""
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        """
        Inicializa o avaliador.
        
        Args:
            model_name: Nome do modelo (ex: 'gemini-flash', 'gpt-5-mini', 'gpt-5-nano')
        """
        self.model_config = get_model_config(model_name)
        self.model_name = model_name
        
        # Verifica se a API key está configurada
        api_key = os.getenv(self.model_config.env_var)
        if not api_key:
            raise ValueError(
                f"{self.model_config.env_var} não encontrada. "
                f"Configure a variável de ambiente para usar {self.model_config.name}."
            )
        
        # Usa a string do modelo diretamente (Pydantic AI resolve automaticamente)
        model_string = self.model_config.model_string
        
        # Agente para extração de informações do pitch deck
        self.extraction_agent = Agent(
            model_string,
            output_type=PitchDeckInfo,
            system_prompt=EXTRACTION_SYSTEM_PROMPT
        )
        
        # Agente para avaliação da startup
        self.evaluation_agent = Agent(
            model_string,
            output_type=AvaliacaoStartup,
            system_prompt=get_evaluation_system_prompt()
        )
        
        # Tracking de uso
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_requests = 0
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calcula o custo estimado em USD."""
        pricing = self.model_config.pricing
        input_cost = (input_tokens / 1_000_000) * pricing.input_per_million
        output_cost = (output_tokens / 1_000_000) * pricing.output_per_million
        return input_cost + output_cost
    
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
            estimated_cost_usd=self._calculate_cost(
                self._total_input_tokens, 
                self._total_output_tokens
            ),
            model_name=self.model_config.name
        )
    
    def reset_usage(self) -> None:
        """Reseta o tracking de uso."""
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_requests = 0
    
    def extract_info(self, pdf_path: str) -> PitchDeckInfo:
        """
        Extrai informações do pitch deck.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            PitchDeckInfo com informações extraídas
        """
        pdf_bytes = Path(pdf_path).read_bytes()
        
        if self.model_config.supports_pdf:
            # Envia PDF diretamente (Gemini)
            result = self.extraction_agent.run_sync([
                EXTRACTION_USER_PROMPT,
                BinaryContent(data=pdf_bytes, media_type='application/pdf')
            ])
        else:
            # Para OpenAI: converte PDF em imagens primeiro
            images = self._pdf_to_images(pdf_path)
            content = [EXTRACTION_USER_PROMPT]
            for img_bytes in images:
                content.append(BinaryContent(data=img_bytes, media_type='image/png'))
            result = self.extraction_agent.run_sync(content)
        
        self._track_usage(result.usage())
        return result.output
    
    def _pdf_to_images(self, pdf_path: str, max_pages: int = 10) -> list[bytes]:
        """
        Converte PDF em imagens para modelos que não suportam PDF direto.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            max_pages: Número máximo de páginas
            
        Returns:
            Lista de bytes das imagens PNG
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "PyMuPDF é necessário para usar OpenAI com PDFs. "
                "Instale com: pip install PyMuPDF"
            )
        
        images = []
        doc = fitz.open(pdf_path)
        
        for page_num in range(min(len(doc), max_pages)):
            page = doc[page_num]
            mat = fitz.Matrix(2.0, 2.0)  # Zoom 2x
            pix = page.get_pixmap(matrix=mat)
            images.append(pix.tobytes("png"))
        
        doc.close()
        return images
    
    def evaluate_startup(self, pdf_info: PitchDeckInfo) -> AvaliacaoStartup:
        """
        Avalia a startup com base nas informações extraídas.
        
        Args:
            pdf_info: Informações extraídas do pitch deck
            
        Returns:
            AvaliacaoStartup com nota e justificativa
        """
        pdf_summary = self._format_pdf_info(pdf_info)
        prompt = get_evaluation_user_prompt(pdf_summary)
        
        result = self.evaluation_agent.run_sync(prompt)
        self._track_usage(result.usage())
        
        return result.output
    
    def _format_pdf_info(self, info: PitchDeckInfo) -> str:
        """Formata as informações do PDF para o prompt."""
        lines = []
        for field_name, field_value in info.model_dump().items():
            if field_value and field_value != "indefinido":
                label = field_name.replace('_', ' ').title()
                lines.append(f"  - {label}: {field_value}")
        return "\n".join(lines) if lines else "  - Nenhuma informação extraída"
    
    def evaluate(self, pdf_path: str) -> dict:
        """
        Realiza avaliação completa da startup.
        
        Args:
            pdf_path: Caminho para o arquivo PDF do pitch deck
            
        Returns:
            Dicionário com nota, justificativa, detalhes e uso
        """
        self.reset_usage()
        
        # Passo 1: Extrai informações do pitch deck
        pdf_info = self.extract_info(pdf_path)
        
        # Passo 2: Avalia a startup
        avaliacao = self.evaluate_startup(pdf_info)
        
        # Obtém informações de uso
        usage = self.get_usage()
        
        # Converte para dicionário com campos adicionais
        result = avaliacao.model_dump()
        result['nota_descricao'] = NOTA_DESCRICOES.get(avaliacao.nota, "Desconhecida")
        result['pdf_info_extracted'] = pdf_info.model_dump()
        result['model_used'] = self.model_config.name
        result['usage'] = {
            'input_tokens': usage.input_tokens,
            'output_tokens': usage.output_tokens,
            'total_tokens': usage.total_tokens,
            'requests': usage.requests,
            'estimated_cost_usd': usage.estimated_cost_usd,
        }
        
        return result
