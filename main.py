#!/usr/bin/env python3
"""
CLI principal para avaliação de startups.
Recebe pitch deck (PDF) e retorna nota de 0-5 com justificativa.
"""

import argparse
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

from evaluator import StartupEvaluator

# Carrega variáveis de ambiente
load_dotenv()

console = Console()


def evaluate_single_startup(pdf_path: str) -> dict:
    """
    Avalia uma única startup.
    
    Args:
        pdf_path: Caminho para o PDF do pitch deck
        
    Returns:
        Resultado da avaliação
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Inicializa o avaliador
        task1 = progress.add_task("[cyan]Inicializando Gemini AI...", total=None)
        try:
            evaluator = StartupEvaluator()
        except Exception as e:
            console.print(f"[red]Erro ao inicializar avaliador: {str(e)}[/red]")
            sys.exit(1)
        progress.update(task1, completed=True)
        
        # Avalia a startup (envia PDF diretamente)
        task2 = progress.add_task("[cyan]Analisando pitch deck e avaliando startup...", total=None)
        try:
            result = evaluator.evaluate(pdf_path)
        except Exception as e:
            console.print(f"[red]Erro na avaliação: {str(e)}[/red]")
            sys.exit(1)
        progress.update(task2, completed=True)
    
    return result


def display_result(result: dict, pdf_name: str):
    """
    Exibe resultado formatado no terminal.
    
    Args:
        result: Resultado da avaliação
        pdf_name: Nome do arquivo PDF
    """
    nota = result.get('nota', 0)
    nota_desc = result.get('nota_descricao', '')
    
    # Cor baseada na nota
    if nota >= 4:
        nota_color = "green"
    elif nota >= 3:
        nota_color = "yellow"
    elif nota >= 1:
        nota_color = "orange1"
    else:
        nota_color = "red"
    
    # Painel principal
    console.print("\n")
    console.print(Panel.fit(
        f"[bold {nota_color}]{nota}/5[/bold {nota_color}] - {nota_desc}",
        title="[bold]Avaliação da Startup[/bold]",
        border_style=nota_color
    ))
    
    # Informações básicas
    info_table = Table(show_header=False, box=None)
    info_table.add_row("[bold]Pitch Deck:[/bold]", pdf_name)
    
    estagio = result.get('estagio_identificado', 'N/A')
    if hasattr(estagio, 'value'):
        estagio = estagio.value
    info_table.add_row("[bold]Estágio Identificado:[/bold]", str(estagio).upper())
    console.print(info_table)
    
    # Informações extraídas do pitch deck
    pdf_info = result.get('pdf_info_extracted', {})
    if pdf_info:
        console.print("\n[bold]Informações Extraídas:[/bold]")
        extracted_table = Table(show_header=False, box=None, padding=(0, 2))
        
        nome = pdf_info.get('nome_startup')
        if nome:
            extracted_table.add_row("[dim]Nome:[/dim]", nome)
        
        localizacao = pdf_info.get('localizacao')
        if localizacao:
            extracted_table.add_row("[dim]Localização:[/dim]", localizacao)
        
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
    
    # Justificativa
    console.print("\n[bold]Justificativa:[/bold]")
    console.print(Panel(result.get('justificativa', 'Não disponível'), border_style="blue"))
    
    # Pontos positivos
    pontos_pos = result.get('pontos_positivos', [])
    if pontos_pos:
        console.print("\n[bold green]✓ Pontos Positivos:[/bold green]")
        for ponto in pontos_pos:
            console.print(f"  • {ponto}")
    
    # Pontos negativos
    pontos_neg = result.get('pontos_negativos', [])
    if pontos_neg:
        console.print("\n[bold red]✗ Pontos Negativos:[/bold red]")
        for ponto in pontos_neg:
            console.print(f"  • {ponto}")
    
    # Critérios atendidos
    criterios = result.get('criterios_atendidos', {})
    if criterios:
        console.print("\n[bold]Critérios Atendidos:[/bold]")
        criterios_table = Table(show_header=True, header_style="bold")
        criterios_table.add_column("Critério")
        criterios_table.add_column("Status")
        
        for criterio, atendido in criterios.items():
            status = "[green]✓ Sim[/green]" if atendido else "[red]✗ Não[/red]"
            criterios_table.add_row(criterio.replace('_', ' ').title(), status)
        
        console.print(criterios_table)


def process_batch(pdf_folder: str):
    """
    Processa múltiplos pitch decks de uma pasta.
    
    Args:
        pdf_folder: Pasta contendo PDFs
    """
    pdf_path = Path(pdf_folder)
    if not pdf_path.exists():
        console.print(f"[red]Pasta não encontrada: {pdf_folder}[/red]")
        sys.exit(1)
    
    pdf_files = list(pdf_path.glob("*.pdf"))
    if not pdf_files:
        console.print(f"[yellow]Nenhum PDF encontrado em {pdf_folder}[/yellow]")
        return
    
    console.print(f"[bold]Encontrados {len(pdf_files)} PDFs[/bold]\n")
    
    results = []
    for pdf_file in pdf_files:
        pdf_name = pdf_file.name
        
        console.print(f"\n[bold cyan]Processando: {pdf_name}[/bold cyan]")
        try:
            result = evaluate_single_startup(str(pdf_file))
            result['pdf_name'] = pdf_name
            results.append(result)
            display_result(result, pdf_name)
        except Exception as e:
            console.print(f"[red]Erro ao processar {pdf_name}: {str(e)}[/red]")
    
    # Resumo final
    if results:
        console.print("\n[bold]═══════════════════════════════════════════[/bold]")
        console.print("[bold]               RESUMO FINAL                [/bold]")
        console.print("[bold]═══════════════════════════════════════════[/bold]\n")
        
        summary_table = Table(show_header=True, header_style="bold")
        summary_table.add_column("PDF")
        summary_table.add_column("Nota")
        summary_table.add_column("Estágio")
        summary_table.add_column("Startup")
        
        for r in sorted(results, key=lambda x: x.get('nota', 0), reverse=True):
            nota = r.get('nota', 0)
            nota_color = "green" if nota >= 4 else "yellow" if nota >= 3 else "red"
            
            estagio = r.get('estagio_identificado', 'N/A')
            if hasattr(estagio, 'value'):
                estagio = estagio.value
            
            nome = r.get('pdf_info_extracted', {}).get('nome_startup', 'N/A')
            
            summary_table.add_row(
                r['pdf_name'],
                f"[{nota_color}]{nota}/5[/{nota_color}]",
                str(estagio).upper(),
                nome or 'N/A'
            )
        
        console.print(summary_table)


def main():
    """Função principal do CLI."""
    parser = argparse.ArgumentParser(
        description="Avaliador de Startups para VC - Analisa pitch decks com Gemini AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Avaliar um pitch deck
  python main.py --pdf pitch.pdf
  
  # Processar pasta de PDFs
  python main.py --folder ./pitch_decks
        """
    )
    
    parser.add_argument(
        '--pdf',
        type=str,
        help='Caminho para o PDF do pitch deck'
    )
    
    parser.add_argument(
        '--folder',
        type=str,
        help='Pasta contendo múltiplos PDFs para processar em lote'
    )
    
    args = parser.parse_args()
    
    # Verifica API key
    if not os.getenv('GEMINI_API_KEY'):
        console.print("[red]Erro: GEMINI_API_KEY não configurada![/red]")
        console.print("Configure a variável de ambiente ou crie um arquivo .env")
        console.print("\nExemplo: export GEMINI_API_KEY='sua-chave-aqui'")
        sys.exit(1)
    
    # Modo batch
    if args.folder:
        process_batch(args.folder)
        return
    
    # Modo single
    if not args.pdf:
        parser.print_help()
        console.print("\n[red]Erro: --pdf é obrigatório no modo single[/red]")
        sys.exit(1)
    
    if not Path(args.pdf).exists():
        console.print(f"[red]PDF não encontrado: {args.pdf}[/red]")
        sys.exit(1)
    
    result = evaluate_single_startup(args.pdf)
    display_result(result, Path(args.pdf).name)


if __name__ == "__main__":
    main()
