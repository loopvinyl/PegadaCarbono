import streamlit as st
import requests
import yfinance as yf
import numpy as np
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Calculadora de Pegada de Carbono",
    page_icon="🌍",
    layout="centered"
)

# ============================================
# FUNÇÕES DE COTAÇÃO EM TEMPO REAL
# ============================================

def obter_cotacao_carbono():
    """Obtém a cotação do carbono via Yahoo Finance (ticker CO2.L)."""
    try:
        ticker = yf.Ticker("CO2.L")
        data = ticker.history(period="1d")
        if not data.empty:
            preco = data['Close'].iloc[-1]
            # Validação básica: preço entre 10 e 200 euros
            if 10 < preco < 200:
                return preco, "€", "Carbon Futures (CO2.L)", True, "Yahoo Finance (CO2.L)"
        return 85.50, "€", "Carbon Emissions (Referência)", False, "Referência"
    except Exception:
        return 85.50, "€", "Carbon Emissions (Referência)", False, "Referência"

def obter_cotacao_euro_real():
    """Obtém a cotação EUR/BRL usando API AwesomeAPI ou fallback."""
    try:
        url = "https://economia.awesomeapi.com.br/last/EUR-BRL"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return float(data['EURBRL']['bid']), "R$", True, "AwesomeAPI"
    except:
        pass
    try:
        url = "https://api.exchangerate-api.com/v4/latest/EUR"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data['rates']['BRL'], "R$", True, "ExchangeRate-API"
    except:
        pass
    return 5.50, "R$", False, "Referência"

def inicializar_cotacoes():
    """Inicializa as variáveis de cotação no session_state."""
    if 'preco_carbono' not in st.session_state:
        preco, moeda, nome, ok, fonte = obter_cotacao_carbono()
        st.session_state.preco_carbono = preco
        st.session_state.moeda_carbono = moeda
        st.session_state.fonte_carbono = fonte
    if 'taxa_cambio' not in st.session_state:
        taxa, moeda_real, ok, fonte = obter_cotacao_euro_real()
        st.session_state.taxa_cambio = taxa
        st.session_state.moeda_real = moeda_real
        st.session_state.fonte_cambio = fonte
    if 'cotacao_atualizada' not in st.session_state:
        st.session_state.cotacao_atualizada = False

# Inicializa cotações
inicializar_cotacoes()

# ============================================
# FUNÇÕES DE CÁLCULO DA PEGADA
# ============================================

def calcular_pegada_gas(m3_gas):
    """Retorna (total_tco2e, detalhes_dict) para gás natural (combustão estacionária)."""
    pci = 0.0000386          # TJ/m³
    consumo_tj = m3_gas * pci

    # Fatores de emissão (t/TJ) – Tabela 2.4 IPCC
    fe_co2 = 56.1    # t CO₂/TJ
    fe_ch4 = 0.005   # t CH₄/TJ
    fe_n2o = 0.0001  # t N₂O/TJ

    # Massa emitida (t)
    m_co2 = consumo_tj * fe_co2
    m_ch4 = consumo_tj * fe_ch4
    m_n2o = consumo_tj * fe_n2o

    # GWP AR6 (20 anos)
    gwp_co2 = 1
    gwp_ch4 = 82.5
    gwp_n2o = 273

    co2e_co2 = m_co2 * gwp_co2
    co2e_ch4 = m_ch4 * gwp_ch4
    co2e_n2o = m_n2o * gwp_n2o

    total = co2e_co2 + co2e_ch4 + co2e_n2o

    detalhes = {
        "Consumo (m³)": m3_gas,
        "Energia (TJ)": consumo_tj,
        "CO₂ (t)": m_co2,
        "CH₄ (t)": m_ch4,
        "N₂O (t)": m_n2o,
        "CO₂e CO₂": co2e_co2,
        "CO₂e CH₄": co2e_ch4,
        "CO₂e N₂O": co2e_n2o,
        "Total (tCO₂e)": total
    }
    return total, detalhes

def calcular_pegada_diesel(litros_diesel):
    """Retorna (total_tco2e, detalhes_dict) para diesel S10 (combustão móvel)."""
    densidade = 0.84          # kg/L
    massa_kg = litros_diesel * densidade
    massa_t = massa_kg / 1000

    pci = 0.043               # TJ/t
    consumo_tj = massa_t * pci

    # Fatores de emissão (t/TJ) – Tabelas 3.2.1 e 3.2.2 (Mobile Combustion)
    fe_co2 = 74.1    # t CO₂/TJ
    fe_ch4 = 0.0039  # t CH₄/TJ
    fe_n2o = 0.0039  # t N₂O/TJ

    m_co2 = consumo_tj * fe_co2
    m_ch4 = consumo_tj * fe_ch4
    m_n2o = consumo_tj * fe_n2o

    gwp_co2 = 1
    gwp_ch4 = 82.5
    gwp_n2o = 273

    co2e_co2 = m_co2 * gwp_co2
    co2e_ch4 = m_ch4 * gwp_ch4
    co2e_n2o = m_n2o * gwp_n2o

    total = co2e_co2 + co2e_ch4 + co2e_n2o

    detalhes = {
        "Diesel (L)": litros_diesel,
        "Massa (t)": massa_t,
        "Energia (TJ)": consumo_tj,
        "CO₂ (t)": m_co2,
        "CH₄ (t)": m_ch4,
        "N₂O (t)": m_n2o,
        "CO₂e CO₂": co2e_co2,
        "CO₂e CH₄": co2e_ch4,
        "CO₂e N₂O": co2e_n2o,
        "Total (tCO₂e)": total
    }
    return total, detalhes

def formatar_br(numero):
    """Formata número no padrão brasileiro (ponto milhar, vírgula decimal)."""
    if pd.isna(numero):
        return "N/A"
    numero = round(numero, 2)
    return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ============================================
# BARRA LATERAL COM COTAÇÕES EM TEMPO REAL
# ============================================

with st.sidebar:
    st.header("💰 Mercado de Carbono e Câmbio")

    # Botão para atualizar cotações manualmente
    if st.button("🔄 Atualizar Cotações", key="atualizar"):
        with st.spinner("Obtendo cotações..."):
            preco, moeda, _, _, fonte = obter_cotacao_carbono()
            st.session_state.preco_carbono = preco
            st.session_state.moeda_carbono = moeda
            st.session_state.fonte_carbono = fonte
            taxa, moeda_real, _, fonte_cambio = obter_cotacao_euro_real()
            st.session_state.taxa_cambio = taxa
            st.session_state.moeda_real = moeda_real
            st.session_state.fonte_cambio = fonte_cambio
            st.session_state.cotacao_atualizada = True
            st.rerun()

    # Exibe as cotações atuais
    st.metric(
        label="Preço do Carbono (tCO₂e)",
        value=f"{st.session_state.moeda_carbono} {formatar_br(st.session_state.preco_carbono)}",
        help=f"Fonte: {st.session_state.fonte_carbono}"
    )
    st.metric(
        label="Euro (EUR/BRL)",
        value=f"{st.session_state.moeda_real} {formatar_br(st.session_state.taxa_cambio)}",
        help=f"Fonte: {st.session_state.fonte_cambio}"
    )
    preco_carbono_reais = st.session_state.preco_carbono * st.session_state.taxa_cambio
    st.metric(
        label="Carbono em Reais (tCO₂e)",
        value=f"R$ {formatar_br(preco_carbono_reais)}",
        help="Preço do carbono convertido para Reais Brasileiros"
    )

    with st.expander("ℹ️ Sobre as cotações"):
        st.markdown("""
        **📊 Fontes:**
        - **Carbono:** Futuros da ICE (CO2.L) – EU ETS
        - **Euro:** API AwesomeAPI / ExchangeRate-API
        - Valores são atualizados automaticamente ao abrir o app.
        - Clique em "Atualizar Cotações" para obter o último preço.
        - Em caso de falha, são usados valores de referência (€85,50 e R$5,50).
        """)

# ============================================
# TÍTULO PRINCIPAL
# ============================================

st.title("🌍 Pegada de Carbono")
st.subheader("Em busca da neutralidade corporativa")
st.markdown("Baseado na apresentação de Cássio Luiz Vellani | Fatores IPCC AR6 e metodologia 2006 GL")
st.markdown("---")

# ============================================
# INTERFACE DE CÁLCULO (abas)
# ============================================

tab1, tab2 = st.tabs(["⚡ Energia (Gás Natural)", "🚛 Transporte (Diesel S10)"])

with tab1:
    st.header("Exemplo prático 1 – Combustão estacionária")
    st.markdown("Usina termelétrica ou caldeira industrial a gás natural.")

    m3 = st.number_input("Consumo de gás natural (m³)", min_value=0.0, value=50000.0, step=1000.0, format="%.0f", key="gas")
    if st.button("Calcular pegada (gás)", key="btn_gas"):
        if m3 > 0:
            total, detalhes = calcular_pegada_gas(m3)
            st.success(f"🌿 Pegada de carbono total: **{formatar_br(total)} tCO₂e**")
            with st.expander("📊 Ver detalhes do cálculo"):
                # Converte os números para formato brasileiro
                detalhes_formatados = {k: formatar_br(v) if isinstance(v, (int, float)) else v for k, v in detalhes.items()}
                st.json(detalhes_formatados)
            # Custo de neutralização com cotações em tempo real
            preco_eur = st.session_state.preco_carbono
            taxa = st.session_state.taxa_cambio
            custo_eur = total * preco_eur
            custo_brl = custo_eur * taxa
            st.info(f"💶 Custo para neutralizar: **€ {formatar_br(custo_eur)}**  |  **R$ {formatar_br(custo_brl)}**")
            st.caption(f"Preço do carbono usado: € {formatar_br(preco_eur)}/tCO₂e | Euro = R$ {formatar_br(taxa)}")
        else:
            st.warning("Digite um consumo válido.")

with tab2:
    st.header("Exemplo prático 2 – Combustão móvel")
    st.markdown("Frota de caminhões rodando com diesel S10.")

    litros = st.number_input("Consumo de diesel S10 (litros)", min_value=0.0, value=30000.0, step=1000.0, format="%.0f", key="diesel")
    if st.button("Calcular pegada (diesel)", key="btn_diesel"):
        if litros > 0:
            total, detalhes = calcular_pegada_diesel(litros)
            st.success(f"🌿 Pegada de carbono total: **{formatar_br(total)} tCO₂e**")
            with st.expander("📊 Ver detalhes do cálculo"):
                detalhes_formatados = {k: formatar_br(v) if isinstance(v, (int, float)) else v for k, v in detalhes.items()}
                st.json(detalhes_formatados)
            preco_eur = st.session_state.preco_carbono
            taxa = st.session_state.taxa_cambio
            custo_eur = total * preco_eur
            custo_brl = custo_eur * taxa
            st.info(f"💶 Custo para neutralizar: **€ {formatar_br(custo_eur)}**  |  **R$ {formatar_br(custo_brl)}**")
            st.caption(f"Preço do carbono usado: € {formatar_br(preco_eur)}/tCO₂e | Euro = R$ {formatar_br(taxa)}")
        else:
            st.warning("Digite um consumo válido.")

st.markdown("---")
st.caption("Nota: Os fatores de emissão e GWP (20 anos) seguem o IPCC AR6 (2021) e as diretrizes IPCC 2006. As cotações são obtidas em tempo real via Yahoo Finance (CO2.L) e APIs de câmbio.")
