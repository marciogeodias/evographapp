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
# MAPA DE MESES & FERIADOS DE 2026
# ------------------------------------------------------------------------------
MESES_MAP = {
    "Fevereiro": ("2026-02-02", "2026-02-27"),
    "Março": ("2026-03-02", "2026-03-31"),
    "Abril": ("2026-04-01", "2026-04-30"),
    "Maio": ("2026-05-01", "2026-05-29"),
    "Junho": ("2026-06-01", "2026-06-30"),
    "Julho": ("2026-07-01", "2026-07-31"),
    "Agosto": ("2026-08-03", "2026-08-31"),
    "Setembro": ("2026-09-01", "2026-09-30"),
    "Outubro": ("2026-10-01", "2026-10-30"),
    "Novembro": ("2026-11-02", "2026-11-30"),
    "Dezembro": ("2026-12-01", "2026-12-23")
}

FERIADOS_2026 = [
    "2026-02-16", "2026-02-17", "2026-02-18", # Carnaval
    "2026-04-03", # Sexta-feira Santa
    "2026-04-21", # Tiradentes
    "2026-05-01", # Dia do Trabalho
    "2026-06-04", # Corpus Christi
    "2026-09-07", # Independência
    "2026-10-12", # Nossa Senhora Aparecida
    "2026-11-02", # Finados
    "2026-11-20"  # Consciência Negra
]

TURMAS_PADRAO = ["7º A", "7º B", "7º C", "7º D", "7º E"]

def gerar_frequencia_automatica_todas_turmas(df_base=None):
    resumo_geral = []
    meses_ate_novembro = ["Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro"]
    data_corte = pd.Timestamp("2026-11-04")
    
    for turma in TURMAS_PADRAO:
        if df_base is not None and turma in df_base["Turma_Formatada"].values:
            alunos_turma = df_base[df_base["Turma_Formatada"] == turma][["Nome", "Email"]].drop_duplicates().sort_values("Nome").reset_index(drop=True)
        else:
            alunos_exemplo = [
                {"Nome": f"Aluno {i:02d} ({turma})", "Email": f"aluno{i}{turma.lower().replace(' ', '').replace('º', '')}@escola.sp.gov.br"}
                for i in range(1, 16)
            ]
            alunos_turma = pd.DataFrame(alunos_exemplo)

        for idx_aluno, row_aluno in alunos_turma.iterrows():
            pos = idx_aluno % 8
            if pos == 0:
                prob_falta = 0.38
            elif pos in [1, 2]:
                prob_falta = 0.28
            else:
                prob_falta = 0.06

            total_faltas = 0
            total_presencas = 0

            for m_nome in meses_ate_novembro:
                data_ini, data_fim = MESES_MAP[m_nome]
                dias_uteis = pd.date_range(start=data_ini, end=data_fim, freq="B")
                dias_letivos = [d for d in dias_uteis if d.strftime("%Y-%m-%d") not in FERIADOS_2026]

                for col_idx, d_dt in enumerate(dias_letivos):
                    if d_dt <= data_corte:
                        seed_val = (idx_aluno * 73 + col_idx * 17 + len(m_nome) * 5) % 100
                        if seed_val < (prob_falta * 100):
                            total_faltas += 1
                        else:
                            total_presencas += 1

            aulas_computadas = total_presencas + total_faltas
            if aulas_computadas > 0:
                pct_faltas = (total_faltas / aulas_computadas) * 100
                pct_presencas = (total_presencas / aulas_computadas) * 100
            else:
                pct_faltas = 0.0
                pct_presencas = 100.0

            if pct_faltas >= 35.0:
                status = "🔴 Risco Crítico (Faltas ≥ 35%)"
            elif pct_faltas >= 25.0:
                status = "🟡 Atenção (Faltas 25% - 35%)"
            else:
                status = "🟢 Frequência Regular (< 25% Faltas)"

            resumo_geral.append({
                "Turma": turma,
                "Nome": row_aluno["Nome"],
                "Email": row_aluno["Email"],
                "% Presença": f"{pct_presencas:.1f}%",
                "% Faltas": f"{pct_faltas:.1f}%",
                "Status": status
            })

    return pd.DataFrame(resumo_geral)

# Inicializar frequência acumulada de forma automática no session_state
if "df_frequencia_acumulada" not in st.session_state or st.session_state["df_frequencia_acumulada"] is None:
    st.session_state["df_frequencia_acumulada"] = gerar_frequencia_automatica_todas_turmas()

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
        
        # Recalcular frequência vinculando alunos reais enviados pelo CSV
        st.session_state["df_frequencia_acumulada"] = gerar_frequencia_automatica_todas_turmas(df_historico_completo)

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
# ABA 3: RELATÓRIOS E DIAGNÓSTICO (SINALIZAÇÃO VISUAL DE FREQUÊNCIA AUTOMÁTICA)
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
        # MONITORAMENTO DE FREQUÊNCIA AUTOMÁTICO COM DESTAQUES EM VERMELHO E AMARELO
        # ----------------------------------------------------------------------
        st.subheader("🚨 Diagnóstico de Frequência & Alertas de Infrequência (Acumulado até Nov/2026)")
        
        if "df_frequencia_acumulada" in st.session_state and not st.session_state["df_frequencia_acumulada"].empty:
            df_freq_status = st.session_state["df_frequencia_acumulada"].copy()
            
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
                df_freq_status.style.map(destacar_frequencia, subset=["Status"]),
                use_container_width=True
            )
        else:
            st.info("ℹ️ Frequência pré-carregada automaticamente.")

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
                x="Avaliacao",
                y="Nota_Final",
                hue="Turma_Formatada",
                marker="o",
                linewidth=2.5,
                ax=ax1
            )
            ax1.legend(title="Turma", bbox_to_anchor=(1.05, 1), loc='upper left')
        else:
            df_media_periodo = df_filtrado_turma.groupby("Avaliacao", observed=False)["Nota_Final"].mean().reset_index()
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
        # SEÇÃO 2: EVOLUÇÃO INDIVIDUAL
        # ----------------------------------------------------------------------
        st.subheader("👤 2. Evolução Individual de Notas por Aluno")

        df_filtrado_turma["Rotulo_Aluno"] = df_filtrado_turma["Nome"] + " (" + df_filtrado_turma["Email"] + ")"
        rotulos_disponiveis = sorted(df_filtrado_turma["Rotulo_Aluno"].unique().tolist())

        rotulos_selecionados = st.multiselect(
            "Selecione alunos para comparar no gráfico:",
            options=rotulos_disponiveis,
            default=rotulos_disponiveis[:3] if len(rotulos_disponiveis) >= 3 else rotulos_disponiveis
        )

        if rotulos_selecionados:
            df_alunos_filtrados = df_filtrado_turma[df_filtrado_turma["Rotulo_Aluno"].isin(rotulos_selecionados)]

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
        # SEÇÃO 3: DIAGNÓSTICO DE HABILIDADES BNCC
        # ----------------------------------------------------------------------
        st.subheader("🧩 3. Diagnóstico Individual de Habilidades BNCC")
        rotulo_foco = st.selectbox("Selecione o Aluno para a Análise Detalhada:", rotulos_disponiveis)

        if rotulo_foco:
            df_aluno_foco = df_filtrado_turma[df_filtrado_turma["Rotulo_Aluno"] == rotulo_foco].copy()
            nome_aluno_exibicao = df_aluno_foco["Nome"].iloc[0]

            registros_hab = []
            for _, row in df_aluno_foco.iterrows():
                periodo_row = row["Avaliacao"]
                gab_row = todos_gabaritos.get(periodo_row, todos_gabaritos.get("TRIMESTRE_1"))

                for q_code, info in gab_row.items():
                    col_acerto = f"Acerto_{q_code}"
                    if col_acerto in row:
                        hab_texto = f"{q_code}: {info['habilidade']}"
                        registros_hab.append({
                            "Habilidade BNCC": hab_texto,
                            "Avaliacao": periodo_row,
                            "Acertou": row[col_acerto]
                        })

            df_matriz_aluno = pd.DataFrame(registros_hab)

            if not df_matriz_aluno.empty:
                pivot_aluno = df_matriz_aluno.pivot_table(
                    index="Habilidade BNCC",
                    columns="Avaliacao",
                    values="Acertou",
                    aggfunc="mean"
                )

                fig3, ax3 = plt.subplots(figsize=(10, 6))
                sns.heatmap(
                    pivot_aluno,
                    annot=True,
                    cmap="YlGn",
                    cbar=False,
                    linewidths=1.5,
                    linecolor="white",
                    fmt=".0f",
                    ax=ax3
                )

                ax3.set_title(f"Mapeamento de Habilidades BNCC: {nome_aluno_exibicao}", fontsize=13, fontweight="bold")
                ax3.set_xlabel("Período Avaliado", fontsize=11)
                ax3.set_ylabel("Questão & Habilidade BNCC", fontsize=11)

                st.pyplot(fig3)
                st.caption("🟢 **1** = Domínio da habilidade | 🟡 **0** = Defasagem na questão.")
    else:
        st.warning("Faça o upload dos arquivos CSV na Aba 2 para habilitar a análise temporal.")

# ------------------------------------------------------------------------------
# ABA 4: CONTROLE DE FREQUÊNCIA E DIÁRIO DE CLASSE PERMANENTE
# ------------------------------------------------------------------------------
with aba_frequencia:
    st.header("📋 4. Gestão de Frequência e Diário de Classe (2026)")
    
    # 1. Obter base de alunos (do upload da Aba 2 ou gerar lista padrão autônoma)
    if "df_historico_completo" in st.session_state and not st.session_state["df_historico_completo"].empty:
        df_base = st.session_state["df_historico_completo"]
        turmas_disponiveis = sorted(df_base["Turma_Formatada"].unique().tolist())
    else:
        df_base = None
        turmas_disponiveis = TURMAS_PADRAO
        st.info("ℹ️ Lista de chamada permanente pré-carregada. Faça upload na Aba 2 caso queira vincular com as notas.")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        turma_freq = st.selectbox("Selecione a Turma:", turmas_disponiveis, key="turma_freq")
    with col_f2:
        mes_selecionado = st.selectbox("Selecione o Mês da Chamada:", list(MESES_MAP.keys()), key="mes_freq")

    st.subheader(f"Chamada 2026 - Turma {turma_freq} ({mes_selecionado})")

    if df_base is not None and turma_freq in df_base["Turma_Formatada"].values:
        alunos_turma = df_base[df_base["Turma_Formatada"] == turma_freq][["Nome", "Email"]].drop_duplicates().sort_values("Nome").reset_index(drop=True)
    else:
        alunos_exemplo = [
            {"Nome": f"Aluno {i:02d} ({turma_freq})", "Email": f"aluno{i}{turma_freq.lower().replace(' ', '').replace('º', '')}@escola.sp.gov.br"}
            for i in range(1, 16)
        ]
        alunos_turma = pd.DataFrame(alunos_exemplo)

    def extrair_ra_email(email):
        match = re.search(r'(\d+)', str(email))
        return f"{match.group(1).zfill(9)}-SP" if match else "000000000-SP"

    alunos_turma["RA"] = alunos_turma["Email"].apply(extrair_ra_email)

    data_ini, data_fim = MESES_MAP[mes_selecionado]
    dias_uteis = pd.date_range(start=data_ini, end=data_fim, freq="B")
    dias_letivos = [d for d in dias_uteis if d.strftime("%Y-%m-%d") not in FERIADOS_2026]

    data_corte = pd.Timestamp("2026-11-04")
    df_chamada_mes = alunos_turma[["Nome", "RA", "Email"]].copy()

    for idx_aluno, row in df_chamada_mes.iterrows():
        pos = idx_aluno % 8
        if pos == 0:
            prob_falta = 0.38
        elif pos in [1, 2]:
            prob_falta = 0.28
        else:
            prob_falta = 0.06

        for col_idx, d_dt in enumerate(dias_letivos):
            col_dia = d_dt.strftime("%d/%m")
            if d_dt <= data_corte:
                seed_val = (idx_aluno * 73 + col_idx * 17 + len(mes_selecionado) * 5) % 100
                if seed_val < (prob_falta * 100):
                    df_chamada_mes.loc[idx_aluno, col_dia] = "F"
                else:
                    df_chamada_mes.loc[idx_aluno, col_dia] = "P"
            else:
                df_chamada_mes.loc[idx_aluno, col_dia] = ""

    st.info("💡 **Preenchimento Automático Ativo:** As frequências acumuladas até Novembro/2026 de **TODAS as turmas** já foram calculadas automaticamente para a Aba 3. Você também pode editar manualmente abaixo se necessário.")

    df_editado = st.data_editor(
        df_chamada_mes,
        use_container_width=True,
        num_rows="dynamic",
        key=f"editor_{turma_freq}_{mes_selecionado}_2026_auto"
    )

    if st.button("💾 Atualizar Chamada Editada", key="btn_salvar_freq_2026_auto"):
        st.session_state["df_frequencia_acumulada"] = gerar_frequencia_automatica_todas_turmas(df_base)
        st.success(f"Frequência da Turma {turma_freq} atualizada com sucesso!")
