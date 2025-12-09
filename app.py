import streamlit as st
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Importar módulos do projeto
from evaluator import StartupEvaluator
from model_config import AVAILABLE_MODELS, DEFAULT_MODEL
from prompts import DEFAULT_PROMPT_VERSION

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="Analisador de Startups - Astella",
    page_icon="🚀",
    layout="wide"
)

# Constantes
INPUT_DIR = Path("Inputs")
OUTPUT_DIR = Path("Outputs")

# Garantir que diretórios existam
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

def save_uploaded_file(uploaded_file):
    """Salva o arquivo enviado no diretório de Inputs."""
    file_path = INPUT_DIR / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def save_analysis_result(result, pdf_name):
    """Salva o resultado da análise em JSON."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Remover extensão .pdf do nome
    base_name = Path(pdf_name).stem
    filename = f"{timestamp}_{base_name}.json"
    file_path = OUTPUT_DIR / filename
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    
    return file_path

def display_result(result):
    """Exibe o resultado da avaliação de forma estruturada."""
    
    # Cabeçalho com Nota e Status
    col1, col2 = st.columns([1, 3])
    
    with col1:
        nota = result.get('nota', 0)
        st.metric("Nota Final", f"{nota}/5")
    
    with col2:
        st.subheader(result.get('nota_descricao', ''))
        
        # Modelos usados (suporta formato antigo e novo)
        extraction_model = result.get('extraction_model', result.get('model_used', 'N/A'))
        evaluation_model = result.get('evaluation_model', result.get('model_used', 'N/A'))
        
        if extraction_model == evaluation_model:
            st.write(f"**Modelo:** {extraction_model}")
        else:
            st.write(f"**Extração:** {extraction_model} | **Avaliação:** {evaluation_model}")
        
        # Tokens usados e link para Logfire
        usage = result.get('usage', {})
        total_tokens = usage.get('total_tokens', 0)
        if total_tokens:
            st.write(f"**Tokens:** {total_tokens:,}")
        st.markdown("[🔍 Ver custos no Logfire](https://logfire.pydantic.dev/)")

    st.divider()

    # Resumo (Usando 'justificativa' já que 'resumo' não existe)
    st.subheader("📝 Justificativa & Resumo")
    st.write(result.get('justificativa', 'Sem justificativa disponível.'))
    
    if result.get('analise_preliminar'):
        with st.expander("Ver Análise Preliminar (Chain of Thought)"):
            st.text(result.get('analise_preliminar'))
    
    st.divider()

    # Critérios Detalhados
    st.subheader("🔍 Análise de Critérios")
    
    criterios = result.get('criterios_atendidos', {})
    
    # Helper para exibir booleanos com ícones
    def check_icon(value):
        return "✅" if value else "❌"

    # Aba para cada seção de critérios
    tab1, tab2, tab3 = st.tabs(["Tese & Estágio", "Métricas & Finanças", "Produto & Time"])
    
    with tab1:
        loc = criterios.get('localizacao', {})
        estagio = criterios.get('estagio_adequado', {})
        
        st.write(f"**Localização (Brasil):** {check_icon(loc.get('atendido'))}")
        st.caption(loc.get('evidencia_encontrada'))
        
        st.write(f"**Estágio Adequado:** {check_icon(estagio.get('atendido'))}")
        st.caption(estagio.get('evidencia_encontrada'))

    with tab2:
        fin = criterios.get('metricas_financeiro', {})
        # Removido tamanho_mercado pois não está no modelo de critérios
        
        st.write(f"**Métricas Financeiras:** {check_icon(fin.get('atendido'))}")
        st.caption(fin.get('evidencia_encontrada'))

    with tab3:
        # Mapeando nomes corretos do modelo
        prod = criterios.get('produto_tracao', {})
        time = criterios.get('equipe', {})
        # Removido cap_table pois não está no modelo de critérios
        
        st.write(f"**Produto & Tração:** {check_icon(prod.get('atendido'))}")
        st.caption(prod.get('evidencia_encontrada'))
        
        st.write(f"**Equipe:** {check_icon(time.get('atendido'))}")
        st.caption(time.get('evidencia_encontrada'))

    st.divider()
    
    # Pontos Fortes e Riscos
    c1, c2 = st.columns(2)
    with c1:
        st.success("💪 Pontos Fortes")
        # Corrigido para 'pontos_positivos'
        for p in result.get('pontos_positivos', []):
            st.write(f"- {p}")
            
    with c2:
        st.error("⚠️ Riscos e Gaps")
        # Corrigido para 'pontos_negativos'
        for r in result.get('pontos_negativos', []):
            st.write(f"- {r}")

    # Removido st.info("Recomendação") pois não existe campo específico, 
    # a recomendação está implícita na justificativa/nota.

def main():
    st.sidebar.title("Configurações")
    
    # Seleção de Modelos
    model_options = list(AVAILABLE_MODELS.keys())
    
    st.sidebar.subheader("🔍 Modelo de Extração")
    extraction_model = st.sidebar.selectbox(
        "Extrai informações do PDF",
        options=model_options,
        index=model_options.index(DEFAULT_MODEL) if DEFAULT_MODEL in model_options else 0,
        key="extraction_model"
    )
    extraction_config = AVAILABLE_MODELS[extraction_model]
    st.sidebar.caption(f"{extraction_config.name}: {extraction_config.description}")
    
    st.sidebar.subheader("📊 Modelo de Avaliação")
    evaluation_model = st.sidebar.selectbox(
        "Avalia a startup",
        options=model_options,
        index=model_options.index(DEFAULT_MODEL) if DEFAULT_MODEL in model_options else 0,
        key="evaluation_model"
    )
    evaluation_config = AVAILABLE_MODELS[evaluation_model]
    st.sidebar.caption(f"{evaluation_config.name}: {evaluation_config.description}")
    
    st.sidebar.divider()
    
    # Seleção de Prompt
    prompt_version = st.sidebar.selectbox(
        "Versão do Prompt",
        ["astella", "v2"],
        index=0
    )

    st.title("Avaliação de Startups via PDF")
    
    tab_analise, tab_historico = st.tabs(["Nova Análise", "Histórico"])
    
    # --- ABA NOVA ANÁLISE ---
    with tab_analise:
        uploaded_file = st.file_uploader("Faça upload do Pitch Deck (PDF)", type="pdf")
        
        if uploaded_file is not None:
            if st.button("Iniciar Análise", type="primary"):
                with st.spinner("Analisando o documento... Isso pode levar alguns minutos."):
                    try:
                        # Salvar arquivo
                        pdf_path = save_uploaded_file(uploaded_file)
                        
                        # Inicializar avaliador
                        evaluator = StartupEvaluator(
                            extraction_model=extraction_model,
                            evaluation_model=evaluation_model,
                            prompt_version=prompt_version
                        )
                        
                        # Executar análise
                        result = evaluator.evaluate(str(pdf_path))
                        
                        # Salvar resultado
                        json_path = save_analysis_result(result, uploaded_file.name)
                        
                        st.success("Análise concluída com sucesso!")
                        display_result(result)
                        
                    except Exception as e:
                        st.error(f"Ocorreu um erro durante a análise: {str(e)}")
                        # Opcional: mostrar traceback se for ambiente dev
                        # st.exception(e)

    # --- ABA HISTÓRICO ---
    with tab_historico:
        # Listar arquivos JSON no diretório Outputs
        history_files = sorted(list(OUTPUT_DIR.glob("*.json")), reverse=True)
        
        if not history_files:
            st.info("Nenhuma análise anterior encontrada.")
        else:
            selected_file = st.selectbox(
                "Selecione uma análise anterior:",
                history_files,
                format_func=lambda x: x.name
            )
            
            if selected_file:
                with open(selected_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                st.markdown(f"### Visualizando: {selected_file.name}")
                display_result(data)

if __name__ == "__main__":
    main()
