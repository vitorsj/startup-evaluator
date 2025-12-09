
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

# Add current directory to path so we can import modules
sys.path.append(os.getcwd())

from evaluator import StartupEvaluator
from model_config import DEFAULT_MODEL

# Load env vars
load_dotenv()

console = Console()

def run_comparison(pdf_folder="Inputs"):
    pdf_path = Path(pdf_folder)
    if not pdf_path.exists():
        console.print(f"[red]Pasta nao encontrada: {pdf_folder}[/red]")
        return

    pdf_files = list(pdf_path.glob("*.pdf"))
    if not pdf_files:
        console.print(f"[yellow]Nenhum PDF encontrado em {pdf_folder}[/yellow]")
        return

    console.print(f"[bold]Iniciando Comparativo V2 vs Astella (V3) para {len(pdf_files)} PDFs[/bold]\n")

    # Initialize evaluators
    try:
        evaluator_v2 = StartupEvaluator(
            extraction_model=DEFAULT_MODEL, 
            evaluation_model=DEFAULT_MODEL, 
            prompt_version="v2"
        )
        evaluator_astella = StartupEvaluator(
            extraction_model=DEFAULT_MODEL, 
            evaluation_model=DEFAULT_MODEL, 
            prompt_version="astella"
        )
    except Exception as e:
        console.print(f"[red]Erro ao inicializar avaliadores: {str(e)}[/red]")
        return

    results = []

    for pdf_file in pdf_files:
        pdf_name = pdf_file.name
        console.print(f"[cyan]Processando: {pdf_name}...[/cyan]")

        row_data = {"pdf": pdf_name}

        # Run V2
        try:
            res_v2 = evaluator_v2.evaluate(str(pdf_file))
            row_data["v2_score"] = res_v2.get("nota", 0)
            row_data["v2_desc"] = res_v2.get("nota_descricao", "")
            # Try to get preliminary analysis or reason from V2 if needed, but score is main metric
        except Exception as e:
            console.print(f"[red]Erro V2 em {pdf_name}: {e}[/red]")
            row_data["v2_score"] = "Erro"
            row_data["v2_desc"] = str(e)

        # Run Astella
        try:
            res_astella = evaluator_astella.evaluate(str(pdf_file))
            row_data["astella_score"] = res_astella.get("nota", 0)
            row_data["astella_desc"] = res_astella.get("nota_descricao", "")
            
            # Extract points from analysis if possible (would need parsing, but nota is enough for now)
            
        except Exception as e:
            console.print(f"[red]Erro Astella em {pdf_name}: {e}[/red]")
            row_data["astella_score"] = "Erro"
            row_data["astella_desc"] = str(e)

        results.append(row_data)

    # Display Comparison Table
    console.print("\n" + "=" * 80)
    console.print("[bold]COMPARATIVO FINAL: PROMPT V2 vs ASTELLA (V3)[/bold]")
    console.print("=" * 80 + "\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("PDF", style="dim")
    table.add_column("Nota V2", justify="center")
    table.add_column("Nota Astella", justify="center")
    table.add_column("Diferença", justify="center")
    table.add_column("Status Astella")

    for r in results:
        v2 = r.get("v2_score")
        astella = r.get("astella_score")
        
        # Format V2
        if isinstance(v2, (int, float)):
            v2_str = f"{v2}/5"
            v2_val = v2
        else:
            v2_str = "Erro"
            v2_val = -1

        # Format Astella
        if isinstance(astella, (int, float)):
            astella_str = f"{astella}/5"
            astella_val = astella
        else:
            astella_str = "Erro"
            astella_val = -1

        # Diff
        if v2_val != -1 and astella_val != -1:
            diff = astella_val - v2_val
            diff_str = f"{diff:+.1f}"
            if diff < 0:
                diff_str = f"[red]{diff_str}[/red]"
            elif diff > 0:
                diff_str = f"[green]{diff_str}[/green]"
            else:
                diff_str = "[dim]0[/dim]"
        else:
            diff_str = "-"

        table.add_row(
            r["pdf"],
            v2_str,
            astella_str,
            diff_str,
            r.get("astella_desc", "")
        )

    console.print(table)

if __name__ == "__main__":
    run_comparison()
