---
name: Agente Avaliação Startups
overview: Criar um agente CLI em Python que analisa pitch decks (PDF) e sites de startups, avaliando-os com base nos critérios do fundo de VC e gerando uma nota de 0-5 com justificativa.
todos:
  - id: setup-project
    content: Criar estrutura do projeto e requirements.txt
    status: pending
  - id: config-criteria
    content: Implementar config.py com critérios do fundo (Pre-Seed, Seed, Series A)
    status: pending
  - id: pdf-extractor
    content: Criar pdf_analyzer.py para extrair texto e imagens de PDFs
    status: pending
  - id: web-scraper
    content: Criar web_scraper.py para extrair informações do site
    status: pending
  - id: evaluator
    content: Implementar evaluator.py com integração OpenAI e lógica de notas
    status: pending
  - id: cli-main
    content: Criar main.py com interface CLI completa
    status: pending
  - id: readme
    content: Criar README.md com instruções de uso
    status: pending
---

# Agente de Avaliação de Startups para VC

## Visão Geral

Sistema CLI em Python que recebe um pitch deck (PDF) e URL do site de uma startup, analisa automaticamente usando GPT-4 Vision da OpenAI, e retorna uma nota de 0-5 com justificativa baseada nos critérios do fundo.

## Arquitetura

```
Bulk Analysis/
├── main.py              # CLI principal
├── config.py            # Critérios do fundo (Pre-Seed, Seed, Series A)
├── pdf_analyzer.py      # Extração de conteúdo do PDF
├── web_scraper.py       # Scraping do site da startup
├── evaluator.py         # Lógica de avaliação com IA
├── requirements.txt     # Dependências
└── README.md            # Instruções de uso
```

## Componentes

### 1. Extração de PDF (`pdf_analyzer.py`)

- Usa `PyMuPDF` para extrair texto e imagens do pitch deck
- Converte páginas em imagens para análise visual com GPT-4 Vision
- Captura métricas, gráficos e informações visuais importantes

### 2. Web Scraper (`web_scraper.py`)

- Usa `requests` + `BeautifulSoup` para extrair conteúdo do site
- Captura: descrição do produto, equipe, clientes, depoimentos
- Identifica sinais de tração e profissionalismo

### 3. Configuração do Fundo (`config.py`)

- Critérios estruturados para cada estágio (Pre-Seed, Seed, Series A)
- Localização: Brasil
- Métricas financeiras, cap table, produto e crescimento
- Sistema de pontuação por critério

### 4. Avaliador (`evaluator.py`)

- Integração com OpenAI GPT-4 Vision
- Prompt estruturado com os critérios do fundo
- Análise combinada: pitch deck + site
- Geração de nota (0-5) + justificativa

### 5. CLI (`main.py`)

- Comando: `python main.py --pdf caminho/pitch.pdf --url https://startup.com`
- Opção para processar múltiplos arquivos de uma pasta
- Saída formatada com nota e justificativa

## Escala de Notas

- **0**: Descartável - não atende critérios básicos
- **1**: Muito fraca - poucos pontos positivos
- **2**: Fraca - alguns pontos, mas gaps significativos
- **3**: Mediana - potencial, mas precisa de mais validação
- **4**: Forte - atende maioria dos critérios, vale conversar
- **5**: Excepcional - prioridade máxima, agendar reunião

## Dependências Principais

- `openai` - API GPT-4 Vision
- `PyMuPDF` (fitz) - Extração de PDFs
- `requests` + `beautifulsoup4` - Web scraping
- `python-dotenv` - Gerenciamento de API keys
- `rich` - Output formatado no terminal

## Configuração

Requer variável de ambiente `OPENAI_API_KEY` para funcionar.