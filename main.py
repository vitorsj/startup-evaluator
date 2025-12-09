#!/usr/bin/env python3
"""
CLI principal para avaliação de startups.
Recebe pitch deck (PDF) e retorna nota de 0-5 com justificativa.
Suporta múltiplos modelos: Gemini e OpenAI.
"""

import argparse
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

# Configura Logger global
logging.basicConfig(
    filename='execution.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger("main")
# Carrega variáveis de ambiente primeiro
load_dotenv()

# Configura Logfire para observabilidade (opcional)
try:
    import logfire
    logfire.configure(send_to_logfire='if-token-present')
    logfire.instrument_pydantic_ai()
    LOGFIRE_ENABLED = True
except ImportError:
    LOGFIRE_ENABLED = False

from evaluator import StartupEvaluator
from model_config import AVAILABLE_MODELS, DEFAULT_MODEL, get_model_config, list_models
from prompts import list_prompt_versions, DEFAULT_PROMPT_VERSION

console = Console()


def evaluate_single_startup(pdf_path: str, model_name: str = DEFAULT_MODEL, prompt_version: str = DEFAULT_PROMPT_VERSION) -> dict:
    """
    Avalia uma única startup.
    
    Args:
        pdf_path: Caminho para o PDF do pitch deck
        model_name: Nome do modelo a usar
        prompt_version: Versão do prompt a usar
        
    Returns:
        Resultado da avaliação
    """
    model_config = get_model_config(model_name)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        task1 = progress.add_task(f"[cyan]Inicializando {model_config.name}...", total=None)
        try:
            evaluator = StartupEvaluator(model_name=model_name, prompt_version=prompt_version)
        except Exception as e:
            console.print(f"[red]Erro ao inicializar avaliador: {str(e)}[/red]")
            sys.exit(1)
        progress.update(task1, completed=True)
        
        task2 = progress.add_task(f"[cyan]Analisando pitch deck e avaliando startup (Prompt: {prompt_version})...", total=None)
        try:
            result = evaluator.evaluate(pdf_path)
        except Exception as e:
            console.print(f"[red]Erro na avaliação: {str(e)}[/red]")
            sys.exit(1)
        progress.update(task2, completed=True)
    
    return result


def display_result(result: dict, pdf_name: str):
    """Exibe resultado formatado no terminal."""
    nota = result.get('nota', 0)
    nota_desc = result.get('nota_descricao', '')
    
    if nota >= 4:
        nota_color = "green"
    elif nota >= 3:
        nota_color = "yellow"
    elif nota >= 1:
        nota_color = "orange1"
    else:
        nota_color = "red"
    
    console.print("\n")
    console.print(Panel.fit(
        f"[bold {nota_color}]{nota}/5[/bold {nota_color}] - {nota_desc}",
        title="[bold]Avaliacao da Startup[/bold]",
        border_style=nota_color
    ))
    
    info_table = Table(show_header=False, box=None)
    info_table.add_row("[bold]Pitch Deck:[/bold]", pdf_name)
    info_table.add_row("[bold]Modelo:[/bold]", result.get('model_used', 'N/A'))
    info_table.add_row("[bold]Prompt Version:[/bold]", result.get('prompt_version', 'N/A'))
    
    estagio = result.get('estagio_identificado', 'N/A')
    if hasattr(estagio, 'value'):
        estagio = estagio.value
    info_table.add_row("[bold]Estagio Identificado:[/bold]", str(estagio).upper())
    console.print(info_table)
    
    pdf_info = result.get('pdf_info_extracted', {})
    if pdf_info:
        console.print("\n[bold]Informacoes Extraidas:[/bold]")
        extracted_table = Table(show_header=False, box=None, padding=(0, 2))
        
        nome = pdf_info.get('nome_startup')
        if nome:
            extracted_table.add_row("[dim]Nome:[/dim]", nome)
        
        localizacao = pdf_info.get('localizacao')
        if localizacao:
            extracted_table.add_row("[dim]Localizacao:[/dim]", localizacao)
        
        receita = pdf_info.get('receita_anual')
        if receita:
            extracted_table.add_row("[dim]Receita Anual:[/dim]", receita)
        
        rodada = pdf_info.get('tamanho_rodada')
        if rodada:
            extracted_table.add_row("[dim]Tamanho Rodada:[/dim]", rodada)
        
        valuation = pdf_info.get('valuation_pre_money')
        if valuation:
            extracted_table.add_row("[dim]Valuation:[/dim]", valuation)
        
        console.print(extracted_table)
    
    analise_preliminar = result.get('analise_preliminar')
    if analise_preliminar:
        console.print("\n[bold cyan]Análise Preliminar (Chain of Thought):[/bold cyan]")
        console.print(Panel(analise_preliminar, border_style="cyan"))
    
    console.print("\n[bold]Justificativa:[/bold]")
    console.print(Panel(result.get('justificativa', 'Nao disponivel'), border_style="blue"))
    
    pontos_pos = result.get('pontos_positivos', [])
    if pontos_pos:
        console.print("\n[bold green]Pontos Positivos:[/bold green]")
        for ponto in pontos_pos:
            console.print(f"  - {ponto}")
    
    pontos_neg = result.get('pontos_negativos', [])
    if pontos_neg:
        console.print("\n[bold red]Pontos Negativos:[/bold red]")
        for ponto in pontos_neg:
            console.print(f"  - {ponto}")
    
    criterios = result.get('criterios_atendidos', {})
    if criterios:
        console.print("\n[bold]Criterios Atendidos:[/bold]")
        criterios_table = Table(show_header=True, header_style="bold")
        criterios_table.add_column("Criterio")
        criterios_table.add_column("Status")
        criterios_table.add_column("Evidencia")
        
        for criterio, criterio_data in criterios.items():
            # Suporta tanto a nova estrutura (dict com 'atendido' e 'evidencia_encontrada')
            # quanto a antiga (bool direto) para compatibilidade
            if isinstance(criterio_data, dict):
                atendido = criterio_data.get('atendido', False)
                evidencia = criterio_data.get('evidencia_encontrada', 'N/A')
            else:
                # Fallback para estrutura antiga (bool)
                atendido = criterio_data
                evidencia = 'N/A'
            
            status = "[green]Sim[/green]" if atendido else "[red]Nao[/red]"
            # Limita o tamanho da evidência para não quebrar a tabela
            evidencia_display = evidencia[:80] + "..." if len(evidencia) > 80 else evidencia
            criterios_table.add_row(
                criterio.replace('_', ' ').title(), 
                status,
                f"[dim]{evidencia_display}[/dim]"
            )
        
        console.print(criterios_table)
    
    usage = result.get('usage', {})
    if usage:
        console.print("\n[bold dim]Uso da API:[/bold dim]")
        usage_table = Table(show_header=False, box=None, padding=(0, 2))
        usage_table.add_row(
            "[dim]Tokens:[/dim]", 
            f"{usage.get('total_tokens', 0):,} (input: {usage.get('input_tokens', 0):,}, output: {usage.get('output_tokens', 0):,})"
        )
        usage_table.add_row("[dim]Requests:[/dim]", str(usage.get('requests', 0)))
        usage_table.add_row(
            "[dim]Custo estimado:[/dim]", 
            f"[cyan]${usage.get('estimated_cost_usd', 0):.4f} USD[/cyan]"
        )
        console.print(usage_table)


def process_batch(pdf_folder: str, model_name: str = DEFAULT_MODEL, prompt_version: str = DEFAULT_PROMPT_VERSION):
    """Processa multiplos pitch decks de uma pasta."""
    pdf_path = Path(pdf_folder)
    if not pdf_path.exists():
        console.print(f"[red]Pasta nao encontrada: {pdf_folder}[/red]")
        sys.exit(1)
    
    pdf_files = list(pdf_path.glob("*.pdf"))
    if not pdf_files:
        console.print(f"[yellow]Nenhum PDF encontrado em {pdf_folder}[/yellow]")
        return
    
    console.print(f"[bold]Encontrados {len(pdf_files)} PDFs[/bold]\n")
    
    results = []
    total_cost = 0.0
    
    for pdf_file in pdf_files:
        pdf_name = pdf_file.name
        
        console.print(f"\n[bold cyan]Processando: {pdf_name}[/bold cyan]")
        try:
            result = evaluate_single_startup(str(pdf_file), model_name, prompt_version)
            result['pdf_name'] = pdf_name
            results.append(result)
            total_cost += result.get('usage', {}).get('estimated_cost_usd', 0)
            display_result(result, pdf_name)
        except Exception as e:
            console.print(f"[red]Erro ao processar {pdf_name}: {str(e)}[/red]")
    
    if results:
        console.print("\n" + "=" * 50)
        console.print("[bold]RESUMO FINAL[/bold]")
        console.print("=" * 50 + "\n")
        
        summary_table = Table(show_header=True, header_style="bold")
        summary_table.add_column("PDF")
        summary_table.add_column("Nota")
        summary_table.add_column("Estagio")
        summary_table.add_column("Startup")
        summary_table.add_column("Custo")
        summary_table.add_column("Prompt")
        
        for r in sorted(results, key=lambda x: x.get('nota', 0), reverse=True):
            nota = r.get('nota', 0)
            nota_color = "green" if nota >= 4 else "yellow" if nota >= 3 else "red"
            
            estagio = r.get('estagio_identificado', 'N/A')
            if hasattr(estagio, 'value'):
                estagio = estagio.value
            
            nome = r.get('pdf_info_extracted', {}).get('nome_startup', 'N/A')
            custo = r.get('usage', {}).get('estimated_cost_usd', 0)
            prompt_ver = r.get('prompt_version', 'N/A')
            
            summary_table.add_row(
                r['pdf_name'],
                f"[{nota_color}]{nota}/5[/{nota_color}]",
                str(estagio).upper(),
                nome or 'N/A',
                f"${custo:.4f}",
                prompt_ver
            )
        
        console.print(summary_table)
        console.print(f"\n[bold]Custo total estimado: [cyan]${total_cost:.4f} USD[/cyan][/bold]")


def main():
    """Funcao principal do CLI."""
    parser = argparse.ArgumentParser(
        description="Avaliador de Startups para VC - Analisa pitch decks com IA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Avaliar com Gemini Flash (padrao) e Prompt V2 (padrao)
  python main.py --pdf pitch.pdf
  
  # Avaliar com Prompt V1 (lógica antiga)
  python main.py --pdf pitch.pdf --prompt-version v1
  
  # Avaliar com GPT-5 Mini
  python main.py --pdf pitch.pdf --model gpt-5-mini
  
  # Processar pasta de PDFs com Prompt V2
  python main.py --folder ./pitch_decks --prompt-version v2
  
  # Listar modelos disponiveis
  python main.py --list-models
        """
    )
    
    parser.add_argument('--pdf', type=str, help='Caminho para o PDF do pitch deck')
    parser.add_argument('--folder', type=str, help='Pasta contendo multiplos PDFs')
    parser.add_argument(
        '--model', '-m',
        type=str,
        default=DEFAULT_MODEL,
        choices=list(AVAILABLE_MODELS.keys()),
        help=f'Modelo a usar (padrao: {DEFAULT_MODEL})'
    )
    parser.add_argument(
        '--prompt-version', '-p',
        type=str,
        default=DEFAULT_PROMPT_VERSION,
        choices=list_prompt_versions(),
        help=f'Versao do prompt (padrao: {DEFAULT_PROMPT_VERSION})'
    )
    parser.add_argument('--list-models', action='store_true', help='Lista modelos disponiveis')
    
    args = parser.parse_args()
    
    if args.list_models:
        console.print(list_models())
        return
    
    try:
        model_config = get_model_config(args.model)
    except ValueError as e:
        console.print(f"[red]Erro: {e}[/red]")
        sys.exit(1)
    
    if not os.getenv(model_config.env_var):
        console.print(f"[red]Erro: {model_config.env_var} nao configurada![/red]")
        console.print(f"Configure a variavel de ambiente para usar {model_config.name}")
        console.print(f"\nExemplo: export {model_config.env_var}='sua-chave-aqui'")
        sys.exit(1)
    
    console.print(f"[bold]Modelo: {model_config.name} | Prompt: {args.prompt_version}[/bold]")
    if LOGFIRE_ENABLED:
        console.print("[dim]Logfire ativo - traces em https://logfire.pydantic.dev[/dim]")
    console.print()
    
    if args.folder:
        process_batch(args.folder, args.model, args.prompt_version)
        return
    
    if not args.pdf:
        parser.print_help()
        console.print("\n[red]Erro: --pdf e obrigatorio no modo single[/red]")
        sys.exit(1)
    
    if not Path(args.pdf).exists():
        console.print(f"[red]PDF nao encontrado: {args.pdf}[/red]")
        sys.exit(1)
    
    result = evaluate_single_startup(args.pdf, args.model, args.prompt_version)
    display_result(result, Path(args.pdf).name)


if __name__ == "__main__":
    main()
