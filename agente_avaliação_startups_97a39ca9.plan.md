---
name: Agente Avaliação Startups
overview: Criar um agente CLI em Python que analisa pitch decks (PDF) de startups, avaliando-os com base nos critérios do fundo de VC e gerando uma nota de 0-5 com justificativa.
todos:
  - id: setup-project
    content: Criar estrutura do projeto e requirements.txt
    status: completed
  - id: config-criteria
    content: Implementar config.py com critérios do fundo (Pre-Seed, Seed, Series A)
    status: completed
  - id: pdf-extractor
    content: Implementar extração de texto e imagens de PDFs (integrado ao evaluator)
    status: completed
  - id: web-scraper
    content: Criar web_scraper.py para extrair informações do site (Recurso futuro)
    status: pending
  - id: evaluator
    content: Implementar evaluator.py com integração OpenAI/Gemini e lógica de notas (Pydantic AI)
    status: completed
  - id: cli-main
    content: Criar main.py com interface CLI completa
    status: completed
  - id: readme
    content: Criar README.md com instruções de uso
    status: completed
---

# Agente de Avaliação de Startups para VC

## Visão Geral

Sistema CLI em Python que recebe um pitch deck (PDF) de uma startup, analisa automaticamente usando LLMs (GPT-4 Vision, Gemini Flash, etc) via Pydantic AI, e retorna uma nota de 0-5 com justificativa baseada nos critérios do fundo.

## Arquitetura Atual

```
Bulk Analysis/
├── main.py              # CLI principal
├── config.py            # Critérios do fundo (Pre-Seed, Seed, Series A)
├── evaluator.py         # Lógica de avaliação e extração (Agentes Pydantic AI)
├── models.py            # Schemas Pydantic de entrada/saída
├── prompts.py           # Gestão de versões de prompts (V1, V2...)
├── model_config.py      # Configuração de múltiplos modelos (OpenAI, Gemini)
├── requirements.txt     # Dependências
└── README.md            # Instruções de uso
```

## Componentes

### 1. Extração e Avaliação (`evaluator.py`)

- Usa `Pydantic AI` para orquestrar agentes
- **Agente de Extração**: Converte PDF em imagens (via `PyMuPDF`) ou envia nativamente para o modelo, extraindo dados estruturados (`PitchDeckInfo`)
- **Agente de Avaliação**: Recebe os dados extraídos, compara com os critérios do fundo e gera avaliação final (`AvaliacaoStartup`)
- Suporta múltiplos modelos (Gemini Flash, GPT-4o, etc) configuráveis via `model_config.py`

### 2. Configuração do Fundo (`config.py`)

- Critérios estruturados para cada estágio (Pre-Seed, Seed, Series A)
- Localização: Brasil
- Métricas financeiras, cap table, produto e crescimento
- Sistema de pontuação por critério

### 3. Gestão de Prompts (`prompts.py`)

- Sistema de versionamento de prompts (V1, V2)
- **V1**: Lógica estrita (elimina se localização não for Brasil explícito)
- **V2**: Lógica de "Presunção de Inocência" (não elimina se localização for indefinida/null)
- Chain of Thought (CoT) para análise preliminar antes da nota

### 4. CLI (`main.py`)

- Comando: `python main.py --pdf caminho/pitch.pdf`
- Opção para processar pasta inteira: `python main.py --folder ./pasta_pdfs`
- Seleção de modelo: `--model gemini-flash`
- Seleção de prompt: `--prompt-version v2`
- Saída formatada com `rich`

### 5. Web Scraper (Pendente)

- Recurso planejado para enriquecer a análise com dados do site da startup.
- Status: Não implementado.

## Escala de Notas

- **0**: Descartável - não atende critérios básicos (ex: fora do Brasil)
- **1**: Muito fraca - poucos pontos positivos
- **2**: Fraca - alguns pontos, mas gaps significativos
- **3**: Mediana - potencial, mas precisa de mais validação
- **4**: Forte - atende maioria dos critérios, vale conversar
- **5**: Excepcional - prioridade máxima, agendar reunião

## Dependências Principais

- `pydantic-ai` - Framework de agentes
- `openai` / `google-generativeai` - Clientes de LLM
- `PyMuPDF` (fitz) - Processamento de PDFs
- `rich` - Output visual no terminal
- `python-dotenv` - Gerenciamento de variáveis de ambiente
