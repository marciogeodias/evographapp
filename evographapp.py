import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Painel de Diagnóstico BNCC", layout="wide")

st.title("📊 Painel de Avaliação e Diagnóstico BNCC - Análise Temporal")
st.markdown("Acompanhamento longitudinal do desenvolvimento das turmas e alunos ao longo do ano.")

# Configuração padrão do gabarito
config_padrao = {
    "Q1": {"resposta": "A", "habilidade": "EF07LP09 - Leitura e Interpretação"},
    "Q2": {"resposta": "C", "habilidade": "EF07LP10 - Coesão e Coerência"},
    "Q3": {"resposta": "B", "habilidade": "EF07LP11 - Gêneros Textuais"},
    "Q4": {"resposta": "D", "habilidade": "EF07LP12 - Morfologia"},
    "Q5": {"resposta": "A", "habilidade": "EF07LP13 - Sintaxe"},
    "Q6": {"resposta": "B", "habilidade": "EF07LP14 - Pontuação"},
    "Q7": {"resposta": "C", "habilidade": "EF07LP15 - Ortografia"},
    "Q8": {"resposta": "D", "habilidade": "EF07LP16 - Variação Linguística"},
    "Q9": {"resposta": "A", "habilidade": "EF07LP17 - Produção Textual"},
    "Q10": {"resposta": "B", "habilidade": "EF07LP18 - Análise Literária"}
}

aba_config, aba_upload, aba_relatorio = st.tabs([
    "1. Configurar Gabarito", 
    "2. Enviar CSVs (Múltiplas Provas)", 
    "3. Análise Temporal & Gráficos"
])

# ------------------------------------------------------------------------------
# ABA 1: CONFIGURAÇÃO DO GABARITO
# ------------------------------------------------------------------------------
with aba_config:
    st.header("1. Cadastro de Gabarito & Habilidades BNCC")
    
    config_prova = {}
    cols = st.columns(2)
    
    for i in range(1, 11):
        q_code = f"Q{i}"
        default_info = config_padrao[q_code]
        
        with cols[0 if i <= 5 else 1]:
            st.markdown(f"**Questão {i}**")
            resp = st.selectbox(
                f"Gabarito {q_code}:", 
                ['A', 'B', 'C', 'D'], 
                index=['A', 'B', 'C', 'D'].index(default_info["resposta"]),
                key=f"resp_{q_code}"
            )
            hab = st.text_input(
                f"Habilidade BNCC {q_code}:", 
                value=default_info["habilidade"], 
                key=f"hab_{q_code}"
            )
            config_prova[q_code] = {"resposta": resp, "habilidade": hab}
            st.divider()

    st.session_state["config_prova"] = config_prova
    st.success("Gabarito configurado com sucesso!")

# ------------------------------------------------------------------------------
# ABA 2: UPLOAD DE MÚLTIPLOS CSVs
# ------------------------------------------------------------------------------
with aba_upload:
    st.header("2. Upload das Avaliações do Ano")
    st.info("Selecione os arquivos CSV de avaliação (TRIMESTRE_1, TRIMESTRE_2, TRIMESTRE_3 e FINAL).")
    
    arquivos_upload = st.file_uploader(
        "Selecione os arquivos CSV de avaliação:", 
        type=["csv"], 
        accept_multiple_files=True
    )
    
    if arquivos_upload:
        lista_dfs = []
        for arquivo in arquivos_upload:
            df_temp = pd.read_csv(arquivo)
            
            nome_limpo = arquivo.name.replace("AVALIACAO_PORTUGUES_", "").replace("_2023.csv", "").replace(".csv", "")
            df_temp["Avaliacao"] = nome_limpo
            
            if "Nome" in df_temp.columns:
                df_temp = df_temp[df_temp["Nome"] != "GABARITO"].copy()
                
            lista_dfs.append(df_temp)
            
        df_historico_completo = pd.concat(lista_dfs, ignore_index=True)
        st.session_state["df_historico_completo"] = df_historico_completo
        
        st.success(f"✅ {len(arquivos_upload)} arquivos consolidados com sucesso! Total de {len(df_historico_completo)} registros lidos.")
        
        colunas_desejadas = ["Avaliacao", "Nome", "Email", "Serie", "Série"]
        colunas_que_existem = [col for col in colunas_desejadas if col in df_historico_completo.columns]
        
        if colunas_que_existem:
            st.dataframe(df_historico_completo[colunas_que_existem].head(6))
        else:
            st.dataframe(df_historico_completo.head(6))

# ------------------------------------------------------------------------------
# ABA 3: RELATÓRIOS TEMPORAIS E NOVO MAPA DE HABILIDADES POR ALUNO
# ------------------------------------------------------------------------------
with aba_relatorio:
    st.header("3. Análise Longitudinal & Evolução Temporal")
    
    if "df_historico_completo" in st.session_state and "config_prova" in st.session_state:
        df_tudo = st.session_state["df_historico_completo"].copy()
        config = st.session_state["config_prova"]
        
        # 1. Processamento de acertos (1/0)
        colunas_acertos = []
        for q_code, info in config.items():
            if q_code in df_tudo.columns:
                col_acerto = f"Acerto_{q_code}"
                df_tudo[col_acerto] = (
                    df_tudo[q_code].astype(str).str[0].str.upper() == info["resposta"].upper()
                ).astype(int)
                colunas_acertos.append(col_acerto)
        
        df_tudo["Nota_Final"] = df_tudo[colunas_acertos].sum(axis=1) * 10
        
        ordem_periodos = ["TRIMESTRE_1_2023", "TRIMESTRE_2_2023", "TRIMESTRE_3_2023", "FINAL_2023", 
                          "TRIMESTRE_1", "TRIMESTRE_2", "TRIMESTRE_3", "FINAL"]
        
        df_tudo["Avaliacao"] = pd.Categorical(df_tudo["Avaliacao"], categories=ordem_periodos, ordered=True)
        df_tudo = df_tudo.sort_values("Avaliacao")
        
        # ----------------------------------------------------------------------
        # SEÇÃO 1: EVOLUÇÃO DA MÉDIA GERAL DA TURMA
        # ----------------------------------------------------------------------
        st.subheader("📈 1. Evolução da Média Geral da Turma")
        df_media_periodo = df_tudo.groupby("Avaliacao", observed=False)["Nota_Final"].mean().reset_index()
        
        fig1, ax1 = plt.subplots(figsize=(10, 3.5))
        sns.lineplot(
            data=df_media_periodo, 
            x="Avaliacao", 
            y="Nota_Final", 
            marker="o", 
            linewidth=3, 
            color="#1f77b4", 
            ax=ax1
        )
        ax1.set_ylim(0, 105)
        ax1.set_ylabel("Média (0 a 100)")
        ax1.set_xlabel("Período Avaliado")
        st.pyplot(fig1)
        
        st.divider()
        
        # ----------------------------------------------------------------------
        # SEÇÃO 2: EVOLUÇÃO INDIVIDUAL DE NOTAS
        # ----------------------------------------------------------------------
        st.subheader("👤 2. Evolução Individual de Notas por Aluno")
        alunos_disponiveis = df_tudo["Nome"].unique().tolist()
        
        alunos_selecionados = st.multiselect(
            "Selecione um ou mais alunos para comparar no gráfico:",
            options=alunos_disponiveis,
            default=alunos_disponiveis[:3] if len(alunos_disponiveis) >= 3 else alunos_disponiveis
        )
        
        if alunos_selecionados:
            df_alunos_filtrados = df_tudo[df_tudo["Nome"].isin(alunos_selecionados)]
            
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            sns.lineplot(
                data=df_alunos_filtrados,
                x="Avaliacao",
                y="Nota_Final",
                hue="Nome",
                style="Nome",
                markers=True,
                dashes=False,
                markersize=9,
                linewidth=2.5,
                ax=ax2
            )
            ax2.set_ylim(0, 105)
            ax2.set_ylabel("Nota Final (0 a 100)")
            ax2.set_xlabel("Período Avaliado")
            ax2.legend(title="Estudante", bbox_to_anchor=(1.05, 1), loc='upper left')
            st.pyplot(fig2)
            
        st.divider()

        # ----------------------------------------------------------------------
        # SEÇÃO 3: NOVA FERRAMENTA - ANÁLISE TEMPORAL POR ALUNO E HABILIDADES
        # ----------------------------------------------------------------------
        st.subheader("🧩 3. Diagnóstico Individual de Habilidades BNCC ao Longo do Ano")
        st.info("Visualize o histórico exato de acertos e erros de um aluno em cada habilidade da BNCC.")
        
        aluno_foco = st.selectbox("Selecione o Aluno para a Análise Detalhada:", alunos_disponiveis)
        
        if aluno_foco:
            df_aluno_foco = df_tudo[df_tudo["Nome"] == aluno_foco].copy()
            
            # Reorganiza os dados para montar a matriz de Habilidades x Período
            registros_hab = []
            for _, row in df_aluno_foco.iterrows():
                for q_code, info in config.items():
                    col_acerto = f"Acerto_{q_code}"
                    if col_acerto in row:
                        registros_hab.append({
                            "Habilidade BNCC": f"{q_code} - {info['habilidade']}",
                            "Avaliacao": row["Avaliacao"],
                            "Acertou": row[col_acerto]
                        })
            
            df_matriz_aluno = pd.DataFrame(registros_hab)
            
            if not df_matriz_aluno.empty:
                # Cria a tabela pivô (1 = Acertou, 0 = Errou)
                pivot_aluno = df_matriz_aluno.pivot_table(
                    index="Habilidade BNCC",
                    columns="Avaliacao",
                    values="Acertou",
                    aggfunc="first"
                )
                
                # Desenha o Mapa de Calor (Heatmap)
                fig3, ax3 = plt.subplots(figsize=(10, 6))
                sns.heatmap(
                    pivot_aluno,
                    annot=True,
                    cmap="YlGn", # Amarelo (0/Errou) a Verde Escuro (1/Acertou)
                    cbar=False,
                    linewidths=1.5,
                    linecolor="white",
                    fmt="g",
                    ax=ax3
                )
                
                ax3.set_title(f"Evolução das Habilidades BNCC: {aluno_foco}", fontsize=13, fontweight="bold")
                ax3.set_xlabel("Período Avaliado", fontsize=11)
                ax3.set_ylabel("Habilidade BNCC", fontsize=11)
                
                st.pyplot(fig3)
                
                st.caption("🟢 **1** = Estudante demonstrou domínio da habilidade | 🟡 **0** = Estudante apresentou defasagem na avaliação.")

    else:
        st.warning("Faça o upload dos arquivos CSV na Aba 2 para habilitar a análise temporal.")
