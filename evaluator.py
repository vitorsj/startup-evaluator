"""
Módulo de avaliação usando Pydantic AI com Google Gemini.
Analisa pitch deck (PDF) e gera nota de 0-5 com justificativa.
"""

import os
from pathlib import Path
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from config import NOTA_DESCRICOES
from models import PitchDeckInfo, AvaliacaoStartup
from prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    EXTRACTION_USER_PROMPT,
    get_evaluation_system_prompt,
    get_evaluation_user_prompt,
)


class StartupEvaluator:
    """Avaliador de startups usando Pydantic AI com Gemini."""
    
    def __init__(self, api_key: str | None = None):
        """
        Inicializa o avaliador.
        
        Args:
            api_key: Chave da API Gemini (ou usa GEMINI_API_KEY do ambiente)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não encontrada. Configure a variável de ambiente ou passe como parâmetro.")
        
        # Configura o provider e modelo Gemini
        self.provider = GoogleProvider(api_key=self.api_key)
        self.model = GoogleModel('gemini-2.5-flash', provider=self.provider)
        
        # Agente para extração de informações do pitch deck
        self.extraction_agent = Agent(
            self.model,
            output_type=PitchDeckInfo,
            system_prompt=EXTRACTION_SYSTEM_PROMPT
        )
        
        # Agente para avaliação da startup
        self.evaluation_agent = Agent(
            self.model,
            output_type=AvaliacaoStartup,
            system_prompt=get_evaluation_system_prompt()
        )
    
    def extract_info(self, pdf_path: str) -> PitchDeckInfo:
        """
        Extrai informações do pitch deck enviando o PDF diretamente.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            PitchDeckInfo com informações extraídas
        """
        # Lê o PDF como bytes
        pdf_bytes = Path(pdf_path).read_bytes()
        
        # Envia o PDF diretamente para o Gemini
        result = self.extraction_agent.run_sync([
            EXTRACTION_USER_PROMPT,
            BinaryContent(data=pdf_bytes, media_type='application/pdf')
        ])
        
        return result.output
    
    def evaluate_startup(self, pdf_info: PitchDeckInfo) -> AvaliacaoStartup:
        """
        Avalia a startup com base nas informações extraídas.
        
        Args:
            pdf_info: Informações extraídas do pitch deck
            
        Returns:
            AvaliacaoStartup com nota e justificativa
        """
        # Formata informações para o prompt
        pdf_summary = self._format_pdf_info(pdf_info)
        
        # Gera o prompt de avaliação
        prompt = get_evaluation_user_prompt(pdf_summary)
        
        result = self.evaluation_agent.run_sync(prompt)
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
            Dicionário com nota, justificativa e detalhes
        """
        # Passo 1: Extrai informações do pitch deck (PDF direto)
        pdf_info = self.extract_info(pdf_path)
        
        # Passo 2: Avalia a startup
        avaliacao = self.evaluate_startup(pdf_info)
        
        # Converte para dicionário com campos adicionais
        result = avaliacao.model_dump()
        result['nota_descricao'] = NOTA_DESCRICOES.get(avaliacao.nota, "Desconhecida")
        result['pdf_info_extracted'] = pdf_info.model_dump()
        
        return result
