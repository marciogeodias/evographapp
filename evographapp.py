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
