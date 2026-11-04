import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import re

st.set_page_config(page_title="Painel de Diagnóstico BNCC & Gestão Escolar", layout="wide")

# ------------------------------------------------------------------------------
# SISTEMA DE LOGIN
# ------------------------------------------------------------------------------
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Acesso ao Painel BNCC")
        
        caminho_imagem = "IMG-20260822-WA0016.jpg"
        if os.path.exists(caminho_imagem):
            st.image(caminho_imagem, use_container_width=True)
        else:
            st.warning("Imagem de login não encontrada no caminho especificado.")
        
        with st.form("form_login"):
            usuario = st.text_input("Usuário:", placeholder="coordenador ou professor")
            senha = st.text_input("Senha:", type="password", placeholder="123456")
            botao_entrar = st.form_submit_button("Entrar")
            
            if botao_entrar:
                usuario_limpo = usuario.strip().lower()
                if usuario_limpo in ["coordenador", "professor"] and senha == "123456":
                    st.session_state["autenticado"] = True
                    st.success("Acesso concedido!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos. Tente novamente.")
    st.stop()

if st.sidebar.button("🚪 Sair / Fazer Logout"):
    st.session_state["autenticado"] = False
    st.rerun()

st.title("📊 Painel de Avaliação, Diagnóstico BNCC e Frequência")
st.markdown("Acompanhamento longitudinal de turmas (7º A ao 7º E) com Diário de Classe Permanente.")

# ------------------------------------------------------------------------------
# LISTA DE HABILIDADES BNCC
# ------------------------------------------------------------------------------
LISTA_HABILIDADES_BNCC = [
    "EF07LP01 - Distinguir fatos de opiniões",
    "EF07LP02 - Analisar estrutura de textos jornalísticos",
    "EF07LP09 - Leitura e interpretação textual",
    "EF07LP10 - Identificar mecanismos de coesão",
    "EF07LP11 - Identificar gêneros textuais",
    "EF07LP12 - Reconhecer classes gramaticais e morfologia",
    "EF07LP13 - Analisar estrutura sintática",
    "EF07LP14 - Empregar pontuação adequadamente",
    "EF07LP15 - Aplicar regras ortográficas",
    "EF07LP16 - Reconhecer variações linguísticas",
    "EF07GE01 - Avaliar a influência da migração na formação territorial",
    "EF07GE02 - Analisar a diversidade socioespacial brasileira",
    "EF07GE03 - Identificar aspectos populacionais do Brasil",
    "EF07GE04 - Analisar a distribuição e dinâmica da população",
    "EF07GE06 - Comparar características dos biomas brasileiros",
    "EF07GE09 - Interpretar mapas temáticos e anamorfoses",
    "EF07GE11 - Caracterizar os domínios morphoclimáticos"
]

periodos_padrao = ["TRIMESTRE_1", "TRIMESTRE_2", "TRIMESTRE_3", "FINAL"]

if "gabaritos_por_prova" not in st.session_state:
    st.session_state["gabaritos_por_prova"] = {
        periodo: {
            f"Q{i}": {
                "resposta": "A",
                "habilidade": LISTA_HABILIDADES_BNCC[(i - 1) % len(LISTA_HABILIDADES_BNCC)]
            } for i in range(1, 11)
        } for periodo in periodos_padrao
    }

aba_config, aba_upload, aba_relatorio, aba_frequencia = st.tabs([
    "1. Configurar Gabaritos & Habilidades",
    "2. Enviar CSVs & Auditoria das Turmas",
    "3. Análise Temporal & Diagnóstico",
    "4. Diário de Classe & Frequência"
])

# ------------------------------------------------------------------------------
# ABA 1: CONFIGURAÇÃO DE GABARITOS
# ------------------------------------------------------------------------------
with aba_config:
    st.header("1. Configuração Dinâmica por Avaliação")

    prova_selecionada = st.selectbox(
        "Selecione a Avaliação para Configurar:",
        options=periodos_padrao,
        key="seletor_prova_config"
    )

    st.subheader(f"📝 Configuração de Gabarito para: {prova_selecionada}")

    gabarito_atual = st.session_state["gabaritos_por_prova"][prova_selecionada]
    config_temp = {}
    cols = st.columns(2)

    for i in range(1, 11):
        q_code = f"Q{i}"
        dados_q = gabarito_atual[q_code]

        with cols[0 if i <= 5 else 1]:
            st.markdown(f"### Questão {i}")

            resp = st.selectbox(
                f"Gabarito {q_code}:",
                ['A', 'B', 'C', 'D'],
                index=['A', 'B', 'C', 'D'].index(dados_q["resposta"]),
                key=f"resp_{prova_selecionada}_{q_code}"
            )

            hab_salva = dados_q["habilidade"]
            index_hab = 0
            if hab_salva in LISTA_HABILIDADES_BNCC:
                index_hab = LISTA_HABILIDADES_BNCC.index(hab_salva)

            hab_selecionada = st.selectbox(
                f"Selecione a Habilidade BNCC para {q_code}:",
                options=LISTA_HABILIDADES_BNCC,
                index=index_hab,
                key=f"select_hab_{prova_selecionada}_{q_code}"
            )

            hab_custom = st.text_input(
                f"Ou digite/edite a Habilidade para {q_code}:",
                value=hab_selecionada,
                key=f"custom_hab_{prova_selecionada}_{q_code}"
            )

            config_temp[q_code] = {"resposta": resp, "habilidade": hab_custom}
            st.divider()

    st.session_state["gabaritos_por_prova"][prova_selecionada] = config_temp
    st.success(f"✅ Gabarito e Habilidades de **{prova_selecionada}** salvos!")

# ------------------------------------------------------------------------------
# ABA 2: UPLOAD E AUDITORIA DE TURMAS
# ------------------------------------------------------------------------------
with aba_upload:
    st.header("2. Upload & Validação das Turmas (7º A ao 7º E)")
    st.info("Envie os CSVs contendo as respostas dos alunos coletadas via Google Forms.")

    arquivos_upload = st.file_uploader(
        "Selecione os arquivos CSV de avaliação:",
        type=["csv"],
        accept_multiple_files=True
    )

    if arquivos_upload:
        lista_dfs = []
        for arquivo in arquivos_upload:
            df_temp = pd.read_csv(arquivo)

            nome_limpo = arquivo.name.upper().replace("AVALIACAO_PORTUGUES_", "").replace("_2023.CSV", "").replace(".CSV", "")

            if "TRIMESTRE_1" in nome_limpo:
                periodo_chave = "TRIMESTRE_1"
            elif "TRIMESTRE_2" in nome_limpo:
                periodo_chave = "TRIMESTRE_2"
            elif "TRIMESTRE_3" in nome_limpo:
                periodo_chave = "TRIMESTRE_3"
            elif "FINAL" in nome_limpo:
                periodo_chave = "FINAL"
            else:
                periodo_chave = nome_limpo

            df_temp["Avaliacao"] = periodo_chave

            if "Email" in df_temp.columns:
                df_temp["Email"] = df_temp["Email"].astype(str).str.strip().str.lower()
                df_temp = df_temp[~df_temp["Email"].str.contains("gabarito")].copy()

            if "Nome" in df_temp.columns:
                df_temp["Nome"] = df_temp["Nome"].astype(str).str.strip().str.title()

            for col_turma in ["Serie", "Série", "Turma", "Grade"]:
                if col_turma in df_temp.columns:
                    df_temp["Turma_Formatada"] = df_temp[col_turma].astype(str).str.strip().str.upper()
                    break
            if "Turma_Formatada" not in df_temp.columns:
                df_temp["Turma_Formatada"] = "GERAL"

            lista_dfs.append(df_temp)

        df_historico_completo = pd.concat(lista_dfs, ignore_index=True)
        st.session_state["df_historico_completo"] = df_historico_completo

        st.success(f"✅ {len(arquivos_upload)} arquivos consolidados com sucesso! Total de {len(df_historico_completo)} respostas processadas.")

        st.divider()

        st.subheader("📊 Resumo de Participação por Turma")

        df_participacao = df_historico_completo.groupby(["Turma_Formatada", "Email", "Nome"])["Avaliacao"].nunique().reset_index()
        df_participacao.rename(columns={"Avaliacao": "Total_Provas_Feitas"}, inplace=True)

        turmas_detectadas = sorted(df_participacao["Turma_Formatada"].unique())

        cols_metrics = st.columns(len(turmas_detectadas) if len(turmas_detectadas) <= 5 else 5)
        for idx, turma_nome in enumerate(turmas_detectadas):
            df_t = df_participacao[df_participacao["Turma_Formatada"] == turma_nome]
            with cols_metrics[idx % 5]:
                st.metric(f"Turma {turma_nome}", f"{len(df_t)} Alunos")

        st.dataframe(df_participacao.sort_values(["Turma_Formatada", "Nome"]), use_container_width=True)

# ------------------------------------------------------------------------------
# ABA 3: RELATÓRIOS E DIAGNÓSTICO (SINALIZAÇÃO VISUAL DE FREQUÊNCIA)
# ------------------------------------------------------------------------------
with aba_relatorio:
    st.header("3. Análise Longitudinal & Diagnóstico de Desempenho")

    if "df_historico_completo" in st.session_state and "gabaritos_por_prova" in st.session_state:
        df_tudo = st.session_state["df_historico_completo"].copy()
        todos_gabaritos = st.session_state["gabaritos_por_prova"]

        lista_dfs_processados = []
        for periodo, df_periodo in df_tudo.groupby("Avaliacao"):
            df_p = df_periodo.copy()
            gabarito_especifico = todos_gabaritos.get(periodo, todos_gabaritos.get("TRIMESTRE_1"))

            colunas_acerto_p = []
            for q_code, info in gabarito_especifico.items():
                if q_code in df_p.columns:
                    col_acerto = f"Acerto_{q_code}"
                    df_p[col_acerto] = (
                        df_p[q_code].astype(str).str[0].str.upper() == info["resposta"].upper()
                    ).astype(int)
                    colunas_acerto_p.append(col_acerto)

            df_p["Nota_Final"] = df_p[colunas_acerto_p].sum(axis=1) * 10
            lista_dfs_processados.append(df_p)

        df_tudo = pd.concat(lista_dfs_processados, ignore_index=True)
        ordem_periodos = ["TRIMESTRE_1", "TRIMESTRE_2", "TRIMESTRE_3", "FINAL"]
        df_tudo["Avaliacao"] = pd.Categorical(df_tudo["Avaliacao"], categories=ordem_periodos, ordered=True)
        df_tudo = df_tudo.sort_values("Avaliacao")

        st.sidebar.header("🎯 Filtros de Visualização")

        turmas_unicas = ["Todas as Turmas (Comparativo)"] + sorted(df_tudo["Turma_Formatada"].dropna().unique().tolist())
        turma_selecionada = st.sidebar.selectbox("Selecione a Turma para analisar:", turmas_unicas)

        if turma_selecionada != "Todas as Turmas (Comparativo)":
            df_filtrado_turma = df_tudo[df_tudo["Turma_Formatada"] == turma_selecionada].copy()
        else:
            df_filtrado_turma = df_tudo.copy()

        # ----------------------------------------------------------------------
        # MONITORAMENTO DE FREQUÊNCIA COM DESTAQUES EM VERMELHO E AMARELO
        # ----------------------------------------------------------------------
        st.subheader("🚨 Diagnóstico de Frequência & Alertas de Infrequência")
        
        if "df_frequencia_acumulada" in st.session_state:
            df_freq_status = st.session_state["df_frequencia_acumulada"]
            
            if turma_selecionada != "Todas as Turmas (Comparativo)":
                df_freq_status = df_freq_status[df_freq_status["Turma"] == turma_selecionada]

            def destacar_frequencia(val):
                if "🔴" in str(val) or ">= 35%" in str(val) or "Crítico" in str(val):
                    return 'background-color: #ffcccc; color: #990000; font-weight: bold;'
                elif "🟡" in str(val) or "Atenção" in str(val) or "25%" in str(val):
                    return 'background-color: #fff2cc; color: #856404; font-weight: bold;'
                elif "🟢" in str(val):
                    return 'background-color: #d4edda; color: #155724;'
                return ''

            st.dataframe(
                df_freq_status.style.applymap(destacar_frequencia, subset=["Status"]),
                use_container_width=True
            )
        else:
            st.info("ℹ️ Salve a chamada na Aba 4 para visualizar aqui os alertas de infrequência destacados em Amarelo (25% - 35%) e Vermelho (≥ 35%).")

        st.divider()

        # ----------------------------------------------------------------------
        # SEÇÃO 1: EVOLUÇÃO DA MÉDIA DA TURMA
        # ----------------------------------------------------------------------
        st.subheader(f"📈 1. Evolução da Média da Turma: {turma_selecionada}")

        fig1, ax1 = plt.subplots(figsize=(10, 3.5))

        if turma_selecionada == "Todas as Turmas (Comparativo)":
            df_media_turmas = df_tudo.groupby(["Avaliacao", "Turma_Formatada"], observed=False)["Nota_Final"].mean().reset_index()
            sns.lineplot(
                data=df_media_turmas,
                x="Avaliac
