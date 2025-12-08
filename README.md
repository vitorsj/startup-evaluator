# Agente de Avaliação de Startups para VC

Sistema automatizado para avaliar pitch decks e sites de startups usando **Pydantic AI** e **Google Gemini**, gerando uma nota de 0-5 com justificativa baseada nos critérios do seu fundo de Venture Capital.

## Características

- ✅ Análise automática de pitch decks em PDF (enviado diretamente ao Gemini)
- ✅ Extração inteligente de informações com Gemini 2.5 Flash
- ✅ Structured outputs garantidos com Pydantic AI
- ✅ Nota de 0-5 com justificativa detalhada
- ✅ Processamento em lote de múltiplos pitch decks
- ✅ Critérios configuráveis por estágio (Pre-Seed, Seed, Series A)

## Instalação

### 1. Clone ou baixe o projeto

```bash
cd "Bulk Analysis"
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python -m venv venv
source venv/bin/activate  # No macOS/Linux
# ou
venv\Scripts\activate  # No Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure a API Key do Google Gemini

Obtenha sua API key em: https://aistudio.google.com/apikey

Crie um arquivo `.env` na raiz do projeto:

```bash
GEMINI_API_KEY=sua_chave_aqui
```

Ou exporte como variável de ambiente:

```bash
export GEMINI_API_KEY=sua_chave_aqui
```

## Uso

### Avaliar um pitch deck

```bash
python main.py --pdf caminho/para/pitch.pdf
```

### Processar múltiplos pitch decks

Coloque todos os PDFs em uma pasta e execute:

```bash
python main.py --folder pitch_decks/
```

## Escala de Notas

- **0**: Descartável - não atende critérios básicos
- **1**: Muito fraca - poucos pontos positivos
- **2**: Fraca - alguns pontos, mas gaps significativos
- **3**: Mediana - potencial, mas precisa de mais validação
- **4**: Forte - atende maioria dos critérios, vale conversar
- **5**: Excepcional - prioridade máxima, agendar reunião

## Critérios de Avaliação

O sistema avalia startups baseado nos seguintes critérios do fundo:

### Pre-Seed
- Receita Anual: R$ 0 – R$ 1 Milhão
- Tamanho da Rodada: R$ 2,5M – R$ 5M
- Valuation (Pre-Money): R$ 15M – R$ 35M
- Foco em validação de hipóteses e caminho para PMF

### Seed
- Receita Anual: R$ 3,5M – R$ 10M
- Tamanho da Rodada: R$ 8M – R$ 20M
- Valuation (Pre-Money): R$ 32M – R$ 60M
- Crescimento: 3x ao ano
- Sinais claros de PMF

### Series A
- Receita Anual: R$ 18M – R$ 30M
- Tamanho da Rodada: R$ 25M – R$ 50M
- Valuation (Pre-Money): R$ 75M – R$ 200M
- Crescimento: 2,5x ao ano
- Máquina de vendas pronta para escalar

**Localização**: Apenas startups brasileiras são consideradas.

## Estrutura do Projeto

```
Bulk Analysis/
├── main.py              # CLI principal
├── config.py            # Critérios do fundo
├── models.py            # Schemas Pydantic
├── evaluator.py         # Lógica de avaliação com Gemini
├── requirements.txt     # Dependências
└── README.md            # Este arquivo
```

## Requisitos

- Python 3.9+
- Google Gemini API Key
- Conexão com internet (para acessar sites e API)

## Limitações

- A qualidade da análise depende da qualidade e completude do pitch deck
- PDFs muito grandes podem demorar mais para processar

## Customização

Os critérios de avaliação podem ser ajustados editando o arquivo `config.py`.

## Suporte

Para problemas ou dúvidas, verifique:
1. Se a `GEMINI_API_KEY` está configurada corretamente
2. Se os PDFs estão acessíveis e não corrompidos

